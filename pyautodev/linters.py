from pylint import checkers
from pylint.lint import PyLinter
from typing import List

from pylint.message import Message
from pylint.reporters import CollectingReporter


class PyLint:

    def __init__(self, options: dict):
        linter = PyLinter(
            reporter=CollectingReporter(),
        )
        checkers.initialize(linter)
        linter.disable("I")  # suppress info messages
        for k, v in options.items():
            linter.global_set_option(k, v)

        self._inner = linter

    def check(self, filenames: List[str]) -> List[Message]:
        self._inner.check(filenames)
        return self._inner.reporter.messages
