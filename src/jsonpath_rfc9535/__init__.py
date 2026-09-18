from __future__ import annotations

from collections.abc import Iterable

from ._debug import tree_view
from ._parser import Parser, Parser_
from ._parser_standard import StandardParser
from .environment import JSONPathEnvironment
from .exceptions import (
    JSONPathError,
    JSONPathNameError,
    JSONPathRecursionError,
    JSONPathSyntaxError,
    JSONPathTypeError,
)
from .node import JSONPathNode, JSONPathNodeList, Node, NodeList
from .query import JSONPathQuery

__all__ = (
    "DEFAULT_ENVIRONMENT",
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

# TODO: docs


def compile(source: str) -> JSONPathQuery:
    return DEFAULT_ENVIRONMENT.compile(source)


def parse(source: str) -> JSONPathQuery:
    return DEFAULT_ENVIRONMENT.parse(source)


def find(source: str, data: object) -> JSONPathNodeList:
    return DEFAULT_ENVIRONMENT.find(source, data)


def finditer(source: str, data: object) -> Iterable[JSONPathNode]:
    return DEFAULT_ENVIRONMENT.finditer(source, data)


def findall(source: str, data: object) -> Iterable[object]:
    return DEFAULT_ENVIRONMENT.findall(source, data)


def search(source: str, data: object) -> JSONPathNode | None:
    return DEFAULT_ENVIRONMENT.search(source, data)


def find_one(source: str, data: object) -> JSONPathNode | None:
    return DEFAULT_ENVIRONMENT.find_one(source, data)
