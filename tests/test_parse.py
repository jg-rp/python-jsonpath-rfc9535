import dataclasses
import operator

import pytest

from jsonpath_rfc9535 import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    query: str
    want: str


TEST_CASES = [
    Case(description="just root", query="$", want="$"),
    Case(description="root dot property", query="$.thing", want="$['thing']"),
    Case(description="root bracket property", query="$['thing']", want="$['thing']"),
    Case(
        description="root double quoted property", query='$["thing"]', want="$['thing']"
    ),
    Case(
        description="root single quoted property", query="$['thing']", want="$['thing']"
    ),
    Case(
        description="root quoted property with non-ident chars",
        query="$['anything{!%']",
        want="$['anything{!%']",
    ),
    Case(description="root bracket index", query="$[1]", want="$[1]"),
    Case(description="root slice", query="$[1:-1]", want="$[1:-1:1]"),
    Case(description="root slice with step", query="$[1:-1:2]", want="$[1:-1:2]"),
    Case(description="root slice with empty start", query="$[:-1]", want="$[:-1:1]"),
    Case(description="root slice with empty stop", query="$[1:]", want="$[1::1]"),
    Case(description="root dot wild", query="$.*", want="$[*]"),
    Case(description="root bracket wild", query="$[*]", want="$[*]"),
    Case(description="root selector list", query="$[1,2]", want="$[1, 2]"),
    Case(
        description="root selector list with slice",
        query="$[1,5:-1:1]",
        want="$[1, 5:-1:1]",
    ),
    Case(
        description="root selector list with quoted properties",
        query="$[\"some\",'thing']",
        want="$['some', 'thing']",
    ),
    Case(
        description="implicit root selector list with mixed selectors",
        query='$["some","thing", 1, 2:-2:2]',
        want="$['some', 'thing', 1, 2:-2:2]",
    ),
    Case(
        description="filter self dot property",
        query="$[?(@.thing)]",
        want="$[?@['thing']]",
    ),
    Case(
        description="filter root dot property",
        query="$.some[?($.thing)]",
        want="$['some'][?$['thing']]",
    ),
    Case(
        description="filter with equality test",
        query="$.some[?(@.thing == 7)]",
        want="$['some'][?@['thing'] == 7]",
    ),
    Case(
        description="filter with >=",
        query="$.some[?(@.thing >= 7)]",
        want="$['some'][?@['thing'] >= 7]",
    ),
    Case(
        description="filter with !=",
        query="$.some[?(@.thing != 7)]",
        want="$['some'][?@['thing'] != 7]",
    ),
    Case(
        description="filter with boolean literals",
        query="$.some[?(true == false)]",
        want="$['some'][?true == false]",
    ),
    Case(
        description="filter with null literal",
        query="$.some[?(@.thing == null)]",
        want="$['some'][?@['thing'] == null]",
    ),
    Case(
        description="filter with string literal",
        query="$.some[?(@.thing == 'foo')]",
        want="$['some'][?@['thing'] == 'foo']",
    ),
    Case(
        description="filter with integer literal",
        query="$.some[?(@.thing == 1)]",
        want="$['some'][?@['thing'] == 1]",
    ),
    Case(
        description="filter with float literal",
        query="$.some[?(@.thing == 1.1)]",
        want="$['some'][?@['thing'] == 1.1]",
    ),
    Case(
        description="filter with logical not",
        query="$.some[?(@.thing > 1 && !$.other)]",
        want="$['some'][?@['thing'] > 1 && !$['other']]",
    ),
    Case(
        description="filter with grouped expression",
        query="$.some[?(@.thing > 1 && ($.foo || $.bar))]",
        want="$['some'][?@['thing'] > 1 && ($['foo'] || $['bar'])]",
    ),
    Case(
        description="comparison to single quoted string literal with escape",
        query="$[?@.foo == 'ba\\'r']",
        want="$[?@['foo'] == 'ba\\'r']",
    ),
    Case(
        description="comparison to double quoted string literal with escape",
        query='$[?@.foo == "ba\\"r"]',
        want="$[?@['foo'] == 'ba\"r']",
    ),
    Case(
        description="not binds more tightly than or",
        query="$[?!@.a || !@.b]",
        want="$[?!@['a'] || !@['b']]",
    ),
    Case(
        description="not binds more tightly than and",
        query="$[?!@.a && !@.b]",
        want="$[?!@['a'] && !@['b']]",
    ),
    Case(
        description="control precedence with parens",
        query="$[?!(@.a && !@.b)]",
        want="$[?!(@['a'] && !@['b'])]",
    ),
    Case(
        description="filter query, multiple bracketed segments",
        query="$[?@[0][1]]",
        want="$[?@[0][1]]",
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_parser(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.query)
    assert str(path) == case.want
