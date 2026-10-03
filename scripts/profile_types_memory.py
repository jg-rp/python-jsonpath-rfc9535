import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, NamedTuple

import msgspec

COUNT = 100_000
x, y, z = (
    1,
    2,
    3,
)  # Shared references to isolate container memory from integer allocation


class PointStandard:
    def __init__(self, x: int, y: int, z: int):
        self.x, self.y, self.z = x, y, z


class PointSlots:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: int, y: int, z: int):
        self.x, self.y, self.z = x, y, z


@dataclass(slots=True)
class PointDC:
    x: int
    y: int
    z: int


class PointNT(NamedTuple):
    x: int
    y: int
    z: int


class PointMsg(msgspec.Struct):
    x: int
    y: int
    z: int


benchmarks: list[tuple[str, Callable[[], Any]]] = [
    ("Tuple", lambda: [(x, y, z) for _ in range(COUNT)]),
    ("msgspec.Struct", lambda: [PointMsg(x, y, z) for _ in range(COUNT)]),
    ("Class (__slots__)", lambda: [PointSlots(x, y, z) for _ in range(COUNT)]),
    ("Dataclass (slots=True)", lambda: [PointDC(x, y, z) for _ in range(COUNT)]),
    ("Standard Class", lambda: [PointStandard(x, y, z) for _ in range(COUNT)]),
    ("Namedtuple", lambda: [PointNT(x, y, z) for _ in range(COUNT)]),
]

# Baseline measurement for raw list container pointers
tracemalloc.start()
base_list = [None] * COUNT
_, base_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
del base_list

results: list[tuple[str, float, float]] = []
for name, fn in benchmarks:
    tracemalloc.start()
    obj_list = fn()
    current_mem, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    net_bytes = current_mem - base_peak
    bytes_per_obj = net_bytes / COUNT
    total_mb_1m = (bytes_per_obj * 1_000_000) / (1024 * 1024)
    results.append((name, bytes_per_obj, total_mb_1m))
    del obj_list

print(
    f"| {'Data Structure':<22} | {'Bytes / Object':<15} | {'1M Instances (MB)':<18} |"
)
print(f"|:{'-' * 22}-|:{'-' * 15}-|:{'-' * 18}-|")
for name, b_obj, mb in results:
    print(f"| {name:<22} | {b_obj:>13.1f} B | {mb:>15.2f} MB |")
