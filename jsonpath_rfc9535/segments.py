"""JSONPath child and descendant segment definitions."""

from __future__ import annotations

import random
from abc import ABC
from abc import abstractmethod
from collections import deque
from typing import TYPE_CHECKING
from typing import Deque
from typing import Iterable
from typing import Tuple

from .exceptions import JSONPathRecursionError
from .node import JSONPathNode

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment
    from .selectors import JSONPathSelector
    from .tokens import Token


class JSONPathSegment(ABC):
    """Base class for all JSONPath segments."""

    __slots__ = ("env", "token", "selectors")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        selectors: Tuple[JSONPathSelector, ...],
    ) -> None:
        self.env = env
        self.token = token
        self.selectors = selectors

    @abstractmethod
    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Apply this segment to each `JSONPathNode` in _nodes_."""


class JSONPathChildSegment(JSONPathSegment):
    """The JSONPath child selection segment."""

    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Select children of each node in _nodes_."""
        for node in nodes:
            for selector in self.selectors:
                yield from selector.resolve(node)

    def __str__(self) -> str:
        return f"[{', '.join(str(itm) for itm in self.selectors)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, JSONPathChildSegment)
            and self.selectors == __value.selectors
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.selectors, self.token))


class JSONPathRecursiveDescentSegment(JSONPathSegment):
    """The JSONPath recursive descent segment."""

    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Select descendants of each node in _nodes_."""
        visitor = (
            self._nondeterministic_visit if self.env.nondeterministic else self._visit
        )

        for node in nodes:
            for _node in visitor(node):
                for selector in self.selectors:
                    yield from selector.resolve(_node)

    def _visit(self, node: JSONPathNode, depth: int = 1) -> Iterable[JSONPathNode]:
        """Depth-first, pre-order node traversal."""
        if depth > self.env.max_recursion_depth:
            raise JSONPathRecursionError("recursion limit exceeded", token=self.token)

        yield node

        if isinstance(node.value, dict):
            for name, val in node.value.items():
                if isinstance(val, (dict, list)):
                    _node = JSONPathNode(
                        value=val,
                        location=node.location + (name,),
                        root=node.root,
                    )
                    yield from self._visit(_node, depth + 1)
        elif isinstance(node.value, list):
            for i, element in enumerate(node.value):
                if isinstance(element, (dict, list)):
                    _node = JSONPathNode(
                        value=element,
                        location=node.location + (i,),
                        root=node.root,
                    )
                    yield from self._visit(_node, depth + 1)

    def _nondeterministic_visit(
        self,
        root: JSONPathNode,
        _: int = 1,
    ) -> Iterable[JSONPathNode]:
        def _children(node: JSONPathNode) -> Iterable[JSONPathNode]:
            if isinstance(node.value, dict):
                items = list(node.value.items())
                random.shuffle(items)
                for name, val in items:
                    yield JSONPathNode(
                        value=val,
                        location=node.location + (name,),
                        root=node.root,
                    )
            elif isinstance(node.value, list):
                for i, element in enumerate(node.value):
                    yield JSONPathNode(
                        value=element,
                        location=node.location + (i,),
                        root=node.root,
                    )

        # (node, depth) tuples
        queue: Deque[Tuple[JSONPathNode, int]] = deque()

        yield root  # visit the root node
        queue.extend([(child, 1) for child in _children(root)])  # queue root's children

        while queue:
            node, depth = queue.popleft()

            if depth >= self.env.max_recursion_depth:
                raise JSONPathRecursionError(
                    "recursion limit exceeded", token=self.token
                )

            yield node
            # Visit child nodes now or queue them for later?
            visit_children = random.choice([True, False])  # noqa: S311

            for child in _children(node):
                if visit_children:
                    yield child
                    # Randomly interleave grandchildren into queue
                    grandchildren = [(child, depth + 2) for child in _children(child)]

                    queue = deque(
                        map(
                            next,
                            random.sample(
                                [iter(queue)] * len(queue)
                                + [iter(grandchildren)] * len(grandchildren),
                                len(queue) + len(grandchildren),
                            ),
                        )
                    )
                else:
                    queue.append((child, depth + 1))

    def __str__(self) -> str:
        return f"..[{', '.join(str(itm) for itm in self.selectors)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, JSONPathRecursiveDescentSegment)
            and self.selectors == __value.selectors
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash(("..", self.selectors, self.token))
