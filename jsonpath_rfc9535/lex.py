"""JSONPath expression lexical scanner."""

from __future__ import annotations

import re
from typing import Callable
from typing import List
from typing import Optional
from typing import Pattern
from typing import Tuple
from typing import TypeAlias

from .exceptions import JSONPathLexerError
from .exceptions import JSONPathSyntaxError
from .tokens import Token
from .tokens import TokenType

# ruff: noqa: D102

RE_WHITESPACE = re.compile(r"[ \n\r\t]+")
RE_PROPERTY = re.compile(r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*")
RE_INDEX = re.compile(r"-?[0-9]+")
RE_INT = re.compile(r"-?[0-9]+(?:[eE]\+?[0-9]+)?")
# RE_FLOAT includes numbers with a negative exponent and no decimal point.
RE_FLOAT = re.compile(r"(:?-?[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?)|(-?[0-9]+[eE]-[0-9]+)")
RE_FUNCTION_NAME = re.compile(r"[a-z][a-z_0-9]*")
ESCAPES = frozenset(["b", "f", "n", "r", "t", "u", "/", "\\"])


StateFn: TypeAlias = Callable[[], Optional["StateFn"]]


class Lexer:
    """JSONPath expression lexical scanner."""

    __slots__ = (
        "filter_depth",
        "func_call_stack",
        "bracket_stack",
        "tokens",
        "start",
        "pos",
        "query",
    )

    def __init__(self, query: str) -> None:
        self.filter_depth = 0
        """Filter nesting level."""

        self.func_call_stack: List[int] = []
        """A running count of parentheses for each, possibly nested, function call.
        
        If the stack is empty, we are not in a function call. Remember that
        function arguments can be arbitrarily nested in parentheses.
        """

        self.bracket_stack: list[tuple[str, int]] = []
        """A stack of opening (parentheses/bracket, index) pairs."""

        self.tokens: List[Token] = []
        """Tokens resulting from scanning a JSONPath expression."""

        self.start = 0
        """Pointer to the start of the current token."""

        self.pos = 0
        """Pointer to the current character."""

        self.query = query
        """The JSONPath expression being scanned."""

    def run(self) -> None:
        """Start scanning this lexer's JSONPath expression."""
        state: Optional[StateFn] = self.lex_root
        while state is not None:
            state = state()

    def emit(self, t: TokenType) -> None:
        """Append a token of type _t_ to the output tokens list."""
        self.tokens.append(
            Token(
                t,
                self.query[self.start : self.pos],
                self.start,
                self.query,
            )
        )
        self.start = self.pos

    def next(self) -> str:
        """Return the next character, or the empty string if no more characters."""
        try:
            c = self.query[self.pos]
            self.pos += 1
            return c
        except IndexError:
            return ""

    def ignore(self) -> None:
        """Ignore characters up to the pointer."""
        self.start = self.pos

    def backup(self) -> None:
        """Move the current position back one."""
        if self.pos <= self.start:
            # Cant backup beyond start.
            msg = "unexpected end of expression"
            raise JSONPathSyntaxError(
                msg, token=Token(TokenType.ERROR, msg, self.pos, self.query)
            )
        self.pos -= 1

    def peek(self) -> str:
        """Return the next character without advancing the pointer."""
        try:
            return self.query[self.pos]
        except IndexError:
            return ""

    def accept(self, s: str) -> bool:
        """Increment the pointer if the current position starts with _s_."""
        if self.query.startswith(s, self.pos):
            self.pos += len(s)
            return True
        return False

    def accept_match(self, pattern: Pattern[str]) -> bool:
        """Match _pattern_ starting from the pointer."""
        match = pattern.match(self.query, self.pos)
        if match:
            self.pos += len(match.group())
            return True
        return False

    def accept_string_literal(self, quote: str, token_type: TokenType) -> bool:
        """Scan and emit a string literal token.

        Return `True` is successful, or `False` otherwise, in which case an error token
        will have been emitted.
        """
        self.ignore()  # ignore opening quote

        if self.peek() == "":
            # an empty string
            self.emit(token_type)
            self.next()
            self.ignore()
            return True

        while True:
            c = self.next()

            if c == "\\":
                peeked = self.peek()
                if peeked in ESCAPES or peeked == quote:
                    self.next()
                else:
                    self.error("invalid escape")
                    return False

            if not c:
                self.error(f"unclosed string starting at index {self.start}")
                return False

            if c == quote:
                self.backup()
                self.emit(token_type)
                self.next()
                self.ignore()  # ignore closing quote
                return True

    def ignore_whitespace(self) -> bool:
        """Move the pointer past any whitespace."""
        if self.pos != self.start:
            msg = (
                "must emit or ignore before consuming whitespace "
                f"({self.query[self.start : self.pos]})"
            )
            raise JSONPathLexerError(
                msg, token=Token(TokenType.ERROR, msg, self.pos, self.query)
            )

        if self.accept_match(RE_WHITESPACE):
            self.ignore()
            return True
        return False

    def error(self, msg: str) -> None:
        """Emit an error token."""
        # TODO: better error messages.
        self.tokens.append(
            Token(
                TokenType.ERROR,
                self.query[self.start : self.pos],
                self.start,
                self.query,
                msg,
            )
        )

    def lex_root(self) -> Optional[StateFn]:
        c = self.next()

        if c != "$":
            self.error(f"expected '$', found {c!r}")
            return None

        self.emit(TokenType.ROOT)
        return self.lex_segment

    def lex_segment(self) -> Optional[StateFn]:  # noqa: PLR0911
        if self.ignore_whitespace() and not self.peek():
            self.error("unexpected trailing whitespace")
            return None

        c = self.next()

        if c == "":
            self.emit(TokenType.EOF)
            return None

        if c == ".":
            if self.peek() == ".":
                self.next()
                self.emit(TokenType.DOUBLE_DOT)
                return self.lex_descendant_segment
            return self.lex_shorthand_selector

        if c == "[":
            self.emit(TokenType.LBRACKET)
            self.bracket_stack.append((c, self.pos - 1))
            return self.lex_inside_bracketed_segment

        if self.filter_depth:
            self.backup()
            return self.lex_inside_filter

        self.error(f"expected '.', '..' or a bracketed selection, found {c!r}")
        return None

    def lex_descendant_segment(self) -> Optional[StateFn]:
        c = self.next()

        if c == "":
            self.error("bald descendant segment")
            return None

        if c == "*":
            self.emit(TokenType.WILD)
            return self.lex_segment

        if c == "[":
            self.emit(TokenType.LBRACKET)
            self.bracket_stack.append((c, self.pos - 1))
            return self.lex_inside_bracketed_segment

        self.backup()

        if self.accept_match(RE_PROPERTY):
            self.emit(TokenType.PROPERTY)
            return self.lex_segment

        self.next()
        self.error(f"unexpected descendant selection token {c!r}")
        return None

    def lex_shorthand_selector(self) -> Optional[StateFn]:
        self.ignore()  # ignore dot

        if self.accept_match(RE_WHITESPACE):
            self.error("unexpected whitespace after dot")
            return None

        c = self.next()

        if c == "*":
            self.emit(TokenType.WILD)
            return self.lex_segment

        self.backup()

        if self.accept_match(RE_PROPERTY):
            self.emit(TokenType.PROPERTY)
            return self.lex_segment

        self.error(f"unexpected shorthand selector {c!r}")
        return None

    def lex_inside_bracketed_segment(self) -> Optional[StateFn]:  # noqa: PLR0911, PLR0912
        while True:
            self.ignore_whitespace()
            c = self.next()

            if c == "]":
                if not self.bracket_stack or self.bracket_stack[-1][0] != "[":
                    self.backup()
                    self.error("unbalanced brackets")
                    return None

                self.bracket_stack.pop()
                self.emit(TokenType.RBRACKET)
                return self.lex_segment

            if c == "":
                self.error("unbalanced brackets")
                return None

            if c == "*":
                self.emit(TokenType.WILD)
                continue

            if c == "?":
                self.emit(TokenType.FILTER)
                self.filter_depth += 1
                return self.lex_inside_filter

            if c == ",":
                self.emit(TokenType.COMMA)
                continue

            if c == ":":
                self.emit(TokenType.COLON)
                continue

            if c == "'":
                # Quoted dict/object key/property name
                if self.accept_string_literal(
                    c, token_type=TokenType.SINGLE_QUOTE_STRING
                ):
                    continue
                return None

            if c == '"':
                # Quoted dict/object key/property name
                if self.accept_string_literal(
                    c, token_type=TokenType.DOUBLE_QUOTE_STRING
                ):
                    continue
                return None

            # default
            self.backup()

            if self.accept_match(RE_INDEX):
                # Index selector or part of a slice selector.
                self.emit(TokenType.INDEX)
                continue

            self.error(f"unexpected token {c!r} in bracketed selection")
            return None

    def lex_inside_filter(self) -> Optional[StateFn]:  # noqa: PLR0911, PLR0912, PLR0915
        while True:
            self.ignore_whitespace()
            c = self.next()

            if c == "":
                self.error("unclosed bracketed selection")
                return None

            if c == "]":
                self.filter_depth -= 1
                self.backup()
                return self.lex_inside_bracketed_segment

            if c == ",":
                self.emit(TokenType.COMMA)
                # If we have unbalanced parens, we are inside a function call and a
                # comma separates arguments. Otherwise a comma separates selectors.
                if self.func_call_stack:
                    continue
                self.filter_depth -= 1
                return self.lex_inside_bracketed_segment

            if c == "'":
                if self.accept_string_literal(
                    c, token_type=TokenType.SINGLE_QUOTE_STRING
                ):
                    continue
                return None

            if c == '"':
                if self.accept_string_literal(
                    c, token_type=TokenType.DOUBLE_QUOTE_STRING
                ):
                    continue
                return None

            if c == "(":
                self.emit(TokenType.LPAREN)
                self.bracket_stack.append((c, self.pos - 1))
                # Are we in a function call? If so, a function argument contains parens.
                if self.func_call_stack:
                    self.func_call_stack[-1] += 1
                continue

            if c == ")":
                if not self.bracket_stack or self.bracket_stack[-1][0] != "(":
                    self.backup()
                    self.error("unbalanced parentheses")
                    return None

                self.bracket_stack.pop()
                self.emit(TokenType.RPAREN)
                # Are we closing a function call or a parenthesized expression?
                if self.func_call_stack:
                    if self.func_call_stack[-1] == 1:
                        self.func_call_stack.pop()
                    else:
                        self.func_call_stack[-1] -= 1
                continue

            if c == "$":
                self.emit(TokenType.ROOT)
                return self.lex_segment

            if c == "@":
                self.emit(TokenType.CURRENT)
                return self.lex_segment

            if c == ".":
                self.backup()
                return self.lex_segment

            if c == "!":
                if self.peek() == "=":
                    self.next()
                    self.emit(TokenType.NE)
                else:
                    self.emit(TokenType.NOT)
                continue

            if c == "=":
                if self.peek() == "=":
                    self.next()
                    self.emit(TokenType.EQ)
                    continue

                self.backup()
                self.error(f"unexpected filter selector token {c!r}")
                return None

            if c == "<":
                if self.peek() == "=":
                    self.next()
                    self.emit(TokenType.LE)
                else:
                    self.emit(TokenType.LT)
                continue

            if c == ">":
                if self.peek() == "=":
                    self.next()
                    self.emit(TokenType.GE)
                else:
                    self.emit(TokenType.GT)
                continue

            self.backup()

            if self.accept("&&"):
                self.emit(TokenType.AND)
            elif self.accept("||"):
                self.emit(TokenType.OR)
            elif self.accept("true"):
                self.emit(TokenType.TRUE)
            elif self.accept("false"):
                self.emit(TokenType.FALSE)
            elif self.accept("null"):
                self.emit(TokenType.NULL)
            elif self.accept_match(RE_FLOAT):
                self.emit(TokenType.FLOAT)
            elif self.accept_match(RE_INT):
                self.emit(TokenType.INT)
            elif self.accept_match(RE_FUNCTION_NAME) and self.peek() == "(":
                # Keep track of parentheses for this function call.
                self.func_call_stack.append(1)
                self.emit(TokenType.FUNCTION)
                self.bracket_stack.append(("(", self.pos))
                self.next()
                self.ignore()  # ignore LPAREN
            else:
                self.error(f"unexpected filter selector token {c!r}")
                return None


def lex(query: str) -> Tuple[Lexer, List[Token]]:
    """Return a lexer for _query_ and an array to be populated with Tokens."""
    lexer = Lexer(query)
    return lexer, lexer.tokens


def tokenize(query: str) -> List[Token]:
    """Scan JSONPath expression _query_ and return a list of tokens."""
    lexer, tokens = lex(query)
    lexer.run()

    if tokens and tokens[-1].type_ == TokenType.ERROR:
        raise JSONPathSyntaxError(tokens[-1].message, token=tokens[-1])

    # Check for remaining opening brackets that have not been closed.
    if lexer.bracket_stack:
        ch, index = lexer.bracket_stack[-1]
        msg = f"unbalanced {'brackets' if ch == '[' else 'parentheses'}"
        raise JSONPathSyntaxError(
            msg,
            token=Token(
                TokenType.ERROR,
                lexer.query[index],
                index,
                lexer.query,
                msg,
            ),
        )

    return tokens
