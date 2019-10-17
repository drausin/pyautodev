from typing import List, Optional

from pycodestyle import StyleGuide, BaseReport
from pylint import checkers
from pylint.lint import PyLinter
from pylint.message import Message
from pylint.reporters import CollectingReporter


class PyLint:
    def __init__(self, options: Optional[dict] = None):
        options = options or {}
        checker = PyLinter(reporter=CollectingReporter())
        checkers.initialize(checker)
        checker.disable("I")  # suppress info messages
        for k, v in options.items():
            checker.global_set_option(k, v)

        self._inner = checker

    def check(self, filenames: List[str]) -> List[Message]:
        self._inner.check(filenames)
        return self._inner.reporter.messages


class PyCodeStyle:
    def __init__(self, options: Optional[dict] = None):
        options = options or {}
        self._style = StyleGuide(
            select="E,W",
            reporter=PyCodeStyle.ErrorReport,
            **options
        )
        self._style.options.max_line_length = 88

    def check(self, filenames: List[str]):
        report = self._style.check_files(filenames)
        return report.errors

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
