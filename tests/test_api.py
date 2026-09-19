import jsonpath_rfc9535 as jsonpath


def test_queries_are_hashable() -> None:
    query = jsonpath.compile("$.a")
    assert isinstance(hash(query), int)
