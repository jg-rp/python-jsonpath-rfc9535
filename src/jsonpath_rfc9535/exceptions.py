from __future__ import annotations

from ._tokens import Token, token_value


class JSONPathError(Exception):
    """The base class for all JSONPath exceptions."""


class DetailedJSONPathError(JSONPathError):
    """A JSONPath exception with contextual information."""

    def __init__(self, msg: str, token: Token, source: str) -> None:
        super().__init__(msg)
        self.token = token
        self.source = source

    def __str__(self) -> str:
        return self.detailed_message()

    def detailed_message(self) -> str:
        """Return an error message formatted with extra context info."""
        span = token_value(self.token, self.source)
        line, col, current_line = self._error_context(self.source, self.token[1])

        pad = " " * len(str(line))
        length = len(span)
        pointer = (" " * col) + ("^" * max(length, 1))

        return (
            f"{self.message}\n"
            f"{pad} -> {self.source!r} {line}:{col}\n"
            f"{pad} |\n"
            f"{line} | {current_line}\n"
            f"{pad} | {pointer} {self.message}\n"
        )

    @property
    def message(self) -> object:
        """The exception's error message if one was given."""
        if self.args:
            return self.args[0]
        return None

    def _error_context(self, source: str, index: int) -> tuple[int, int, str]:
        lines = source.splitlines(keepends=True)
        cumulative_length = 0
        target_line_index = -1

        for i, line in enumerate(lines):
            cumulative_length += len(line)
            if index < cumulative_length:
                target_line_index = i
                break

        if target_line_index == -1:
            # Point to end of input
            return len(lines), len(lines[-1]), lines[-1].rstrip()

        # Line number (1-based)
        line_number = target_line_index + 1
        # Column number within the line
        column_number = index - (cumulative_length - len(lines[target_line_index]))

        current_line = lines[target_line_index].rstrip()
        return line_number, column_number, current_line


class JSONPathNameError(DetailedJSONPathError):
    """The exception raised when a function extension can not be resolved."""


class JSONPathSyntaxError(DetailedJSONPathError):
    """The exception raised due to a malformed JSONPath query."""


class JSONPathTypeError(DetailedJSONPathError):
    """The exceptions raised when a JSONPath query is not well typed."""


class JSONPathRecursionError(JSONPathError):
    """The exception raised when a recursion limit is reached.

    This could be raised at parse time if a JSONPath query contains deeply
    nested expressions. Or at query resolution time if `max_recursion_depth`
    is reached by the descendant segment (`..`).
    """
