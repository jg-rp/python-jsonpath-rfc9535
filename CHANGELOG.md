# Python JSONPath RFC 9535 Change Log

## Version 2.0.2 (unreleased)

**Fixes**

- Restored support for traversing `dict` and `list` subclasses. See [#32](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/32).

## Version 2.0.1

**Fixes**

- Fixed trailing comma detection in bracketed segments. Previously we failed to consume whitespace after a comma and before checking for `]`. See [#26](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/26).

- Fixed comparison operators `<`, `>`, `<=` and `>=` when comparing `true` and/or `false` with `1` and `0`. Previously we were leaking Python behavior. See [#27](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/27).

- Fixed `\u` escaped sequence decoding. Previously we would not recognize lower case `e` and `f` hex digits due to a typo in a regular expression. See [#24](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/24).

- Fixed `\u` escape sequence rejection of code points less than or equal to 0x1F. The spec requires us to reject literals of 0x1F or lower, not escape sequences. See [#24](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/24).

- Fixed the shorthand name selector to accept the full range of allow Unicode code points and reject names containing `-`. See [#25](https://github.com/jg-rp/python-jsonpath-rfc9535/issues/25).

## Version 2.0.0

This release includes performance improvements and some breaking API changes. JSONPath syntax and semantics are unchanged.

- Dropped support for Python 3.8, 3.9, 3.10 and 3.11.
- Added a configurable regex cache to the standard `match` and `search` functions.
- Added detailed error messages to JSONPath exceptions.
- Added support for multiple JSONPath evaluation strategies. Initially there's the standard strategy that includes location information for every node, and the faster, more memory efficient "basic" strategy that does not keep track of node location.
- Removed non-deterministic features for validating the CTS.

**API changes**

- Changed `JSONPathEnvironment` class variables `parser_class`, `max_index`, `min_index` and `max_recursion_depth` to be instance variables. The `JSONPathEnvironment` initializer now accepts these as arguments.
- Changed `ExpressionType` (for defining function extensions) from an enum to a type alias and distinct constants `LOGICAL_TYPE`, `NODES_TYPE` and `VALUE_TYPE`.
- Added `jsonpath_rfc9535.parse()` and `JSONPathEnvironment.parse()` as aliases for `jsonpath_rfc9535.compile()` and `JSONPathEnvironment.compile()`.
- Added `jsonpath_rfc9535.search()`, `JSONPathEnvironment.search()` and `JSONPathQuery.search()` as aliases for `find_one()`.
- Added `jsonpath_rfc9535.findall()`, `JSONPathEnvironment.findall()` and `JSONPathQuery.findall()`, which is like `find()` but returns a list of JSON-like values not `JSONPathNode` instances.
- Added `JSONPathEnvironment.max_expression_depth` to guard against maliciously crafted queries hitting Python's recursion limit during parsing. Now a `JSONPathRecursionError` is raised if `max_expression_depth` is reached.
- `JSONPathNode.parent` is now a method, not a property. Parent `JSONPathNode` instances are instantiated lazily from an internal "tuple node".
- Removed `JSONPathNode.root`. It was meant for internal use only.
- Removed `JSONPathNode.new_child()`. It was meant for internal use only.
- Removed `JSONPathNodeList.empty()`. It's a list subclass, use `if not nodes` or `if nodes`.
- Removed `JSONPathLexerError`.
- Renamed `JSONPathEnvironment.function_extensions` to `JSONPathEnvironment.functions`.
- Removed `JSONPathEnvironment.validate_function_extension_signature()` and `JSONPathEnvironment.check_well_typedness()`. These now live on the parser.

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
