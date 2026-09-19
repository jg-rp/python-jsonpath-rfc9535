from ._node import NodeList


class _Nothing:
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Nothing) or (
            isinstance(other, NodeList) and len(other) == 0
        )

    def __str__(self) -> str:
        return "NOTHING"


NOTHING = _Nothing()
