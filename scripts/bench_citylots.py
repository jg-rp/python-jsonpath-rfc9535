import dataclasses
import json
import timeit

from jsonpath_rfc9535 import JSONPathQuery, parse


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
    "shallow": parse("$.features..properties"),
    "deep": parse("$.features..properties.BLOCK_NUM"),
    "conditional": parse(
        "$.features[?@.properties.STREET=='UNKNOWN'].properties.BLOCK_NUM"
    ),
}


def go(query: JSONPathQuery, data: object) -> None:
    list(query.findall(data))


NUMBER = 1
REPEAT = 5

print(f"{'Benchmark':<35} | {'Min (s)':<10} | {'Mean (s)':<10}")
print("-" * 62)

for fixture in FIXTURES:
    for q_name, segments in QUERIES.items():
        bench_name = f"{fixture.name}:{q_name}"

        times = timeit.repeat(
            stmt=lambda segments=segments, fixture=fixture: go(segments, fixture.data),
            repeat=REPEAT,
            number=NUMBER,
        )

        per_run_times = [t / NUMBER for t in times]
        min_time = min(per_run_times)
        mean_time = sum(per_run_times) / len(per_run_times)

        print(f"{bench_name:<35} | {min_time:<10.4f} | {mean_time:<10.4f}")
