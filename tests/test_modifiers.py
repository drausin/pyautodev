from textwrap import dedent

import libcst as cst
import pytest
from libcst import Module, MetadataWrapper

from pyautodev.modifiers import CommentWrap


@pytest.mark.parametrize(
    "orig_raw, expected_raw",
    [
        # no-ops
        #   +------25 chars----------+
        (
                """
                # a short comment
                """,
                """
                # a short comment
                """,
        ),
        (
                """
                import os
                
                # a fn comment
                def foo():
                    return bar
                """,
                """
                import os
                
                # a fn comment
                def foo():
                    return bar
                """,
        ),
        (
                """
                def foo():
                    return bar  # inline
                """,
                """
                def foo():
                    return bar  # inline
                """,
        ),
        # wraps
        #   +------25 chars----------+
        (
                """
                def foo():
                    # some very long comment that needs to be wrapped
                    return bar
                """,
                """
                def foo():
                    # some very long
                    # comment that needs
                    # to be wrapped
                    return bar
                """,
        ),
        (
                """
                def foo():
                    a = 1  # some inline comment that is also long
                """,
                """
                def foo():
                    # some inline comment
                    # that is also long
                    a = 1
                """,
        ),
        (
                """
                def foo():
                    a = 1  # some inline comment
                """,
                """
                def foo():
                    # some inline comment
                    a = 1
                """,
        ),
        (
                """
                def foo():
                    # above line
                    a = 1  # some inline comment
                """,
                """
                def foo():
                    # above line. some
                    # inline comment
                    a = 1
                """,
        ),
        (
                """
                # this is a pretend long comment
                
                def foo():
                    return True
                """,
                """
                # this is a pretend long
                # comment
                
                def foo():
                    return True
                """,
        ),
    ],
)
def test_comment_wrap(orig_raw, expected_raw):
    t = CommentWrap(max_line_length=25)
    orig = MetadataWrapper(_parse(orig_raw))
    updated_cst = orig.visit(t)

    assert updated_cst.code == dedent(expected_raw)


def _parse(code: str) -> Module:
    return cst.parse_module(dedent(code))
