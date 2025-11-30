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

    parent = node.parent
    assert parent is not None
    assert parent.value == {"baz": new_value}
    assert parent.value["baz"] == new_value  # type: ignore
