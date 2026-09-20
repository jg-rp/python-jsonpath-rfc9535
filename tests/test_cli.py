"""Test cases for the command line interface."""

import argparse
import json
import pathlib

import pytest

from jsonpath_rfc9535 import JSONPathSyntaxError, JSONPathTypeError
from jsonpath_rfc9535.__about__ import __version__
from jsonpath_rfc9535.cli import handle_path_command, setup_parser

SAMPLE_DATA: dict[str, object] = {
    "categories": [
        {
            "name": "footwear",
            "products": [
                {
                    "title": "Trainers",
                    "description": "Fashionable trainers.",
                    "price": 89.99,
                },
                {
                    "title": "Barefoot Trainers",
                    "description": "Running trainers.",
                    "price": 130.00,
                },
            ],
        },
        {
            "name": "headwear",
            "products": [
                {
                    "title": "Cap",
                    "description": "Baseball cap",
                    "price": 15.00,
                },
                {
                    "title": "Beanie",
                    "description": "Winter running hat.",
                    "price": 9.00,
                },
            ],
        },
    ],
    "price_cap": 10,
}


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return setup_parser()


@pytest.fixture()
def invalid_target(tmp_path: pathlib.Path) -> str:
    target_path = tmp_path / "source.json"
    with open(target_path, "w") as fd:
        fd.write(r"}}invalid")
    return str(target_path)


@pytest.fixture()
def outfile(tmp_path: pathlib.Path) -> str:
    output_path = tmp_path / "result.json"
    return str(output_path)


@pytest.fixture()
def sample_target(tmp_path: pathlib.Path) -> str:
    target_path = tmp_path / "source.json"
    with open(target_path, "w") as fd:
        json.dump(SAMPLE_DATA, fd)
    return str(target_path)


def test_help(
    parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that the CLI can display a help message without a command."""
    with pytest.raises(SystemExit) as err:
        parser.parse_args(["-h"])

    captured = capsys.readouterr()
    assert err.value.code == 0
    assert captured.out == parser.format_help()


def test_version(
    parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that the CLI can display a version number without a command."""
    with pytest.raises(SystemExit) as err:
        parser.parse_args(["--version"])

    captured = capsys.readouterr()
    assert err.value.code == 0
    assert captured.out.strip() == f"jsonpath-rfc9535, version {__version__}"


def test_path_command_invalid_target(
    parser: argparse.ArgumentParser,
    invalid_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle invalid JSON."""
    args = parser.parse_args(["-q", "$.foo", "-f", invalid_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("target document json decode error:")


def test_path_command_invalid_target_debug(
    parser: argparse.ArgumentParser,
    invalid_target: str,
) -> None:
    """Test that we can debug invalid JSON."""
    args = parser.parse_args(["--debug", "-q", "$.foo", "-f", invalid_target])
    with pytest.raises(json.JSONDecodeError):
        handle_path_command(args)


def test_jsonpath_syntax_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["-q", "$.1", "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("syntax error")


def test_jsonpath_syntax_error_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["--debug", "-q", "$.1", "-f", sample_target])
    with pytest.raises(JSONPathSyntaxError):
        handle_path_command(args)


def test_jsonpath_type_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a JSONPath with a type error."""
    args = parser.parse_args(["-q", "$.foo[?count(@.bar, 'baz')]", "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("type error")


def test_jsonpath_type_error_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
) -> None:
    """Test that we handle a JSONPath with a type error."""
    args = parser.parse_args(
        ["--debug", "-q", "$.foo[?count(@.bar, 'baz')]", "-f", sample_target]
    )

    with pytest.raises(JSONPathTypeError):
        handle_path_command(args)


def test_jsonpath_not_well_typed(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we get an error when a JSONPath query is not well-typed."""
    # `count()` must be compared
    query = "$[?count(@..*)]"

    args = parser.parse_args(
        [
            "-q",
            query,
            "-f",
            sample_target,
        ]
    )

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("type error")


def test_jsonpath_index_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["-q", f"$.foo[{2**53}]", "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("syntax error")


def test_jsonpath_index_error_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["--debug", "-q", f"$.foo[{2**53}]", "-f", sample_target])

    with pytest.raises(JSONPathSyntaxError):
        handle_path_command(args)


def test_jsonpath(
    parser: argparse.ArgumentParser,
    sample_target: str,
    outfile: str,
) -> None:
    """Test a valid JSONPath."""
    args = parser.parse_args(
        ["-q", "$..products.*", "-f", sample_target, "-o", outfile]
    )

    handle_path_command(args)

    with open(outfile, "r") as fd:
        assert len(json.load(fd)) == 4
