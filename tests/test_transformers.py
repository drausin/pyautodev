import os

from black import dump_to_file

from pyautodev.transformers import Black

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEST_FILE = os.path.join(TEST_DIR, "bad_continuation_tabs.py")


def test_black():
    with open(TEST_FILE, 'r') as f:
        orig_contents = f.read()
        orig_filepath = dump_to_file(orig_contents)

    expected_file = TEST_FILE.replace(".py", ".blacked.py")
    with open(expected_file, 'r') as f:
        expected_contents = f.read()

    transformer = Black()
    transformer.transform([orig_filepath])

    with open(orig_filepath, 'r') as f:
        actual_contents = f.read()
    os.remove(orig_filepath)

    assert actual_contents == expected_contents
