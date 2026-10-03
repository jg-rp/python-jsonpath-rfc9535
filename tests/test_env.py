import pytest

from jsonpath_rfc9535 import JSONPathEnvironment


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def test_find_one(env: JSONPathEnvironment) -> None:
    """Test that we can get the first node from a node iterator."""
    match = env.find_one("$.some", {"some": 1, "thing": 2})
    assert match is not None
    assert match.value == 1


def test_find_one_no_match(env: JSONPathEnvironment) -> None:
    """Test that we get `None` if there are no matches."""
    match = env.find_one("$.other", {"some": 1, "thing": 2})
    assert match is None


# TODO:
