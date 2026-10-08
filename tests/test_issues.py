import pytest

import jsonpath_rfc9535 as jsonpath


def test_issue_13() -> None:
    # This was failing with "unbalanced parentheses".
    _q = jsonpath.compile("$[? count(@.likes[? @.location]) > 3]")


def test_issue_21() -> None:
    data = {"foo": {"bar": {"baz": 42}}}
    node = jsonpath.find_one("$.foo.bar.baz", data)

    expected = 42
    assert node is not None
    assert node.value == expected
    assert data["foo"]["bar"]["baz"] == expected

    new_value = 99
    node.value = new_value
    assert node.value == new_value
    assert data["foo"]["bar"]["baz"] == new_value

    parent = node.parent()
    assert parent is not None
    assert parent.value == {"baz": new_value}
    assert parent.value["baz"] == new_value  # type: ignore


def test_issue_26() -> None:
    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.compile("$[1,]")

    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.compile("$[1, ]")

    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.compile("$[ 1, ]")


def test_issue_27() -> None:
    assert jsonpath.findall("$[?@ > false]", [0, 1, True, False]) == []
    assert jsonpath.findall("$[?@ < true]", [0, 1, True]) == []
    assert jsonpath.findall("$[?@ >= 0]", [True, False, 0]) == [0]
