import json
import timeit
from typing import NamedTuple


class CTSCase(NamedTuple):
    query: str
    data: object


def valid_queries() -> list[CTSCase]:
    with open("tests/cts/cts.json") as fd:
        data = json.load(fd)

    return [
        (CTSCase(t["selector"], t["document"]))
        for t in data["tests"]
        if not t.get("invalid_selector", False)
    ]


QUERIES = valid_queries()

benchmarks: dict[str, tuple[str, str]] = {
    "parse and evaluate (nodes)": (
        "import jsonpath_rfc9535 as jsonpath",
        "for source, data in QUERIES:\n    jsonpath.find(source, data)",
    ),
    "parse and evaluate (values)": (
        "import jsonpath_rfc9535 as jsonpath",
        "for source, data in QUERIES:\n    jsonpath.findall(source, data)",
    ),
    "just parse": (
        "import jsonpath_rfc9535 as jsonpath",
        "for source, _ in QUERIES:\n    jsonpath.parse(source)",
    ),
    "just evaluate (nodes)": (
        "import jsonpath_rfc9535 as jsonpath\ncompiled_queries = [(jsonpath.parse(q), d) for q, d in QUERIES]",
        "for query, data in compiled_queries:\n    query.find(data)",
    ),
    "just evaluate (values)": (
        "import jsonpath_rfc9535 as jsonpath\ncompiled_queries = [(jsonpath.parse(q), d) for q, d in QUERIES]",
        "for query, data in compiled_queries:\n    query.findall(data)",
    ),
}

NUMBER = 100
REPEAT = 3

title = f"Benchmark {len(QUERIES) * NUMBER:,} queries"
print(f"{title:<35} | {'Min (s)':<10} | {'Mean (s)':<10}")
print("-" * 62)

for bench_name, (setup, stmt) in benchmarks.items():
    times = timeit.repeat(
        stmt=stmt,
        setup=setup,
        globals={"QUERIES": QUERIES},
        repeat=REPEAT,
        number=NUMBER,
    )

    min_time = min(times)
    mean_time = sum(times) / len(times)

    print(f"{bench_name:<35} | {min_time:<10.4f} | {mean_time:<10.4f}")
