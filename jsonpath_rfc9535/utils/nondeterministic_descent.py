"""Utilities for exploring nondeterminism in the recursive descent segment."""

from __future__ import annotations

import os
import random
import sys
from collections import deque
from typing import TYPE_CHECKING
from typing import Deque
from typing import Iterable
from typing import List
from typing import Optional
from typing import TextIO
from typing import Tuple

if TYPE_CHECKING:
    from jsonpath_rfc9535.environment import JSONValue


HORIZONTAL_SEP = "\N{BOX DRAWINGS LIGHT HORIZONTAL}" * 2
VERTICAL_SEP = "\N{BOX DRAWINGS LIGHT VERTICAL}"
BRANCH = "\N{BOX DRAWINGS LIGHT VERTICAL AND RIGHT}" + HORIZONTAL_SEP + " "
TERMINAL_BRANCH = "\N{BOX DRAWINGS LIGHT UP AND RIGHT}" + HORIZONTAL_SEP + " "
INDENT = VERTICAL_SEP + " " * 3
TERMINAL_INDENT = " " * 4

COLOR_CODES = [
    ("\033[92m", "\033[0m"),
    ("\033[93m", "\033[0m"),
    ("\033[94m", "\033[0m"),
    ("\033[95m", "\033[0m"),
    ("\033[96m", "\033[0m"),
    ("\033[91m", "\033[0m"),
]


class AuxNode:
    """A auxiliary tree node, including a list of child nodes and depth.

    Use the `from_(value)` static method to build an auxiliary tree instead of
    instantiating this class directly.
    """

    def __init__(
        self,
        depth: int,
        value: object,
        children: Optional[List[AuxNode]] = None,
    ) -> None:
        self.value = value
        self.children = children or []
        self.depth = depth

    def __str__(self) -> str:
        c_start, c_stop = COLOR_CODES[self.depth % len(COLOR_CODES)]
        return f"{c_start}{self.value}{c_stop}"

    @staticmethod
    def from_(value: JSONValue, *, collections_only: bool = False) -> AuxNode:
        """Build a tree from JSON-like _value_."""

        def _visit(node: AuxNode, depth: int = 0) -> None:
            if isinstance(node.value, dict):
                for val in node.value.values():
                    if not collections_only or isinstance(val, (list, dict)):
                        _node = AuxNode(depth + 1, val)
                        _visit(_node, depth + 1)
                        node.children.append(_node)

            elif isinstance(node.value, list):
                for val in node.value:
                    if not collections_only or isinstance(val, (list, dict)):
                        _node = AuxNode(depth + 1, val)
                        _visit(_node, depth + 1)
                        node.children.append(_node)

        root = AuxNode(0, value)
        _visit(root)
        return root


def pp_tree(
    node: AuxNode,
    indent: str = "",
    buf: TextIO = sys.stdout,
) -> None:
    """Pretty print the tree rooted at `node`."""
    # Pre-order tree traversal
    buf.write(str(node) + os.linesep)

    if node.children:
        # Recursively call pptree for all but the last child of `node`.
        for child in node.children[:-1]:
            buf.write(indent + BRANCH)
            pp_tree(child, indent=indent + INDENT, buf=buf)

        # Terminal branch case for last, possibly only, child of `node`.
        buf.write(indent + TERMINAL_BRANCH)
        pp_tree(node.children[-1], indent=indent + TERMINAL_INDENT, buf=buf)

    # Base case. No children.


def pre_order_visit(node: AuxNode) -> Iterable[AuxNode]:
    """Generate nodes rooted at _node_ from a pre-order traversal."""
    yield node

    for child in node.children:
        yield from pre_order_visit(child)


def breadth_first_visit(node: AuxNode) -> Iterable[AuxNode]:
    """Generate nodes rooted at _node_ from a level-order traversal."""
    queue: Deque[AuxNode] = deque([node])

    while queue:
        _node = queue.popleft()
        yield _node
        queue.extend(_node.children)


def nondeterministic_visit(root: AuxNode) -> Iterable[AuxNode]:
    """Generate nodes rooted at _node_ from a nondeterministic traversal."""
    yield root
    queue: Deque[AuxNode] = deque(root.children)

    while queue:
        _node = queue.popleft()
        yield _node
        # Randomly choose to visit child nodes now or queue them for later?
        visit_children = random.choice([True, False])
        for child in _node.children:
            if visit_children:
                yield child

                # Queue grandchildren by randomly interleaving them into the
                # queue while maintaining queue and grandchild order.
                grandchildren = child.children

                queue = deque(
                    [
                        next(n)
                        for n in random.sample(
                            [iter(queue)] * len(queue)
                            + [iter(grandchildren)] * len(grandchildren),
                            len(queue) + len(grandchildren),
                        )
                    ]
                )
            else:
                queue.append(child)


def all_perms(root: AuxNode) -> List[Tuple[AuxNode, ...]]:
    """Return a list of valid permutations for the auxiliary tree _root_."""
    perms = {tuple(nondeterministic_visit(root)) for _ in range(1000)}
    return sorted(perms, key=lambda t: str(t))
