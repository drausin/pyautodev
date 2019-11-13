import os

from pyautodev.checkers import PyLint, PyCodeStyle, PyFlakes

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEST_FILE = os.path.join(TEST_DIR, "bad_continuation_tabs.py")


def test_pylint():
    checker = PyLint(options={"indent-string": "\t", "indent-after-paren": 1})

    msgs = checker.check([TEST_FILE])

    assert len(msgs) == 4

    msg = msgs[0]
    assert msg.code == "C0330"
    assert msg.description == "bad-continuation"
    assert msg.line == 26
    assert msg.column == 0

    msg = msgs[1]
    assert msg.code == "C0330"
    assert msg.description == "bad-continuation"
    assert msg.line == 40
    assert msg.column == 0

    msg = msgs[2]
    assert msg.code == "W0109"
    assert msg.description == "duplicate-key"
    assert msg.line == 55
    assert msg.column == 9

    msg = msgs[3]
    assert msg.code == "R0201"
    assert msg.description == "no-self-use"
    assert msg.line == 54
    assert msg.column == 1


def test_pycodestyle():
    checker = PyCodeStyle()

    msgs = checker.check([TEST_FILE])

    assert len(msgs) == 65

    code_lines = {}
    for msg in msgs:
        if msg.code not in code_lines:
            code_lines[msg.code] = []
        code_lines[msg.code].append(msg.line)

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
    checker = PyFlakes()

    msgs = checker.check([TEST_FILE])

    assert len(msgs) == 2

    msg = msgs[0]
    assert msg.code == "MultiValueRepeatedKeyLiteral"
    assert msg.line == 55
    assert msg.column == 10

    msg = msgs[1]
    assert msg.code == "MultiValueRepeatedKeyLiteral"
    assert msg.line == 55
    assert msg.column == 20

