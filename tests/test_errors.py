import re

import pytest

from jsonpath_rfc9535 import (
    JSONPathEnvironment,
    JSONPathRecursionError,
    JSONPathSyntaxError,
    JSONPathTypeError,
)


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize(
    ("query"),
    [
        "$[1,2",
        "$[?@.a < 1",
    ],
)
def test_missing_right_bracket(query: str, env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError, match=r"unexpected end of query"):
        env.compile(query)


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("$[?(length()==1)]", "length() takes 1 argument (0 given)"),
        ("$[?(match('foo'))]", "match() takes 2 arguments (1 given)"),
        ("$[?(count(@.a, @.b))]", "count() takes 1 argument (2 given)"),
    ],
)
def test_function_arity(query: str, message: str, env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathTypeError, match=re.escape(message)):
        env.compile(query)


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("$[?@.* > 2]", "non-singular query is not comparable"),
    ],
)
def test_compare_non_singular(
    query: str, message: str, env: JSONPathEnvironment
) -> None:
    with pytest.raises(JSONPathTypeError, match=re.escape(message)):
        env.compile(query)


def test_recursive_data(env: JSONPathEnvironment) -> None:
    source = "$..a"
    data: dict[str, list[object]] = {"a": []}
    data["a"].append(data)

    with pytest.raises(JSONPathRecursionError, match="recursion limit reached"):
        env.find(source, data)


def test_low_recursion_limit() -> None:
    env = JSONPathEnvironment(max_recursion_depth=3)
    source = "$..a"
    data = {"foo": [{"bar": [1, 2, 3]}]}

    with pytest.raises(JSONPathRecursionError, match="recursion limit reached"):
        env.find(source, data)


def test_unbalanced_parens(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError, match="unbalanced brackets"):
        env.compile("$.values[?match(@.a, value($..['regex'])]")


def test_compile_time_recursion_error(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathRecursionError):
        env.compile("$[?" + "!" * 50 + "@.a]")


def test_single_amp(env: JSONPathEnvironment) -> None:
    with pytest.raises(
        JSONPathSyntaxError, match=re.escape("unexpected '&', did you mean '&&'?")
    ):
        env.compile("$[?(@.a & @.b)]")


def test_single_pipe(env: JSONPathEnvironment) -> None:
    with pytest.raises(
        JSONPathSyntaxError, match=re.escape("unexpected '|', did you mean '||'?")
    ):
        env.compile("$[?(@.a | @.b)]")
