from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal

from . import functions
from ._node import JSONPathNode, JSONPathNodeList
from ._parser import Parser
from ._parser_standard import StandardParser
from ._resolver_basic_abstract import BasicResolverAbstract
from ._resolver_basic_native import BasicResolverNative
from ._resolver_basic_strict import BasicResolverStrict
from ._resolver_standard_abstract import StandardResolverAbstract
from ._resolver_standard_native import StandardResolverNative
from ._resolver_standard_strict import StandardResolverStrict
from .query import JSONPathQuery

if TYPE_CHECKING:
    from ._resolver import BasicResolver, Resolver
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
        The JSONPath query parser to use. You can subclass ``StandardParser`` to
        customize JSONPath parsing behavior.
    composite_types
        One of ``"strict"``, ``"native"`` or ``"abstract"``.

        In order from fastest to slowest, the strict strategy works with data composed of
        :class:`list` and :class:`dict` instances. The native strategy works with data
        composed of lists, dicts and list/dict subclasses. And the abstract strategy
        works with data composed of Mapping and Sequence types.

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
        composite_types: Literal["strict", "native", "abstract"] = "native",
    ) -> None:

        self.max_recursion_depth = max_recursion_depth
        self.max_expression_depth = max_expression_depth
        self.max_index = max_index
        self.min_index = min_index

        self.parser: Parser = parser

        if composite_types == "strict":
            self.resolver: Resolver = StandardResolverStrict
            self.basic_resolver: BasicResolver = BasicResolverStrict
        elif composite_types == "native":
            self.resolver = StandardResolverNative
            self.basic_resolver = BasicResolverNative
        else:
            self.resolver = StandardResolverAbstract
            self.basic_resolver = BasicResolverAbstract

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
        """Apply JSONPath query `expr` to `data` and return a list of nodes.

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
        """Apply JSONPath query `expr` to `data` and return a list of values.

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
