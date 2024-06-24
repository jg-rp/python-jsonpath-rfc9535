"""JSONPath node locations as persistent linked lists."""

from __future__ import annotations

from typing import Iterator
from typing import Optional
from typing import Union


class Location:
    """JSONPath node location."""

    __slots__ = ("value", "next")

    def __init__(
        self, value: Union[int, str, None], _next: Optional[Location] = None
    ) -> None:
        self.value = value
        self.next = _next

    def __iter__(self) -> Iterator[Union[int, str]]:
        if self.value is not None:
            yield self.value

        _next = self.next
        while _next is not None:
            if _next.value is not None:
                yield _next.value
            _next = _next.next

    def prepend(self, value: Union[int, str]) -> Location:
        """Return a copy of this location with _value_ appended to the front."""
        return Location(value, self)
