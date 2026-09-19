from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, TypeGuard

from ._ast import *
from ._tokens import *
from .exceptions import (
    JSONPathNameError,
    JSONPathSyntaxError,
    JSONPathTypeError,
)
from .functions import LOGICAL_TYPE, NODES_TYPE, VALUE_TYPE, ExpressionType
from .query import JSONPathQuery

if TYPE_CHECKING:
    from ._environment import JSONPathEnvironment

_RE_ESCAPE_U = re.compile(r"(\\u[0-9a-dA-F]{4}|\\.)")


class Parser(Protocol):
    """The parser interface."""

    def parse(self, env: JSONPathEnvironment, source: str) -> JSONPathQuery:
        """Parse JSONPath query source text with configuration from *env*."""
        ...


class Parser_(ABC):
    """A base query parser with methods common to both standard and extra parsers."""

    __slots__ = ("env", "eoi", "length", "pos", "source", "tokens")

    def __init__(
        self,
        env: JSONPathEnvironment,
        source: str,
        tokens: Sequence[Token],
    ) -> None:
        self.env = env
        self.source = source
        self.tokens = tokens
        self.length = len(tokens)
        self.pos = 0
        self.eoi: Token = (TOKEN_EOI, self.length, self.length)

    @abstractmethod
    def parse_query(self) -> tuple[Segment, ...]: ...

    def current(self) -> Token:
        """Return the current token without advancing the pointer."""
        if self.pos < self.length:
            return self.tokens[self.pos]
        return self.eoi

    def kind(self) -> int:
        """Return the kind of the current token without advancing the pointer."""
        if self.pos < self.length:
            return self.tokens[self.pos][0]
        return TOKEN_EOI

    def value(self) -> str:
        """Return the string value associated with the current token."""
        if self.pos < self.length:
            return token_value(self.tokens[self.pos], self.source)
        return ""

    def next(self) -> Token:
        """Return the current token and advance the pointer."""
        if self.pos < self.length:
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return self.eoi

    def peek(self, n: int = 1) -> Token:
        """Return the token a pos+n without advancing the pointer."""
        if self.pos + n < self.length:
            return self.tokens[self.pos + n]
        return self.eoi

    def peek_kind(self, n: int = 1) -> int:
        if self.pos + n < self.length:
            return self.tokens[self.pos + n][0]
        return TOKEN_EOI

    def eat(self, kind: int, message: str | None = None) -> Token:
        token = self.current()
        if token[0] != kind:
            raise JSONPathSyntaxError(
                message or f"unexpected {token_value(token, self.source)!r}",
                token,
                self.source,
            )

        self.pos += 1
        return token

    def skip(self, kind: int) -> bool:
        if self.kind() == kind:
            self.pos += 1
            return True
        return False

    def raise_for_not_compared(self, expr: Expression, token: Token) -> None:
        if self.is_literal_expression(expr):
            raise JSONPathTypeError(
                "filter expression literals must be compared",
                token,
                self.source,
            )

        if expr[0] != FUNCTION_EXPR:
            return

        name = expr[2]
        func = self.env.functions.get(name)

        if not func:
            raise JSONPathNameError(
                f"unknown function {name!r}",
                token,
                self.source,
            )

        if func.return_type == VALUE_TYPE:
            raise JSONPathTypeError(
                f"result of {name!r} must be compared",
                token,
                self.source,
            )

    def raise_for_not_comparable(self, expr: Expression, token: Token) -> None:
        if self.is_query_expression(expr) and not self.is_singular_query(expr):
            raise JSONPathTypeError(
                "non-singular query is not comparable",
                token,
                self.source,
            )

        if expr[0] != FUNCTION_EXPR:
            return

        name = expr[2]
        func = self.env.functions.get(name)

        if not func:
            raise JSONPathNameError(
                f"unknown function {name!r}",
                token,
                self.source,
            )

        if func.return_type != VALUE_TYPE:
            raise JSONPathTypeError(
                f"result of {name!r} is not comparable",
                token,
                self.source,
            )

    def validate_function_signature(
        self, token: Token, name: str, args: list[Expression]
    ) -> None:
        func = self.env.functions.get(name)

        if not func:
            raise JSONPathNameError(
                f"unknown function {name!r}",
                token,
                self.source,
            )

        count = len(func.arg_types)

        if len(args) != count:
            raise JSONPathTypeError(
                f"{name}() takes {count} argument{'' if count == 1 else 's'} ({len(args)} given)",
                token,
                self.source,
            )

        for i, (arg, typ) in enumerate(zip(args, func.arg_types)):
            if typ == VALUE_TYPE and not self.is_value_type_expression(arg):
                raise JSONPathTypeError(
                    f"{name}() argument {i} must be a value type",
                    token,
                    self.source,
                )

            if typ == LOGICAL_TYPE and not (
                self.is_query_expression(arg) or self.is_infix_expression(arg)
            ):
                raise JSONPathTypeError(
                    f"{name}() argument {i} must be a logical type",
                    token,
                    self.source,
                )

            if typ == NODES_TYPE and not (
                self.is_query_expression(arg)
                or self.function_return_type(arg) == NODES_TYPE
            ):
                raise JSONPathTypeError(
                    f"{name}() argument {i} must be a nodes type",
                    token,
                    self.source,
                )

    def parse_i_json_int(self, token: Token) -> int:
        value = token_value(token, self.source)

        if len(value) > 1 and value.startswith(("0", "-0")):
            raise JSONPathSyntaxError(
                f"invalid index {value!r}",
                token,
                self.source,
            )

        n = int(value)

        if n < self.env.min_index or n > self.env.max_index:
            # TODO: Different exception?
            raise JSONPathSyntaxError(
                f"index out of range {n}",
                token,
                self.source,
            )

        return n

    def function_return_type(self, expr: Expression) -> ExpressionType | None:
        if expr[0] == FUNCTION_EXPR:
            func = self.env.functions.get(expr[2])
            if func:
                return func.return_type

        return None

    def decode_string_literal(self, token: Token) -> str:
        kind = token[0]
        value = token_value(token, self.source)

        if kind == TOKEN_SINGLE_QUOTED_STRING or kind == TOKEN_DOUBLE_QUOTED_STRING:
            return value

        if kind == TOKEN_SINGLE_QUOTED_ESC_STRING:
            value = value.replace('"', '\\"').replace("\\'", "'")

        return self.unescape(value, token)

    def unescape(self, escaped: str, token: Token) -> str:
        unescaped: list[str] = []
        parts = [p for p in _RE_ESCAPE_U.split(escaped) if p]
        length = len(parts)
        pos = 0

        while pos < length:
            part = parts[pos]
            pos += 1

            if not part.startswith("\\"):
                unescaped.append(part)
            elif part == '\\"':
                unescaped.append('"')
            elif part == "\\\\":
                unescaped.append("\\")
            elif part == "\\/":
                unescaped.append("/")
            elif part == "\\b":
                unescaped.append("\b")
            elif part == "\\f":
                unescaped.append("\f")
            elif part == "\\n":
                unescaped.append("\n")
            elif part == "\\r":
                unescaped.append("\r")
            elif part == "\\t":
                unescaped.append("\t")
            elif part == "\\u":
                # Subsequent \u is guaranteed to be followed by four hex digits.
                raise JSONPathSyntaxError(
                    "invalid escape sequence",
                    token,
                    self.source,
                )
            elif part.startswith("\\u"):
                code_point = int(part[2:], 16)  # noqa: FURB166

                if is_low_surrogate(code_point):
                    raise JSONPathSyntaxError(
                        "invalid escape sequence",
                        token,
                        self.source,
                    )

                if is_high_surrogate(code_point):
                    if pos >= length:
                        raise JSONPathSyntaxError(
                            "invalid escape sequence",
                            token,
                            self.source,
                        )

                    next_part = parts[pos]
                    pos += 1

                    if not (len(next_part) == 6 and next_part.startswith("\\u")):
                        raise JSONPathSyntaxError(
                            "invalid escape sequence",
                            token,
                            self.source,
                        )

                    low_surrogate = int(next_part[2:], 16)  # noqa: FURB166

                    if not is_low_surrogate(low_surrogate):
                        raise JSONPathSyntaxError(
                            "invalid escape sequence",
                            token,
                            self.source,
                        )

                    code_point = 0x10000 + (
                        ((code_point & 0x03FF) << 10) | (low_surrogate & 0x03FF)
                    )

                if code_point <= 0x1F:
                    raise JSONPathSyntaxError(
                        "invalid escape sequence",
                        token,
                        self.source,
                    )

                unescaped.append(chr(code_point))
            else:
                raise JSONPathSyntaxError(
                    "invalid escape sequence",
                    token,
                    self.source,
                )

        return "".join(unescaped)

    def is_literal_expression(
        self, expr: Expression
    ) -> TypeGuard[
        NullExpression
        | BoolExpression
        | StringExpression
        | IntExpression
        | FloatExpression
    ]:
        return expr[0] in (
            NULL_EXPR,
            BOOL_EXPR,
            STRING_EXPR,
            INT_EXPR,
            FLOAT_EXPR,
        )

    def is_value_type_expression(self, expr: Expression) -> bool:
        if expr[0] in (
            NULL_EXPR,
            BOOL_EXPR,
            STRING_EXPR,
            INT_EXPR,
            FLOAT_EXPR,
        ):
            return True

        if self.is_query_expression(expr) and self.is_singular_query(expr):
            return True

        return self.function_return_type(expr) == VALUE_TYPE

    def is_query_expression(
        self, expr: Expression
    ) -> TypeGuard[AbsoluteQueryExpression | RelativeQueryExpression]:
        return expr[0] in (ABSOLUTE_QUERY_EXPR, RELATIVE_QUERY_EXPR)

    def is_infix_expression(
        self,
        expr: Expression,
    ) -> TypeGuard[
        AndExpression
        | OrExpression
        | EqExpression
        | NeExpression
        | GtExpression
        | GeExpression
        | LtExpression
        | LeExpression
    ]:
        return expr[0] in (
            AND_EXPR,
            OR_EXPR,
            EQ_EXPR,
            NE_EXPR,
            GT_EXPR,
            GE_EXPR,
            LT_EXPR,
            LE_EXPR,
        )

    def is_singular_query(
        self, query: AbsoluteQueryExpression | RelativeQueryExpression
    ) -> bool:
        for kind, _, selectors in query[2]:
            if kind == DESCENDANT_SEGMENT:
                return False

            if len(selectors) > 1:
                return False

            if selectors[0][0] in (NAME_SELECTOR, INDEX_SELECTOR):  # pyright: ignore[reportGeneralTypeIssues]
                continue

            return False

        return True


def is_high_surrogate(codepoint: int) -> bool:
    return 0xD800 <= codepoint <= 0xDBFF


def is_low_surrogate(codepoint: int) -> bool:
    return 0xDC00 <= codepoint <= 0xDFFF
