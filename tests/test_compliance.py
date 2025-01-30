"""Test Python JSONPath against the JSONPath Compliance Test Suite.

The CTS is a submodule located in /tests/cts. After a git clone, run
`git submodule update --init` from the root of the repository.
"""

import json
import operator
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pytest

import jsonpath_rfc9535 as jsonpath
from jsonpath_rfc9535.environment import JSONValue


@dataclass
class Case:
    name: str
    selector: str
    document: JSONValue = None
    result: Any = None
    result_paths: Optional[List[Any]] = None
    results: Optional[List[Any]] = None
    results_paths: Optional[List[Any]] = None
    invalid_selector: Optional[bool] = None
    tags: List[str] = field(default_factory=list)


SKIP: Dict[str, str] = {}


def cases() -> List[Case]:
    with open("tests/cts/cts.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    return [case for case in cases() if not case.invalid_selector]


def invalid_cases() -> List[Case]:
    return [case for case in cases() if case.invalid_selector]


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])  # no cov

    assert case.document is not None
    nodes = jsonpath.JSONPathNodeList(jsonpath.find(case.selector, case.document))

    if case.results is not None:
        assert isinstance(case.results_paths, list)
        assert nodes.values() in case.results
        assert nodes.paths() in case.results_paths
    else:
        assert nodes.values() == case.result
        assert nodes.paths() == case.result_paths


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_selectors(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])  # no cov

    with pytest.raises(jsonpath.JSONPathError):
        jsonpath.compile(case.selector)
