from __future__ import annotations

from collections.abc import Iterable

from ._debug import tree_view
from ._environment import JSONPathEnvironment
from ._node import JSONPathNode, JSONPathNodeList, Node, NodeList
from ._parser import Parser, Parser_
from ._parser_standard import StandardParser
from .exceptions import (
    JSONPathError,
    JSONPathNameError,
    JSONPathRecursionError,
    JSONPathSyntaxError,
    JSONPathTypeError,
)
from .functions import (
    LOGICAL_TYPE,
    NODES_TYPE,
    VALUE_TYPE,
    ExpressionType,
    FunctionExtension,
)
from .query import JSONPathQuery

__all__ = (
    "DEFAULT_ENVIRONMENT",
    "LOGICAL_TYPE",
    "NODES_TYPE",
    "VALUE_TYPE",
    "ExpressionType",
    "FunctionExtension",
    "JSONPathEnvironment",
    "JSONPathError",
    "JSONPathNameError",
    "JSONPathNode",
    "JSONPathNodeList",
    "JSONPathQuery",
    "JSONPathRecursionError",
    "JSONPathSyntaxError",
    "JSONPathTypeError",
    "Node",
    "NodeList",
    "Parser",
    "Parser_",
    "StandardParser",
    "parse",
    "tree_view",
)

DEFAULT_ENVIRONMENT = JSONPathEnvironment()
"""Default JSONPath configuration equivalent to `JSONPathEnvironment()` with no arguments."""


def compile(expr: str) -> JSONPathQuery:
    """Compile JSONPath query `expr` using the default configuration.

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
        `JSONPathRecursionError` inherits from `RecursionError` too.
    JSONPathSyntaxError
        If `expr` is syntactically invalid.
    JSONPathTypeError
        If `expr` is semantically invalid - Calling a function extension with
        arguments of the wrong type or arity, for example.
    """
    return DEFAULT_ENVIRONMENT.compile(expr)


def parse(expr: str) -> JSONPathQuery:
    """An alias for `compile`.

    See Also
    --------
    compile
    """
    return DEFAULT_ENVIRONMENT.parse(expr)


def find(expr: str, data: object) -> JSONPathNodeList:
    """Return nodes found by apply query expression `expr` to `data` using the default
    configuration.

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
    return DEFAULT_ENVIRONMENT.find(expr, data)


def finditer(expr: str, data: object) -> Iterable[JSONPathNode]:
    """Generate nodes from applying query expression `expr` to `data` using the default
    configuration.

    Parameters
    ----------
    expr
        A JSONPath query expression.
    data
        JSON-like data to apply `expr` to.

    Yields
    ------
    JSONPathNode
        Matched JSON-like values and their locations in `data`.

    Raises
    ------
    JSONPathError
        The same as `find`.

    See Also
    --------
    find
    """
    return DEFAULT_ENVIRONMENT.finditer(expr, data)


def findall(expr: str, data: object) -> list[object]:
    """Return all values found from applying query expression `expr` to `data`.

    Use `findall` if you just need values from `data`, without their location or
    normalized path. It can be significantly faster and more memory efficient than
    find` or `finditer`.

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
    return DEFAULT_ENVIRONMENT.findall(expr, data)


def search(expr: str, data: object) -> JSONPathNode | None:
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
    return DEFAULT_ENVIRONMENT.search(expr, data)


def find_one(expr: str, data: object) -> JSONPathNode | None:
    """An alias for `search`.

    See Also
    --------
    search
    """
    return DEFAULT_ENVIRONMENT.find_one(expr, data)
