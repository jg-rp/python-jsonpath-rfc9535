from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, ClassVar

from ._ast import *
from ._lexer import tokenize
from ._parser import Parser_
from ._tokens import *
from .exceptions import JSONPathRecursionError, JSONPathSyntaxError
from .query import JSONPathQuery

if TYPE_CHECKING:
    from ._environment import JSONPathEnvironment


class StandardParser(Parser_):
    """A JSONPath query parser that follows RFC 9535 strictly."""

    PREC_LOWEST = 1
    PREC_LOGICAL_OR = 3
    PREC_LOGICAL_AND = 4
    PREC_RELATIONAL = 5
    PREC_PREFIX = 7

    PRECEDENCES: ClassVar = {
        TOKEN_AND: PREC_LOGICAL_AND,
        TOKEN_EQ: PREC_RELATIONAL,
        TOKEN_GE: PREC_RELATIONAL,
        TOKEN_GT: PREC_RELATIONAL,
        TOKEN_LE: PREC_RELATIONAL,
        TOKEN_LT: PREC_RELATIONAL,
        TOKEN_NE: PREC_RELATIONAL,
        TOKEN_OR: PREC_LOGICAL_OR,
        TOKEN_RIGHT_PAREN: PREC_LOWEST,
    }

    # A mapping of infix operator token kinds to a flag indicating if the
    # operator is a comparison operator.
    INFIX_OPERATORS: ClassVar = {
        TOKEN_AND: False,
        TOKEN_EQ: True,
        TOKEN_GE: True,
        TOKEN_GT: True,
        TOKEN_LE: True,
        TOKEN_LT: True,
        TOKEN_NE: True,
        TOKEN_OR: False,
    }

    __slots__ = ()

    @classmethod
    def parse(cls, env: JSONPathEnvironment, source: str) -> JSONPathQuery:
        try:
            segments = cls(env, source, tokenize(source)).parse_query()
        except RecursionError as err:
            raise JSONPathRecursionError(str(err)) from err

        return JSONPathQuery(env, segments)

    def parse_query(self) -> tuple[Segment, ...]:
        self.eat(TOKEN_DOLLAR)
        segments = tuple(self.parse_segments())
        self.eat(TOKEN_EOI)
        return segments

    def parse_segments(self) -> Iterable[Segment]:
        self.raise_for_depth()
        segments: list[Segment] = []

        while True:
            kind = self.kind()

            if kind == TOKEN_TRIVIA:
                self.pos += 1
                if self.kind() == TOKEN_EOI:
                    raise JSONPathSyntaxError(
                        "unexpected trailing whitespace",
                        self.current(),
                        self.source,
                    )

            elif kind == TOKEN_DOUBLE_DOT:
                token = self.next()
                selectors, end_token = self.parse_descendant_selectors()
                segments.append((DESCENDANT_SEGMENT, span(token, end_token), selectors))

            elif kind == TOKEN_DOT:
                token = self.next()
                selectors, end_token = self.parse_shorthand_selector()
                segments.append((CHILD_SEGMENT, span(token, end_token), selectors))

            elif kind == TOKEN_LEFT_BRACKET:
                token = self.current()
                selectors, end_token = self.parse_bracketed_selectors()
                segments.append((CHILD_SEGMENT, span(token, end_token), selectors))

            else:
                break

        return segments

    def parse_descendant_selectors(self) -> tuple[tuple[Selector, ...], Token]:
        kind = self.kind()

        if kind == TOKEN_WORD or kind == TOKEN_ASTERISK:
            return self.parse_shorthand_selector()

        if kind == TOKEN_LEFT_BRACKET:
            return self.parse_bracketed_selectors()

        raise JSONPathSyntaxError(
            "expected a selector",
            self.current(),
            self.source,
        )

    def parse_shorthand_selector(self) -> tuple[tuple[Selector, ...], Token]:
        kind = self.kind()

        if kind == TOKEN_WORD:
            token = self.next()
            return ((NAME_SELECTOR, token, token_value(token, self.source)),), token

        if kind == TOKEN_ASTERISK:
            token = self.next()
            return ((WILDCARD_SELECTOR, token),), token

        raise JSONPathSyntaxError(
            "expected a shorthand selector",
            self.current(),
            self.source,
        )

    def parse_bracketed_selectors(self) -> tuple[tuple[Selector, ...], Token]:
        start_token = self.eat(TOKEN_LEFT_BRACKET)
        selectors: list[Selector] = []

        while True:
            self.skip(TOKEN_TRIVIA)
            kind = self.kind()

            if kind == TOKEN_RIGHT_BRACKET:
                break

            if kind == TOKEN_INT:
                selectors.append(self.parse_index_or_slice())

            elif kind in (
                TOKEN_DOUBLE_QUOTED_STRING,
                TOKEN_DOUBLE_QUOTED_ESC_STRING,
                TOKEN_SINGLE_QUOTED_STRING,
                TOKEN_SINGLE_QUOTED_ESC_STRING,
            ):
                token = self.next()
                selectors.append(
                    (NAME_SELECTOR, token, self.decode_string_literal(token))
                )

            elif kind == TOKEN_COLON:
                selectors.append(self.parse_slice_selector())

            elif kind == TOKEN_ASTERISK:
                selectors.append((WILDCARD_SELECTOR, self.next()))

            elif kind == TOKEN_QUESTION:
                selectors.append(self.parse_filter_selector())

            elif kind == TOKEN_EOI:
                raise JSONPathSyntaxError(
                    "unexpected end of query",
                    self.current(),
                    self.source,
                )

            else:
                raise JSONPathSyntaxError(
                    "unexpected token",
                    self.current(),
                    self.source,
                )

            self.skip(TOKEN_TRIVIA)
            kind = self.kind()

            if kind == TOKEN_RIGHT_BRACKET:
                break

            if kind == TOKEN_EOI:
                raise JSONPathSyntaxError(
                    "unexpected end of query",
                    self.current(),
                    self.source,
                )

            self.eat(TOKEN_COMMA)
            if self.kind() == TOKEN_RIGHT_BRACKET:
                raise JSONPathSyntaxError(
                    "unexpected trailing comma",
                    self.current(),
                    self.source,
                )

        self.skip(TOKEN_TRIVIA)
        end_token = self.eat(TOKEN_RIGHT_BRACKET)

        if not len(selectors):
            raise JSONPathSyntaxError(
                "unexpected empty segment",
                span(start_token, end_token),
                self.source,
            )

        return tuple(selectors), end_token

    def parse_index_or_slice(self) -> Selector:
        token = self.eat(TOKEN_INT)
        start_index = self.parse_i_json_int(token)

        self.skip(TOKEN_TRIVIA)

        if self.kind() != TOKEN_COLON:
            return (INDEX_SELECTOR, token, start_index)

        stop: int | None = None
        step: int | None = None

        end_token = self.eat(TOKEN_COLON)
        self.skip(TOKEN_TRIVIA)

        if self.kind() == TOKEN_INT:
            end_token = self.next()
            stop = self.parse_i_json_int(end_token)
            self.skip(TOKEN_TRIVIA)

        if self.kind() == TOKEN_COLON:
            end_token = self.next()
            self.skip(TOKEN_TRIVIA)

            if self.kind() == TOKEN_INT:
                end_token = self.next()
                step = self.parse_i_json_int(end_token)

        return (SLICE_SELECTOR, span(token, end_token), slice(start_index, stop, step))

    def parse_slice_selector(self) -> SliceSelector:
        token = self.eat(TOKEN_COLON)
        end_token = token
        self.skip(TOKEN_TRIVIA)

        stop: int | None = None
        step: int | None = None

        if self.kind() == TOKEN_INT:
            end_token = self.next()
            stop = self.parse_i_json_int(end_token)
            self.skip(TOKEN_TRIVIA)

        if self.kind() == TOKEN_COLON:
            end_token = self.next()
            self.skip(TOKEN_TRIVIA)

            if self.kind() == TOKEN_INT:
                end_token = self.next()
                step = self.parse_i_json_int(end_token)

        return (SLICE_SELECTOR, span(token, end_token), slice(None, stop, step))

    def parse_filter_selector(self) -> FilterSelector:
        token = self.eat(TOKEN_QUESTION)
        expr = self.parse_filter_expression()
        self.raise_for_not_compared(expr, expr[1])
        return (FILTER_SELECTOR, span(token, expr[1]), expr)

    def parse_filter_expression(self, *, precedence: int = PREC_LOWEST) -> Expression:
        self.raise_for_depth()
        left = self.parse_primary()

        while True:
            self.skip(TOKEN_TRIVIA)
            kind = self.kind()

            if (
                kind not in self.INFIX_OPERATORS
                or self.PRECEDENCES.get(kind, self.PREC_LOWEST) < precedence
            ):
                return left

            left = self.parse_infix_expression(left, kind)

    def parse_primary(self) -> Expression:
        self.skip(TOKEN_TRIVIA)
        kind = self.kind()

        if kind in (
            TOKEN_SINGLE_QUOTED_STRING,
            TOKEN_SINGLE_QUOTED_ESC_STRING,
            TOKEN_DOUBLE_QUOTED_STRING,
            TOKEN_DOUBLE_QUOTED_ESC_STRING,
        ):
            token = self.next()
            return (STRING_EXPR, token, self.decode_string_literal(token))

        if kind == TOKEN_WORD:
            word = self.value()
            if word == "null":
                return (NULL_EXPR, self.next())

            if word == "true":
                return (BOOL_EXPR, self.next(), True)

            if word == "false":
                return (BOOL_EXPR, self.next(), False)

            return self.parse_function_expression(word)

        if kind == TOKEN_LEFT_PAREN:
            return self.parse_grouped_expression()

        if kind == TOKEN_INT or kind == TOKEN_INTEGER:
            return self.parse_integer_literal()

        if kind == TOKEN_FLOAT:
            return self.parse_float_literal()

        if kind == TOKEN_DOLLAR:
            return self.parse_absolute_query()

        if kind == TOKEN_AT:
            return self.parse_relative_query()

        if kind == TOKEN_EXCLAMATION:
            return self.parse_prefix_expression()

        raise JSONPathSyntaxError(
            f"unexpected token {TOKENS[self.kind()]} ({token_value(self.current(), self.source)})",
            self.current(),
            self.source,
        )

    def parse_infix_expression(self, left: Expression, kind: int) -> Expression:
        op_token = self.next()
        prec = self.PRECEDENCES.get(kind, self.PREC_LOWEST)
        right = self.parse_filter_expression(precedence=prec)
        span_ = span(left[1], right[1])

        if self.INFIX_OPERATORS[kind]:
            self.raise_for_not_comparable(left, span_)
            self.raise_for_not_comparable(right, span_)

            if kind == TOKEN_EQ:
                return (EQ_EXPR, span_, left, right)
            if kind == TOKEN_NE:
                return (NE_EXPR, span_, left, right)
            if kind == TOKEN_LT:
                return (LT_EXPR, span_, left, right)
            if kind == TOKEN_LE:
                return (LE_EXPR, span_, left, right)
            if kind == TOKEN_GT:
                return (GT_EXPR, span_, left, right)
            if kind == TOKEN_GE:
                return (GE_EXPR, span_, left, right)

            raise JSONPathSyntaxError(
                f"unknown infix operator {token_value(op_token, self.source)!r}",
                op_token,
                self.source,
            )

        self.raise_for_not_compared(left, span_)
        self.raise_for_not_compared(right, span_)

        if kind == TOKEN_AND:
            return (AND_EXPR, span_, left, right)
        if kind == TOKEN_OR:
            return (OR_EXPR, span_, left, right)

        raise JSONPathSyntaxError(
            f"unknown infix operator {token_value(op_token, self.source)!r}",
            op_token,
            self.source,
        )

    def parse_prefix_expression(self) -> Expression:
        token = self.eat(TOKEN_EXCLAMATION)
        expr = self.parse_filter_expression(precedence=self.PREC_PREFIX)
        return (NOT_EXPR, span(token, expr[1]), expr)

    def parse_grouped_expression(self) -> Expression:
        self.eat(TOKEN_LEFT_PAREN)
        expr = self.parse_filter_expression(precedence=self.PREC_LOWEST)
        self.skip(TOKEN_TRIVIA)

        if self.kind() == TOKEN_EOI:
            raise JSONPathSyntaxError(
                "unbalanced parentheses",
                self.current(),
                self.source,
            )

        self.eat(TOKEN_RIGHT_PAREN)
        return expr

    def parse_function_expression(self, name: str) -> FunctionExpression:
        name_token = self.next()
        args: list[Expression] = []

        self.eat(TOKEN_LEFT_PAREN)

        while self.kind() != TOKEN_RIGHT_PAREN:
            args.append(self.parse_filter_expression())
            self.skip(TOKEN_TRIVIA)

            if self.kind() != TOKEN_RIGHT_PAREN:
                self.skip(TOKEN_TRIVIA)
                self.eat(TOKEN_COMMA, message="unbalanced brackets or missing comma")

        self.skip(TOKEN_TRIVIA)
        self.eat(TOKEN_RIGHT_PAREN)
        self.validate_function_signature(name_token, name, args)
        return (FUNCTION_EXPR, span(name_token, args[-1][1]), name, tuple(args))

    def parse_integer_literal(self) -> IntExpression:
        token = self.next()
        value = token_value(token, self.source)

        if value.startswith("0") and len(value) > 1:
            raise JSONPathSyntaxError(
                "invalid integer",
                token,
                self.source,
            )

        if token[0] == TOKEN_INT:
            # TOKEN_INT does not have an exponent
            return (INT_EXPR, token, int(value))

        # TOKEN_INTEGER does have an exponent, so cast to float first.
        return (INT_EXPR, token, int(float(value)))

    def parse_float_literal(self) -> FloatExpression:
        token = self.next()
        value = token_value(token, self.source)

        if value.startswith("0") and len(value.split(".")[0]) > 1:
            raise JSONPathSyntaxError(
                "invalid float",
                token,
                self.source,
            )

        return (FLOAT_EXPR, token, float(value))

    def parse_absolute_query(self) -> AbsoluteQueryExpression:
        ident_token = self.next()
        segments = tuple(self.parse_segments())
        token = span(ident_token, segments[-1][1]) if len(segments) else ident_token
        return (ABSOLUTE_QUERY_EXPR, token, segments)

    def parse_relative_query(self) -> RelativeQueryExpression:
        ident_token = self.next()
        segments = tuple(self.parse_segments())
        token = span(ident_token, segments[-1][1]) if len(segments) else ident_token
        return (RELATIVE_QUERY_EXPR, token, segments)
