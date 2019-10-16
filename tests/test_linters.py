import os

from pyautodev.linters import PyLint


def test_pylint():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    test_file = os.path.join(test_dir, "bad_continuation_tabs.py")
    linter = PyLint(options={
        "indent-string": "\t",
        "indent-after-paren": 1,
    })

    msgs = linter.check([test_file])

    assert len(msgs) == 2

    assert msgs[0].msg_id == "C0330"
    assert msgs[0].symbol == "bad-continuation"
    assert msgs[0].line == 26
    assert msgs[0].column == 0

    assert msgs[1].msg_id == "C0330"
    assert msgs[1].symbol == "bad-continuation"
    assert msgs[1].line == 40
    assert msgs[1].column == 0


