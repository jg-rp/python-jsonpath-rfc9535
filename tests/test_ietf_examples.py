"""Test cases from examples in draft-ietf-jsonpath-base-11.

The test cases defined here are taken from version 11 of the JSONPath
internet draft, draft-ietf-jsonpath-base-11. In accordance with
https://trustee.ietf.org/license-info, Revised BSD License text
is included bellow.

See https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-11

Copyright (c) 2023 IETF Trust and the persons identified as authors
of the code. All rights reserved.Redistribution and use in source and
binary forms, with or without modification, are permitted provided
that the following conditions are met:

- Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the
  distribution.
- Neither the name of Internet Society, IETF or IETF Trust, nor the
  names of specific contributors, may be used to endorse or promote
  products derived from this software without specific prior written
  permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
“AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import dataclasses
import operator
from typing import Any

import pytest

from jsonpath_rfc9535 import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    query: str
    data: Any
    want: Any


FILTER_SELECTOR_DATA: dict[str, object] = {
    "a": [3, 5, 1, 2, 4, 6, {"b": "j"}, {"b": "k"}, {"b": {}}, {"b": "kilo"}],
    "o": {"p": 1, "q": 2, "r": 3, "s": 5, "t": {"u": 6}},
    "e": "f",
}


TEST_CASES = [
    Case(description="root", query="$", data={"k": "v"}, want=[{"k": "v"}]),
    Case(
        description="name selector - named value in nested object (single quote)",
        query="$.o['j j']['k.k']",
        data={"o": {"j j": {"k.k": 3}}, "'": {"@": 2}},
        want=[3],
    ),
    Case(
        description="name selector - named value in nested object (double quote)",
        query='$.o["j j"]["k.k"]',
        data={"o": {"j j": {"k.k": 3}}, "'": {"@": 2}},
        want=[3],
    ),
    Case(
        description="name selector - unusual member names",
        query='$["\'"]["@"]',
        data={"o": {"j j": {"k.k": 3}}, "'": {"@": 2}},
        want=[2],
    ),
    Case(
        description="wildcard selector - object values",
        query="$[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[{"j": 1, "k": 2}, [5, 3]],
    ),
    Case(
        description="wildcard selector - object values (dot property)",
        query="$.o[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[1, 2],
    ),
    Case(
        description="wildcard selector - double wild",
        query="$.o[*, *]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[1, 2, 1, 2],
    ),
    Case(
        description="wildcard selector - dot property wild",
        query="$.a[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[5, 3],
    ),
    Case(
        description="index selector - element of array",
        query="$[1]",
        data=["a", "b"],
        want=["b"],
    ),
    Case(
        description="index selector - element of array, from the end",
        query="$[-2]",
        data=["a", "b"],
        want=["a"],
    ),
    Case(
        description="array slice selector - slice with default step",
        query="$[1:3]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["b", "c"],
    ),
    Case(
        description="array slice selector - slice with no end index",
        query="$[5:]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["f", "g"],
    ),
    Case(
        description="array slice selector - slice with negative step",
        query="$[5:1:-2]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["f", "d"],
    ),
    Case(
        description="array slice selector - slice in reverse order",
        query="$[::-1]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["g", "f", "e", "d", "c", "b", "a"],
    ),
    Case(
        description="filter selector - Member value comparison",
        query="$.a[?(@.b == 'kilo')]",
        data=FILTER_SELECTOR_DATA,
        want=[{"b": "kilo"}],
    ),
    Case(
        description="filter selector - Array value comparison",
        query="$.a[?(@>3.5)]",
        data=FILTER_SELECTOR_DATA,
        want=[5, 4, 6],
    ),
    Case(
        description="filter selector - Array value existence",
        query="$.a[?(@.b)]",
        data=FILTER_SELECTOR_DATA,
        want=[{"b": "j"}, {"b": "k"}, {"b": {}}, {"b": "kilo"}],
    ),
    Case(
        description="filter selector - Existence of non-singular queries",
        query="$[?(@.*)]",
        data=FILTER_SELECTOR_DATA,
        want=[
            [3, 5, 1, 2, 4, 6, {"b": "j"}, {"b": "k"}, {"b": {}}, {"b": "kilo"}],
            {"p": 1, "q": 2, "r": 3, "s": 5, "t": {"u": 6}},
        ],
    ),
    Case(
        description="filter selector - Nested filters",
        query="$[?(@[?(@.b)])]",
        data=FILTER_SELECTOR_DATA,
        want=[[3, 5, 1, 2, 4, 6, {"b": "j"}, {"b": "k"}, {"b": {}}, {"b": "kilo"}]],
    ),
    Case(
        description="filter selector - Array value logical OR",
        query='$.a[?(@<2 || @.b == "k")]',
        data=FILTER_SELECTOR_DATA,
        want=[1, {"b": "k"}],
    ),
    Case(
        description="filter selector - Array value regular expression match",
        query='$.a[?match(@.b, "[jk]")]',
        data=FILTER_SELECTOR_DATA,
        want=[{"b": "j"}, {"b": "k"}],
    ),
    Case(
        description="filter selector - Array value regular expression search",
        query='$.a[?search(@.b, "[jk]")]',
        data=FILTER_SELECTOR_DATA,
        want=[{"b": "j"}, {"b": "k"}, {"b": "kilo"}],
    ),
    Case(
        description="filter selector - Object value logical AND",
        query="$.o[?(@>1 && @<4)]",
        data=FILTER_SELECTOR_DATA,
        want=[2, 3],
    ),
    Case(
        description="filter selector - Object value logical OR",
        query="$.o[?(@.u || @.x)]",
        data=FILTER_SELECTOR_DATA,
        want=[{"u": 6}],
    ),
    Case(
        description="filter selector - Comparison of queries with no values",
        query="$.a[?(@.b == $.x)]",
        data=FILTER_SELECTOR_DATA,
        want=[3, 5, 1, 2, 4, 6],
    ),
    Case(
        description=(
            "filter selector - Comparisons of primitive and of structured values"
        ),
        query="$.a[?(@ == @)]",
        data=FILTER_SELECTOR_DATA,
        want=[3, 5, 1, 2, 4, 6, {"b": "j"}, {"b": "k"}, {"b": {}}, {"b": "kilo"}],
    ),
    Case(
        description=("child segment - Indices"),
        query="$[0, 3]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["a", "d"],
    ),
    Case(
        description=("child segment - Slice and index"),
        query="$[0:2, 5]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["a", "b", "f"],
    ),
    Case(
        description=("child segment - Duplicated entries"),
        query="$[0, 0]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["a", "a"],
    ),
    Case(
        description=("descendant segment - Object values"),
        query="$..j",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3, [{"j": 4}, {"k": 6}]]},
        want=[1, 4],
    ),
    Case(
        description=("descendant segment - Array values"),
        query="$..[0]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3, [{"j": 4}, {"k": 6}]]},
        want=[5, {"j": 4}],
    ),
    Case(
        description=("descendant segment - All values"),
        query="$..[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3, [{"j": 4}, {"k": 6}]]},
        want=[
            {"j": 1, "k": 2},
            [5, 3, [{"j": 4}, {"k": 6}]],
            1,
            2,
            5,
            3,
            [{"j": 4}, {"k": 6}],
            {"j": 4},
            {"k": 6},
            4,
            6,
        ],
    ),
    Case(
        description=("descendant segment - Input value is visited"),
        query="$..o",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3, [{"j": 4}, {"k": 6}]]},
        want=[{"j": 1, "k": 2}],
    ),
    Case(
        description=("descendant segment - Multiple segments"),
        query="$.a..[0, 1]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3, [{"j": 4}, {"k": 6}]]},
        want=[5, 3, {"j": 4}, {"k": 6}],
    ),
    Case(
        description=("null semantics - Object value"),
        query="$.a",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[None],
    ),
    Case(
        description=("null semantics - null used as array"),
        query="$.a[0]",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[],
    ),
    Case(
        description=("null semantics - null used as object"),
        query="$.a.d",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[],
    ),
    Case(
        description=("null semantics - Array value"),
        query="$.b[0]",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[None],
    ),
    Case(
        description=("null semantics - Array value wild"),
        query="$.b[*]",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[None],
    ),
    Case(
        description=("null semantics - Existence"),
        query="$.b[?(@)]",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[None],
    ),
    Case(
        description=("null semantics - Comparison"),
        query="$.b[?(@==null)]",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[None],
    ),
    Case(
        description=("null semantics - Comparison with 'missing' value"),
        query="$.c[?(@.d==null)]",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[],
    ),
    Case(
        description=(
            "null semantics - Not JSON null at all, just a member name string"
        ),
        query="$.null",
        data={"a": None, "b": [None], "c": [{}], "null": 1},
        want=[1],
    ),
    Case(
        description=("filter, length function, string data"),
        query="$[?(length(@.a)>=2)]",
        data=[{"a": "ab"}, {"a": "d"}],
        want=[{"a": "ab"}],
    ),
    Case(
        description=("filter, length function, array data"),
        query="$[?(length(@.a)>=2)]",
        data=[{"a": [1, 2, 3]}, {"a": [1]}],
        want=[{"a": [1, 2, 3]}],
    ),
    Case(
        description=("filter, length function, missing data"),
        query="$[?(length(@.a)>=2)]",
        data=[{"d": "f"}],
        want=[],
    ),
    Case(
        description=("filter, count function"),
        query="$[?(count(@..*)>2)]",
        data=[{"a": [1, 2, 3]}, {"a": [1], "d": "f"}, {"a": 1, "d": "f"}],
        want=[{"a": [1, 2, 3]}, {"a": [1], "d": "f"}],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_ietf(env: JSONPathEnvironment, case: Case) -> None:
    query = env.compile(case.query)
    assert query.find(case.data).values() == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_hash_path(env: JSONPathEnvironment, case: Case) -> None:
    """Test that paths are hashable."""
    hash(env.compile(case.query))
