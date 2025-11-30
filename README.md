<h1 align="center">RFC 9535 JSONPath: Query Expressions for JSON in Python</h1>

<p align="center">
We follow <a href="https://datatracker.ietf.org/doc/html/rfc9535">RFC 9535</a> strictly and test against the <a href="https://github.com/jsonpath-standard/jsonpath-compliance-test-suite">JSONPath Compliance Test Suite</a>.
</p>

<p align="center">
  <a href="https://github.com/jg-rp/python-jsonpath-rfc9535/blob/main/LICENSE.txt">
    <img src="https://img.shields.io/pypi/l/jsonpath-rfc9535.svg?style=flat-square" alt="License">
  </a>
  <a href="https://github.com/jg-rp/python-jsonpath-rfc9535/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/jg-rp/python-jsonpath-rfc9535/tests.yaml?branch=main&label=tests&style=flat-square" alt="Tests">
  </a>
  <br>
  <a href="https://pypi.org/project/jsonpath-rfc9535">
    <img src="https://img.shields.io/pypi/v/jsonpath-rfc9535.svg?style=flat-square" alt="PyPi - Version">
  </a>
  <a href="https://pypi.org/project/jsonpath-rfc9535">
    <img src="https://img.shields.io/pypi/pyversions/jsonpath-rfc9535.svg?style=flat-square" alt="Python versions">
  </a>
</p>

---

**Table of Contents**

- [Install](#install)
- [Example](#example)
- [Links](#links)
- [Related projects](#related-projects)
- [API](#api)
- [License](#license)

## Install

Install Python JSONPath RFC 9535 using [pip](https://pip.pypa.io/en/stable/getting-started/):

```
pip install jsonpath-rfc9535
```

Or [Pipenv](https://pipenv.pypa.io/en/latest/):

```
pipenv install -u jsonpath-rfc9535
```

## Example

```python
import jsonpath_rfc9535 as jsonpath

data = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "Sally", "score": 84, "admin": False},
        {"name": "John", "score": 86, "admin": True},
        {"name": "Jane", "score": 55},
    ],
    "moderator": "John",
}

for node in jsonpath.find("$.users[?@.score > 85]", data):
    print(node.value)

# {'name': 'Sue', 'score': 100}
# {'name': 'John', 'score': 86, 'admin': True}
```

Or, reading JSON data from a file:

```python
import json
import jsonpath_rfc9535 as jsonpath

with open("/path/to/some.json", encoding="utf-8") as fd:
    data = json.load(fd)

nodes = jsonpath.find("$.some.query", data)
values = nodes.values()
# ...
```

You could read data from a YAML formatted file too. If you have [PyYaml](https://pyyaml.org/wiki/PyYAML) installed:

```python
import jsonpath_rfc9535 as jsonpath
import yaml

with open("some.yaml") as fd:
    data = yaml.safe_load(fd)

products = jsonpath.find("$..products.*", data).values()
# ...
```

## Links

- Change log: https://github.com/jg-rp/python-jsonpath-rfc9535/blob/main/CHANGELOG.md
- PyPi: https://pypi.org/project/jsonpath-rfc9535
- Source code: https://github.com/jg-rp/python-jsonpath-rfc9535
- Issue tracker: https://github.com/jg-rp/python-jsonpath-rfc9535/issues

## Related projects

- [Python JSONPath](https://github.com/jg-rp/python-jsonpath) - Another Python package implementing JSONPath, but with additional features and customization options.
- [JSON P3](https://github.com/jg-rp/json-p3) - RFC 9535 implemented in TypeScript.

## API

### find

`find(query: str, value: JSONValue) -> JSONPathNodeList`

Apply JSONPath expression _query_ to _value_. _value_ should arbitrary, possible nested, Python dictionaries, lists, strings, integers, floats, Booleans or `None`, as you would get from [`json.load()`](https://docs.python.org/3/library/json.html#json.load).

A list of `JSONPathNode` instances is returned, one node for each value matched by _query_. The returned list will be empty if there were no matches.

Each `JSONPathNode` has properties:

- `value` - The JSON-like value associated with the node.
- `location` - A tuple of property names and array/list indexes that were required to reach the node's value in the target JSON document.
- `parent` (_New in version 0.2.0_) - The node's parent node, or `None` if the current node is the root.

```python
import jsonpath_rfc9535 as jsonpath

data = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "John", "score": 86, "admin": True},
        {"name": "Sally", "score": 84, "admin": False},
        {"name": "Jane", "score": 55},
    ],
    "moderator": "John",
}

nodes = jsonpath.find("$.users[?@.score > 85]", data)

for node in nodes:
    print(f"{node.value} at '{node.path()}'")

# {'name': 'Sue', 'score': 100} at '$['users'][0]'
# {'name': 'John', 'score': 86, 'admin': True} at '$['users'][1]'
```

`JSONPathNode.path()` returns the normalized path to the node in the target JSON document.

`JSONPathNodeList` is a subclass of `list` with some helper methods.

- `values()` returns a list of values, one for each node.
- `items()` returns a list of `(normalized path, value)` tuples.

**_New in version 0.2.0_**

Assigning to `JSONPathNode.value` will update the node's value **and mutate source data**. Beware,updating data after evaluating a query can invalidate existing child node paths.

```python
# ... continued from above

node = jsonpath.find_one("$.users[@.name == 'John'].score")
if node:
    node.value = 999

print(data["users"][1])  # {'name': 'John', 'score': 999, 'admin': True}
```

### find_one

`find_one(query: str, value: JSONValue) -> Optional[JSONPathNode]`

`find_one()` accepts the same arguments as [`find()`](#findquery-value), but returns the first available `JSONPathNode`, or `None` if there were no matches.

`find_one()` is equivalent to:

```python
def find_one(query, value):
    try:
        return next(iter(jsonpath.finditer(query, value)))
    except StopIteration:
        return None
```

### finditer

`finditer(query: str, value: JSONValue) -> Iterable[JSONPathNode]`

`finditer()` accepts the same arguments as [`find()`](#findquery-value), but returns an iterator over `JSONPathNode` instances rather than a list. This could be useful if you're expecting a large number of results that you don't want to load into memory all at once.

### compile

`compile(query: str) -> JSONPathQuery`

`find(query, value)` is a convenience function for `JSONPathEnvironment().compile(query).apply(value)`. Use `compile(query)` to obtain a `JSONPathQuery` instance which can be applied to difference JSON-like values repeatedly.

```python
import jsonpath_rfc9535 as jsonpath

value = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "John", "score": 86, "admin": True},
        {"name": "Sally", "score": 84, "admin": False},
        {"name": "Jane", "score": 55},
    ],
    "moderator": "John",
}

query = jsonpath.compile("$.users[?@.score > 85]")

for node in query.apply(value):
    print(f"{node.value} at '{node.path()}'")

# {'name': 'Sue', 'score': 100} at '$['users'][0]'
# {'name': 'John', 'score': 86, 'admin': True} at '$['users'][1]'
```

A `JSONPathQuery` has a `finditer(value)` method too, and `find(value)` is an alias for `apply(value)`.

## License

`python-jsonpath-rfc9535` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
