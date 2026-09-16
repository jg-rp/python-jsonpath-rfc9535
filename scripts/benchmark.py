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

COMPILE_AND_FIND_SETUP = "import jsonpath_rfc9535 as jsonpath"

COMPILE_AND_FIND_STMT = """\
for source, data in QUERIES:
    jsonpath.find(source, data)"""

COMPILE_AND_FIND_VALUES_STMT = """\
for source, data in QUERIES:
    list(jsonpath.findall(source, data))"""

JUST_COMPILE_SETUP = "import jsonpath_rfc9535 as jsonpath"

JUST_COMPILE_STMT = """\
for source, _ in QUERIES:
    jsonpath.parse(source)"""

JUST_FIND_SETUP = """\
import jsonpath_rfc9535 as jsonpath
compiled_queries = [(jsonpath.parse(q), d) for q, d in QUERIES]
"""

JUST_FIND_STMT = """\
for query, data in compiled_queries:
    query.find(data)"""

JUST_FIND_VALUES_STMT = """\
for query, data in compiled_queries:
    list(query.findall(data))"""


def benchmark(number: int = 100, best_of: int = 3) -> None:
    print(f"repeating {len(QUERIES)} queries {number} times, best of {best_of} rounds")

    results = timeit.repeat(
        COMPILE_AND_FIND_STMT,
        setup=COMPILE_AND_FIND_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("compile and find".ljust(30), f"\033[92m{min(results):.3f}\033[0m")

    results = timeit.repeat(
        COMPILE_AND_FIND_VALUES_STMT,
        setup=COMPILE_AND_FIND_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("compile and find (values)".ljust(30), f"{min(results):.3f}")

    results = timeit.repeat(
        JUST_COMPILE_STMT,
        setup=JUST_COMPILE_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("just compile".ljust(30), f"{min(results):.3f}")

    results = timeit.repeat(
        JUST_FIND_STMT,
        setup=JUST_FIND_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("just find".ljust(30), f"\033[92m{min(results):.3f}\033[0m")

    results = timeit.repeat(
        JUST_FIND_VALUES_STMT,
        setup=JUST_FIND_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("just find (values)".ljust(30), f"{min(results):.3f}")


if __name__ == "__main__":
    benchmark()
