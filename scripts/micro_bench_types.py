import timeit

SETUP = """
import msgspec

x, y, z = 1, 2, 3

class PointSlots:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

from dataclasses import dataclass
@dataclass(slots=True)
class PointDC:
    x: int; y: int; z: int

class Point:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

from collections import namedtuple
PointNT = namedtuple('PointNT', 'x y z')

class PointStruct(msgspec.Struct):
    x: int; y: int; z: int
"""

benchmarks = [
    ("Tuple (literal constant)", "(1, 2, 3)"),
    ("Tuple (dynamic creation)", "(x, y, z)"),
    ("msgspec.Struct", "PointStruct(1, 2, 3)"),
    ("Dataclass (slots=True)", "PointDC(x, y, z)"),
    ("Class (__slots__)", "PointSlots(x, y, z)"),
    ("Standard Class", "Point(x, y, z)"),
    ("Namedtuple", "PointNT(x, y, z)"),
]

NUMBER, REPEAT = 5_000_000, 5
results: list[tuple[str, float]] = []

for name, stmt in benchmarks:
    times = timeit.repeat(stmt, setup=SETUP, number=NUMBER, repeat=REPEAT)
    min_ns = (min(times) / NUMBER) * 1e9
    results.append((name, min_ns))

dyn_tuple_time = results[1][1]

print(f"| {'Data Structure':<24} | {'Time (ns/op)':<12} | {'vs Dynamic Tuple':<16} |")
print(f"|:{'-' * 24}-|:{'-' * 12}-|:{'-' * 16}-|")
for name, ns in results:
    ratio = ns / dyn_tuple_time
    print(f"| {name:<24} | {ns:>9.2f} ns | {ratio:>15.1f}x |")
