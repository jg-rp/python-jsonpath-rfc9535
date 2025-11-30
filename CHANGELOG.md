# Python JSONPath RFC 9535 Change Log

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
