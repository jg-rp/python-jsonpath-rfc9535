import json

import pyperf  # type: ignore

from jsonpath_rfc9535 import parse

with open("tests/cts/cts.json") as fd:
    QUERIES = [
        (t["selector"], t["document"])
        for t in json.load(fd)["tests"]
        if not t.get("invalid_selector")
    ]

COMPILED = [(parse(q), d) for q, d in QUERIES]


def resolve() -> None:
    for q, data in COMPILED:
        q.find(data)


runner = pyperf.Runner()
runner.bench_func("resolve", resolve)  # type: ignore
