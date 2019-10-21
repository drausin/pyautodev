from pathlib import Path
from typing import List

from black import reformat_one, FileMode, DEFAULT_LINE_LENGTH, Report, WriteBack, \
    Changed


class Black:
    def __init__(self):
        self._mode = FileMode.from_configuration(
            py36=False,
            pyi=False,
            skip_string_normalization=False,
            skip_numeric_underscore_normalization=False,
        )

    def transform(self, filepaths: List[str]):
        report = Black.CollectingReport()
        for filepath in filepaths:
            reformat_one(
                src=Path(filepath),
                line_length=DEFAULT_LINE_LENGTH,
                fast=False,
                write_back=WriteBack.YES,
                mode=self._mode,
                report=report,
            )
        return report

    class CollectingReport(Report):

        def __init__(self):
            self.done_paths_changed = {}
            self.failed_paths_msg = {}

        def done(self, src: Path, changed: Changed) -> None:
            self.done_paths_changed[src] = changed

        def failed(self, src: Path, message: str):
            self.failed_paths_msg[src] = message
