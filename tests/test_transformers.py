import os

from black import dump_to_file

from pyautodev.transformers import Black, PyAutoDev

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def test_black():
    test_file = os.path.join(TEST_DIR, "bad_continuation_tabs.py")
    with open(test_file, "r") as f:
        orig_contents = f.read()
        orig_filepath = dump_to_file(orig_contents)

    expected_file = test_file.replace(".py", ".blacked.py")
    with open(expected_file, "r") as f:
        expected_contents = f.read()

    transformer = Black()
    transformer.transform([orig_filepath])

    with open(orig_filepath, "r") as f:
        actual_contents = f.read()
    os.remove(orig_filepath)

    assert actual_contents == expected_contents


def test_pyautodev():
    test_file = os.path.join(TEST_DIR, "comment_overflow.py")
    with open(test_file, 'r') as f:
        orig_contents = f.read()
        orig_filepath = dump_to_file(orig_contents)

    expected_file = test_file.replace(".py", ".pyautodev.py")
    with open(expected_file, "r") as f:
        expected_contents = f.read()

    transformer = PyAutoDev()
    transformer.transform([orig_filepath])

    with open(orig_filepath, "r") as f:
        actual_contents = f.read()
    os.remove(orig_filepath)

    assert actual_contents == expected_contents
