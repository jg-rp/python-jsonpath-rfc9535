import json
from collections.abc import Sequence

from . import _ast
from ._ast import Expression, Segment, Selector


def canonical_string(value: str) -> str:
    """Return `value` as a canonically formatted string including quotes."""
    single_quoted = (
        json.dumps(value, ensure_ascii=False)[1:-1]
        .replace('\\"', '"')
        .replace("'", "\\'")
    )
    return f"'{single_quoted}'"


def canonical_path(segments: Sequence[Segment]) -> str:
    """Return JSONPath segments as a canonically formatted path."""
    return "$" + "".join(_canonical_segment(s) for s in segments)


_PREC_LOWEST = 1
_PREC_LOGICAL_OR = 3
_PREC_LOGICAL_AND = 4
_PREC_PREFIX = 7


def _canonical_segment(segment: Segment) -> str:
    match segment:
        case (_ast.CHILD_SEGMENT, _, selectors):
            return f"[{', '.join(_canonical_selector(s) for s in selectors)}]"

        case (_ast.DESCENDANT_SEGMENT, _, selectors):
            return f"..[{', '.join(_canonical_selector(s) for s in selectors)}]"


def _canonical_selector(selector: Selector) -> str:
    match selector:
        case (_ast.NAME_SELECTOR, _, name):
            return canonical_string(name)

        case (_ast.INDEX_SELECTOR, _, index):
            return str(index)

        case (_ast.SLICE_SELECTOR, _, slice_):
            stop = slice_.stop if slice_.stop is not None else ""
            start = slice_.start if slice_.start is not None else ""
            step = slice_.step if slice_.step is not None else "1"
            return f"{start}:{stop}:{step}"

        case (_ast.WILDCARD_SELECTOR, _):
            return "*"

        case (_ast.FILTER_SELECTOR, _, expr):
            return f"?{_canonical_expression(expr, _PREC_LOWEST)}"


def _canonical_expression(expression: Expression, parent_precedence: int) -> str:
    match expression:
        case (_ast.AND_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOGICAL_AND)
            right_ = _canonical_expression(right, _PREC_LOGICAL_AND)
            expr = f"{left_} && {right_}"
            return f"({expr})" if parent_precedence >= _PREC_LOGICAL_AND else expr

        case (_ast.OR_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOGICAL_OR)
            right_ = _canonical_expression(right, _PREC_LOGICAL_OR)
            expr = f"{left_} || {right_}"
            return f"({expr})" if parent_precedence >= _PREC_LOGICAL_OR else expr

        case (_ast.NOT_EXPR, _, right):
            right_ = _canonical_expression(right, _PREC_PREFIX)
            expr = f"!{right_}"
            return f"({expr})" if parent_precedence > _PREC_PREFIX else expr

        case (_ast.NULL_EXPR, _):
            return "null"

        case (
            _ast.BOOL_EXPR | _ast.INT_EXPR | _ast.FLOAT_EXPR,
            _,
            value,
        ):
            return str(value).lower()

        case (_ast.STRING_EXPR, _, value):
            return canonical_string(value)

        case (_ast.EQ_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOWEST)
            right_ = _canonical_expression(right, _PREC_LOWEST)
            return f"{left_} == {right_}"

        case (_ast.NE_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOWEST)
            right_ = _canonical_expression(right, _PREC_LOWEST)
            return f"{left_} != {right_}"

        case (_ast.LT_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOWEST)
            right_ = _canonical_expression(right, _PREC_LOWEST)
            return f"{left_} < {right_}"

        case (_ast.LE_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOWEST)
            right_ = _canonical_expression(right, _PREC_LOWEST)
            return f"{left_} <= {right_}"

        case (_ast.GT_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOWEST)
            right_ = _canonical_expression(right, _PREC_LOWEST)
            return f"{left_} > {right_}"

        case (_ast.GE_EXPR, _, left, right):
            left_ = _canonical_expression(left, _PREC_LOWEST)
            right_ = _canonical_expression(right, _PREC_LOWEST)
            return f"{left_} >= {right_}"

        case (_ast.ABSOLUTE_QUERY_EXPR, _, segments):
            return "$" + "".join(_canonical_segment(s) for s in segments)

        case (_ast.RELATIVE_QUERY_EXPR, _, segments):
            return "@" + "".join(_canonical_segment(s) for s in segments)

        case (_ast.FUNCTION_EXPR, _, name, args):
            args_ = [_canonical_expression(a, _PREC_LOWEST) for a in args]
            return f"{name}({', '.join(args_)})"
