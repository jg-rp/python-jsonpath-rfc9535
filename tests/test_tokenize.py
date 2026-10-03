import dataclasses
import operator

import pytest

from jsonpath_rfc9535 import _lexer
from jsonpath_rfc9535._tokens import *
from jsonpath_rfc9535.exceptions import JSONPathSyntaxError


@dataclasses.dataclass
class Case:
    name: str
    source: str
    want: list[tuple[int, str]]


def tokenize(source: str) -> list[tuple[int, str]]:
    ts = _lexer.tokenize(source)
    return [(t[0], token_value(t, source)) for t in ts]


CASES: list[Case] = [
    Case("just root", "$", [(TOKEN_DOLLAR, "$")]),
    Case(
        "root dot prop",
        "$.some.thing",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "thing"),
        ],
    ),
    Case(
        "root bracket prop, single",
        "$['some']['thing']",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_SINGLE_QUOTED_STRING, "some"),
            (TOKEN_RIGHT_BRACKET, "]"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_SINGLE_QUOTED_STRING, "thing"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root bracket prop, double",
        '$["some"]["thing"]',
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_DOUBLE_QUOTED_STRING, "some"),
            (TOKEN_RIGHT_BRACKET, "]"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_DOUBLE_QUOTED_STRING, "thing"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root dot bracket prop",
        "$.['some']['thing']",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_SINGLE_QUOTED_STRING, "some"),
            (TOKEN_RIGHT_BRACKET, "]"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_SINGLE_QUOTED_STRING, "thing"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root bracket index",
        "$[1]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root bracket negative index",
        "$[-1]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "-1"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root dot bracket index",
        "$.[1]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice default start, stop and step",
        "[:]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_COLON, ":"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice default start, stop and step with two colons",
        "[::]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_COLON, ":"),
            (TOKEN_COLON, ":"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice default stop and step",
        "[1:]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_COLON, ":"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice default start and step",
        "[:-1]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_COLON, ":"),
            (TOKEN_INT, "-1"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice default step",
        "[1:7]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_COLON, ":"),
            (TOKEN_INT, "7"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice default step",
        "[1:7]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_COLON, ":"),
            (TOKEN_INT, "7"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "slice explicit step",
        "[1:7:2]",
        [
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_COLON, ":"),
            (TOKEN_INT, "7"),
            (TOKEN_COLON, ":"),
            (TOKEN_INT, "2"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root dot wild",
        "$.*",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_ASTERISK, "*"),
        ],
    ),
    Case(
        "root bracket wild",
        "$[*]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_ASTERISK, "*"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "root descend",
        "$..",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOUBLE_DOT, ".."),
        ],
    ),
    Case(
        "root descend prop",
        "$..thing",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOUBLE_DOT, ".."),
            (TOKEN_WORD, "thing"),
        ],
    ),
    Case(
        "root descend dot prop",
        "$...thing",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOUBLE_DOT, ".."),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "thing"),
        ],
    ),
    Case(
        "root selector list",
        "$[1,4,5]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_INT, "1"),
            (TOKEN_COMMA, ","),
            (TOKEN_INT, "4"),
            (TOKEN_COMMA, ","),
            (TOKEN_INT, "5"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter, current node identifier",
        "$[?(@.some)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter, root node identifier",
        "$[?($.some)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter eq",
        "$[?(@.some == 1.1)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_EQ, "=="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_FLOAT, "1.1"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter le",
        "$[?(@.some <= 1.1e2)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_LE, "<="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_FLOAT, "1.1e2"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter lt",
        "$[?(@.some < 1e2)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_LT, "<"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_INTEGER, "1e2"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter ge",
        "$[?(@.some >= 1)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_GE, ">="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_INT, "1"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter gt",
        "$[?(@.some > 1)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_GT, ">"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_INT, "1"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "filter ne",
        "$[?(@.some != 1)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_NE, "!="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_INT, "1"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "logical and",
        "$[?(@.some && @.thing)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_AND, "&&"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "thing"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "logical or",
        "$[?(@.some || @.thing)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_OR, "||"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "thing"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "logical not",
        "$[?(!@.some)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_EXCLAMATION, "!"),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "single quoted with escape sequence",
        "$[?(@.some == 'a\\nb')]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_EQ, "=="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_SINGLE_QUOTED_ESC_STRING, "a\\nb"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "true",
        "$[?(@.some == true)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_EQ, "=="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_WORD, "true"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "false",
        "$[?(@.some == false)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_EQ, "=="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_WORD, "false"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "null",
        "$[?(@.some == null)]",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_LEFT_BRACKET, "["),
            (TOKEN_QUESTION, "?"),
            (TOKEN_LEFT_PAREN, "("),
            (TOKEN_AT, "@"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "some"),
            (TOKEN_TRIVIA, " "),
            (TOKEN_EQ, "=="),
            (TOKEN_TRIVIA, " "),
            (TOKEN_WORD, "null"),
            (TOKEN_RIGHT_PAREN, ")"),
            (TOKEN_RIGHT_BRACKET, "]"),
        ],
    ),
    Case(
        "dot false",
        "$.false",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "false"),
        ],
    ),
    Case(
        "dot true",
        "$.true",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "true"),
        ],
    ),
    Case(
        "dot null",
        "$.null",
        [
            (TOKEN_DOLLAR, "$"),
            (TOKEN_DOT, "."),
            (TOKEN_WORD, "null"),
        ],
    ),
]


@pytest.mark.parametrize("case", CASES, ids=operator.attrgetter("name"))
def test_tokenizer(case: Case) -> None:
    got = tokenize(case.source)
    assert got == case.want


def test_truncated_eq() -> None:
    with pytest.raises(JSONPathSyntaxError):
        tokenize("$[?(@.a = @.b)]")


def test_unknown_symbol() -> None:
    with pytest.raises(JSONPathSyntaxError):
        tokenize("$[`]")


def test_unclosed_string_literal() -> None:
    with pytest.raises(JSONPathSyntaxError):
        tokenize("$[@.a == 'foo]")


def test_unclosed_string_literal_after_escape() -> None:
    with pytest.raises(JSONPathSyntaxError):
        tokenize("$[@.a == 'foo\\]")


def test_unclosed_string_literal_eoi() -> None:
    with pytest.raises(JSONPathSyntaxError):
        tokenize("$[@.a == 'foo")
