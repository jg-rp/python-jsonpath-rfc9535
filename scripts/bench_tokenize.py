import json

import pyperf  # type: ignore

from jsonpath_rfc9535._lexer import tokenize

with open("tests/cts/cts.json") as fd:
    QUERIES = [
        t["selector"] for t in json.load(fd)["tests"] if not t.get("invalid_selector")
    ]


def tokenize_() -> None:
    for query in QUERIES:
        tokenize(query)


runner = pyperf.Runner()
runner.bench_func("tokenize", tokenize_)  # type: ignore
