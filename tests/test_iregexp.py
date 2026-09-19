"""I-Regexp checking tests.

Some of these test cases are derived from https:github.com/f3ath/iregexp.
Thanks go to @f3ath. The project's license is included here.

MIT License

Copyright (c) 2023 Alexey

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import dataclasses
import operator

import pytest
from iregexp_check import check


@dataclasses.dataclass
class Case:
    description: str
    pattern: str


VALID_TEST_CASES = [
    Case("dot", r"a.b"),
    Case("char_class_expr", r"[0-9]"),
    Case("branch", r"foo|bar"),
    Case("range_quantifier_exact", r"[ab]{3}"),
    Case("range_quantifier", r"[ab]{3,5}"),
    Case("range_quantifier_open_ended", r"[ab]{3,}"),
    Case("char_class_expr_negation", r"[^ab]"),
    Case("unicode_character_category_letter", r"\p{L}"),
    Case("unicode_character_category_letter_uppercase", r"\p{Lu}"),
    Case("unicode_character_category_letter_lowercase", r"\p{Ll}"),
    Case("unicode_character_category_letter_titlecase", r"\p{Lt}"),
    Case("unicode_character_category_letter_modifier", r"\p{Lm}"),
    Case("unicode_character_category_letter_other", r"\p{Lo}"),
    Case("unicode_character_category_mark_nonspcaing", r"\p{Mn}"),
    Case("unicode_character_category_mark_spacing_combining", r"\p{Mc}"),
    Case("unicode_character_category_mark_enclosing", r"\p{Me}"),
    Case("unicode_character_category_number_decimal_digit", r"\p{Nd}"),
    Case("unicode_character_category_number_letter", r"\p{Nl}"),
    Case("unicode_character_category_number_other", r"\p{No}"),
    Case("unicode_character_category_punctuation_connector", r"\p{Pc}"),
    Case("unicode_character_category_punctuation_dash", r"\p{Pd}"),
    Case("unicode_character_category_punctuation_open", r"\p{Ps}"),
    Case("unicode_character_category_punctuation_close", r"\p{Pe}"),
    Case("unicode_character_category_punctuation_initial_quote", r"\p{Pi}"),
    Case("unicode_character_category_punctuation_final_quote", r"\p{Pf}"),
    Case("unicode_character_category_punctuation_other", r"\p{Po}"),
    Case("unicode_character_category_symbol_math", r"\p{Sm}"),
    Case("unicode_character_category_symbol_currency", r"\p{Sc}"),
    Case("unicode_character_category_symbol_modifier", r"\p{Sk}"),
    Case("unicode_character_category_symbol_other", r"\p{So}"),
    Case("unicode_character_category_separator_space", r"\p{Zs}"),
    Case("unicode_character_category_separator_line", r"\p{Zl}"),
    Case("unicode_character_category_separator_paragraph", r"\p{Zp}"),
    Case("unicode_character_category_other_control", r"\p{Cc}"),
    Case("unicode_character_category_other_format", r"\p{Cf}"),
    Case("unicode_character_category_other_private_use", r"\p{Co}"),
    Case("unicode_character_category_other_not_assigned", r"\p{Cn}"),
    Case("unicode_character_category_inverted_letter", r"\P{L}"),
    Case("unicode_character_category_inverted_letter_uppercase", r"\P{Lu}"),
    Case("unicode_character_category_inverted_letter_lowercase", r"\P{Ll}"),
    Case("unicode_character_category_inverted_letter_titlecase", r"\P{Lt}"),
    Case("unicode_character_category_inverted_letter_modifier", r"\P{Lm}"),
    Case("unicode_character_category_inverted_letter_other", r"\P{Lo}"),
    Case("unicode_character_category_inverted_mark_nonspacing", r"\P{Mn}"),
    Case("unicode_character_category_inverted_mark_spacing_combining", r"\P{Mc}"),
    Case("unicode_character_category_inverted_mark_enclosing", r"\P{Me}"),
    Case("unicode_character_category_inverted_number_decimal_digit", r"\P{Nd}"),
    Case("unicode_character_category_inverted_number_letter", r"\P{Nl}"),
    Case("unicode_character_category_inverted_number_other", r"\P{No}"),
    Case("unicode_character_category_inverted_punctuation_connector", r"\P{Pc}"),
    Case("unicode_character_category_inverted_punctuation_dash", r"\P{Pd}"),
    Case("unicode_character_category_inverted_punctuation_open", r"\P{Ps}"),
    Case("unicode_character_category_inverted_punctuation_close", r"\P{Pe}"),
    Case("unicode_character_category_inverted_punctuation_initial_quote", r"\P{Pi}"),
    Case("unicode_character_category_inverted_punctuation_final_quote", r"\P{Pf}"),
    Case("unicode_character_category_inverted_punctuation_other", r"\P{Po}"),
    Case("unicode_character_category_inverted_symbol_math", r"\P{Sm}"),
    Case("unicode_character_category_inverted_symbol_currency", r"\P{Sc}"),
    Case("unicode_character_category_inverted_symbol_modifier", r"\P{Sk}"),
    Case("unicode_character_category_inverted_symbol_other", r"\P{So}"),
    Case("unicode_character_category_inverted_separator_space", r"\P{Zs}"),
    Case("unicode_character_category_inverted_separator_line", r"\P{Zl}"),
    Case("unicode_character_category_inverted_separator_paragraph", r"\P{Zp}"),
    Case("unicode_character_category_inverted_other_control", r"\P{Cc}"),
    Case("unicode_character_category_inverted_other_format", r"\P{Cf}"),
    Case("unicode_character_category_inverted_other_private_use", r"\P{Co}"),
    Case("unicode_character_category_inverted_other_not_assigned", r"\P{Cn}"),
]

INVALID_TEST_CASES = [
    Case("named_group", r"(?<group>[a-z]*)"),
    Case("multi_char_escape", r"\d"),
    Case("multi_char_escape_class_expr", r"[\S ]"),
    Case("non_greedy_repetition", r"[0-9]*?"),
    Case("back_reference", r"(\w)\1"),
    Case("lookahead", r"(?=.*[a-z])(?=.*[A-Z])(?=.*)[a-zA-Z]{8,}"),
    Case("lookbehind", r"(?<=[a-z]{4})\[a-z]{2}"),
    Case("non_capturing_group", r"(?:[a-z]+)"),
    Case("atomic_group", r"(?>[a-z]+)"),
    Case("conditional_group", r"(?(1)a|b)"),
    Case("comment", r"(?#comment)"),
    Case("flag", r"(?i)[a-z]+"),
]


@pytest.mark.parametrize(
    "case", VALID_TEST_CASES, ids=operator.attrgetter("description")
)
def test_valid_iregexp(case: Case) -> None:
    assert check(case.pattern)


@pytest.mark.parametrize(
    "case", INVALID_TEST_CASES, ids=operator.attrgetter("description")
)
def test_invalid_iregexp(case: Case) -> None:
    assert not check(case.pattern)
