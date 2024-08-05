"""Test against the JSONPath Compliance Test Suite with nondeterminism enabled.

The CTS is a submodule located in /tests/cts. After a git clone, run
`git submodule update --init` from the root of the repository.
"""

import json
import operator
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

import pytest

from jsonpath_rfc9535 import JSONPathEnvironment
from jsonpath_rfc9535 import JSONValue


@dataclass
class Case:
    name: str
    selector: str
    document: JSONValue = None
    result: Any = None
    results: Optional[List[Any]] = None
    invalid_selector: Optional[bool] = None
    tags: List[str] = field(default_factory=list)


def cases() -> List[Case]:
    with open("tests/cts/cts.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    return [case for case in cases() if not case.invalid_selector]


def nondeterministic_cases() -> List[Case]:
    return [case for case in valid_cases() if isinstance(case.results, list)]


class MockEnv(JSONPathEnvironment):
    nondeterministic = True


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_nondeterminism_valid_cases(case: Case) -> None:
    assert case.document is not None
    env = MockEnv()
    rv = env.find(case.selector, case.document).values()

    if case.results is not None:
        assert rv in case.results
    else:
        assert rv == case.result


@pytest.mark.parametrize(
    "case", nondeterministic_cases(), ids=operator.attrgetter("name")
)
def test_nondeterminism(case: Case) -> None:
    """Test that we agree with CTS when it comes to nondeterministic results."""
    assert case.document is not None
    assert case.results is not None

    def _result_repr(rv: List[object]) -> Tuple[str, ...]:
        """Return a hashable representation of a result list."""
        return tuple([str(value) for value in rv])

    env = MockEnv()

    # Repeat enough times so as to have high probability that we've covered all
    # valid permutations.
    results = {
        _result_repr(env.find(case.selector, case.document).values())
        for _ in range(1000)
    }

    assert len(results) == len(case.results)
    assert results == {_result_repr(result) for result in case.results}
