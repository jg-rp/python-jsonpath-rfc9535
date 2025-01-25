"""JSONPath filter selector expressions."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Generic
from typing import List
from typing import Sequence
from typing import TypeVar

from jsonpath_rfc9535.function_extensions.filter_function import ExpressionType
from jsonpath_rfc9535.function_extensions.filter_function import FilterFunction

from .exceptions import JSONPathTypeError
from .node import JSONPathNodeList
from .serialize import canonical_string

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment
    from .environment import JSONValue
    from .query import JSONPathQuery
    from .tokens import Token


class Expression(ABC):
    """Base class for all filter expression nodes."""

    __slots__ = ("token",)

    def __init__(self, token: Token) -> None:
        self.token = token

    @abstractmethod
    def evaluate(self, context: FilterContext) -> object:
        """Evaluate the filter expression in the given _context_.

        Arguments:
            context: Contextual information the expression might choose
                use during evaluation.

        Returns:
            The result of evaluating the expression.
        """


PRECEDENCE_LOWEST = 1
PRECEDENCE_LOGICAL_OR = 3
PRECEDENCE_LOGICAL_AND = 4
PRECEDENCE_PREFIX = 7


class FilterExpression(Expression):
    """An expression that evaluates to `true` or `false`."""

    __slots__ = ("expression",)

    def __init__(self, token: Token, expression: Expression) -> None:
        super().__init__(token)
        self.expression = expression

    def __str__(self) -> str:
        return self._canonical_string(self.expression, PRECEDENCE_LOWEST)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FilterExpression) and self.expression == other.expression
        )

    def evaluate(self, context: FilterContext) -> bool:
        """Evaluate the filter expression in the given _context_."""
        return _is_truthy(self.expression.evaluate(context))

    def _canonical_string(self, expression: Expression, parent_precedence: int) -> str:
        if isinstance(expression, LogicalExpression):
            if expression.operator == "&&":
                left = self._canonical_string(expression.left, PRECEDENCE_LOGICAL_AND)
                right = self._canonical_string(expression.right, PRECEDENCE_LOGICAL_AND)
                expr = f"{left} && {right}"
                return (
                    f"({expr})" if parent_precedence >= PRECEDENCE_LOGICAL_AND else expr
                )

            if expression.operator == "||":
                left = self._canonical_string(expression.left, PRECEDENCE_LOGICAL_OR)
                right = self._canonical_string(expression.right, PRECEDENCE_LOGICAL_OR)
                expr = f"{left} || {right}"
                return (
                    f"({expr})" if parent_precedence >= PRECEDENCE_LOGICAL_OR else expr
                )

        if isinstance(expression, PrefixExpression):
            operand = self._canonical_string(expression.right, PRECEDENCE_PREFIX)
            expr = f"!{operand}"
            return f"({expr})" if parent_precedence > PRECEDENCE_PREFIX else expr

        return str(expression)


LITERAL_T = TypeVar("LITERAL_T")


class FilterExpressionLiteral(Expression, Generic[LITERAL_T]):
    """Base class for filter expression literals."""

    __slots__ = ("value",)

    def __init__(self, token: Token, value: LITERAL_T) -> None:
        super().__init__(token=token)
        self.value = value

    def __str__(self) -> str:
        return repr(self.value).lower()

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    def evaluate(self, _: FilterContext) -> LITERAL_T:
        """Return the value associated with this literal."""
        return self.value


class BooleanLiteral(FilterExpressionLiteral[bool]):
    """A Boolean `true` or `false`."""

    __slots__ = ()


class StringLiteral(FilterExpressionLiteral[str]):
    """A string literal."""

    __slots__ = ()

    def __str__(self) -> str:
        return canonical_string(self.value)


class IntegerLiteral(FilterExpressionLiteral[int]):
    """An integer literal."""

    __slots__ = ()


class FloatLiteral(FilterExpressionLiteral[float]):
    """A float literal."""

    __slots__ = ()


class NullLiteral(FilterExpressionLiteral[None]):
    """A null literal."""

    __slots__ = ()

    def __str__(self) -> str:
        return "null"


class PrefixExpression(Expression):
    """An expression composed of a prefix operator and another expression."""

    __slots__ = ("operator", "right")

    def __init__(self, token: Token, operator: str, right: Expression):
        self.operator = operator
        self.right = right
        super().__init__(token)

    def __str__(self) -> str:
        return f"{self.operator}{self.right}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PrefixExpression)
            and self.operator == other.operator
            and self.right == other.right
        )

    def evaluate(self, context: FilterContext) -> object:
        """Evaluate the filter expression in the given _context_."""
        if self.operator == "!":
            return not _is_truthy(self.right.evaluate(context))
        raise JSONPathTypeError(f"unknown operator {self.operator} {self.right}")


class LogicalExpression(Expression):
    """A pair of expressions and a logical operator."""

    __slots__ = ("left", "operator", "right")

    def __init__(
        self,
        token: Token,
        left: Expression,
        operator: str,
        right: Expression,
    ):
        super().__init__(token)
        self.left = left
        self.operator = operator
        self.right = right

    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, LogicalExpression)
            and self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )

    def evaluate(self, context: FilterContext) -> bool:
        """Evaluate the filter expression in the given _context_."""
        # TODO: sort circuit eval of right if left is false
        return _compare(
            self.left.evaluate(context), self.operator, self.right.evaluate(context)
        )


class ComparisonExpression(Expression):
    """A pair of expressions and a comparison operator."""

    __slots__ = ("left", "operator", "right")

    def __init__(
        self,
        token: Token,
        left: Expression,
        operator: str,
        right: Expression,
    ):
        super().__init__(token)
        self.left = left
        self.operator = operator
        self.right = right

    def __str__(self) -> str:
        return f"{self.left} {self.operator} {self.right}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, LogicalExpression)
            and self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )

    def evaluate(self, context: FilterContext) -> bool:
        """Evaluate the filter expression in the given _context_."""
        left = self.left.evaluate(context)
        if isinstance(left, JSONPathNodeList) and len(left) == 1:
            left = left[0].value

        right = self.right.evaluate(context)
        if isinstance(right, JSONPathNodeList) and len(right) == 1:
            right = right[0].value

        return _compare(left, self.operator, right)


class FilterQuery(Expression, ABC):
    """Base class for all query selectors."""

    __slots__ = ("query",)

    def __init__(self, token: Token, query: JSONPathQuery) -> None:
        super().__init__(token)
        self.query = query

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FilterQuery) and str(self) == str(other)


class RelativeFilterQuery(FilterQuery):
    """A JSONPath expression starting at the current node."""

    __slots__ = ()

    def __str__(self) -> str:
        return "@" + str(self.query)[1:]

    def evaluate(self, context: FilterContext) -> object:
        """Evaluate the filter expression in the given _context_."""
        if not isinstance(context.current, (list, dict)):
            if self.query.empty():
                return context.current
            return JSONPathNodeList()

        return JSONPathNodeList(self.query.find(context.current))


class RootFilterQuery(FilterQuery):
    """A JSONPath expression starting at the root node."""

    __slots__ = ()

    def __str__(self) -> str:
        return str(self.query)

    def evaluate(self, context: FilterContext) -> object:
        """Evaluate the filter expression in the given _context_."""
        return JSONPathNodeList(self.query.find(context.root))


class FunctionExtension(Expression):
    """A filter function."""

    __slots__ = ("name", "args")

    def __init__(self, token: Token, name: str, args: Sequence[Expression]) -> None:
        super().__init__(token)
        self.name = name
        self.args = args

    def __str__(self) -> str:
        args = [str(arg) for arg in self.args]
        return f"{self.name}({', '.join(args)})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FunctionExtension)
            and other.name == self.name
            and other.args == self.args
        )

    def evaluate(self, context: FilterContext) -> object:
        """Evaluate the filter expression in the given _context_."""
        try:
            func = context.env.function_extensions[self.name]
        except KeyError:
            return NOTHING
        args = [arg.evaluate(context) for arg in self.args]
        return func(*self._unpack_node_lists(func, args))

    def _unpack_node_lists(
        self, func: FilterFunction, args: List[object]
    ) -> List[object]:
        _args: List[object] = []
        for idx, arg in enumerate(args):
            if func.arg_types[idx] != ExpressionType.NODES and isinstance(
                arg, JSONPathNodeList
            ):
                if len(arg) == 0:
                    # If the query results in an empty nodelist, the
                    # argument is the special result Nothing.
                    _args.append(NOTHING)
                elif len(arg) == 1:
                    # If the query results in a nodelist consisting of a
                    # single node, the argument is the value of the node
                    _args.append(arg[0].value)
                else:
                    # This should not be possible as a non-singular query
                    # would have been rejected when checking function
                    # well-typedness.
                    _args.append(arg)
            else:
                _args.append(arg)

        return _args


class FilterContext:
    """Contextual information and data for evaluating a filter expression."""

    __slots__ = (
        "current",
        "env",
        "root",
    )

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        current: object,
        root: JSONValue,
    ) -> None:
        self.env = env
        self.current = current
        self.root = root

    def __str__(self) -> str:
        return f"FilterContext(current={self.current})"


class Nothing:
    """The special result "Nothing"."""

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nothing) or (
            isinstance(other, JSONPathNodeList) and other.empty()
        )

    def __str__(self) -> str:
        return "<NOTHING>"

    def __repr__(self) -> str:
        return "<NOTHING>"


NOTHING = Nothing()


def _is_truthy(obj: object) -> bool:
    """Test for truthiness when evaluating filter expressions."""
    if isinstance(obj, JSONPathNodeList) and len(obj) == 0:
        return False
    if obj is NOTHING:
        return False
    if obj is None:
        return True
    return bool(obj)


def _compare(  # noqa: PLR0911
    left: object, operator: str, right: object
) -> bool:
    """Object comparison within filter expressions.

    Args:
        left: The left hand side of the comparison expression.
        operator: The comparison expression's operator.
        right: The right hand side of the comparison expression.

    Returns:
        `True` if the comparison between _left_ and _right_, with the
        given _operator_, is truthy. `False` otherwise.
    """
    if operator == "&&":
        return _is_truthy(left) and _is_truthy(right)
    if operator == "||":
        return _is_truthy(left) or _is_truthy(right)
    if operator == "==":
        return _eq(left, right)
    if operator == "!=":
        return not _eq(left, right)
    if operator == "<":
        return _lt(left, right)
    if operator == ">":
        return _lt(right, left)
    if operator == ">=":
        return _lt(right, left) or _eq(left, right)
    if operator == "<=":
        return _lt(left, right) or _eq(left, right)
    return False


def _eq(left: object, right: object) -> bool:  # noqa: PLR0911
    if isinstance(right, JSONPathNodeList):
        left, right = right, left

    if isinstance(left, JSONPathNodeList):
        if isinstance(right, JSONPathNodeList):
            return left == right
        if left.empty():
            return right is NOTHING
        if len(left) == 1:
            return left[0] == right
        return False

    if left is NOTHING and right is NOTHING:
        return True

    # Remember 1 == True and 0 == False in Python
    if isinstance(right, bool):
        left, right = right, left

    if isinstance(left, bool):
        return isinstance(right, bool) and left == right

    return left == right


def _lt(left: object, right: object) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left < right

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left < right

    return False
