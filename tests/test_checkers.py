import os

from pyautodev.checkers import PyLint, PyCodeStyle


def test_pylint():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    test_file = os.path.join(test_dir, "bad_continuation_tabs.py")
    checker = PyLint(options={"indent-string": "\t", "indent-after-paren": 1})

    msgs = checker.check([test_file])

    assert len(msgs) == 2

    assert msgs[0].msg_id == "C0330"
    assert msgs[0].symbol == "bad-continuation"
    assert msgs[0].line == 26
    assert msgs[0].column == 0

    assert msgs[1].msg_id == "C0330"
    assert msgs[1].symbol == "bad-continuation"
    assert msgs[1].line == 40
    assert msgs[1].column == 0


def test_pycodestyle():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    test_file = os.path.join(test_dir, "bad_continuation_tabs.py")
    checker = PyCodeStyle()

    msgs = checker.check([test_file])

    assert len(msgs) == 62

    code_lines = {}
    for msg in msgs:
        code, line = msg[3], msg[1]
        if code not in code_lines:
            code_lines[code] = []
        code_lines[code].append(line)

    # check we have all the errors codes
    assert sorted(code_lines.keys()) == [
        "E101",
        "E117",
        "E123",
        "E124",
        "E126",
        "E261",
        "E302",
        "E501",
        "W191",
    ]

    # check most of the error code line numbers
    assert code_lines["E101"] == [12, 26, 39, 45, 46, 51, 52]
    assert code_lines["E117"] == [
        18,
        19,
        20,
        24,
        25,
        29,
        30,
        36,
        37,
        38,
        43,
        44,
        49,
        50,
    ]
    assert code_lines["E123"] == [14]
    assert code_lines["E124"] == [40, 52]
    assert code_lines["E126"] == [26]
    assert code_lines["E261"] == [45, 46]
    assert code_lines["E501"] == [2]
