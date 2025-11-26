from jsonpath_rfc9535 import find_one


def test_parent() -> None:
    data = {"a": {"b": {"c": 1}}}
    query = "$.a.b.c"
    node = find_one(query, data)
    assert node is not None
    assert node.value == 1
    assert node.parent is not None
    assert node.parent.value == data["a"]["b"]


def test_parent_of_root() -> None:
    data = {"a": {"b": {"c": 1}}}
    query = "$"
    node = find_one(query, data)
    assert node is not None
    assert node.value == data
    assert node.parent is None


def test_set_dict_value() -> None:
    data = {"a": {"b": {"c": 1}}}
    query = "$.a.b.c"
    node = find_one(query, data)
    assert node is not None

    new_value = 99
    node.value = new_value
    assert node.value == new_value
    assert data["a"]["b"]["c"] == new_value


def test_set_list_value() -> None:
    data = {"a": {"b": [1, 2, 3]}}
    query = "$.a.b[1]"
    node = find_one(query, data)
    assert node is not None

    new_value = 99
    node.value = new_value
    assert node.value == new_value
    assert data["a"]["b"][1] == new_value


def test_set_root_value() -> None:
    data = {"a": {"b": {"c": 1}}}
    query = "$"
    node = find_one(query, data)
    assert node is not None

    new_value = 99
    node.value = new_value
    assert node.value == new_value
    assert data == {"a": {"b": {"c": 1}}}
