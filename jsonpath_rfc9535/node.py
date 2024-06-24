"""JSONPath node and node list definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import List
from typing import Tuple

if TYPE_CHECKING:
    from .environment import JSONValue
    from .location import Location


class JSONPathNode:
    """A JSON-like value and its location in a JSON document.

    Attributes:
        value: The JSON-like value at this node.
        location: The names indices that make up the normalized path to _value_.
    """

    __slots__ = (
        "value",
        "location",
        "root",
    )

    def __init__(
        self,
        *,
        value: object,
        location: Location,
        root: JSONValue,
    ) -> None:
        self.value: object = value
        self.location: Location = location
        self.root = root

    def path(self) -> str:
        """Return the normalized path to this node."""
        return "$" + "".join(
            (
                f"['{p}']" if isinstance(p, str) else f"[{p}]"
                for p in reversed(list(self.location))
            )
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

    def items(self) -> List[Tuple[str, object]]:
        """Return a list of (path, value) pairs, one for each node in the list."""
        return [(node.path(), node.value) for node in self]

    def empty(self) -> bool:
        """Return `True` if this node list is empty."""
        return not self

    def __str__(self) -> str:
        return f"NodeList{super().__str__()}"
