import os
from textwrap import dedent

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


def test_comment_wrap():
    orig = _parse(
        """
        # this is a pretend long comment
        """
    )
    orig = MetadataWrapper(orig)
    expected = _parse(
        """
        # this is a pretend
        # long comment
        """
    )

    t = CommentWrap(max_line_length=20)
    updated_cst = orig.visit(t)

    assert updated_cst.code == expected.code


def _parse(code: str) -> Module:
    return cst.parse_module(dedent(code))
