# Python JSONPath RFC 9535 Change Log

## Version 2.0.0 (unreleased)

- Dropped support for Python 3.8, 3.9, 3.10 and 3.11.
- Added a configurable regex cache to the standard `match` and `search` functions.
- Added detailed error messages to JSONPath exceptions.
- Improved performance.
- Removed non-deterministic features for validating the CTS.

**API changes**

- Added `jsonpath_rfc9535.parse()` and `JSONPathEnvironment.parse()` as aliases for `jsonpath_rfc9535.compile()` and `JSONPathEnvironment.compile()`.
- Added `jsonpath_rfc9535.search()`, `JSONPathEnvironment.search()` and `JSONPathQuery.search()` as aliases for `find_one()`.
- Added `jsonpath_rfc9535.findall()`, `JSONPathEnvironment.findall()` and `JSONPathQuery.findall()`, which is like `find()` but returns a list of values not `JSONPathNode`.

- `JSONPathNode.parent` is now a method, not a property. Parent JSONPathNode instances are instantiated lazily from an internal "tuple node".
- Removed `JSONPathNode.root`. It was meant for internal use only.
- Removed `JSONPathNode.new_child()`. It was meant for internal use only.
- Removed `JSONPathNodeList.empty()`. It's a list subclass, use `not node_list`.
- Removed `JSONPathLexerError` and `JSONPathIndexError`.
- Renamed `JSONPathEnvironment.function_extensions` to `JSONPathEnvironment.functions`.
- Removed `JSONPathEnvironment.validate_function_extension_signature()` and `JSONPathEnvironment.check_well_typedness()`. These now live on the parser.
- Changed `JSONPathEnvironment` class variables `max_index`, `min_index` and `max_recursion_depth` to be instance variables.
- Removed class variable `JSONPathEnvironment.parser_class`. The `JSONPathEnvironment` initializer now accepts a `parser` argument.
- Changed `ExpressionType` (for defining function extensions) from an enum to distinct constants `LOGICAL_TYPE`, `NODES_TYPE` and `VALUE_TYPE`.

## Version 1.0.0

Bump to stable status.

## Version 0.2.0

**Features**

- Added `JSONPathNode.parent`, a reference the the node's parent node. See [#21](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/21).
- Changed `JSONPathNode.value` to be a `@property` and `setter`. When assigning to `JSONPathNode.value`, source data is updated too. See [#21](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/21).

## Version 0.1.6

- Added py.typed.

## Version 0.1.5

**Fixes**

- Fixed "unbalanced parentheses" errors for queries that do have balanced brackets. See [#13](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/13).

## Version 0.1.4

**Fixes**

- Fixed normalized paths produced by `JSONPathNode.path()`. Previously we were not handling some escape sequences correctly in name selectors.
- Fixed serialization of `JSONPathQuery` instances. `JSONPathQuery.__str__()` now serialized name selectors and string literals to the canonical format, similar to normalized paths. We're also now minimizing the use of parentheses when serializing logical expressions.
- Fixed parsing of filter queries with multiple bracketed segments.

## Version 0.1.3

**Fixes**

- Fixed decoding of escape sequences in quoted name selectors and string literals. We now raise a `JSONPathSyntaxError` for invalid code points.
- Fixed parsing of number literals with an exponent. We now allow 'e' to be upper case.
- Fixed handling of trailing commas in bracketed segments. We now raise a `JSONPathSyntaxError` in such cases.
- Fixed handling of invalid number literals. We now raise a syntax error for invalid leading zeros and extra negative signs.

## Version 0.1.2

**Fixes**

- Handle end of query when lexing inside a filter expression.
- Check patterns passed to `search` and `match` are valid I-Regexp patterns. Both of these functions now return _LogicalFalse_ if the pattern is not valid according to RFC 9485.

## Version 0.1.1

Fix PyPi classifiers and README.

## Version 0.1.0

Initial release.
