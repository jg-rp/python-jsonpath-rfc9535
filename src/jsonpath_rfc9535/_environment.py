from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from . import functions
from ._node import JSONPathNode, JSONPathNodeList
from ._parser import Parser
from ._parser_standard import StandardParser
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
    max_expression_depth
        The maximum number of nested expressions allowed in a query before a
        `JSONPathRecursionError` is raised.
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
        max_expression_depth: int = 30,
        parser: Parser = StandardParser,
    ) -> None:

        self.max_recursion_depth = max_recursion_depth
        self.max_expression_depth = max_expression_depth
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

    def compile(self, expr: str) -> JSONPathQuery:
        """Prepare JSONPath query `expr` for repeated application to different data.

        Parameters
        ----------
        expr
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
            If `expr` is crafted in such a way to hit Python's recursion limit.
        JSONPathSyntaxError
            If `expr` is syntactically invalid.
        JSONPathTypeError
            If `expr` is semantically invalid - Calling a function extension with
            arguments of the wrong type or arity, for example.
        """
        return self.parser.parse(self, expr)

    def parse(self, expr: str) -> JSONPathQuery:
        """An alias for `compile`.

        See Also
        --------
        compile
        """
        return self.parser.parse(self, expr)

    def find(self, expr: str, data: object) -> JSONPathNodeList:
        """Return nodes found by apply query expression `expr` to `data`.

        Parameters
        ----------
        expr
            A JSONPath query expression.
        data
            JSON-like data to apply `expr` to.

        Returns
        -------
        JSONPathNodeList
            A list of JSON-like values and their location in `data`.

        Raises
        ------
        JSONPathNameError
            If a function extension can not be resolved.
        JSONPathRecursionError
            If `expr` is crafted in such a way to hit Python's recursion limit. Or if
            a descendent segment visits nodes to a depth that exceeds the configured
            `max_recursion_depth`.
        JSONPathSyntaxError
            If `expr` is syntactically invalid.
        JSONPathTypeError
            If `expr` is semantically invalid - Calling a function extension with
            arguments of the wrong type or arity, for example.
        """
        return self.parser.parse(self, expr).find(data)

    def findall(self, expr: str, data: object) -> list[object]:
        """Return values found by apply query expression `expr` to `data`.

        Parameters
        ----------
        expr
            A JSONPath query expression.
        data
            JSON-like data to apply `expr` to.

        Returns
        -------
        list[object]
            All values found by applying `expr` to `data`.

        Raises
        ------
        JSONPathError
            The same as `find`.

        See Also
        --------
        find
        """
        return self.parser.parse(self, expr).findall(data)

    def finditer(self, expr: str, data: object) -> Iterable[JSONPathNode]:
        """Generate nodes from applying query expression `expr` to `data`.

        Parameters
        ----------
        expr
            A JSONPath query expression.
        data
            JSON-like data to apply `expr` to.

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
        return self.parser.parse(self, expr).finditer(data)

    def search(self, expr: str, data: object) -> JSONPathNode | None:
        """Return the first node found by applying query expression `expr` to `data`.

        Parameters
        ----------
        expr
            A JSONPath query expression.
        data
            JSON-like data to apply `expr` to.

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
        return self.parser.parse(self, expr).find_one(data)

    def find_one(self, expr: str, data: object) -> JSONPathNode | None:
        """An alias for `search`.

        See Also
        --------
        search
        """
        return self.parser.parse(self, expr).find_one(data)
