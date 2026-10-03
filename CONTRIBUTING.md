# Contributing to Python JSONPath RFC 9535

Hi. Your contributions and questions are always welcome. Feel free to ask questions, report bugs or request features on the [issue tracker](https://github.com/jg-rp/python-jsonpath-rfc9535/issues) or on [Github Discussions](https://github.com/jg-rp/python-jsonpath-rfc9535/discussions). Pull requests are welcome too.

**Table of contents**

- [Development](#development)
- [Documentation](#documentation)

## Development

The [JSONPath Compliance Test Suite](https://github.com/jsonpath-standard/jsonpath-compliance-test-suite) is included in this repository as Git [submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules). Clone this project and initialize the submodule with something like:

```shell
$ git clone git@github.com:jg-rp/python-jsonpath-rfc9535.git
$ cd python-jsonpath
$ git submodule update --init
```

We use [hatch](https://hatch.pypa.io/latest/) to manage project dependencies and development environments.

Run tests with the _test_ script.

```shell
$ hatch run test
```

Lint with [ruff](https://beta.ruff.rs/docs/).

```shell
$ hatch run lint
```

Typecheck with [Mypy](https://mypy.readthedocs.io/en/stable/).

```shell
$ hatch run typing
```

Check coverage with pytest-cov.

```shell
$ hatch run cov
```

Then open `htmlcov/index.html` in your browser.

## Documentation

Documentation lives in the `docs` directory and is built with Sphinx. Build it to the `site` directory with:

```shell
$ hatch run docs-build
```
