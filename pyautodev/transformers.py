import re
from pathlib import Path
from typing import List

import black
import libcst as cst
from black import reformat_one, FileMode, Report, WriteBack, Changed
from libcst import (
    Comment,
    EmptyLine,
    CSTNodeT,
    Module,
    TrailingWhitespace,
)
from libcst.metadata import (
    WhitespaceInclusivePositionProvider,
    PositionProvider,
)

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

    METADATA_DEPENDENCIES = (PositionProvider, WhitespaceInclusivePositionProvider)

    def __init__(self, max_line_length=MAX_LINE_LENGTH):
        super().__init__()
        self._max_line_length = max_line_length

    def on_leave(self, original_node: CSTNodeT, updated_node: CSTNodeT):
        return self._wrap_leading_lines(original_node, updated_node)

    def _wrap_leading_lines(self, original_node, updated_node: CSTNodeT) -> CSTNodeT:

        orig_leading_lines = getattr(updated_node, "leading_lines", None)
        if isinstance(updated_node, Module):
            orig_leading_lines = updated_node.header
        orig_trailing_whitespace = getattr(updated_node, "trailing_whitespace", None)

        if not orig_leading_lines and not orig_trailing_whitespace:
            return updated_node

        new_ll, unwrapped = [], list(orig_leading_lines)
        new_tw = orig_trailing_whitespace

        if new_tw and new_tw.comment:
            comment = new_tw.comment
            pos = self.get_metadata(WhitespaceInclusivePositionProvider, comment)
            start_col = pos.start.column
            if start_col + len(comment.value) > self._max_line_length:
                new_tw = TrailingWhitespace()
                # inline comment overflows line length and so should be moved to a
                # leading line
                if len(unwrapped) == 0:
                    unwrapped.append(EmptyLine(comment=Comment(value=comment.value)))
                else:
                    unwrapped[-1].comment += f"; {comment.value}"

        # default start column for comment to that of node
        pos = self.get_metadata(PositionProvider, original_node)
        start_col = pos.start.column

        wrapped_from_prev_line = ""
        while len(unwrapped) > 0:
            line = unwrapped.pop(0)
            comment = line.comment
            if not comment:
                new_ll.append(line)
                continue

            pos = self.get_metadata(
                WhitespaceInclusivePositionProvider, comment, default=None
            )
            if pos:
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
                new_ll.append(line)
                continue

            updated_comment, wrapped_from_prev_line = self._get_next_comment(
                value=comment.value,
                wrapped_from_prev_line=wrapped_from_prev_line,
                start_col=start_col,
            )
            new_ll.append(line.with_changes(comment=updated_comment))

        # add additional comment lines for remainder, if needed
        while len(wrapped_from_prev_line) > 0:
            updated_comment, wrapped_from_prev_line = self._get_next_comment(
                value="",  # no existing comment
                wrapped_from_prev_line=wrapped_from_prev_line,
                start_col=start_col,
            )
            new_ll.append(EmptyLine(comment=updated_comment))

        if isinstance(updated_node, Module):
            updated_node = updated_node.with_changes(header=new_ll)
        else:
            updated_node = updated_node.with_changes(leading_lines=new_ll)

        if orig_trailing_whitespace is not None:
            updated_node = updated_node.with_changes(trailing_whitespace=new_tw)

        return updated_node

    def _get_next_comment(
        self, value: str, wrapped_from_prev_line: str, start_col: int
    ):
        wrapped_value = value
        if wrapped_from_prev_line:
            wrapped_value = (
                "# " + wrapped_from_prev_line + re.sub("^# ?", " ", wrapped_value)
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
