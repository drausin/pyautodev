from typing import List

from checkers import PyLint, PyCodeStyle, PyFlakes
from transformers import Black


class Processor:

    def __init__(self):

        # checkers
        self.pylint = PyLint()
        self.pycodestyle = PyCodeStyle()
        self.pyflakes = PyFlakes()

        # transformers
        self.black = Black()

    def process(self, filepaths: List[str]):
        pylint_msgs = self.pylint.check(filepaths)
        pyflakes_msgs = self.pyflakes.check(filepaths)

        self.black.transform(filepaths)

        # black should (??) mean that we get few if any pycodestyle messages,
        # but run just to be sure
        pycodestyle_msgs = self.pycodestyle.check(filepaths)

        all_msgs = pylint_msgs + pyflakes_msgs + pycodestyle_msgs
        return all_msgs

