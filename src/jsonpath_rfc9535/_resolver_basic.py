# pyright: reportOperatorIssue=false
# pyright: reportUnknownArgumentType=false
# pyright: reportArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportIndexIssue=false
# pyright: reportUnknownMemberType=false
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from . import _ast
from ._ast import *
from ._nothing import NOTHING
from .exceptions import JSONPathRecursionError
from .functions import NODES_TYPE
from .node import BasicNodeList

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment


class BasicResolver:
    """A memory efficient JSONPath evaluator that does not track node locations."""

    __slots__ = ("env", "root")

    def __init__(self, env: JSONPathEnvironment, root: object) -> None:
        self.env = env
        self.root = root

    @classmethod
    def resolve(
        cls,
        env: JSONPathEnvironment,
        segments: Sequence[Segment],
        root: str,
        data: object,
    ) -> Iterable[object]:
        return cls(env, data)._resolve(segments)

    def _resolve(self, segments: Sequence[Segment]) -> Iterable[object]:
        nodes: Iterable[object] = [self.root]
        for segment in segments:
            nodes = self._resolve_segment(segment, nodes)
        return nodes

    def _resolve_segment(
        self, segment: Segment, nodes: Iterable[object]
    ) -> Iterable[object]:
        match segment:
            case (_ast.CHILD_SEGMENT, _, selectors):
                for node in nodes:
                    for selector in selectors:
                        yield from self._resolve_selector(selector, node)

            case (_ast.DESCENDANT_SEGMENT, _, selectors):
                for node in nodes:
                    for node_ in self.visit(node):
                        for selector in selectors:
                            yield from self._resolve_selector(selector, node_)

    def _resolve_selector(self, selector: Selector, obj: object) -> Iterable[object]:
        match selector:
            case (_ast.NAME_SELECTOR, _, name):
                if type(obj) is dict and name in obj:
                    yield obj[name]

            case (_ast.INDEX_SELECTOR, _, index):
                if type(obj) is list and len(obj) >= abs(index) + int(index >= 0):
                    if index < 0 and len(obj) >= abs(index):
                        index = len(obj) + index

                    yield obj[index]

            case (_ast.SLICE_SELECTOR, _, slice_):
                if type(obj) is list and slice_.step != 0:
                    for i, elem in zip(range(*slice_.indices(len(obj))), obj[slice_]):
                        yield elem

            case (_ast.WILDCARD_SELECTOR, _):
                if type(obj) is dict:
                    for k, v in obj.items():
                        yield v

                elif type(obj) is list:
                    for i, elem in enumerate(obj):
                        yield elem

            case (_ast.FILTER_SELECTOR, _, expr):
                if type(obj) is dict:
                    for k, v in obj.items():
                        if truthy(self._evaluate_expression(expr, k, v)):
                            yield v

                elif type(obj) is list:
                    for i, elem in enumerate(obj):
                        if truthy(self._evaluate_expression(expr, i, elem)):
                            yield elem

    def _evaluate_expression(
        self,
        expr: Expression,
        current_key: int | str,
        current_value: object,
    ) -> object:
        match expr:
            case (_ast.NULL_EXPR, _):
                return None

            case (
                _ast.BOOL_EXPR | _ast.STRING_EXPR | _ast.INT_EXPR | _ast.FLOAT_EXPR,
                _,
                value,
            ):
                return value

            case (_ast.NOT_EXPR, _, right):
                return not truthy(
                    self._evaluate_expression(right, current_key, current_value)
                )

            case (_ast.AND_EXPR, _, left, right):
                return truthy(
                    self._evaluate_expression(left, current_key, current_value)
                ) and truthy(
                    self._evaluate_expression(right, current_key, current_value)
                )

            case (_ast.OR_EXPR, _, left, right):
                return truthy(
                    self._evaluate_expression(left, current_key, current_value)
                ) or truthy(
                    self._evaluate_expression(right, current_key, current_value)
                )

            case (_ast.EQ_EXPR, _, left, right):
                left_ = self._evaluate_expression(left, current_key, current_value)
                if isinstance(left_, BasicNodeList) and len(left_) == 1:
                    left_ = left_[0]

                right_ = self._evaluate_expression(right, current_key, current_value)
                if isinstance(right_, BasicNodeList) and len(right_) == 1:
                    right_ = right_[0]

                return eq(left_, right_)

            case (_ast.NE_EXPR, _, left, right):
                left_ = self._evaluate_expression(left, current_key, current_value)
                if isinstance(left_, BasicNodeList) and len(left_) == 1:
                    left_ = left_[0]

                right_ = self._evaluate_expression(right, current_key, current_value)
                if isinstance(right_, BasicNodeList) and len(right_) == 1:
                    right_ = right_[0]

                return not eq(left_, right_)

            case (_ast.LT_EXPR, _, left, right):
                left_ = self._evaluate_expression(left, current_key, current_value)
                if isinstance(left_, BasicNodeList) and len(left_) == 1:
                    left_ = left_[0]

                right_ = self._evaluate_expression(right, current_key, current_value)
                if isinstance(right_, BasicNodeList) and len(right_) == 1:
                    right_ = right_[0]

                return lt(left_, right_)

            case (_ast.LE_EXPR, _, left, right):
                left_ = self._evaluate_expression(left, current_key, current_value)
                if isinstance(left_, BasicNodeList) and len(left_) == 1:
                    left_ = left_[0]

                right_ = self._evaluate_expression(right, current_key, current_value)
                if isinstance(right_, BasicNodeList) and len(right_) == 1:
                    right_ = right_[0]

                return lt(left_, right_) or eq(left_, right_)

            case (_ast.GT_EXPR, _, left, right):
                left_ = self._evaluate_expression(left, current_key, current_value)
                if isinstance(left_, BasicNodeList) and len(left_) == 1:
                    left_ = left_[0]

                right_ = self._evaluate_expression(right, current_key, current_value)
                if isinstance(right_, BasicNodeList) and len(right_) == 1:
                    right_ = right_[0]

                return lt(right_, left_)

            case (_ast.GE_EXPR, _, left, right):
                left_ = self._evaluate_expression(left, current_key, current_value)
                if isinstance(left_, BasicNodeList) and len(left_) == 1:
                    left_ = left_[0]

                right_ = self._evaluate_expression(right, current_key, current_value)
                if isinstance(right_, BasicNodeList) and len(right_) == 1:
                    right_ = right_[0]

                return lt(right_, left_) or eq(left_, right_)

            case (_ast.ABSOLUTE_QUERY_EXPR, _, segments):
                return BasicNodeList(self.resolve(self.env, segments, "$", self.root))

            case (_ast.RELATIVE_QUERY_EXPR, _, segments):
                return BasicNodeList(
                    self.resolve(self.env, segments, "@", current_value)
                )

            case (_ast.FUNCTION_EXPR, _, name, args):
                # Functions are validated at parse time.
                func = self.env.functions[name]

                args_ = [
                    self._evaluate_expression(
                        arg,
                        current_key,
                        current_value,
                    )
                    for arg in args
                ]

                for i, arg in enumerate(args_):
                    if (
                        isinstance(arg, BasicNodeList)
                        and func.arg_types[i] != NODES_TYPE
                    ):
                        if len(arg) == 0:
                            # If the query results in an empty nodelist, the
                            # argument is the special result Nothing.
                            args_[i] = NOTHING
                        elif len(arg) == 1:
                            # If the query results in a nodelist consisting of a
                            # single node, the argument is the value of the node.
                            args_[i] = arg[0]

                return func(*args_)

    def visit(self, node: object) -> Iterable[object]:
        max_depth = self.env.max_recursion_depth

        def visit_(obj: object, depth: int) -> Iterable[object]:

            if depth > max_depth:
                raise JSONPathRecursionError("recursion limit reached")

            yield obj

            if type(obj) is dict:
                for k, v in obj.items():
                    vt = type(v)
                    if isinstance(k, str) and (vt is list or vt is dict):
                        yield from visit_(v, depth + 1)

            elif type(obj) is list:
                for elem in obj:
                    et = type(elem)
                    if et is list or et is dict:
                        yield from visit_(elem, depth + 1)

        return visit_(node, 1)


# TODO: centralize these in a `Resolver_` base class


def truthy(obj: object) -> bool:
    if isinstance(obj, BasicNodeList):
        return len(obj) > 0
    if obj is NOTHING:
        return False
    if obj is None:
        return True
    return bool(obj)


def eq(left: object, right: object) -> bool:
    if isinstance(right, BasicNodeList):
        left, right = right, left

    if isinstance(left, BasicNodeList):
        if isinstance(right, BasicNodeList):
            return left == right
        if len(left) == 0:
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


def lt(left: object, right: object) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left < right

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left < right

    return False
