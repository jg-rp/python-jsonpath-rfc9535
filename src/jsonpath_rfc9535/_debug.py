from collections.abc import Iterable, Sequence
from itertools import chain

from . import _ast
from ._ast import *
from ._tokens import token_value


def tree_view(segments: Sequence[Segment], source: str) -> str:
    """Return a tree representation of segments for debugging."""
    lines = chain(
        [f"Query [0:{len(source)}] {source!r}"],
        _debug_segments(segments, source),
    )

    # Align last column
    lines_ = [l.split("]", 1) for l in lines]
    index = max(len(prefix) for prefix, _ in lines_)
    return "\n".join((f"{p}] {' ' * (index - len(p))}{s}") for p, s in lines_)


def _debug_segments(
    segments: Sequence[Segment],
    source: str,
    prefix: str = "",
) -> Iterable[str]:

    for i, segment in enumerate(segments):
        last = i == len(segments) - 1
        yield from _debug_segment(segment, source, prefix, last)


def _debug_segment(
    segment: Segment,
    source: str,
    prefix: str,
    last: bool,
) -> Iterable[str]:
    kind, token, selectors = segment

    assert kind in (CHILD_SEGMENT, DESCENDANT_SEGMENT)

    name = "Child" if kind == CHILD_SEGMENT else "Descendant"

    yield (
        f"{prefix}{'└── ' if last else '├── '}"
        f"{name} [{token[1]}:{token[2]}] "
        f"{token_value(token, source)!r}"
    )

    child_prefix = prefix + ("    " if last else "│   ")

    for i, selector in enumerate(selectors):
        selector_last = i == len(selectors) - 1
        yield from _debug_selector(selector, source, child_prefix, selector_last)


_selector_labels = {
    FILTER_SELECTOR: "Filter",
    INDEX_SELECTOR: "Index",
    NAME_SELECTOR: "Name",
    SLICE_SELECTOR: "Slice",
    WILDCARD_SELECTOR: "Wildcard",
}


def _debug_selector(
    selector: Selector,
    source: str,
    prefix: str,
    last: bool,
) -> Iterable[str]:
    token = selector[1]

    yield (
        f"{prefix}{'└── ' if last else '├── '}"
        f"{_selector_labels[selector[0]]} "
        f"[{token[1]}:{token[2]}] "
        f"{token_value(token, source)!r}"
    )

    match selector:
        case (_ast.FILTER_SELECTOR, _, expr):
            child_prefix = prefix + ("    " if last else "│   ")
            yield from _debug_expression(expr, source, child_prefix, True)
        case _:
            pass


_expression_labels = {
    ABSOLUTE_QUERY_EXPR: "Absolute",
    AND_EXPR: "And",
    BOOL_EXPR: "Bool",
    EQ_EXPR: "Eq",
    FLOAT_EXPR: "Float",
    FUNCTION_EXPR: "Function",
    GE_EXPR: "Ge",
    GT_EXPR: "Gt",
    INT_EXPR: "Int",
    LE_EXPR: "Le",
    LT_EXPR: "Lt",
    NE_EXPR: "Ne",
    NOT_EXPR: "Not",
    NULL_EXPR: "Null",
    OR_EXPR: "Or",
    RELATIVE_QUERY_EXPR: "Relative",
    STRING_EXPR: "String",
}


def _debug_expression(
    expression: Expression,
    source: str,
    prefix: str,
    last: bool,
) -> Iterable[str]:
    label = _expression_labels[expression[0]]
    token = expression[1]

    yield (
        f"{prefix}{'└── ' if last else '├── '}"
        f"{label} [{token[1]}:{token[2]}] "
        f"{token_value(token, source)!r}"
    )

    child_prefix = prefix + ("    " if last else "│   ")

    match expression:
        case (
            _ast.NULL_EXPR
            | _ast.BOOL_EXPR
            | _ast.STRING_EXPR
            | _ast.INT_EXPR
            | _ast.FLOAT_EXPR,
            *_,
        ):
            pass

        case (_ast.NOT_EXPR, _, expr):
            yield from _debug_expression(expr, source, child_prefix, True)

        case (
            _ast.AND_EXPR
            | _ast.OR_EXPR
            | _ast.EQ_EXPR
            | _ast.NE_EXPR
            | _ast.LT_EXPR
            | _ast.LE_EXPR
            | _ast.GT_EXPR
            | _ast.GE_EXPR,
            _,
            left,
            right,
        ):
            yield from _debug_expression(left, source, child_prefix, False)
            yield from _debug_expression(right, source, child_prefix, True)

        case (
            _ast.ABSOLUTE_QUERY_EXPR | _ast.RELATIVE_QUERY_EXPR,
            _,
            segments,
        ):
            yield from _debug_segments(segments, source, child_prefix)

        case (_ast.FUNCTION_EXPR, _, _, args):
            for i, arg in enumerate(args):
                arg_last = i == len(args) - 1
                yield from _debug_expression(arg, source, child_prefix, arg_last)
