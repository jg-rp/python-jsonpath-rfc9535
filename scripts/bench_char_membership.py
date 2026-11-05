import statistics
import timeit
from collections.abc import Container

chars = r"()*+-...?[\\]^nrt{|}"

containers: dict[str, Container[str]] = {
    "string": chars,
    "tuple": tuple(chars),
    "set": set(chars),
    "frozenset": frozenset(chars),
}

test_chars = {
    "hit": "n",
    "miss": "z",
}

NUMBER = 1_000_000
REPEAT = 7

print(f"Iterations per run: {NUMBER:,}")
print(f"Repeats: {REPEAT}")
print()

for test_name, ch in test_chars.items():
    print(f"--- {test_name.upper()} ({ch!r}) ---")

    results: list[tuple[str, float, float]] = []

    for container_name, container in containers.items():
        stmt = "ch in container"
        setup = "pass"

        times = timeit.repeat(
            stmt=stmt,
            setup=setup,
            globals={"ch": ch, "container": container},
            number=NUMBER,
            repeat=REPEAT,
        )

        best = min(times)
        median = statistics.median(times)

        results.append((container_name, best, median))

    # Sort by best execution time
    results.sort(key=lambda x: x[1])

    fastest = results[0][1]

    for name, best, median in results:
        print(
            f"{name:10s}: "
            f"best={best:.6f}s  "
            f"median={median:.6f}s  "
            f"relative={best / fastest:.2f}x"
        )

    print()
