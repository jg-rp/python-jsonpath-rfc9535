import pytest
import regex

from jsonpath_rfc9535 import JSONPathError
from jsonpath_rfc9535.functions import Search


def test_patterns_are_cached() -> None:
    search = Search(cache_capacity=2)
    assert len(search.cache) == 0
    assert search("abcdef", "bc.")
    assert len(search.cache) == 1


def test_malformed_patterns_are_cached() -> None:
    search = Search(cache_capacity=2)
    assert len(search.cache) == 0
    assert search("abcdef", "bc[") is False
    assert len(search.cache) == 1
    assert search.cache["bc["] == search.INVALID_PATTERN


def test_invalid_iregexp_patterns_are_cached() -> None:
    search = Search(cache_capacity=2)
    assert len(search.cache) == 0
    assert search("ab123cdef", "\\d+") is False
    assert len(search.cache) == 1
    assert search.cache["\\d+"] == search.INVALID_PATTERN


def test_cache_capacity() -> None:
    search = Search(cache_capacity=2)
    assert len(search.cache) == 0
    assert search("1abcdef", "ab[a-z]")
    assert len(search.cache) == 1
    assert search("2abcdef", "bc[a-z]")
    assert len(search.cache) == 2
    assert search("3abcdef", "cd[a-z]")
    assert len(search.cache) == 2
    assert "cd[a-z]" in search.cache
    assert "bc[a-z]" in search.cache
    assert "ab[a-z]" not in search.cache


def test_debug_regex_patterns() -> None:
    search = Search(cache_capacity=2, debug=True)
    assert len(search.cache) == 0

    with pytest.raises((JSONPathError, regex.error)):
        search("abcdef", "bc[")
