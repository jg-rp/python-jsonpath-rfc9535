from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from . import functions
from ._parser import Parser
from ._parser_standard import StandardParser
from .node import JSONPathNode, JSONPathNodeList
from .query import JSONPathQuery

if TYPE_CHECKING:
    from .functions import FunctionExtension


class JSONPathEnvironment:
    """JSONPath parser and evaluator configuration.

    Parameters
    ----------
    max_index
        The maximum integer allowed when selecting array items by index.
    min_index
        The minimum integer allowed when selecting array items by index.
    max_recursion_depth
        The maximum depth the descendant segment can go before a `JSONPathRecursionError`
        is raised.
    parser
        The JSONPath query parser to use. You can subclass `StandardParser` to customize
        JSONPath parsing behavior.

    Attributes
    ----------
    functions
        A map of JSONPath function extension names to implementation - classes
        inheriting from `FunctionExtension`.
    """

    def __init__(
        self,
        *,
        max_index: int = (2**53) - 1,
        min_index: int = -(2**53) + 1,
        max_recursion_depth: int = 100,
        parser: Parser = StandardParser,
    ) -> None:

        self.max_recursion_depth = max_recursion_depth
        self.max_index = max_index
        self.min_index = min_index

        self.parser: Parser = parser

        self.functions: dict[str, FunctionExtension] = {
            "count": functions.Count(),
            "length": functions.Length(),
            "match": functions.Match(),
            "search": functions.Search(),
            "value": functions.Value(),
        }

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, JSONPathEnvironment)
            and self.functions == other.functions
            and self.max_recursion_depth == other.max_recursion_depth
            and self.max_index == other.max_index
            and self.min_index == other.min_index
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.max_recursion_depth,
                self.max_index,
                self.min_index,
                tuple(self.functions.items()),
            )
        )

    def compile(self, source: str) -> JSONPathQuery:
        """Prepare JSONPath query `source` for repeated application to different data.

        Parameters
        ----------
        source
            A JSONPath query expression.

        Returns
        -------
        query
            A compiled query ready to match against JSON-like data.

        Raises
        ------
        JSONPathNameError
            If a function extension can not be resolved.
        JSONPathRecursionError
            If `source` is crafted in such a way to hit Python's recursion limit.
            `JSONPathRecursionError` inherits from `RecursionError` too.
        JSONPathSyntaxError
            If `source` is syntactically invalid.
        JSONPathTypeError
            If `source` is semantically invalid - Calling a function extension with
            arguments of the wrong type or arity, for example.
        """
        return self.parser.parse(self, source)

    def parse(self, source: str) -> JSONPathQuery:
        """An alias for `compile`.

        See Also
        --------
        compile
        """
        return self.parser.parse(self, source)

    def find(self, source: str, data: object) -> JSONPathNodeList:
        """Return values found by apply query expression `source` to `data`.

        Parameters
        ----------
        source
            A JSONPath query expression.
        data
            JSON-like data to apply `source` to.

        Returns
        -------
        JSONPathNodeList
            The list of nodes found by applying `source` to `data`

        Raises
        ------
        JSONPathNameError
            If a function extension can not be resolved.
        JSONPathRecursionError
            If `source` is crafted in such a way to hit Python's recursion limit. Or if
            a descendent segment visits nodes to a depth that exceeds the configured
            `max_recursion_depth`.
        JSONPathSyntaxError
            If `source` is syntactically invalid.
        JSONPathTypeError
            If `source` is semantically invalid - Calling a function extension with
            arguments of the wrong type or arity, for example.
        """
        return self.parser.parse(self, source).find(data)

    def findall(self, source: str, data: object) -> list[object]:
        """Return values found by apply query expression `source` to `data`.

        Parameters
        ----------
        source
            A JSONPath query expression.
        data
            JSON-like data to apply `source` to.

        Returns
        -------
        list[object]
            All values found by applying `source` to `data`.

        Raises
        ------
        JSONPathError
            The same as `find`.

        See Also
        --------
        find
        """
        return self.parser.parse(self, source).findall(data)

    def finditer(self, source: str, data: object) -> Iterable[JSONPathNode]:
        """Generate a `JSONPathNode` instance for each match of query expression `source`
        in `data`.

        Parameters
        ----------
        source
            A JSONPath query expression.
        data
            JSON-like data to apply `source` to.

        Yields
        ------
        JSONPathNode
            The matched value and its location in `data`.

        Raises
        ------
        JSONPathError
            The same as `find`.

        See Also
        --------
        find
        """
        return self.parser.parse(self, source).finditer(data)

    def search(self, source: str, data: object) -> JSONPathNode | None:
        """Return the first node found by applying query expression `source` to `data`.

        Parameters
        ----------
        source
            A JSONPath query expression.
        data
            JSON-like data to apply `source` to.

        Returns
        -------
        node : JSONPathNode, Optional
            The first available `JSONPathNode` instance, or `None` if there are no
            matches.

        Raises
        ------
        JSONPathError
            The same as `find`.

        See Also
        --------
        find
        """
        return self.parser.parse(self, source).find_one(data)

    def find_one(self, source: str, data: object) -> JSONPathNode | None:
        """An alias for `search`.

        See Also
        --------
        search
        """
        return self.parser.parse(self, source).find_one(data)
