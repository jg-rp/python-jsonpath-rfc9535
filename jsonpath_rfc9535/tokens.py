"""JSONPath expression tokens, as produced by the lexer."""

from __future__ import annotations

from collections import deque
from enum import Enum
from enum import auto
from typing import Deque
from typing import Iterable
from typing import Iterator
from typing import Tuple

from .exceptions import JSONPathSyntaxError


class TokenType(Enum):
    """JSONPath expression token types."""

    EOF = auto()
    ERROR = auto()
    INIT = auto()

    SHORTHAND_PROPERTY = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    DOUBLE_DOT = auto()
    FILTER = auto()
    INDEX = auto()
    LBRACKET = auto()
    PROPERTY = auto()
    RBRACKET = auto()
    ROOT = auto()
    WILD = auto()

    AND = auto()
    CURRENT = auto()
    DOUBLE_QUOTE_STRING = auto()
    EQ = auto()
    FALSE = auto()
    FLOAT = auto()
    FUNCTION = auto()
    GE = auto()
    GT = auto()
    INT = auto()
    LE = auto()
    LPAREN = auto()
    LT = auto()
    NE = auto()
    NOT = auto()
    NULL = auto()
    OP = auto()
    OR = auto()
    RPAREN = auto()
    SINGLE_QUOTE_STRING = auto()
    TRUE = auto()


class Token:
    """A JSONPath expression token, as produced by the lexer.

    Attributes:
        kind (TokenType): The token's type.
        value (str): The _path_ substring containing text for the token.
        index (str): The index at which _value_ starts in _path_.
        query (str): A reference to the complete JSONPath string from which this
            token derives.
    """

    __slots__ = ("type_", "value", "index", "query", "message")

    def __init__(
        self,
        type_: TokenType,
        value: str,
        index: int,
        query: str,
        message: str | None = None,
    ) -> None:
        self.type_ = type_
        self.value = value
        self.index = index
        self.query = query
        self.message = message

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Token(type={self.type_.name!r}, value={self.value!r}, "
            f"index={self.index}, query={self.query!r}, message={self.message!r})"
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Token)
            and self.type_ == other.type_
            and self.value == other.value
            and self.index == other.index
            and self.query == other.query
        )

    def __hash__(self) -> int:
        return hash((self.type_, self.value, self.index, self.query))

    def position(self) -> Tuple[int, int]:
        """Return the line and column number for the start of this token."""
        line_number = self.value.count("\n", 0, self.index) + 1
        column_number = self.index - self.value.rfind("\n", 0, self.index)
        return (line_number, column_number - 1)


class TokenStream:
    """Step through or iterate a stream of tokens."""

    def __init__(self, token_iter: Iterable[Token]):
        self.iter = iter(token_iter)
        self._pushed: Deque[Token] = deque()
        self.current = Token(TokenType.INIT, "", -1, "")
        next(self)

    class TokenStreamIterator:
        """An iterable token stream."""

        def __init__(self, stream: TokenStream):
            self.stream = stream

        def __iter__(self) -> Iterator[Token]:
            return self

        def __next__(self) -> Token:
            tok = self.stream.current
            if tok.type_ is TokenType.EOF:
                self.stream.close()
                raise StopIteration
            next(self.stream)
            return tok

    def __iter__(self) -> Iterator[Token]:
        return self.TokenStreamIterator(self)

    def __next__(self) -> Token:
        tok = self.current
        if self._pushed:
            self.current = self._pushed.popleft()
        elif self.current.type_ is not TokenType.EOF:
            try:
                self.current = next(self.iter)
            except StopIteration:
                self.close()
        return tok

    def __str__(self) -> str:  # pragma: no cover
        return f"current: {self.current}\nnext: {self.peek}"

    def next_token(self) -> Token:
        """Return the next token from the stream."""
        return next(self)

    @property
    def peek(self) -> Token:
        """Look at the next token."""
        current = next(self)
        result = self.current
        self.push(current)
        return result

    def push(self, tok: Token) -> None:
        """Push a token back to the stream."""
        self._pushed.append(self.current)
        self.current = tok

    def close(self) -> None:
        """Close the stream."""
        self.current = Token(TokenType.EOF, "", -1, "")

    def expect(self, *typ: TokenType) -> None:
        """Raise an exception if the current token type is not one of _type_."""
        if self.current.type_ not in typ:
            if len(typ) == 1:
                _typ = repr(typ[0])
            else:
                _typ = f"one of {[t.name for t in typ]!r}"
            raise JSONPathSyntaxError(
                f"expected {_typ}, found {self.current.type_.name!r}",
                token=self.current,
            )

    def expect_peek(self, *typ: TokenType) -> None:
        """Raise an exception if the next token type is not one of _type_."""
        if self.peek.type_ not in typ:
            if len(typ) == 1:
                _typ = repr(typ[0].name)
            else:
                _typ = f"one of {[t.name for t in typ]!r}"
            raise JSONPathSyntaxError(
                f"expected {_typ}, found {self.peek.type_.name!r}",
                token=self.peek,
            )

    def expect_peek_not(self, typ: TokenType, message: str) -> None:
        """Raise an exception if the next token type is not one of _type_."""
        if self.peek.type_ == typ:
            raise JSONPathSyntaxError(message, token=self.peek)
