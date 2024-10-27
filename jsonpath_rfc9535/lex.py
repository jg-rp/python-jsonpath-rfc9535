"""JSONPath expression lexical scanner."""

from __future__ import annotations

import re
from typing import Callable
from typing import List
from typing import Optional
from typing import Pattern
from typing import Tuple

from .exceptions import JSONPathLexerError
from .exceptions import JSONPathSyntaxError
from .tokens import Token
from .tokens import TokenType

RE_WHITESPACE = re.compile(r"[ \n\r\t]+")
RE_PROPERTY = re.compile(r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*")
RE_INDEX = re.compile(r"-?[0-9]+")
RE_INT = re.compile(r"-?[0-9]+")
RE_EXPONENT = re.compile(r"[eE][+-]?[0-9]+")
RE_NEGATIVE_EXPONENT = re.compile(r"[eE]-[0-9]+")
RE_FUNCTION_NAME = re.compile(r"[a-z][a-z_0-9]*")
RE_AND = re.compile(r"&&")
RE_OR = re.compile(r"\|\|")
RE_TRUE = re.compile(r"true")
RE_FALSE = re.compile(r"false")
RE_NULL = re.compile(r"null")
RE_ESCAPE = re.compile(r"\\[bfnrtu/]")


class Lexer:
    """JSONPath expression lexical scanner."""

    __slots__ = ("filter_depth", "paren_stack", "tokens", "start", "pos", "query")

    def __init__(self, query: str) -> None:
        self.filter_depth = 0
        """Filter nesting level."""

        self.paren_stack: List[int] = []
        """A running count of parentheses for each, possibly nested, function call.
        
        If the stack is empty, we are not in a function call. Remember that
        function arguments can be arbitrarily nested in parentheses.
        """

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
        state: Optional[StateFn] = lex_root
        while state is not None:
            state = state(self)

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
        # TODO: benchmark ty/except approach
        if self.pos >= len(self.query):
            return ""

        c = self.query[self.pos]
        self.pos += 1
        return c

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
        # TODO: benchmark try/except without self.next()
        c = self.next()
        if c:
            self.backup()
        return c

    def accept(self, s: str) -> bool:
        """Increment the pointer if the current position starts with _s_."""
        # TODO: benchmark using accept instead of accept_match for known words
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

    def ignore_whitespace(self) -> bool:
        """Move the pointer past any whitespace."""
        if self.pos != self.start:
            msg = (
                "must emit or ignore before consuming whitespace "
                f"({self.query[self.start: self.pos]})"
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
        # TODO: move msg out of Token.value. We'll need the value too when implementing
        # better error messages.
        self.tokens.append(Token(TokenType.ERROR, msg, self.pos, self.query))


StateFn = Callable[[Lexer], Optional["StateFn"]]


def lex_root(l: Lexer) -> Optional[StateFn]:  # noqa: D103
    # TODO: benchmark peek/next instead of next/backup
    c = l.next()

    if c != "$":
        l.backup()
        l.error(f"expected '$', found {c!r}")
        return None

    l.emit(TokenType.ROOT)
    return lex_segment


def lex_segment(l: Lexer) -> Optional[StateFn]:  # noqa: D103, PLR0911
    if l.ignore_whitespace() and not l.peek():
        l.error("unexpected trailing whitespace")
        return None

    c = l.next()

    if c == "":
        l.emit(TokenType.EOF)
        return None

    if c == ".":
        if l.peek() == ".":
            l.next()
            l.emit(TokenType.DOUBLE_DOT)
            return lex_descendant_segment
        return lex_shorthand_selector

    if c == "[":
        l.emit(TokenType.LBRACKET)
        return lex_inside_bracketed_segment

    # default
    l.backup()
    if l.filter_depth:
        return lex_inside_filter

    l.error(f"expected '.', '..' or a bracketed selection, found {c!r}")
    return None


def lex_descendant_segment(l: Lexer) -> Optional[StateFn]:  # noqa: D103
    c = l.next()

    if c == "":
        l.error("bald descendant segment")
        return None

    if c == "*":
        l.emit(TokenType.WILD)
        return lex_segment

    if c == "[":
        l.emit(TokenType.LBRACKET)
        return lex_inside_bracketed_segment

    # default
    l.backup()

    if l.accept_match(RE_PROPERTY):
        l.emit(TokenType.PROPERTY)
        return lex_segment

    l.error(f"unexpected descendant selection token {c!r}")
    return None


def lex_shorthand_selector(l: Lexer) -> Optional[StateFn]:  # noqa: D103
    l.ignore()  # ignore dot

    if l.ignore_whitespace():
        l.error("unexpected whitespace after dot")
        return None

    c = l.next()

    if c == "*":
        l.emit(TokenType.WILD)
        return lex_segment

    l.backup()

    if l.accept_match(RE_PROPERTY):
        l.emit(TokenType.PROPERTY)
        return lex_segment

    l.error(f"unexpected shorthand selector {c!r}")
    return None


def lex_inside_bracketed_segment(l: Lexer) -> Optional[StateFn]:  # noqa: PLR0911, D103
    while True:
        l.ignore_whitespace()
        c = l.next()

        if c == "]":
            l.emit(TokenType.RBRACKET)
            if l.filter_depth:
                return lex_inside_filter
            return lex_segment

        if c == "":
            l.error("unclosed bracketed selection")
            return None

        if c == "*":
            l.emit(TokenType.WILD)
            continue

        if c == "?":
            l.emit(TokenType.FILTER)
            l.filter_depth += 1
            return lex_inside_filter

        if c == ",":
            l.emit(TokenType.COMMA)
            continue

        if c == ":":
            l.emit(TokenType.COLON)
            continue

        if c == "'":
            # Quoted dict/object key/property name
            return lex_single_quoted_string_inside_bracket_segment

        if c == '"':
            # Quoted dict/object key/property name
            return lex_double_quoted_string_inside_bracket_segment

        # default
        l.backup()

        if l.accept_match(RE_INDEX):
            # Index selector or part of a slice selector.
            l.emit(TokenType.INDEX)
            continue

        l.error(f"unexpected token {c!r} in bracketed selection")
        return None


def lex_inside_filter(l: Lexer) -> Optional[StateFn]:  # noqa: D103, PLR0915, PLR0912, PLR0911
    while True:
        l.ignore_whitespace()
        c = l.next()

        if c == "":
            l.error("unclosed bracketed selection")
            return None

        if c == "]":
            l.filter_depth -= 1
            if len(l.paren_stack) == 1:
                l.error("unbalanced parentheses")
                return None

            l.backup()
            return lex_inside_bracketed_segment

        if c == ",":
            l.emit(TokenType.COMMA)
            # If we have unbalanced parens, we are inside a function call and a
            # comma separates arguments. Otherwise a comma separates selectors.
            if l.paren_stack:
                continue
            l.filter_depth -= 1
            return lex_inside_bracketed_segment

        if c == "'":
            # String literal
            return lex_single_quoted_string_inside_filter_expression

        if c == '"':
            # String literal
            return lex_double_quoted_string_inside_filter_expression

        if c == "(":
            l.emit(TokenType.LPAREN)
            # Are we in a function call? If so, a function argument contains parens.
            if l.paren_stack:
                l.paren_stack[-1] += 1
            continue

        if c == ")":
            l.emit(TokenType.RPAREN)
            # Are we closing a function call or a parenthesized expression?
            if l.paren_stack:
                if l.paren_stack[-1] == 1:
                    l.paren_stack.pop()
                else:
                    l.paren_stack[-1] -= 1
            continue

        if c == "$":
            l.emit(TokenType.ROOT)
            return lex_segment

        if c == "@":
            l.emit(TokenType.CURRENT)
            return lex_segment

        if c == ".":
            l.backup()
            return lex_segment

        if c == "!":
            if l.peek() == "=":
                l.next()
                l.emit(TokenType.NE)
            else:
                l.emit(TokenType.NOT)
            continue

        if c == "=":
            if l.peek() == "=":
                l.next()
                l.emit(TokenType.EQ)
                continue

            l.backup()
            l.error(f"unexpected filter selector token {c!r}")
            return None

        if c == "<":
            if l.peek() == "=":
                l.next()
                l.emit(TokenType.LE)
            else:
                l.emit(TokenType.LT)
            continue

        if c == ">":
            if l.peek() == "=":
                l.next()
                l.emit(TokenType.GE)
            else:
                l.emit(TokenType.GT)
            continue

        # default
        l.backup()

        # numbers
        # TODO: try accept_match(RE_FLOAT), including negative exponent
        if l.accept_match(RE_INT):
            if l.peek() == ".":
                # A float
                l.next()
                if not l.accept_match(RE_INT):
                    l.error("a fractional digit is required after a decimal point")
                    return None

                l.accept_match(RE_EXPONENT)
                l.emit(TokenType.FLOAT)
                continue

            # An int, or float if exponent is negative
            if l.accept_match(RE_NEGATIVE_EXPONENT):
                l.emit(TokenType.FLOAT)
            else:
                l.accept_match(RE_EXPONENT)
                l.emit(TokenType.INT)
            continue

        if l.accept_match(RE_AND):
            l.emit(TokenType.AND)
            continue

        if l.accept_match(RE_OR):
            l.emit(TokenType.OR)
            continue

        if l.accept_match(RE_TRUE):
            l.emit(TokenType.TRUE)
            continue

        if l.accept_match(RE_FALSE):
            l.emit(TokenType.FALSE)
            continue

        if l.accept_match(RE_NULL):
            l.emit(TokenType.NULL)
            continue

        # functions
        if l.accept_match(RE_FUNCTION_NAME) and l.peek() == "(":
            # Keep track of parentheses for this function call.
            l.paren_stack.append(1)
            l.emit(TokenType.FUNCTION)
            l.next()
            l.ignore()  # ignore LPAREN
            continue

        l.error(f"unexpected filter selector token {c!r}")
        return None


def lex_string_factory(quote: str, state: StateFn) -> StateFn:
    """Return a state function for scanning string literals.

    Arguments:
        quote: One of `'` or `"`. The string delimiter.
        state: The state function to return control to after scanning the string.
    """
    tt = (
        TokenType.SINGLE_QUOTE_STRING if quote == "'" else TokenType.DOUBLE_QUOTE_STRING
    )

    def _lex_string(l: Lexer) -> Optional[StateFn]:
        l.ignore()  # ignore opening quote

        if l.peek() == "":
            # an empty string
            l.emit(tt)
            l.next()
            l.ignore()
            return state

        while True:
            head = l.query[l.pos : l.pos + 2]
            c = l.next()

            if head in ("\\\\", f"\\{quote}"):
                l.next()
                continue

            # TODO: replace use of `head` with peek
            if c == "\\" and not RE_ESCAPE.match(head):
                l.error("invalid escape")
                return None

            if not c:
                l.error(f"unclosed string starting at index {l.start}")
                return None

            if c == quote:
                l.backup()
                l.emit(tt)
                l.next()
                l.ignore()  # ignore closing quote
                return state

    return _lex_string


lex_single_quoted_string_inside_bracket_segment = lex_string_factory(
    "'", lex_inside_bracketed_segment
)

lex_double_quoted_string_inside_bracket_segment = lex_string_factory(
    '"', lex_inside_bracketed_segment
)


lex_single_quoted_string_inside_filter_expression = lex_string_factory(
    "'", lex_inside_filter
)

lex_double_quoted_string_inside_filter_expression = lex_string_factory(
    '"', lex_inside_filter
)


def lex(query: str) -> Tuple[Lexer, List[Token]]:
    """Return a lexer for _query_ and an array to be populated with Tokens."""
    lexer = Lexer(query)
    return lexer, lexer.tokens


def tokenize(query: str) -> List[Token]:
    """Scan JSONPath expression _query_ and return a list of tokens."""
    lexer, tokens = lex(query)
    lexer.run()

    if tokens and tokens[-1].type_ == TokenType.ERROR:
        raise JSONPathSyntaxError(tokens[-1].value, token=tokens[-1])

    return tokens
