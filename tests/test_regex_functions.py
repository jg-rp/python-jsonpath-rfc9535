import pytest

from jsonpath_rfc9535 import JSONPathEnvironment, functions


@pytest.mark.parametrize(
    ("expr", "data", "want", "escape"),
    [
        ("$[?match(@, '^ab.*')]", ["abc", "axc", "ab", "xab"], ["abc", "ab"], False),
        ("$[?match(@, '.*bc$')]", ["abc", "axc", "ab", "abcx"], ["abc"], False),
        ("$[?match(@, '^ab.*')]", ["abc", "axc", "^ab", "xab"], ["^ab"], True),
        ("$[?match(@, '.*bc$')]", ["abc", "axc", "ab", "abc$"], ["abc$"], True),
    ],
)
def test_escape_anchors(expr: str, data: object, want: object, escape: bool) -> None:
    env = JSONPathEnvironment()
    env.functions["match"] = functions.Match(escape_anchors=escape)
    env.functions["search"] = functions.Search(escape_anchors=escape)

    assert env.findall(expr, data) == want
