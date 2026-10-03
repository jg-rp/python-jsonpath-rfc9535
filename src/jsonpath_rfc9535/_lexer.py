import re

from ._tokens import *
from .exceptions import JSONPathSyntaxError

RE_FLOAT = re.compile(r"(:?-?[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?)|(-?[0-9]+[eE]-[0-9]+)")
RE_INT = re.compile(r"-?[0-9]+")
RE_INT_EXP = re.compile(r"-?[0-9]+[eE]\+?[0-9]+")
RE_NAME = re.compile(r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*")
RE_TRIVIA = re.compile(r"[ \n\r\t]+")


def tokenize(source: str) -> list[Token]:
    """Transform a JSONPath query source string into a list of tokens.

    This tokenizer emits some non-standard tokens. The parser is responsible
    for reject non-standard tokens with a syntax error if desired.
    """
    tokens: list[Token] = []
    length = len(source)
    pos = 0

    while pos < length:
        ch = source[pos]

        if ch == "*":
            tokens.append((TOKEN_ASTERISK, pos, pos + 1))
            pos += 1
        elif ch == "@":
            tokens.append((TOKEN_AT, pos, pos + 1))
            pos += 1
        elif ch == ":":
            tokens.append((TOKEN_COLON, pos, pos + 1))
            pos += 1
        elif ch == ",":
            tokens.append((TOKEN_COMMA, pos, pos + 1))
            pos += 1
        elif ch == "$":
            tokens.append((TOKEN_DOLLAR, pos, pos + 1))
            pos += 1
        elif ch == "(":
            tokens.append((TOKEN_LEFT_PAREN, pos, pos + 1))
            pos += 1
        elif ch == "[":
            tokens.append((TOKEN_LEFT_BRACKET, pos, pos + 1))
            pos += 1
        elif ch == ")":
            tokens.append((TOKEN_RIGHT_PAREN, pos, pos + 1))
            pos += 1
        elif ch == "]":
            tokens.append((TOKEN_RIGHT_BRACKET, pos, pos + 1))
            pos += 1
        elif ch == "?":
            tokens.append((TOKEN_QUESTION, pos, pos + 1))
            pos += 1
        elif ch == "&":
            if pos + 1 < length and source[pos + 1] == "&":
                tokens.append((TOKEN_AND, pos, pos + 2))
                pos += 2
            else:
                raise JSONPathSyntaxError(
                    "unexpected '&', did you mean '&&'?",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )
        elif ch == "|":
            if pos + 1 < length and source[pos + 1] == "|":
                tokens.append((TOKEN_OR, pos, pos + 2))
                pos += 2
            else:
                raise JSONPathSyntaxError(
                    "unexpected '|', did you mean '||'?",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )
        elif ch == ".":
            if pos + 1 < length and source[pos + 1] == ".":
                tokens.append((TOKEN_DOUBLE_DOT, pos, pos + 2))
                pos += 2
            else:
                tokens.append((TOKEN_DOT, pos, pos + 1))
                pos += 1
        elif ch == "=":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append((TOKEN_EQ, pos, pos + 2))
                pos += 2
            else:
                raise JSONPathSyntaxError(
                    "unexpected '=', did you mean '=='?",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )
        elif ch == "!":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append((TOKEN_NE, pos, pos + 2))
                pos += 2
            else:
                tokens.append((TOKEN_EXCLAMATION, pos, pos + 1))
                pos += 1
        elif ch == ">":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append((TOKEN_GE, pos, pos + 2))
                pos += 2
            else:
                tokens.append((TOKEN_GT, pos, pos + 1))
                pos += 1
        elif ch == "<":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append((TOKEN_LE, pos, pos + 2))
                pos += 2
            else:
                tokens.append((TOKEN_LT, pos, pos + 1))
                pos += 1
        elif ch == "'":
            token, pos = _scan_string_literal(
                source,
                pos + 1,
                "'",
                '"',
                TOKEN_SINGLE_QUOTED_STRING,
                TOKEN_SINGLE_QUOTED_ESC_STRING,
            )
            tokens.append(token)
        elif ch == '"':
            token, pos = _scan_string_literal(
                source,
                pos + 1,
                '"',
                "'",
                TOKEN_DOUBLE_QUOTED_STRING,
                TOKEN_DOUBLE_QUOTED_ESC_STRING,
            )
            tokens.append(token)
        elif _is_name_first_ch(ord(ch)):
            if match := _scan(RE_NAME, source, pos):
                tokens.append((TOKEN_WORD, pos, pos + len(match)))
                pos += len(match)
            else:
                raise JSONPathSyntaxError(
                    "internal error",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )
        elif _is_trivia(ord(ch)):
            if match := _scan(RE_TRIVIA, source, pos):
                tokens.append((TOKEN_TRIVIA, pos, pos + len(match)))
                pos += len(match)
            else:
                raise JSONPathSyntaxError(
                    "internal error",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )
        elif _is_number_ch(ord(ch)):
            if match := _scan(RE_FLOAT, source, pos):
                tokens.append((TOKEN_FLOAT, pos, pos + len(match)))
                pos += len(match)
            elif match := _scan(RE_INT_EXP, source, pos):
                tokens.append((TOKEN_INTEGER, pos, pos + len(match)))
                pos += len(match)
            elif match := _scan(RE_INT, source, pos):
                tokens.append((TOKEN_INT, pos, pos + len(match)))
                pos += len(match)
            else:
                raise JSONPathSyntaxError(
                    "internal error",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )

        else:
            raise JSONPathSyntaxError(
                f"unexpected {ch!r}",
                token=(TOKEN_ERROR, pos, pos + 1),
                source=source,
            )

    return tokens


def _scan(pattern: re.Pattern[str], source: str, pos: int) -> str | None:
    m = pattern.match(source, pos)
    return m.group() if m else None


def _scan_string_literal(
    source: str,
    pos: int,
    quote: str,
    other_quote: str,
    kind: int,
    esc_kind: int,
) -> tuple[Token, int]:
    start = pos
    length = len(source)

    while pos < length:
        ch = source[pos]

        if ch == quote:
            # Token excludes opening and closing quotes.
            return ((kind, start, pos), pos + 1)
        elif ch == "\\":
            if pos + 1 < length and source[pos + 1] == other_quote:
                raise JSONPathSyntaxError(
                    "invalid escape sequence",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )

            if pos + 1 >= length:
                raise JSONPathSyntaxError(
                    "invalid escape sequence",
                    token=(TOKEN_ERROR, pos, pos + 1),
                    source=source,
                )

            pos += 2
            kind = esc_kind
        elif ord(ch) <= 0x1F:
            raise JSONPathSyntaxError(
                f"invalid character {ord(ch):x}",
                token=(TOKEN_ERROR, pos, pos + 1),
                source=source,
            )
        else:
            pos += 1

    raise JSONPathSyntaxError(
        "unclosed string literal",
        token=(TOKEN_ERROR, start, pos),
        source=source,
    )


def _is_name_first_ch(ch: int) -> bool:
    return (
        (ch >= 65 and ch <= 90)
        or (ch >= 97 and ch <= 122)
        or ch == 95
        or (ch >= 0x80 and ch <= 0xFFFF)
    )


def _is_number_ch(ch: int) -> bool:
    return ch == 45 or (ch >= 48 and ch <= 57)


def _is_trivia(ch: int) -> bool:
    return ch == 32 or ch == 9 or ch == 10 or ch == 13
