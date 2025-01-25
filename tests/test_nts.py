"""Test Python JSONPath against the Normalized Path Test Suite."""

import json
import operator
from dataclasses import dataclass
from typing import List

import pytest

import jsonpath_rfc9535 as jsonpath
from jsonpath_rfc9535.environment import JSONValue


@dataclass
class NormalizedCase:
    name: str
    query: str
    document: JSONValue
    paths: list[str]


def normalized_cases() -> List[NormalizedCase]:
    with open("tests/nts/normalized_paths.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [NormalizedCase(**case) for case in data["tests"]]


@pytest.mark.parametrize("case", normalized_cases(), ids=operator.attrgetter("name"))
def test_nts_normalized_paths(case: NormalizedCase) -> None:
    nodes = jsonpath.find(case.query, case.document)
    paths = [node.path() for node in nodes]
    assert paths == case.paths


@dataclass
class CanonicalCase:
    name: str
    query: str
    canonical: str


def canonical_cases() -> List[CanonicalCase]:
    with open("tests/nts/canonical_paths.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [CanonicalCase(**case) for case in data["tests"]]


@pytest.mark.parametrize("case", canonical_cases(), ids=operator.attrgetter("name"))
def test_nts_canonical_paths(case: CanonicalCase) -> None:
    query = jsonpath.compile(case.query)
    assert str(query) == case.canonical
