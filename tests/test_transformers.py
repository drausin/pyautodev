import os
from textwrap import dedent

import pytest
import libcst as cst
from black import dump_to_file
from libcst import Module, MetadataWrapper

from pyautodev.transformers import Black, CommentWrap

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEST_FILE = os.path.join(TEST_DIR, "bad_continuation_tabs.py")


def test_black():
    with open(TEST_FILE, "r") as f:
        orig_contents = f.read()
        orig_filepath = dump_to_file(orig_contents)

    expected_file = TEST_FILE.replace(".py", ".blacked.py")
    with open(expected_file, "r") as f:
        expected_contents = f.read()

    transformer = Black()
    transformer.transform([orig_filepath])

    with open(orig_filepath, "r") as f:
        actual_contents = f.read()
    os.remove(orig_filepath)

    assert actual_contents == expected_contents


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
            # this is a pretend long comment
            """,
            """
            # this is a pretend long
            # comment
            """,
        ),
        (
            """
            # this is a pretend long comment
            # that also wraps
            """,
            """
            # this is a pretend long
            # comment that also wraps
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
