"""The default JSONPath parser."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from jsonpath_rfc9535.function_extensions.filter_function import ExpressionType
from jsonpath_rfc9535.function_extensions.filter_function import FilterFunction

from .exceptions import JSONPathSyntaxError
from .exceptions import JSONPathTypeError
from .filter_expressions import BooleanLiteral
from .filter_expressions import ComparisonExpression
from .filter_expressions import Expression
from .filter_expressions import FilterExpression
from .filter_expressions import FilterExpressionLiteral
from .filter_expressions import FilterQuery
from .filter_expressions import FloatLiteral
from .filter_expressions import FunctionExtension
from .filter_expressions import IntegerLiteral
from .filter_expressions import LogicalExpression
from .filter_expressions import NullLiteral
from .filter_expressions import PrefixExpression
from .filter_expressions import RelativeFilterQuery
from .filter_expressions import RootFilterQuery
from .filter_expressions import StringLiteral
from .query import JSONPathQuery
from .segments import JSONPathChildSegment
from .segments import JSONPathRecursiveDescentSegment
from .segments import JSONPathSegment
from .selectors import Filter
from .selectors import IndexSelector
from .selectors import JSONPathSelector
from .selectors import NameSelector
from .selectors import SliceSelector
from .selectors import WildcardSelector
from .tokens import Token
from .tokens import TokenType

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment
    from .tokens import TokenStream

# ruff: noqa: D102


class Parser:
    """A JSONPath expression parser bound to a `JSONPathEnvironment`."""

    PRECEDENCE_LOWEST = 1
    PRECEDENCE_LOGICAL_OR = 3
    PRECEDENCE_LOGICAL_AND = 4
    PRECEDENCE_RELATIONAL = 5
    PRECEDENCE_PREFIX = 7

    PRECEDENCES = {
        TokenType.AND: PRECEDENCE_LOGICAL_AND,
        TokenType.EQ: PRECEDENCE_RELATIONAL,
        TokenType.GE: PRECEDENCE_RELATIONAL,
        TokenType.GT: PRECEDENCE_RELATIONAL,
        TokenType.LE: PRECEDENCE_RELATIONAL,
        TokenType.LT: PRECEDENCE_RELATIONAL,
        TokenType.NE: PRECEDENCE_RELATIONAL,
        TokenType.NOT: PRECEDENCE_PREFIX,
        TokenType.OR: PRECEDENCE_LOGICAL_OR,
        TokenType.RPAREN: PRECEDENCE_LOWEST,
    }

    # Mapping of operator token to canonical string.
    BINARY_OPERATORS = {
        TokenType.AND: "&&",
        TokenType.EQ: "==",
        TokenType.GE: ">=",
        TokenType.GT: ">",
        TokenType.LE: "<=",
        TokenType.LT: "<",
        TokenType.NE: "!=",
        TokenType.OR: "||",
    }

    COMPARISON_OPERATORS = frozenset(
        [
            "==",
            ">=",
            ">",
            "<=",
            "<",
            "!=",
        ]
    )

    def __init__(self, *, env: JSONPathEnvironment) -> None:
        self.env = env

        self.token_map: Dict[TokenType, Callable[[TokenStream], Expression]] = {
            TokenType.DOUBLE_QUOTE_STRING: self.parse_string_literal,
            TokenType.FALSE: self.parse_boolean,
            TokenType.FLOAT: self.parse_float_literal,
            TokenType.FUNCTION: self.parse_function_extension,
            TokenType.INT: self.parse_integer_literal,
            TokenType.LPAREN: self.parse_grouped_expression,
            TokenType.NOT: self.parse_prefix_expression,
            TokenType.NULL: self.parse_null,
            TokenType.ROOT: self.parse_root_query,
            TokenType.CURRENT: self.parse_relative_query,
            TokenType.SINGLE_QUOTE_STRING: self.parse_string_literal,
            TokenType.TRUE: self.parse_boolean,
        }

        # TODO: can a function argument be a grouped expression?
        # TODO: can a function argument contain a !?

        self.function_argument_map: Dict[
            TokenType, Callable[[TokenStream], Expression]
        ] = {
            TokenType.DOUBLE_QUOTE_STRING: self.parse_string_literal,
            TokenType.FALSE: self.parse_boolean,
            TokenType.FLOAT: self.parse_float_literal,
            TokenType.FUNCTION: self.parse_function_extension,
            TokenType.INT: self.parse_integer_literal,
            TokenType.NULL: self.parse_null,
            TokenType.ROOT: self.parse_root_query,
            TokenType.CURRENT: self.parse_relative_query,
            TokenType.SINGLE_QUOTE_STRING: self.parse_string_literal,
            TokenType.TRUE: self.parse_boolean,
        }

    def parse(self, stream: TokenStream) -> Iterable[JSONPathSegment]:
        """Parse a JSONPath expression from a stream of tokens."""
        stream.expect(TokenType.ROOT)
        stream.next_token()
        yield from self.parse_query(stream, in_filter=False)

        if stream.current.type_ != TokenType.EOF:
            raise JSONPathSyntaxError(
                f"unexpected token {stream.current.value!r}",
                token=stream.current,
            )

    def parse_query(
        self,
        stream: TokenStream,
        *,
        in_filter: bool = False,
    ) -> Iterable[JSONPathSegment]:
        """Parse a top-level JSONPath expression or a filter query."""
        while True:
            if stream.current.type_ == TokenType.DOUBLE_DOT:
                tok = stream.next_token()
                selectors = self.parse_selectors(stream)
                yield JSONPathRecursiveDescentSegment(
                    env=self.env,
                    token=tok,
                    selectors=selectors,
                )
            elif stream.current.type_ in {
                TokenType.LBRACKET,
                TokenType.PROPERTY,
                TokenType.WILD,
            }:
                tok = stream.current
                selectors = self.parse_selectors(stream)
                yield JSONPathChildSegment(
                    env=self.env,
                    token=tok,
                    selectors=selectors,
                )
            else:
                if in_filter:
                    stream.push(stream.current)
                break

            stream.next_token()

    def parse_selectors(self, stream: TokenStream) -> Tuple[JSONPathSelector, ...]:
        """Parse JSONPath selectors from a stream of tokens."""
        if stream.current.type_ == TokenType.PROPERTY:
            return (
                NameSelector(
                    env=self.env,
                    token=stream.current,
                    name=stream.current.value,
                ),
            )

        if stream.current.type_ == TokenType.WILD:
            return (WildcardSelector(env=self.env, token=stream.current),)

        if stream.current.type_ == TokenType.LBRACKET:
            return tuple(self.parse_bracketed_selection(stream))

        return ()

    def parse_slice(self, stream: TokenStream) -> SliceSelector:
        """Parse a slice selector."""
        tok = stream.current
        start: Optional[int] = None
        stop: Optional[int] = None
        step: Optional[int] = None

        def _maybe_index(token: Token) -> bool:
            if token.type_ == TokenType.INDEX:
                if len(token.value) > 1 and token.value.startswith(("0", "-0")):
                    raise JSONPathSyntaxError(
                        f"invalid index {token.value!r}", token=token
                    )
                return True
            return False

        # 1: or :
        if _maybe_index(stream.current):
            start = int(stream.current.value)
            stream.next_token()

        stream.expect(TokenType.COLON)
        stream.next_token()

        # 1 or 1: or : or ?
        if _maybe_index(stream.current):
            stop = int(stream.current.value)
            stream.next_token()
            if stream.current.type_ == TokenType.COLON:
                stream.next_token()
        elif stream.current.type_ == TokenType.COLON:
            stream.expect(TokenType.COLON)
            stream.next_token()

        # 1 or ?
        if _maybe_index(stream.current):
            step = int(stream.current.value)
            stream.next_token()

        stream.push(stream.current)

        return SliceSelector(
            env=self.env,
            token=tok,
            start=start,
            stop=stop,
            step=step,
        )

    def parse_bracketed_selection(self, stream: TokenStream) -> List[JSONPathSelector]:  # noqa: PLR0912
        """Parse a comma separated list of JSONPath selectors."""
        tok = stream.next_token()  # Skip LBRACKET
        selectors: List[JSONPathSelector] = []

        while stream.current.type_ != TokenType.RBRACKET:
            if stream.current.type_ == TokenType.INDEX:
                if stream.peek.type_ == TokenType.COLON:
                    selectors.append(self.parse_slice(stream))
                else:
                    if (
                        len(stream.current.value) > 1
                        and stream.current.value.startswith("0")
                    ) or stream.current.value.startswith("-0"):
                        raise JSONPathSyntaxError(
                            "leading zero in index selector", token=stream.current
                        )
                    selectors.append(
                        IndexSelector(
                            env=self.env,
                            token=stream.current,
                            index=int(stream.current.value),
                        )
                    )
            elif stream.current.type_ in (
                TokenType.DOUBLE_QUOTE_STRING,
                TokenType.SINGLE_QUOTE_STRING,
            ):
                selectors.append(
                    NameSelector(
                        env=self.env,
                        token=stream.current,
                        name=self._decode_string_literal(stream.current),
                    ),
                )
            elif stream.current.type_ == TokenType.COLON:
                selectors.append(self.parse_slice(stream))
            elif stream.current.type_ == TokenType.WILD:
                selectors.append(
                    WildcardSelector(
                        env=self.env,
                        token=stream.current,
                    )
                )
            elif stream.current.type_ == TokenType.FILTER:
                selectors.append(self.parse_filter(stream))
            elif stream.current.type_ == TokenType.EOF:
                raise JSONPathSyntaxError(
                    "unexpected end of query", token=stream.current
                )
            else:
                raise JSONPathSyntaxError(
                    f"unexpected token in bracketed selection {stream.current.type_!r}",
                    token=stream.current,
                )

            if stream.peek.type_ == TokenType.EOF:
                raise JSONPathSyntaxError(
                    "unexpected end of selector list",
                    token=stream.current,
                )

            if stream.peek.type_ != TokenType.RBRACKET:
                stream.expect_peek(TokenType.COMMA)
                stream.next_token()
                stream.expect_peek_not(TokenType.RBRACKET, "unexpected trailing comma")

            stream.next_token()

        if not selectors:
            raise JSONPathSyntaxError("empty bracketed segment", token=tok)

        return selectors

    def parse_filter(self, stream: TokenStream) -> Filter:
        tok = stream.next_token()
        expr = self.parse_filter_selector(stream)

        if isinstance(expr, FunctionExtension):
            func = self.env.function_extensions.get(expr.name)
            if (
                func
                and isinstance(func, FilterFunction)
                and func.return_type == ExpressionType.VALUE
            ):
                raise JSONPathTypeError(
                    f"result of {expr.name}() must be compared", token=tok
                )

        if isinstance(expr, FilterExpressionLiteral):
            raise JSONPathSyntaxError(
                "filter expression literals outside of "
                "function expressions must be compared",
                token=expr.token,
            )

        return Filter(
            env=self.env,
            token=tok,
            expression=FilterExpression(token=expr.token, expression=expr),
        )

    def parse_boolean(self, stream: TokenStream) -> Expression:
        if stream.current.type_ == TokenType.TRUE:
            return BooleanLiteral(stream.current, True)  # noqa: FBT003
        return BooleanLiteral(stream.current, False)  # noqa: FBT003

    def parse_null(self, stream: TokenStream) -> Expression:
        return NullLiteral(stream.current, None)

    def parse_string_literal(self, stream: TokenStream) -> Expression:
        return StringLiteral(
            stream.current, value=self._decode_string_literal(stream.current)
        )

    def parse_integer_literal(self, stream: TokenStream) -> Expression:
        value = stream.current.value
        if value.startswith("0") and len(value) > 1:
            raise JSONPathSyntaxError("invalid integer literal", token=stream.current)

        # Convert to float first to handle scientific notation.
        try:
            return IntegerLiteral(stream.current, value=int(float(value)))
        except ValueError as err:
            raise JSONPathSyntaxError(
                "invalid integer literal", token=stream.current
            ) from err

    def parse_float_literal(self, stream: TokenStream) -> Expression:
        value = stream.current.value
        if value.startswith("0") and len(value.split(".")[0]) > 1:
            raise JSONPathSyntaxError("invalid float literal", token=stream.current)

        try:
            return FloatLiteral(stream.current, value=float(stream.current.value))
        except ValueError as err:
            raise JSONPathSyntaxError(
                "invalid float literal", token=stream.current
            ) from err

    def parse_prefix_expression(self, stream: TokenStream) -> Expression:
        tok = stream.next_token()
        assert tok.type_ == TokenType.NOT
        return PrefixExpression(
            tok,
            operator="!",
            right=self.parse_filter_selector(stream, precedence=self.PRECEDENCE_PREFIX),
        )

    def parse_infix_expression(
        self, stream: TokenStream, left: Expression
    ) -> Expression:
        tok = stream.next_token()
        precedence = self.PRECEDENCES.get(tok.type_, self.PRECEDENCE_LOWEST)
        right = self.parse_filter_selector(stream, precedence)
        operator = self.BINARY_OPERATORS[tok.type_]

        if operator in self.COMPARISON_OPERATORS:
            self._raise_for_non_comparable_function(left, tok)
            self._raise_for_non_comparable_function(right, tok)
            return ComparisonExpression(tok, left, operator, right)

        if isinstance(left, FilterExpressionLiteral):
            raise JSONPathSyntaxError(
                "filter expression literals outside of "
                "function expressions must be compared",
                token=left.token,
            )
        if isinstance(right, FilterExpressionLiteral):
            raise JSONPathSyntaxError(
                "filter expression literals outside of "
                "function expressions must be compared",
                token=right.token,
            )

        return LogicalExpression(tok, left, operator, right)

    def parse_grouped_expression(self, stream: TokenStream) -> Expression:
        stream.next_token()
        expr = self.parse_filter_selector(stream)
        stream.next_token()

        while stream.current.type_ != TokenType.RPAREN:
            if stream.current.type_ == TokenType.EOF:
                raise JSONPathSyntaxError(
                    "unbalanced parentheses", token=stream.current
                )
            # TODO: only if binary op
            expr = self.parse_infix_expression(stream, expr)

        stream.expect(TokenType.RPAREN)
        return expr

    def parse_root_query(self, stream: TokenStream) -> Expression:
        root = stream.next_token()
        assert root.type_ == TokenType.ROOT
        return RootFilterQuery(
            token=root,
            query=JSONPathQuery(
                env=self.env,
                segments=tuple(self.parse_query(stream, in_filter=True)),
            ),
        )

    def parse_relative_query(self, stream: TokenStream) -> Expression:
        tok = stream.next_token()
        return RelativeFilterQuery(
            token=tok,
            query=JSONPathQuery(
                env=self.env, segments=tuple(self.parse_query(stream, in_filter=True))
            ),
        )

    def parse_function_extension(self, stream: TokenStream) -> Expression:
        function_arguments: List[Expression] = []
        tok = stream.next_token()

        while stream.current.type_ != TokenType.RPAREN:
            try:
                func = self.function_argument_map[stream.current.type_]
            except KeyError as err:
                raise JSONPathSyntaxError(
                    f"unexpected {stream.current.value!r}",
                    token=stream.current,
                ) from err

            expr = func(stream)

            # The argument could be a comparison or logical expression
            peek_kind = stream.peek.type_
            while peek_kind in self.BINARY_OPERATORS:
                stream.next_token()
                expr = self.parse_infix_expression(stream, expr)
                peek_kind = stream.peek.type_

            function_arguments.append(expr)

            if stream.peek.type_ != TokenType.RPAREN:
                stream.expect_peek(TokenType.COMMA)
                stream.next_token()

            stream.next_token()

        return FunctionExtension(
            token=tok,
            name=tok.value,
            args=self.env.validate_function_extension_signature(
                tok, function_arguments
            ),
        )

    def parse_filter_selector(
        self, stream: TokenStream, precedence: int = PRECEDENCE_LOWEST
    ) -> Expression:
        try:
            left = self.token_map[stream.current.type_](stream)
        except KeyError as err:
            if stream.current.type_ in (TokenType.EOF, TokenType.RBRACKET):
                msg = "end of expression"
            else:
                msg = repr(stream.current.value)
            raise JSONPathSyntaxError(
                f"unexpected {msg}", token=stream.current
            ) from err

        while True:
            peek_kind = stream.peek.type_
            if (
                peek_kind in (TokenType.EOF, TokenType.RBRACKET)
                or self.PRECEDENCES.get(peek_kind, self.PRECEDENCE_LOWEST) < precedence
            ):
                break

            if peek_kind not in self.BINARY_OPERATORS:
                return left

            stream.next_token()
            left = self.parse_infix_expression(stream, left)

        return left

    def _decode_string_literal(self, token: Token) -> str:
        if token.type_ == TokenType.SINGLE_QUOTE_STRING:
            value = token.value.replace('"', '\\"').replace("\\'", "'")
        else:
            value = token.value

        return self._unescape_string(value, token)

    def _unescape_string(self, value: str, token: Token) -> str:
        unescaped: List[str] = []
        index = 0

        while index < len(value):
            ch = value[index]
            if ch == "\\":
                index += 1
                _ch, index = self._decode_escape_sequence(value, index, token)
                unescaped.append(_ch)
            else:
                self._string_from_codepoint(ord(ch), token)
                unescaped.append(ch)
            index += 1
        return "".join(unescaped)

    def _decode_escape_sequence(  # noqa: PLR0911
        self, value: str, index: int, token: Token
    ) -> Tuple[str, int]:
        ch = value[index]
        if ch == '"':
            return '"', index
        if ch == "\\":
            return "\\", index
        if ch == "/":
            return "/", index
        if ch == "b":
            return "\x08", index
        if ch == "f":
            return "\x0c", index
        if ch == "n":
            return "\n", index
        if ch == "r":
            return "\r", index
        if ch == "t":
            return "\t", index
        if ch == "u":
            codepoint, index = self._decode_hex_char(value, index, token)
            return self._string_from_codepoint(codepoint, token), index

        raise JSONPathSyntaxError(
            f"unknown escape sequence at index {token.index + index - 1}",
            token=token,
        )

    def _decode_hex_char(self, value: str, index: int, token: Token) -> Tuple[int, int]:
        length = len(value)

        if index + 4 >= length:
            raise JSONPathSyntaxError(
                f"incomplete escape sequence at index {token.index + index - 1}",
                token=token,
            )

        index += 1  # move past 'u'
        codepoint = self._parse_hex_digits(value[index : index + 4], token)

        if self._is_low_surrogate(codepoint):
            raise JSONPathSyntaxError(
                f"unexpected low surrogate at index {token.index + index - 1}",
                token=token,
            )

        if self._is_high_surrogate(codepoint):
            # expect a surrogate pair
            if not (
                index + 9 < length
                and value[index + 4] == "\\"
                and value[index + 5] == "u"
            ):
                raise JSONPathSyntaxError(
                    f"incomplete escape sequence at index {token.index + index - 2}",
                    token=token,
                )

            low_surrogate = self._parse_hex_digits(value[index + 6 : index + 10], token)

            if not self._is_low_surrogate(low_surrogate):
                raise JSONPathSyntaxError(
                    f"unexpected codepoint at index {token.index + index + 4}",
                    token=token,
                )

            codepoint = 0x10000 + (
                ((codepoint & 0x03FF) << 10) | (low_surrogate & 0x03FF)
            )

            return (codepoint, index + 9)

        return (codepoint, index + 3)

    def _parse_hex_digits(self, digits: str, token: Token) -> int:
        codepoint = 0
        for digit in digits.encode():
            codepoint <<= 4
            if digit >= 48 and digit <= 57:
                codepoint |= digit - 48
            elif digit >= 65 and digit <= 70:
                codepoint |= digit - 65 + 10
            elif digit >= 97 and digit <= 102:
                codepoint |= digit - 97 + 10
            else:
                raise JSONPathSyntaxError(
                    "invalid \\uXXXX escape sequence",
                    token=token,
                )
        return codepoint

    def _string_from_codepoint(self, codepoint: int, token: Token) -> str:
        if codepoint <= 0x1F:
            raise JSONPathSyntaxError("invalid character", token=token)
        return chr(codepoint)

    def _is_high_surrogate(self, codepoint: int) -> bool:
        return codepoint >= 0xD800 and codepoint <= 0xDBFF

    def _is_low_surrogate(self, codepoint: int) -> bool:
        return codepoint >= 0xDC00 and codepoint <= 0xDFFF

    def _raise_for_non_comparable_function(
        self, expr: Expression, token: Token
    ) -> None:
        if isinstance(expr, FilterQuery) and not expr.query.singular_query():
            raise JSONPathTypeError("non-singular query is not comparable", token=token)

        if isinstance(expr, FunctionExtension):
            func = self.env.function_extensions.get(expr.name)
            if (
                isinstance(func, FilterFunction)
                and func.return_type != ExpressionType.VALUE
            ):
                raise JSONPathTypeError(
                    f"result of {expr.name}() is not comparable", token
                )
