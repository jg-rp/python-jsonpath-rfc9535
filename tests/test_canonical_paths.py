import dataclasses
import json
import operator

import pytest

from jsonpath_rfc9535 import parse


@dataclasses.dataclass
class Case:
    name: str
    source: str
    want: str


with open("tests/canonical_paths.json") as fd:
    CASES = [
        Case(t["name"], t["query"], t["canonical"]) for t in json.load(fd)["tests"]
    ]


@pytest.mark.parametrize("case", CASES, ids=operator.attrgetter("name"))
def test_canonical_paths(case: Case) -> None:
    """Test the string representation of a compiled JSONPath query."""
    assert str(parse(case.source)) == case.want
