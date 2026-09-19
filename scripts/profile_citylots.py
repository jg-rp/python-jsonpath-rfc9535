import dataclasses
import json
import tracemalloc

from jsonpath_rfc9535 import compile


@dataclasses.dataclass
class Fixture:
    name: str
    path: str
    want: dict[str, int]
    data: object = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        with open(self.path) as fd:
            self.data = json.load(fd)


FIXTURES: list[Fixture] = [
    Fixture(
        name="small-citylots",
        path="../ref/small-citylots.json",
        want={"shallow": 49998, "deep": 49998, "conditional": 643},
    ),
    Fixture(
        name="medium-citylots",
        path="../ref/medium-citylots.json",
        want={"shallow": 99998, "deep": 99998, "conditional": 824},
    ),
    Fixture(
        name="citylots",
        path="../ref/citylots.json",
        want={"shallow": 206560, "deep": 206560, "conditional": 2843},
    ),
]

QUERIES = {
    "shallow": compile("$.features..properties"),
    "deep": compile("$.features..properties.BLOCK_NUM"),
    "conditional": compile(
        "$.features[?@.properties.STREET=='UNKNOWN'].properties.BLOCK_NUM"
    ),
    "regex": compile(
        "$.features[?match(@.properties.STREET, 'UNKNOWN')].properties.BLOCK_NUM"
    ),
}

print(f"{'Profile':<35} | {'Mem (MB)':<10} | {'Peak Mem (MB)':<10}")
print("-" * 66)

for fixture in FIXTURES:
    for name, query in QUERIES.items():
        profile_name = f"{fixture.name}:{name}"

        tracemalloc.start()

        _ = query.findall(fixture.data)

        eval_current, eval_peak = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        tracemalloc.stop()

        mem = eval_current / (1024 * 1024)
        peak = eval_peak / (1024 * 1024)

        print(f"{profile_name:<35} | {mem:<10.4f} | {peak:<10.4f}")
