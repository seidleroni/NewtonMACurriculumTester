"""Answer normalization + grading: equivalent forms grade correct, near-misses don't."""

from fractions import Fraction

from hypothesis import given
from hypothesis import strategies as st

from mathkids.answers import FractionAnswer, IntegerAnswer


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
