import re
from pathlib import Path
from typing import List, Sequence

import black
import libcst as cst

from black import reformat_one, FileMode, Report, WriteBack, Changed
from libcst import SimpleString, Comment, EmptyLine, CSTNodeT, Module
from libcst.metadata import BasicPositionProvider, WhitespaceInclusivePositionProvider

MAX_LINE_LENGTH = black.DEFAULT_LINE_LENGTH


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
                line_length=MAX_LINE_LENGTH,
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


class CommentWrap(cst.CSTTransformer):

    METADATA_DEPENDENCIES = (WhitespaceInclusivePositionProvider,)

    def __init__(self, max_line_length=MAX_LINE_LENGTH):
        super().__init__()
        self._max_line_length = max_line_length

    def leave_Module(
        self, original_node: Module, updated_node: Module
    ):
        orig_header = updated_node.header
        if orig_header:
            updated_node = updated_node.with_changes(
                header=self._wrap_leading_lines(orig_header)
            )

        return updated_node

    def on_leave(
        self, original_node: CSTNodeT, updated_node: CSTNodeT
    ):
        updated_node = super().on_leave(original_node, updated_node)
        orig_leading_lines = getattr(original_node, 'leading_lines', None)
        if orig_leading_lines:
            updated_node.leading_lines = self._wrap_leading_lines(orig_leading_lines)

        return updated_node

    def _wrap_leading_lines(self, orig: Sequence[EmptyLine]) -> Sequence[EmptyLine]:
        if len(orig) == 0:
            return orig

        wrapped, unwrapped = [], list(orig)

        wrapped_from_prev_line = ""
        start_col = 0
        while len(unwrapped) > 0:
            line = unwrapped.pop(0)
            comment = line.comment
            if not comment:
                wrapped.append(line)
                continue

            pos = self.get_metadata(WhitespaceInclusivePositionProvider, comment)
            start_col = pos.start.column
            if start_col > self._max_line_length:
                # not quite sure how to handle this yet, so fail and investigate
                raise ValueError(
                    f"unexpectedly have starting position {start_col} > "
                    f"{self._max_line_length} on line {pos.start.line}"
                )

            if (
                not wrapped_from_prev_line
                and start_col + len(comment.value) <= self._max_line_length
            ):
                # existing comment can stay as-is
                wrapped.append(line)
                continue

            updated_comment, wrapped_from_prev_line = self._get_next_comment(
                value=comment.value,
                wrapped_from_prev_line=wrapped_from_prev_line,
                start_col=start_col,
            )
            wrapped.append(line.with_changes(comment=updated_comment))

        # add additional comment lines for remainder, if needed
        while len(wrapped_from_prev_line) > 0:
            updated_comment, wrapped_from_prev_line = self._get_next_comment(
                value="",  # no existing comment
                wrapped_from_prev_line=wrapped_from_prev_line,
                start_col=start_col,
            )
            wrapped.append(EmptyLine(comment=updated_comment))

        return wrapped

    def _get_next_comment(self, value: str, wrapped_from_prev_line: str, start_col: int):
        wrapped_value = value
        if wrapped_from_prev_line:
            wrapped_value = (
                "# " + wrapped_from_prev_line + re.sub("^# ?", "", wrapped_value)
            )

        if start_col + len(wrapped_value) <= self._max_line_length:
            return Comment(value=wrapped_value), ""

        # get the last space before max line length
        last_idx = 0
        for idx, char in enumerate(wrapped_value):
            if char == " ":
                last_idx = idx
            if start_col + idx > self._max_line_length:
                break

        wrapped_for_next_line = wrapped_value[last_idx:].lstrip()
        return Comment(value=wrapped_value[:last_idx]), wrapped_for_next_line

