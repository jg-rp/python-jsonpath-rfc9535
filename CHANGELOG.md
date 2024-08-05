# Python JSONPath RFC 9535 Change Log

## Version 0.1.3 (unreleased)

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
