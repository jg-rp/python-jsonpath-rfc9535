import jsonpath_rfc9535 as jsonpath


def test_issue_13() -> None:
    # This was failing with "unbalanced parentheses".
    _q = jsonpath.compile("$[? count(@.likes[? @.location]) > 3]")
