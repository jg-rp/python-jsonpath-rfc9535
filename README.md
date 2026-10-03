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
- [Links](#links)
- [Example](#example)
- [Related projects](#related-projects)
- [License](#license)

## Install

Install Python JSONPath RFC 9535 using [pip](https://pip.pypa.io/en/stable/getting-started/):

```
python -m pip install jsonpath-rfc9535
```

Or [uv](https://docs.astral.sh/uv/):

```
uv add jsonpath-rfc9535
```

Or [Pipenv](https://pipenv.pypa.io/en/latest/):

```
pipenv install -u jsonpath-rfc9535
```

## Links

- Documentation: https://jg-rp.github.io/python-jsonpath-rfc9535/
- Change log: https://github.com/jg-rp/python-jsonpath-rfc9535/blob/main/CHANGELOG.md
- PyPi: https://pypi.org/project/jsonpath-rfc9535
- Source code: https://github.com/jg-rp/python-jsonpath-rfc9535
- Issue tracker: https://github.com/jg-rp/python-jsonpath-rfc9535/issues

## Example

```python
import jsonpath_rfc9535 as jsonpath

expr = "$.users[?@.status == 'pending'].name"

data: dict[str, object] = {
    "users": [
        {"id": "usr_101", "name": "Alice", "status": "pending"},
        {"id": "usr_102", "name": "Bob", "status": "active"},
        {"id": "usr_103", "name": "Charlie", "status": "pending"},
    ],
}

nodes = jsonpath.find(expr, data)

print(nodes.values())  # ['Alice', 'Charlie']
print(nodes.locations())  # [('users', 0, 'name'), ('users', 2, 'name')]
print(nodes.paths())  # ["$['users'][0]['name']", "$['users'][2]['name']"]
```

## Related projects

- [Python JSONPath](https://github.com/jg-rp/python-jsonpath) - Another Python package implementing JSONPath, but with additional features and customization options.
- [JSON P3](https://github.com/jg-rp/json-p3) - RFC 9535 implemented in TypeScript.

## License

`python-jsonpath-rfc9535` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
