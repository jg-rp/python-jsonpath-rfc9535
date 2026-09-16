import json
import operator
from dataclasses import dataclass, field

import pytest

import jsonpath_rfc9535 as jsonpath


@dataclass
class Case:
    name: str
    selector: str
    document: object = None
    result: object = None
    result_paths: list[object] | None = None
    results: list[object] | None = None
    results_paths: list[object] | None = None
    invalid_selector: bool | None = None
    tags: list[str] = field(default_factory=list[str])


with open("tests/cts/cts.json", encoding="utf8") as fd:
    # cts is a git submodule. Run `git submodule update --init` from the root
    # of the repository.
    TEST_CASES = [Case(**case) for case in json.load(fd)["tests"]]


@pytest.mark.parametrize(
    "case",
    [c for c in TEST_CASES if not c.invalid_selector],
    ids=operator.attrgetter("name"),
)
def test_compliance(case: Case) -> None:
    nodes = jsonpath.find(case.selector, case.document)

    if case.results is not None:
        assert isinstance(case.results_paths, list)
        assert nodes.values() in case.results
        assert nodes.paths() in case.results_paths
    else:
        assert nodes.values() == case.result
        assert nodes.paths() == case.result_paths


@pytest.mark.parametrize(
    "case",
    [c for c in TEST_CASES if c.invalid_selector],
    ids=operator.attrgetter("name"),
)
def test_invalid_selectors(case: Case) -> None:
    with pytest.raises(jsonpath.JSONPathError):
        jsonpath.parse(case.selector)
