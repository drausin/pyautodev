from typing import List, Optional, Tuple

from attr import dataclass
from pycodestyle import StyleGuide, BaseReport
from pyflakes.api import checkPath
from pyflakes.reporter import Reporter
from pylint import checkers
from pylint.lint import PyLinter
from pylint.message import Message as PyLintMessage
from pyflakes.messages import Message as PyFlakesMessage
from pylint.reporters import CollectingReporter


@dataclass
class Message:
    code: Optional[str]
    description: Optional[str]
    filepath: str
    line: Optional[int]
    column: Optional[int]

    def __str__(self):
        return ":".join(
            [
                self.filepath,
                str(self.line),
                str(self.column),
                self.code,
                self.description,
            ]
        )


class Checker:
    def check(self, filepaths: List[str]) -> List[Message]:
        raise NotImplementedError


class PyLint(Checker):
    def __init__(self, options: Optional[dict] = None):
        options = options or {}
        checker = PyLinter(reporter=CollectingReporter())
        checkers.initialize(checker)
        checker.disable("I")  # suppress info messages
        for k, v in options.items():
            checker.global_set_option(k, v)

        self._inner = checker

    def check(self, filepaths: List[str]) -> List[Message]:
        self._inner.check(filepaths)
        return [self._to_msg(m) for m in self._inner.reporter.messages]

    @staticmethod
    def _to_msg(m: PyLintMessage) -> Message:
        return Message(
            code=m.msg_id,
            description=m.symbol,
            filepath=m.abspath,
            line=m.line,
            column=m.column,
        )


class PyCodeStyle(Checker):
    def __init__(self, options: Optional[dict] = None):
        options = options or {}
        self._style = StyleGuide(
            select="E,W", reporter=PyCodeStyle.ErrorReport, **options
        )
        self._style.options.max_line_length = 88

    def check(self, filepaths: List[str]) -> List[Message]:
        report = self._style.check_files(filepaths)
        return [self._to_msg(e) for e in report.errors]

    @staticmethod
    def _to_msg(err: Tuple) -> Message:
        return Message(
            code=err[3], description=err[4], filepath=err[0], line=err[1], column=err[2]
        )

    class ErrorReport(BaseReport):
        def __init__(self, options):
            super().__init__(options)
            self.errors = []

        def error(self, line_number, offset, text, check):
            code = super().error(line_number, offset, text, check)
            if code:
                self.errors.append(
                    (self.filename, line_number, offset, code, text[5:], check.__doc__)
                )


class PyFlakes(Checker):
    def check(self, filepaths: List[str]) -> List[Message]:
        reporter = PyFlakes.CollectingReporter()
        for filepath in filepaths:
            checkPath(filepath, reporter=reporter)

        msgs = [self._error_to_msg(e) for e in reporter.errors]
        msgs.extend([self._flake_to_msg(f) for f in reporter.flakes])
        return msgs

    @staticmethod
    def _error_to_msg(err: Tuple) -> Message:
        m = Message(
            code=None, description=err[1], filepath=err[0], line=None, column=None
        )
        if len(err) > 2:
            m.line = err[2]
            m.column = err[3]

        return m

    @staticmethod
    def _flake_to_msg(m: PyFlakesMessage) -> Message:
        return Message(
            code=m.__class__.__name__,
            description=str(m),
            filepath=m.filename,
            line=m.lineno,
            column=m.col,
        )

    class CollectingReporter(Reporter):
        def __init__(self, warningStream=None, errorStream=None):
            super().__init__(warningStream, errorStream)
            self.errors = []
            self.flakes = []

        def unexpectedError(self, filepath, msg):
            self.errors.append((filepath, msg))

        def syntaxError(self, filepath, msg, lineno, offset, text):
            self.errors.append((filepath, msg, lineno, offset, text))

        def flake(self, message):
            self.flakes.append(message)
