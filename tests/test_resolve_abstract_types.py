import sys
from collections.abc import Iterator, Mapping, Sequence

import pytest

from jsonpath_rfc9535 import JSONPathEnvironment


@pytest.mark.skipif(sys.version_info < (3, 15), reason="requires python3.15 or higher")
def test_frozendict() -> None:
    expr = "$.a.b"
    data: Mapping[str, object] = frozendict({"a": frozendict({"b": 42})})  # type: ignore  # noqa: F821

    assert JSONPathEnvironment(composite_types="strict").findall(expr, data) == []  # type: ignore
    assert JSONPathEnvironment(composite_types="native").findall(expr, data) == []  # type: ignore
    assert JSONPathEnvironment(composite_types="abstract").findall(expr, data) == [42]  # type: ignore


def test_mapping_and_sequence() -> None:
    class MockMapping(Mapping[str, int]):
        def __getitem__(self, key: str) -> int:
            if key == "a":
                return 42
            raise KeyError(key)

        def __iter__(self) -> Iterator[str]:
            return iter(["a"])

        def __len__(self) -> int:
            return 1

    class MockSequence(Sequence[object]):
        def __init__(self, items: list[object]) -> None:
            self.items = items

        def __getitem__(self, index: int) -> object:  # type: ignore
            return self.items[index]

        def __len__(self) -> int:
            return len(self.items)

    expr = "$[1].a"
    data = MockSequence([MockMapping(), MockMapping()])

    assert JSONPathEnvironment(composite_types="strict").findall(expr, data) == []
    assert JSONPathEnvironment(composite_types="native").findall(expr, data) == []
    assert JSONPathEnvironment(composite_types="abstract").findall(expr, data) == [42]
