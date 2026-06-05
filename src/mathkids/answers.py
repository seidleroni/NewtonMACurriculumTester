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
from decimal import Decimal, InvalidOperation
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


# --- comparator (<, =, >) -------------------------------------------------

_COMPARATOR_WORDS = {
    "greater": ">", "greater than": ">", "more": ">", "bigger": ">", "gt": ">",
    "less": "<", "less than": "<", "fewer": "<", "smaller": "<", "lt": "<",
    "equal": "=", "equals": "=", "equal to": "=", "same": "=", "eq": "=",
}


@dataclass(frozen=True)
class ComparatorAnswer(Answer):
    value: str  # one of "<", "=", ">"
    answer_type: str = "comparator"

    def grade(self, raw: str) -> GradeResult:
        s = (raw or "").strip().lower()
        given = s if s in ("<", "=", ">") else _COMPARATOR_WORDS.get(s, "")
        return GradeResult(given == self.value, self.value, given)

    def canonical(self) -> str:
        return self.value


# --- decimal (0.7 == 0.70) ------------------------------------------------

@dataclass(frozen=True)
class DecimalAnswer(Answer):
    text: str  # e.g. "0.62" — grading is by decimal value, display by this text
    answer_type: str = "decimal"

    @property
    def value(self) -> Decimal:
        return Decimal(self.text)

    def grade(self, raw: str) -> GradeResult:
        try:
            given = Decimal((raw or "").strip().replace(",", "").replace("$", ""))
        except (InvalidOperation, ValueError):
            return GradeResult(False, self.text, "")
        return GradeResult(given == self.value, self.text, str(given))

    def canonical(self) -> str:
        return self.text


# --- word / label (with synonyms) -----------------------------------------

def _norm_word(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower()).rstrip(".")


@dataclass(frozen=True)
class WordAnswer(Answer):
    value: str
    aliases: tuple[str, ...] = ()
    answer_type: str = "word"

    def grade(self, raw: str) -> GradeResult:
        given = _norm_word(raw)
        accepted = {_norm_word(self.value)} | {_norm_word(a) for a in self.aliases}
        return GradeResult(given in accepted, self.value, given)

    def canonical(self) -> str:
        return self.value


# --- ordered integer sequence ---------------------------------------------

def _parse_ints(raw: str) -> list[int]:
    return [int(tok) for tok in re.findall(r"-?\d+", raw or "")]


@dataclass(frozen=True)
class SequenceAnswer(Answer):
    values: tuple[int, ...]
    answer_type: str = "sequence"

    def grade(self, raw: str) -> GradeResult:
        given = _parse_ints(raw)
        return GradeResult(given == list(self.values), self.canonical(), ", ".join(map(str, given)))

    def canonical(self) -> str:
        return ", ".join(map(str, self.values))


# --- unordered integer set (e.g. "list all factors") ----------------------

@dataclass(frozen=True)
class SetAnswer(Answer):
    values: frozenset[int]
    answer_type: str = "set"

    def grade(self, raw: str) -> GradeResult:
        given = set(_parse_ints(raw))
        return GradeResult(given == set(self.values), self.canonical(), ", ".join(map(str, sorted(given))))

    def canonical(self) -> str:
        return ", ".join(map(str, sorted(self.values)))


# --- time (H:MM) ----------------------------------------------------------

_TIME_RE = re.compile(r"(\d{1,2})\s*:\s*(\d{1,2})")


@dataclass(frozen=True)
class TimeAnswer(Answer):
    hour: int
    minute: int
    answer_type: str = "time"

    def grade(self, raw: str) -> GradeResult:
        m = _TIME_RE.search(raw or "")
        given_disp = ""
        ok = False
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            given_disp = f"{h}:{mi:02d}"
            ok = (h % 12, mi) == (self.hour % 12, self.minute)
        return GradeResult(ok, self.canonical(), given_disp)

    def canonical(self) -> str:
        return f"{self.hour}:{self.minute:02d}"


# --- money (accepts $1.04, 104¢, 1.04, bare cents) ------------------------

@dataclass(frozen=True)
class MoneyAnswer(Answer):
    cents: int
    answer_type: str = "money"

    def _parse(self, raw: str) -> int | None:
        s = (raw or "").strip().lower().replace(",", "").replace(" ", "")
        is_cents = "¢" in s or s.endswith("c") or "cent" in s
        s = s.replace("¢", "").replace("$", "").replace("cents", "").replace("cent", "")
        if s.endswith("c"):
            s = s[:-1]
        if not s:
            return None
        try:
            if "." in s:
                return int(round(float(s) * 100))
            n = int(s)
            return n if is_cents or n < 100 else n  # bare integer treated as cents
        except ValueError:
            return None

    def grade(self, raw: str) -> GradeResult:
        given = self._parse(raw)
        return GradeResult(given == self.cents, self.canonical(), "" if given is None else self.display_of(given))

    @staticmethod
    def display_of(cents: int) -> str:
        return f"${cents // 100}.{cents % 100:02d}"

    def canonical(self) -> str:
        return self.display_of(self.cents)


# --- quotient with remainder (e.g. "434 R 3") -----------------------------

@dataclass(frozen=True)
class QuotientRemainderAnswer(Answer):
    quotient: int
    remainder: int
    answer_type: str = "quotient_remainder"

    def grade(self, raw: str) -> GradeResult:
        ints = _parse_ints(raw)
        ok = False
        if len(ints) == 1 and self.remainder == 0:
            ok = ints[0] == self.quotient
        elif len(ints) >= 2:
            ok = (ints[0], ints[1]) == (self.quotient, self.remainder)
        return GradeResult(ok, self.canonical(), raw.strip() if raw else "")

    def canonical(self) -> str:
        if self.remainder == 0:
            return str(self.quotient)
        return f"{self.quotient} R {self.remainder}"


# Registry of answer types -> classes, for metadata validation in tests.
ANSWER_TYPES = {
    "integer": IntegerAnswer,
    "fraction": FractionAnswer,
    "comparator": ComparatorAnswer,
    "decimal": DecimalAnswer,
    "word": WordAnswer,
    "sequence": SequenceAnswer,
    "set": SetAnswer,
    "time": TimeAnswer,
    "money": MoneyAnswer,
    "quotient_remainder": QuotientRemainderAnswer,
}
