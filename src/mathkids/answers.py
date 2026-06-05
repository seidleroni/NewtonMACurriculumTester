"""Typed answers: normalization + deterministic grading.

Every answer knows how to (a) grade a raw text input from a kid after sensible
normalization, and (b) produce a canonical string form of itself (used by the
property tests to feed a known-correct answer back through grading).

Grading depends only on *value*, never on exact input formatting:
  - integers ignore commas, surrounding whitespace, and trailing units ("85 apples" -> 85)
  - fractions accept reduced/unreduced and mixed<->improper ("5 1/2" == "11/2" == "22/4")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class GradeResult:
    correct: bool
    expected_display: str
    given_display: str


class Answer:
    """Base class. Subclasses implement grade() and canonical()."""

    answer_type: str = "abstract"

    def grade(self, raw: str) -> GradeResult:  # pragma: no cover - abstract
        raise NotImplementedError

    def canonical(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    @property
    def display(self) -> str:
        return self.canonical()


_INT_RE = re.compile(r"-?\d[\d,]*")


def _parse_int(raw: str) -> int | None:
    if raw is None:
        return None
    m = _INT_RE.search(raw.strip())
    if not m:
        return None
    try:
        return int(m.group(0).replace(",", ""))
    except ValueError:
        return None


@dataclass(frozen=True)
class IntegerAnswer(Answer):
    value: int
    answer_type: str = "integer"

    def grade(self, raw: str) -> GradeResult:
        given = _parse_int(raw)
        return GradeResult(
            correct=given is not None and given == self.value,
            expected_display=str(self.value),
            given_display="" if given is None else str(given),
        )

    def canonical(self) -> str:
        return str(self.value)


# Matches "3", "13/4", "5 1/2" (mixed). Allows extra inner whitespace.
_MIXED_RE = re.compile(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$")
_FRAC_RE = re.compile(r"^(-?\d+)\s*/\s*(\d+)$")
_WHOLE_RE = re.compile(r"^(-?\d+)$")


def _parse_fraction(raw: str) -> Fraction | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    m = _MIXED_RE.match(s)
    if m:
        whole, num, den = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if den == 0:
            return None
        sign = -1 if whole < 0 else 1
        return Fraction(sign * (abs(whole) * den + num), den)
    m = _FRAC_RE.match(s)
    if m:
        num, den = int(m.group(1)), int(m.group(2))
        if den == 0:
            return None
        return Fraction(num, den)
    m = _WHOLE_RE.match(s)
    if m:
        return Fraction(int(m.group(1)), 1)
    return None


def _fraction_display(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class FractionAnswer(Answer):
    value: Fraction
    answer_type: str = "fraction"

    def grade(self, raw: str) -> GradeResult:
        given = _parse_fraction(raw)
        return GradeResult(
            correct=given is not None and given == self.value,
            expected_display=_fraction_display(self.value),
            given_display="" if given is None else _fraction_display(given),
        )

    def canonical(self) -> str:
        return _fraction_display(self.value)

    @property
    def display(self) -> str:
        # Friendly mixed-number form for display, e.g. 11/2 -> "5 1/2".
        v = self.value
        if v.denominator == 1 or abs(v.numerator) < v.denominator:
            return _fraction_display(v)
        whole = int(v.numerator / v.denominator)
        rem = v - whole
        if rem == 0:
            return str(whole)
        return f"{whole} {abs(rem.numerator)}/{rem.denominator}"
