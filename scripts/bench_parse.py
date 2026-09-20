import json

import pyperf  # type: ignore

from jsonpath_rfc9535 import parse

with open("tests/cts/cts.json") as fd:
    QUERIES = [
        t["selector"] for t in json.load(fd)["tests"] if not t.get("invalid_selector")
    ]


def parse_() -> None:
    for query in QUERIES:
        parse(query)


runner = pyperf.Runner()
runner.bench_func("parse", parse_)  # type: ignore
