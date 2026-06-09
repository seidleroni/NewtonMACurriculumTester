"""Answer normalization + grading: equivalent forms grade correct, near-misses don't."""

from fractions import Fraction

from hypothesis import given
from hypothesis import strategies as st

from mathkids.answers import (
    ANSWER_TYPES,
    ComparatorAnswer,
    DecimalAnswer,
    FractionAnswer,
    IntegerAnswer,
    MoneyAnswer,
    QuotientRemainderAnswer,
    SequenceAnswer,
    SetAnswer,
    TimeAnswer,
    WordAnswer,
)


def test_integer_accepts_equivalent_forms():
    a = IntegerAnswer(85)
    for raw in ["85", " 85 ", "85 apples", "+85", "85\n"]:
        assert a.grade(raw).correct, raw


def test_integer_accepts_thousands_separators():
    assert IntegerAnswer(1234).grade("1,234").correct
    assert IntegerAnswer(89991).grade("89,991").correct


def test_integer_rejects_wrong_and_garbage():
    a = IntegerAnswer(85)
    for raw in ["84", "850", "", "  ", "eighty-five", "-85"]:
        assert not a.grade(raw).correct, raw


def test_integer_canonical_round_trips():
    a = IntegerAnswer(42)
    assert a.grade(a.canonical()).correct


def test_fraction_accepts_reduced_and_unreduced():
    a = FractionAnswer(Fraction(1, 2))
    for raw in ["1/2", "2/4", "3/6", "4 / 8", " 50/100 "]:
        assert a.grade(raw).correct, raw


def test_fraction_accepts_mixed_and_improper():
    a = FractionAnswer(Fraction(11, 2))  # 5 1/2
    for raw in ["11/2", "5 1/2", "22/4", "5 2/4"]:
        assert a.grade(raw).correct, raw


def test_fraction_whole_number():
    a = FractionAnswer(Fraction(3, 1))
    for raw in ["3", "3/1", "6/2"]:
        assert a.grade(raw).correct, raw


def test_fraction_rejects_wrong():
    a = FractionAnswer(Fraction(2, 5))
    for raw in ["3/5", "2/3", "1/5", "", "1/0", "abc"]:
        assert not a.grade(raw).correct, raw


def test_fraction_display_is_mixed_for_improper():
    assert FractionAnswer(Fraction(11, 2)).display == "5 1/2"
    assert FractionAnswer(Fraction(3, 5)).display == "3/5"
    assert FractionAnswer(Fraction(4, 1)).display == "4"


@given(st.integers(min_value=-9999, max_value=9999))
def test_integer_property_roundtrip(n):
    a = IntegerAnswer(n)
    assert a.grade(str(n)).correct
    assert not a.grade(str(n + 1)).correct


@given(
    st.integers(min_value=1, max_value=50),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=2, max_value=6),
)
def test_fraction_property_unreduced(num, den, k):
    value = Fraction(num, den)
    a = FractionAnswer(value)
    assert a.grade(f"{num * k}/{den * k}").correct


def test_comparator():
    a = ComparatorAnswer(">")
    assert a.grade(">").correct
    assert a.grade("greater than").correct
    assert not a.grade("<").correct
    assert not a.grade("").correct
    assert ComparatorAnswer("=").grade("equal").correct


def test_decimal_equivalence():
    a = DecimalAnswer("0.7")
    assert a.grade("0.7").correct
    assert a.grade("0.70").correct
    assert a.grade(".7").correct
    assert not a.grade("0.07").correct
    assert not a.grade("abc").correct


def test_word_with_aliases():
    a = WordAnswer("fourths", aliases=("quarters", "fourth"))
    assert a.grade("Fourths").correct
    assert a.grade(" quarters ").correct
    assert a.grade("fourth.").correct
    assert not a.grade("thirds").correct


def test_sequence_ordered():
    a = SequenceAnswer((35, 40, 45))
    assert a.grade("35, 40, 45").correct
    assert a.grade("35 40 45").correct
    assert not a.grade("35, 45, 40").correct
    assert not a.grade("35, 40").correct


def test_set_unordered():
    a = SetAnswer(frozenset({1, 2, 3, 6}))
    assert a.grade("1, 2, 3, 6").correct
    assert a.grade("6 3 2 1").correct
    assert not a.grade("1, 2, 3").correct


def test_time():
    a = TimeAnswer(3, 45)
    assert a.grade("3:45").correct
    assert a.grade("3 : 45").correct
    assert not a.grade("3:40").correct
    assert not a.grade("nope").correct


def test_money():
    a = MoneyAnswer(104)
    assert a.grade("$1.04").correct
    assert a.grade("1.04").correct
    assert a.grade("104¢").correct
    assert a.grade("104 cents").correct
    assert not a.grade("$1.40").correct
    assert a.canonical() == "$1.04"


def test_money_whole_dollars():
    # A kid answering $3.00 naturally types "3", "$3", or "3 dollars".
    a = MoneyAnswer(300)
    assert a.grade("3").correct
    assert a.grade("$3").correct
    assert a.grade("3 dollars").correct
    assert a.grade("300").correct
    assert a.grade("300 cents").correct
    assert a.grade("3.00").correct
    assert not a.grade("30").correct
    # Explicit cent markers are never reinterpreted as dollars.
    assert not a.grade("3¢").correct
    assert not a.grade("3 cents").correct
    # Bare integers still mean cents when that matches.
    b = MoneyAnswer(85)
    assert b.grade("85").correct
    assert b.grade("85¢").correct
    assert not b.grade("$85").correct


def test_quotient_remainder():
    a = QuotientRemainderAnswer(434, 3)
    assert a.grade("434 R 3").correct
    assert a.grade("434 r 3").correct
    assert a.grade("434 remainder 3").correct
    assert not a.grade("434").correct
    assert not a.grade("433 R 3").correct
    # remainder 0 may be written as just the quotient
    b = QuotientRemainderAnswer(136, 0)
    assert b.grade("136").correct


def test_all_answer_types_canonical_round_trip():
    samples = [
        IntegerAnswer(42),
        FractionAnswer(Fraction(3, 4)),
        ComparatorAnswer("<"),
        DecimalAnswer("0.45"),
        WordAnswer("hexagon"),
        SequenceAnswer((2, 4, 6)),
        SetAnswer(frozenset({1, 5})),
        TimeAnswer(10, 5),
        MoneyAnswer(250),
        QuotientRemainderAnswer(7, 2),
    ]
    for ans in samples:
        assert ans.grade(ans.canonical()).correct, ans
        assert ans.answer_type in ANSWER_TYPES
