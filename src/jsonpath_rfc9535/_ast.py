from typing import Literal

from ._tokens import Token

__all__ = (
    "ABSOLUTE_QUERY_EXPR",
    "AND_EXPR",
    "BOOL_EXPR",
    "CHILD_SEGMENT",
    "DESCENDANT_SEGMENT",
    "EQ_EXPR",
    "FILTER_SELECTOR",
    "FLOAT_EXPR",
    "FUNCTION_EXPR",
    "GE_EXPR",
    "GT_EXPR",
    "INDEX_SELECTOR",
    "INT_EXPR",
    "LE_EXPR",
    "LT_EXPR",
    "NAME_SELECTOR",
    "NE_EXPR",
    "NOT_EXPR",
    "NULL_EXPR",
    "OR_EXPR",
    "RELATIVE_QUERY_EXPR",
    "SLICE_SELECTOR",
    "STRING_EXPR",
    "WILDCARD_SELECTOR",
    "AbsoluteQueryExpression",
    "AndExpression",
    "BoolExpression",
    "ChildSegment",
    "DescendantSegment",
    "EqExpression",
    "Expression",
    "FilterSelector",
    "FloatExpression",
    "FunctionExpression",
    "GeExpression",
    "GtExpression",
    "IndexSelector",
    "IntExpression",
    "LeExpression",
    "LtExpression",
    "NameSelector",
    "NeExpression",
    "NotExpression",
    "NullExpression",
    "OrExpression",
    "RelativeQueryExpression",
    "Segment",
    "Selector",
    "SliceSelector",
    "StringExpression",
    "WildcardSelector",
)

CHILD_SEGMENT: Literal[0] = 0
DESCENDANT_SEGMENT: Literal[1] = 1

type Segment = ChildSegment | DescendantSegment

type ChildSegment = tuple[Literal[0], Token, tuple[Selector, ...]]
type DescendantSegment = tuple[Literal[1], Token, tuple[Selector, ...]]


FILTER_SELECTOR: Literal[2] = 2
INDEX_SELECTOR: Literal[3] = 3
NAME_SELECTOR: Literal[4] = 4
SLICE_SELECTOR: Literal[5] = 5
WILDCARD_SELECTOR: Literal[6] = 6

type Selector = (
    NameSelector | IndexSelector | SliceSelector | WildcardSelector | FilterSelector
)

type FilterSelector = tuple[Literal[2], Token, Expression]
type IndexSelector = tuple[Literal[3], Token, int]
type NameSelector = tuple[Literal[4], Token, str]
type SliceSelector = tuple[Literal[5], Token, slice]
type WildcardSelector = tuple[Literal[6], Token]


ABSOLUTE_QUERY_EXPR: Literal[7] = 7
AND_EXPR: Literal[8] = 8
BOOL_EXPR: Literal[9] = 9
EQ_EXPR: Literal[10] = 10
FLOAT_EXPR: Literal[11] = 11
FUNCTION_EXPR: Literal[12] = 12
GE_EXPR: Literal[13] = 13
GT_EXPR: Literal[14] = 14
INT_EXPR: Literal[15] = 15
LE_EXPR: Literal[16] = 16
LT_EXPR: Literal[17] = 17
NE_EXPR: Literal[18] = 18
NOT_EXPR: Literal[19] = 19
NULL_EXPR: Literal[20] = 20
OR_EXPR: Literal[21] = 21
RELATIVE_QUERY_EXPR: Literal[22] = 22
STRING_EXPR: Literal[23] = 23

type Expression = (
    AbsoluteQueryExpression
    | AndExpression
    | BoolExpression
    | EqExpression
    | FloatExpression
    | FunctionExpression
    | GeExpression
    | GtExpression
    | IntExpression
    | LeExpression
    | LtExpression
    | NeExpression
    | NotExpression
    | NullExpression
    | OrExpression
    | RelativeQueryExpression
    | StringExpression
)

type AbsoluteQueryExpression = tuple[Literal[7], Token, tuple[Segment, ...]]
type AndExpression = tuple[Literal[8], Token, Expression, Expression]
type BoolExpression = tuple[Literal[9], Token, bool]
type EqExpression = tuple[Literal[10], Token, Expression, Expression]
type FloatExpression = tuple[Literal[11], Token, float]
type FunctionExpression = tuple[Literal[12], Token, str, tuple[Expression, ...]]
type GeExpression = tuple[Literal[13], Token, Expression, Expression]
type GtExpression = tuple[Literal[14], Token, Expression, Expression]
type IntExpression = tuple[Literal[15], Token, int]
type LeExpression = tuple[Literal[16], Token, Expression, Expression]
type LtExpression = tuple[Literal[17], Token, Expression, Expression]
type NeExpression = tuple[Literal[18], Token, Expression, Expression]
type NotExpression = tuple[Literal[19], Token, Expression]
type NullExpression = tuple[Literal[20], Token]
type OrExpression = tuple[Literal[21], Token, Expression, Expression]
type RelativeQueryExpression = tuple[Literal[22], Token, tuple[Segment, ...]]
type StringExpression = tuple[Literal[23], Token, str]
