import os

from pyflakes.messages import MultiValueRepeatedKeyLiteral

from pyautodev.checkers import PyLint, PyCodeStyle, PyFlakes


def test_pylint():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    test_file = os.path.join(test_dir, "bad_continuation_tabs.py")
    checker = PyLint(options={"indent-string": "\t", "indent-after-paren": 1})

    msgs = checker.check([test_file])

    assert len(msgs) == 4

    msg = msgs[0]
    assert msg.msg_id == "C0330"
    assert msg.symbol == "bad-continuation"
    assert msg.line == 26
    assert msg.column == 0

    msg = msgs[1]
    assert msg.msg_id == "C0330"
    assert msg.symbol == "bad-continuation"
    assert msg.line == 40
    assert msg.column == 0

    msg = msgs[2]
    assert msg.msg_id == "W0109"
    assert msg.symbol == "duplicate-key"
    assert msg.line == 55
    assert msg.column == 9

    msg = msgs[3]
    assert msg.msg_id == "R0201"
    assert msg.symbol == "no-self-use"
    assert msg.line == 54
    assert msg.column == 1


def test_pycodestyle():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    test_file = os.path.join(test_dir, "bad_continuation_tabs.py")
    checker = PyCodeStyle()

    msgs = checker.check([test_file])

    assert len(msgs) == 65

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
        55,
    ]
    assert code_lines["E123"] == [14]
    assert code_lines["E124"] == [40, 52]
    assert code_lines["E126"] == [26]
    assert code_lines["E261"] == [45, 46]
    assert code_lines["E501"] == [2]


def test_pyflakes():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    test_file = os.path.join(test_dir, "bad_continuation_tabs.py")
    checker = PyFlakes()

    msgs = checker.check([test_file])

    assert len(msgs) == 2

    msg = msgs[0]
    assert isinstance(msg, MultiValueRepeatedKeyLiteral)
    assert msg.lineno == 55
    assert msg.col == 10

    msg = msgs[1]
    assert isinstance(msg, MultiValueRepeatedKeyLiteral)
    assert msg.lineno == 55
    assert msg.col == 20
