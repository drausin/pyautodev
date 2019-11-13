import re
from typing import List, Sequence, Tuple, Union

import black
import libcst as cst
from libcst import (
    Comment,
    EmptyLine,
    CSTNodeT,
    Module,
    TrailingWhitespace,
    RemovalSentinel,
    ClassDef,
    Decorator,
    With,
    While,
    Try,
    SimpleStatementLine,
    If,
    FunctionDef,
    For,
    Finally,
    ExceptHandler,
    Else,
)
from libcst.metadata import PositionProvider

MAX_LINE_LENGTH = black.DEFAULT_LINE_LENGTH

_COMMENT_PREFIX = re.compile("^# ?")


class CommentWrap(cst.CSTTransformer):

    METADATA_DEPENDENCIES = (PositionProvider,)
    LEAVE_NODE_TYPES = {
        ClassDef,
        Decorator,
        Else,
        ExceptHandler,
        Finally,
        For,
        FunctionDef,
        If,
        Module,
        SimpleStatementLine,
        Try,
        While,
        With,
    }

    def __init__(self, max_line_length=MAX_LINE_LENGTH):
        super().__init__()
        self._init_leave_methods()
        self._max_line_length = max_line_length

    @classmethod
    def _init_leave_methods(cls):
        for node_type in cls.LEAVE_NODE_TYPES:
            method_name = f"leave_{node_type.__name__}"
            setattr(cls, method_name, cls._leave_node)

    def _leave_node(
        self, original_node: CSTNodeT, updated_node: CSTNodeT
    ) -> Union[CSTNodeT, RemovalSentinel]:

        leading_lines = getattr(updated_node, "leading_lines", None)
        if isinstance(updated_node, Module):
            leading_lines = updated_node.header
        trailing_whitespace = getattr(updated_node, "trailing_whitespace", None)

        if not leading_lines and not (trailing_whitespace and trailing_whitespace.comment):
            # nodes with no leading lines and no whitespace after are unchanged
            return updated_node

        new_ll, new_tw = self._maybe_move_inline_comment(
            leading_lines, trailing_whitespace
        )
        new_ll = self._wrap_leading_lines(new_ll, original_node)

        if new_tw:
            updated_node = updated_node.with_changes(trailing_whitespace=new_tw)

        if isinstance(updated_node, Module):
            return updated_node.with_changes(header=new_ll)

        return updated_node.with_changes(leading_lines=new_ll)

    def _maybe_move_inline_comment(
        self,
        leading_lines: Sequence[EmptyLine],
        trailing_whitespace: TrailingWhitespace,
    ) -> Tuple[List[EmptyLine], TrailingWhitespace]:

        new_ll = list(leading_lines)
        new_tw = trailing_whitespace

        if not trailing_whitespace or not trailing_whitespace.comment:
            # return original LLs & TW unless TW is present with a comment
            return new_ll, new_tw

        inline_comment = new_tw.comment
        pos = self.get_metadata(PositionProvider, inline_comment)
        start_col = pos.start.column

        if start_col + len(inline_comment.value) <= self._max_line_length:
            # return original LLs & TW when end of inline comment is before max line
            # length
            return new_ll, new_tw

        if len(new_ll) == 0:
            # inline comment should be moved to a new leading line
            new_ll.append(EmptyLine(comment=Comment(value=inline_comment.value)))

        else:
            # inline comment should be appended to the last leading line
            last_ll = new_ll[-1]

            last_ll = last_ll.with_changes(
                comment=Comment(
                    value=self._join_comment_values(
                        last_ll.comment.value, inline_comment.value, "."
                    )
                )
            )
            new_ll[-1] = last_ll

        return new_ll, TrailingWhitespace()

    def _wrap_leading_lines(
        self, leading_lines: List[EmptyLine], original_node: CSTNodeT
    ) -> List[EmptyLine]:

        new_ll = []
        wrapped_from_prev_line = ""
        node_pos = self.get_metadata(PositionProvider, original_node)
        start_col = node_pos.start.column

        while len(leading_lines) > 0:
            line = leading_lines.pop(0)
            comment = line.comment

            if not comment:
                # empty line has no comment, so nothing to wrap
                new_ll.append(line)
                continue

            start_col = self._get_start_column(comment, start_col)
            end_col = start_col + len(comment.value)

            if not wrapped_from_prev_line and end_col < self._max_line_length:
                # existing comment with no previous wrapped content can stay as-is
                # b/c within max line length
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

        return new_ll

    def _get_start_column(self, comment: Comment, fallback_start_col: int) -> int:
        # we may not have a position for the comment if it was just created from
        # a different inline comment
        comment_pos = self.get_metadata(PositionProvider, comment, default=None)

        # get comment start column from its original position, but fall back to
        # node start column if it's not available
        comment_start_col = fallback_start_col
        if comment_pos:
            comment_start_col = comment_pos.start.column

        if comment_start_col > self._max_line_length:
            # not quite sure how to handle this yet, so fail and investigate
            raise ValueError(
                f"unexpectedly have starting position {comment_start_col} > "
                f"{self._max_line_length} on line {comment_pos.start.line}"
            )

        return comment_start_col

    def _get_next_comment(
        self, value: str, wrapped_from_prev_line: str, start_col: int
    ) -> Tuple[Comment, str]:

        wrapped_value = value
        if wrapped_from_prev_line:
            wrapped_value = self._join_comment_values(
                wrapped_from_prev_line, wrapped_value
            )

        if start_col + len(wrapped_value) <= self._max_line_length:
            return Comment(value=wrapped_value), ""

        # get the last space before max line length
        last_idx = 0
        for idx, char in enumerate(wrapped_value):
            if char == " ":
                last_idx = idx
            if start_col + idx >= self._max_line_length:
                break

        wrapped_for_next_line = wrapped_value[last_idx:].lstrip()
        return Comment(value=wrapped_value[:last_idx]), wrapped_for_next_line

    @staticmethod
    def _join_comment_values(value_1: str, value_2: str, sep: str = "") -> str:
        stripped_1 = re.sub(_COMMENT_PREFIX, "", value_1)
        joined = f"# {stripped_1}"
        if value_2:
            stripped_2 = re.sub(_COMMENT_PREFIX, "", value_2)
            joined += f"{sep} {stripped_2}"

        return joined

