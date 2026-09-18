from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ._resolve_standard import StandardResolver
from ._resolver_basic import BasicResolver
from ._serialize import canonical_path
from .node import JSONPathNode, JSONPathNodeList

if TYPE_CHECKING:
    from ._ast import Segment
    from .environment import JSONPathEnvironment


class JSONPathQuery:
    """A compiled JSONPath expression ready to be applied to JSON-like data.

    Parameters
    ----------
    env
        The JSONPath configuration object this query is bound to.
    segments
        Our internal representation of a compiled JSONPath query.
    """

    __slots__ = ("env", "segments")

    def __init__(self, env: JSONPathEnvironment, segments: tuple[Segment, ...]) -> None:
        self.env = env
        self.segments = segments

    def __str__(self) -> str:
        return canonical_path(self.segments)

    def __hash__(self) -> int:
        return hash((self.env, self.segments))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, JSONPathQuery) and other.segments == self.segments

    def findall(self, data: object) -> list[object]:
        """Return values found by apply this query to `data`.

        Parameters
        ----------
        data
            JSON-like data to apply this query to.

        Returns
        -------
        list[object]
            All values found by applying this query to `data`.

        Raises
        ------
        JSONPathRecursionError
            If a descendent segment visits nodes to a depth that exceeds the configured
            `max_recursion_depth`.
        """
        return list(BasicResolver.resolve(self.env, self.segments, "$", data))

    def finditer(self, data: object) -> Iterable[JSONPathNode]:
        """Generate `JSONPathNode` instances for each match of this query in `data`.

        Parameters
        ----------
        data
            JSON-like data to apply this query to.

        Yields
        ------
        JSONPathNode
            The matched value and its location in `data`.

        Raises
        ------
        JSONPathRecursionError
            If a descendent segment visits nodes to a depth that exceeds the configured
            `max_recursion_depth`.
        """
        for node in StandardResolver.resolve(self.env, self.segments, "$", data):
            yield JSONPathNode(node)

    def find(self, data: object) -> JSONPathNodeList:
        """Return the list of nodes found by applying this query to `data`.

        Parameters
        ----------
        data
            JSON-like data to apply this query to.

        Returns
        -------
        JSONPathNodeList
            The list of nodes found by applying this query to `data`

        Raises
        ------
        JSONPathRecursionError
            If a descendent segment visits nodes to a depth that exceeds the configured
            `max_recursion_depth`.
        """
        return JSONPathNodeList(self.finditer(data))

    def search(self, data: object) -> JSONPathNode | None:
        """Return the first node found by applying this query to `data`.

        Parameters
        ----------
        data
            JSON-like data to apply this query to.

        Returns
        -------
        node : JSONPathNode, Optional
            The first available `JSONPathNode` instance, or `None` if there are no
            matches.

        Raises
        ------
        JSONPathRecursionError
            If a descendent segment visits nodes to a depth that exceeds the configured
            `max_recursion_depth`.
        """
        try:
            return next(iter(self.finditer(data)))
        except StopIteration:
            return None

    def find_one(self, data: object) -> JSONPathNode | None:
        """An alias for `search`.

        See Also
        --------
        search
        """
        return self.search(data)
