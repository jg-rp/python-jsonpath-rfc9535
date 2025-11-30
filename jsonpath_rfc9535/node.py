"""JSONPath node and node list definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .serialize import canonical_string

if TYPE_CHECKING:
    from .environment import JSONValue


class JSONPathNode:
    """A JSON-like value and its location in a JSON document.

    Assigning to `JSONPathNode.value` will update and mutate source data too.
    Updating data after evaluating a query can invalidate existing child
    nodes. Use at your own risk.

    Attributes:
        value: The JSON-like value at this node.
        location: The names indices that make up the normalized path to _value_.
        parent: The parent node, or None if this is the root node.
    """

    __slots__ = (
        "_value",
        "location",
        "parent",
        "root",
    )

    def __init__(
        self,
        *,
        value: object,
        location: Tuple[Union[int, str], ...],
        parent: Optional[JSONPathNode],
        root: JSONValue,
    ) -> None:
        self._value: object = value
        self.location: Tuple[Union[int, str], ...] = location
        self.parent = parent
        self.root = root

    @property
    def value(self) -> object:
        """The JSON-like value at this node."""
        return self._value

    @value.setter
    def value(self, val: object) -> None:
        parent = self.parent
        if parent is not None and self.location:
            # If data has changed since this node was created, this could fail.
            # Letting the exception raise is probably the most useful thing we can do.
            parent._value[self.location[-1]] = val  # type: ignore  # noqa: SLF001
        self._value = val

    def path(self) -> str:
        """Return the normalized path to this node."""
        return "$" + "".join(
            f"[{canonical_string(p)}]" if isinstance(p, str) else f"[{p}]"
            for p in self.location
        )

    def new_child(
        self,
        value: object,
        key: Union[int, str],
        parent: Optional[JSONPathNode],
    ) -> JSONPathNode:
        """Return a new node using this node's location."""
        return JSONPathNode(
            value=value,
            location=self.location + (key,),
            parent=parent,
            root=self.root,
        )

    def __str__(self) -> str:
        return f"JSONPathNode({self.path()!r})"


class JSONPathNodeList(List[JSONPathNode]):
    """A list JSONPathNode instances.

    This is a `list` subclass with some helper methods.
    """

    def values(self) -> List[object]:
        """Return the values from this node list."""
        return [node.value for node in self]

    def paths(self) -> List[str]:
        """Return normalized paths from this node list."""
        return [node.path() for node in self]

    def items(self) -> List[Tuple[str, object]]:
        """Return a list of (path, value) pairs, one for each node in the list."""
        return [(node.path(), node.value) for node in self]

    def empty(self) -> bool:
        """Return `True` if this node list is empty."""
        return not self

    def __str__(self) -> str:
        return f"NodeList{super().__str__()}"
