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
RE_INT = re.compile(r"-?[0-9]+(?:[eE]\+?[0-9]+)?")
# RE_FLOAT includes numbers with a negative exponent and no decimal point.
RE_FLOAT = re.compile(r"(:?-?[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?)|(-?[0-9]+[eE]-[0-9]+)")
RE_FUNCTION_NAME = re.compile(r"[a-z][a-z_0-9]*")
ESCAPES = frozenset(["b", "f", "n", "r", "t", "u", "/", "\\"])


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


StateFn = Callable[[Lexer], Optional["StateFn"]]


def lex_root(l: Lexer) -> Optional[StateFn]:  # noqa: D103
    c = l.next()

    if c != "$":
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
        l.bracket_stack.append((c, l.pos - 1))
        return lex_inside_bracketed_segment

    if l.filter_depth:
        l.backup()
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
        l.bracket_stack.append((c, l.pos - 1))
        return lex_inside_bracketed_segment

    l.backup()

    if l.accept_match(RE_PROPERTY):
        l.emit(TokenType.PROPERTY)
        return lex_segment

    l.next()
    l.error(f"unexpected descendant selection token {c!r}")
    return None


def lex_shorthand_selector(l: Lexer) -> Optional[StateFn]:  # noqa: D103
    l.ignore()  # ignore dot

    if l.accept_match(RE_WHITESPACE):
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
            if not l.bracket_stack or l.bracket_stack[-1][0] != "[":
                l.backup()
                l.error("unbalanced brackets")
                return None

            l.bracket_stack.pop()
            l.emit(TokenType.RBRACKET)
            return lex_segment

        if c == "":
            l.error("unbalanced brackets")
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
            l.backup()
            return lex_inside_bracketed_segment

        if c == ",":
            l.emit(TokenType.COMMA)
            # If we have unbalanced parens, we are inside a function call and a
            # comma separates arguments. Otherwise a comma separates selectors.
            if l.func_call_stack:
                continue
            l.filter_depth -= 1
            return lex_inside_bracketed_segment

        if c == "'":
            return lex_single_quoted_string_inside_filter_expression

        if c == '"':
            return lex_double_quoted_string_inside_filter_expression

        if c == "(":
            l.emit(TokenType.LPAREN)
            l.bracket_stack.append((c, l.pos - 1))
            # Are we in a function call? If so, a function argument contains parens.
            if l.func_call_stack:
                l.func_call_stack[-1] += 1
            continue

        if c == ")":
            if not l.bracket_stack or l.bracket_stack[-1][0] != "(":
                l.backup()
                l.error("unbalanced parentheses")
                return None

            l.bracket_stack.pop()
            l.emit(TokenType.RPAREN)
            # Are we closing a function call or a parenthesized expression?
            if l.func_call_stack:
                if l.func_call_stack[-1] == 1:
                    l.func_call_stack.pop()
                else:
                    l.func_call_stack[-1] -= 1
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

        l.backup()

        if l.accept("&&"):
            l.emit(TokenType.AND)
        elif l.accept("||"):
            l.emit(TokenType.OR)
        elif l.accept("true"):
            l.emit(TokenType.TRUE)
        elif l.accept("false"):
            l.emit(TokenType.FALSE)
        elif l.accept("null"):
            l.emit(TokenType.NULL)
        elif l.accept_match(RE_FLOAT):
            l.emit(TokenType.FLOAT)
        elif l.accept_match(RE_INT):
            l.emit(TokenType.INT)
        elif l.accept_match(RE_FUNCTION_NAME) and l.peek() == "(":
            # Keep track of parentheses for this function call.
            l.func_call_stack.append(1)
            l.emit(TokenType.FUNCTION)
            l.bracket_stack.append(("(", l.pos))
            l.next()
            l.ignore()  # ignore LPAREN
        else:
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
            c = l.next()

            if c == "\\":
                peeked = l.peek()
                if peeked in ESCAPES or peeked == quote:
                    l.next()
                else:
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

    # Check for remaining opening brackets that have not been closes.
    if lexer.bracket_stack:
        ch, index = lexer.bracket_stack[0]
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

    if tokens and tokens[-1].type_ == TokenType.ERROR:
        raise JSONPathSyntaxError(tokens[-1].message, token=tokens[-1])

    return tokens
