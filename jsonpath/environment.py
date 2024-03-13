"""JSONPath configuration.

A JSONPathEnvironment is where you'd register functions extensions and
control recursion limits, for example.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Type
from typing import Union

from . import function_extensions
from .exceptions import JSONPathNameError
from .exceptions import JSONPathTypeError
from .expressions import ComparisonExpression
from .expressions import FunctionExtension
from .expressions import JSONPathLiteral
from .expressions import LogicalExpression
from .expressions import Path
from .function_extensions import ExpressionType
from .function_extensions import FilterFunction
from .lex import Lexer
from .parse import Parser
from .path import JSONPath
from .tokens import TokenStream

if TYPE_CHECKING:
    from .expressions import Expression
    from .node import JSONPathNode
    from .tokens import Token


class JSONPathEnvironment:
    """JSONPath configuration."""

    lexer_class: Type[Lexer] = Lexer
    parser_class: Type[Parser] = Parser

    max_int_index = (2**53) - 1
    min_int_index = -(2**53) + 1

    def __init__(self) -> None:
        self.lexer: Lexer = self.lexer_class(env=self)
        """The lexer bound to this environment."""

        self.parser: Parser = self.parser_class(env=self)
        """The parser bound to this environment."""

        self.function_extensions: Dict[str, FilterFunction] = {}
        """A list of function extensions available to filters."""

        self.setup_function_extensions()

    def compile(self, path: str) -> JSONPath:  # noqa: A003
        """Prepare a path string ready for repeated matching against different data.

        Arguments:
            path: A JSONPath query string.

        Returns:
            A `JSONPath` ready to match against some data.

        Raises:
            JSONPathSyntaxError: If _path_ is invalid.
            JSONPathTypeError: If filter functions are given arguments of an
                unacceptable type.
        """
        tokens = self.lexer.tokenize(path)
        stream = TokenStream(tokens)
        return JSONPath(env=self, segments=self.parser.parse(stream))

    def query(
        self, path: str, data: Union[Sequence[Any], Mapping[str, Any]]
    ) -> Iterable[JSONPathNode]:
        """Apply the JSONPath query _path_ to JSON-like _data_.

        Arguments:
            path: A JSONPath query string.
            data: A Python object implementing the `Sequence` or `Mapping` interfaces.

        Returns:
            An iterator yielding `JSONPathMatch` objects for each match.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        return self.compile(path).query(data)

    def setup_function_extensions(self) -> None:
        """Initialize function extensions."""
        self.function_extensions["length"] = function_extensions.Length()
        self.function_extensions["count"] = function_extensions.Count()
        self.function_extensions["match"] = function_extensions.Match()
        self.function_extensions["search"] = function_extensions.Search()
        self.function_extensions["value"] = function_extensions.Value()

    def validate_function_extension_signature(
        self, token: Token, args: List[Any]
    ) -> List[Any]:
        """Compile-time validation of function extension arguments.

        RFC 9535 requires us to reject paths that use filter functions with
        too many or too few arguments.
        """
        try:
            func = self.function_extensions[token.value]
        except KeyError as err:
            raise JSONPathNameError(
                f"function {token.value!r} is not defined", token=token
            ) from err

        self.check_well_typedness(token, func, args)
        return args

    def check_well_typedness(
        self,
        token: Token,
        func: FilterFunction,
        args: List[Expression],
    ) -> None:
        """Check the well-typedness of a function's arguments at compile-time."""
        # Correct number of arguments?
        if len(args) != len(func.arg_types):
            raise JSONPathTypeError(
                f"{token.value!r}() requires {len(func.arg_types)} arguments",
                token=token,
            )

        # Argument types
        for idx, typ in enumerate(func.arg_types):
            arg = args[idx]
            if typ == ExpressionType.VALUE:
                if not (
                    isinstance(arg, JSONPathLiteral)
                    or (isinstance(arg, Path) and arg.path.singular_query())
                    or (self._function_return_type(arg) == ExpressionType.VALUE)
                ):
                    raise JSONPathTypeError(
                        f"{token.value}() argument {idx} must be of ValueType",
                        token=token,
                    )
            elif typ == ExpressionType.LOGICAL:
                if not isinstance(
                    arg, (Path, (LogicalExpression, ComparisonExpression))
                ):
                    raise JSONPathTypeError(
                        f"{token.value}() argument {idx} must be of LogicalType",
                        token=token,
                    )
            elif typ == ExpressionType.NODES and not (
                isinstance(arg, Path)
                or self._function_return_type(arg) == ExpressionType.NODES
            ):
                raise JSONPathTypeError(
                    f"{token.value}() argument {idx} must be of NodesType",
                    token=token,
                )

    def _function_return_type(self, expr: Expression) -> Optional[ExpressionType]:
        """Return a filter function's return type.

        Returns `None` if _expr_ is not a function expression.
        """
        if not isinstance(expr, FunctionExtension):
            return None
        func = self.function_extensions.get(expr.name)
        if isinstance(func, FilterFunction):
            return func.return_type
        return None
