"""Grade 4 Number & Operations—Fractions skills.

Builds on the grade-3 meaning of a fraction toward fourth-grade fluency:
generating equivalent fractions, comparing unlike fractions by cross-
multiplication, adding and subtracting fractions with like denominators,
multiplying a fraction by a whole number, adding tenths and hundredths, and
moving between fraction and decimal notation for tenths/hundredths.

All skills are text-only (phase 1). Every problem is generated using ONLY the
injected ``rng`` so the same (skill, level, seed) reproduces an identical
problem, and every declared answer is computed in Python so grading never
depends on presentation.
"""

from __future__ import annotations

import random
from fractions import Fraction

from mathkids.answers import (
    ComparatorAnswer,
    DecimalAnswer,
    FractionAnswer,
    IntegerAnswer,
)
from mathkids.engine.base import Lesson, Problem, Skill, register

_FRACTION_DENOMS = (2, 3, 4, 5, 6, 8)
_EQUIV_DENOMS = (2, 3, 4, 5, 6, 8, 10, 12)


def _compare_symbol(left: Fraction, right: Fraction) -> str:
    """Return '<', '=', or '>' for left compared to right (no float math)."""
    if left < right:
        return "<"
    if left > right:
        return ">"
    return "="


class EquivalentFractions(Skill):
    id = "4.NF.A.1"
    slug = "g4-equivalent-fractions"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Equivalent fractions"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Pick a base fraction a/b, then a bigger denominator that is a whole
        # multiple of b so the equivalent numerator is a whole number.
        if level <= 1:
            b = rng.choice((2, 3, 4, 5))
            mult = rng.randint(2, 3)
        elif level == 2:
            b = rng.choice((2, 3, 4, 5, 6))
            mult = rng.randint(2, 4)
        else:
            b = rng.choice(_EQUIV_DENOMS)
            mult = rng.randint(2, 5)
        a = rng.randint(1, b - 1)
        big = b * mult
        num = a * mult
        prompt = f"Fill in the missing number: {a}/{b} = ?/{big}"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(num),
            payload={"a": a, "b": b, "big": big, "mult": mult, "num": num},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        equal = Fraction(p["a"], p["b"]) == Fraction(p["num"], p["big"])
        return equal and problem.answer.value == p["num"] and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Equivalent fractions name the very same amount with different numbers. "
                "If you multiply the top and the bottom by the SAME number, the value does "
                "not change: 2/3 = 4/6 = 6/9, because you scaled both parts equally. To fill "
                "in 2/3 = ?/12, ask how many times bigger the new bottom is (12 ÷ 3 = 4), "
                "then multiply the top by that same 4: 2 × 4 = 8, so 2/3 = 8/12."
            ),
            strategy="Find how many times the bottom grew, then grow the top by the same amount.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        return [
            f"How many times bigger is the new bottom? {p['big']} ÷ {p['b']} = {p['mult']}.",
            "Multiply the top number by that same amount to keep the fraction equal.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"{p['a']}/{p['b']} = ?/{p['big']}: the bottom grew ×{p['mult']} "
            f"({p['b']} × {p['mult']} = {p['big']}), so the top grows ×{p['mult']} too: "
            f"{p['a']} × {p['mult']} = {p['num']}. Answer = {p['num']}."
        )


class CompareUnlikeFractions(Skill):
    id = "4.NF.A.2"
    slug = "g4-compare-unlike-fractions"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Compare unlike fractions"
    max_level = 3
    answer_type = "comparator"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            denoms = (2, 3, 4, 5, 6)
        elif level == 2:
            denoms = (2, 3, 4, 5, 6, 8)
        else:
            denoms = _EQUIV_DENOMS
        # Different numerator AND different denominator for both fractions.
        while True:
            d1, d2 = rng.sample(denoms, 2)
            n1 = rng.randint(1, d1 - 1)
            n2 = rng.randint(1, d2 - 1)
            if n1 != n2:
                break
        f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
        sym = _compare_symbol(f1, f2)
        left, right = f"{n1}/{d1}", f"{n2}/{d2}"
        prompt = f"Compare the fractions. Type <, =, or >:  {left} ? {right}"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=ComparatorAnswer(sym),
            payload={
                "n1": n1, "d1": d1, "n2": n2, "d2": d2,
                "left": left, "right": right, "sym": sym,
                "cross1": n1 * d2, "cross2": n2 * d1,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        expected = _compare_symbol(Fraction(p["n1"], p["d1"]), Fraction(p["n2"], p["d2"]))
        return (
            problem.answer.value == expected
            and problem.answer.value in ("<", "=", ">")
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When two fractions have different tops AND different bottoms, you cannot "
                "just look at them. Use cross-multiplication: for a/b ? c/d, compare a×d with "
                "c×b. Whichever cross-product is bigger sits over the bigger fraction. For "
                "2/3 ? 3/5: 2×5 = 10 and 3×3 = 9; 10 > 9, so 2/3 > 3/5."
            ),
            strategy="Cross-multiply: compare top-left×bottom-right with top-right×bottom-left.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        return [
            "Different tops and bottoms — cross-multiply to compare them fairly.",
            (
                f"Compare {p['n1']} × {p['d2']} = {p['cross1']} with "
                f"{p['n2']} × {p['d1']} = {p['cross2']}; the bigger product is over the "
                "bigger fraction."
            ),
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"{p['left']} ? {p['right']}: cross-multiply — {p['n1']} × {p['d2']} = "
            f"{p['cross1']} and {p['n2']} × {p['d1']} = {p['cross2']}. Since "
            f"{p['cross1']} {p['sym']} {p['cross2']}, the answer is {p['sym']}."
        )


class AddSubFractions(Skill):
    id = "4.NF.B.3"
    slug = "g4-add-sub-fractions"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Add & subtract fractions (like denominators)"
    max_level = 3
    answer_type = "fraction"
    phase = 1

    def generate(self, level, rng):
        d = rng.choice((2, 3, 4, 5, 6, 8))
        if level <= 1 and (d == 2 or rng.random() < 0.5):
            a = rng.randint(1, d - 1)
            b = rng.randint(1, d - a)
            value = Fraction(a + b, d)
            prompt = f"{a}/{d} + {b}/{d} = ?"
        elif level <= 1:
            a = rng.randint(2, d - 1)
            b = rng.randint(1, a - 1)
            value = Fraction(a - b, d)
            prompt = f"{a}/{d} - {b}/{d} = ?"
        else:
            a, b = rng.randint(1, d - 1), rng.randint(1, d - 1)
            value = Fraction(a + b, d)
            prompt = f"{a}/{d} + {b}/{d} = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={"d": d},
        )

    def invariant(self, problem):
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self):
        return Lesson(
            title=self.title,
            body=(
                "Same bottom number means same-size pieces, so add or subtract the top "
                "numbers and keep the bottom. 2/5 + 1/5 = 3/5."
            ),
            strategy="Same bottom? Combine the tops, keep the bottom.",
        )

    def hints(self, problem):
        return [
            "The denominators match, so just work the top numbers.",
            "Add/subtract the numerators; keep the denominator; simplify.",
        ]

    def worked_example(self, problem):
        return f"Combine the tops, keep the bottom. Answer = {problem.answer.display}."


class FractionTimesWhole(Skill):
    id = "4.NF.B.4"
    slug = "g4-fraction-times-whole"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Fraction × whole number"
    max_level = 3
    answer_type = "fraction"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            d = rng.choice((2, 3, 4))
            n = rng.randint(2, 4)
        elif level == 2:
            d = rng.choice(_FRACTION_DENOMS)
            n = rng.randint(2, 6)
        else:
            d = rng.choice(_FRACTION_DENOMS)
            n = rng.randint(3, 9)
        a = rng.randint(1, d - 1)  # proper fraction a/d
        value = Fraction(n) * Fraction(a, d)
        prompt = f"{n} × {a}/{d} = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={"n": n, "a": a, "d": d, "top": n * a},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        expected = Fraction(p["n"]) * Fraction(p["a"], p["d"])
        return (
            problem.answer.value == expected
            and problem.answer.value >= 0
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Multiplying a whole number by a fraction is repeated addition of that "
                "fraction. 3 × 2/5 means 2/5 + 2/5 + 2/5 = 6/5. The shortcut: multiply the "
                "whole number by the top, keep the bottom: 3 × 2/5 = (3 × 2)/5 = 6/5. Then "
                "simplify or write it as a mixed number if you like (6/5 = 1 1/5)."
            ),
            strategy="Multiply the whole number by the top; keep the bottom.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        return [
            f"Think of {p['n']} copies of {p['a']}/{p['d']} added together.",
            (
                f"Multiply the whole number by the top: {p['n']} × {p['a']} = {p['top']}, "
                f"and keep the bottom {p['d']}."
            ),
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"{p['n']} × {p['a']}/{p['d']} = ({p['n']} × {p['a']})/{p['d']} = "
            f"{p['top']}/{p['d']}. Answer = {problem.answer.display}."
        )


class AddTenthsHundredths(Skill):
    id = "4.NF.C.5"
    slug = "g4-add-tenths-hundredths"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Add tenths & hundredths"
    max_level = 3
    answer_type = "fraction"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            x = rng.randint(1, 5)
            y = rng.randint(1, 9)
        elif level == 2:
            x = rng.randint(1, 9)
            y = rng.randint(1, 9)
        else:
            x = rng.randint(1, 9)
            y = rng.randint(10, 90)
        hundredths = 10 * x + y
        value = Fraction(hundredths, 100)
        prompt = (
            f"Rewrite {x}/10 as hundredths and add: {x}/10 + {y}/100 = ?/100 "
            f"(write your answer as a fraction)"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={"x": x, "y": y, "hundredths": hundredths},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        expected = Fraction(10 * p["x"] + p["y"], 100)
        return (
            problem.answer.value == expected
            and problem.answer.value >= 0
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Tenths and hundredths are different-size pieces, so first make them match. "
                "One tenth equals ten hundredths: 3/10 = 30/100. Then add like denominators: "
                "3/10 + 4/100 = 30/100 + 4/100 = 34/100. The trick is 10x/100 + y/100 = "
                "(10x + y)/100."
            ),
            strategy="Turn tenths into hundredths (×10 top and bottom), then add the tops.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        return [
            f"Rename {p['x']}/10 as hundredths: {p['x']}/10 = {p['x'] * 10}/100.",
            (
                f"Now both are hundredths, so add the tops: {p['x'] * 10} + {p['y']} = "
                f"{p['hundredths']}, over 100."
            ),
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"{p['x']}/10 = {p['x'] * 10}/100, so {p['x']}/10 + {p['y']}/100 = "
            f"{p['x'] * 10}/100 + {p['y']}/100 = {p['hundredths']}/100. "
            f"Answer = {problem.answer.display}."
        )


class DecimalNotation(Skill):
    id = "4.NF.C.6"
    slug = "g4-decimal-notation"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Decimal notation for fractions"
    max_level = 3
    answer_type = "decimal"
    phase = 1

    def _to_decimal(self, level: int, rng: random.Random) -> Problem:
        # "Write n/10 (or n/100) as a decimal."
        if level <= 1:
            den = 10
            n = rng.randint(1, 9)
            text = f"0.{n}"
        else:
            den = 100
            n = rng.randint(1, 99)
            text = f"0.{n:02d}"
        prompt = f"Write {n}/{den} as a decimal. = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=DecimalAnswer(text),
            payload={"variant": "to_decimal", "n": n, "den": den, "text": text},
        )

    def _to_fraction(self, level: int, rng: random.Random) -> Problem:
        # "Write 0.45 as a fraction."  Keep it over 10 or 100 (value is what grades).
        if level <= 1:
            n = rng.randint(1, 9)
            den = 10
            text = f"0.{n}"
        else:
            n = rng.randint(1, 99)
            den = 100
            text = f"0.{n:02d}"
        value = Fraction(n, den)
        prompt = f"Write {text} as a fraction. = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={"variant": "to_fraction", "n": n, "den": den, "text": text},
        )

    def generate(self, level: int, rng: random.Random) -> Problem:
        if rng.random() < 0.5:
            return self._to_decimal(level, rng)
        return self._to_fraction(level, rng)

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        if p["variant"] == "to_decimal":
            ok = Fraction(p["n"], p["den"]) == Fraction(problem.answer.text)
        else:
            ok = problem.answer.value == Fraction(p["n"], p["den"])
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Decimals are just fractions with bottoms of 10 or 100. The first place after "
                "the dot is tenths, the second is hundredths. So 7/10 = 0.7 and 45/100 = 0.45. "
                "Going back, 0.7 means 7 tenths = 7/10, and 0.45 means 45 hundredths = 45/100."
            ),
            strategy="Tenths fill 1 place after the dot; hundredths fill 2 places.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["variant"] == "to_decimal":
            place = "place" if p["den"] == 10 else "two places"
            return [
                f"A bottom of {p['den']} means the digits go in the {place} after the dot.",
                "Tenths fill one place (0.x); hundredths fill two places (0.xx).",
            ]
        return [
            "Count the places after the dot: one place is tenths, two places is hundredths.",
            f"Write the digits over {p['den']}, since {p['text']} has that many places.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["variant"] == "to_decimal":
            return (
                f"{p['n']}/{p['den']} puts {p['n']} in the "
                f"{'tenths' if p['den'] == 10 else 'hundredths'} place, so it is "
                f"{p['text']}. Answer = {p['text']}."
            )
        return (
            f"{p['text']} means {p['n']} "
            f"{'tenths' if p['den'] == 10 else 'hundredths'}, so it is {p['n']}/{p['den']}. "
            f"Answer = {problem.answer.display}."
        )


class CompareDecimals(Skill):
    id = "4.NF.C.7"
    slug = "g4-compare-decimals"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Compare decimals to hundredths"
    max_level = 3
    answer_type = "comparator"
    phase = 1

    def _decimal_text(self, hundredths: int, places: int) -> str:
        if places == 1:
            return f"0.{hundredths // 10}"
        return f"0.{hundredths:02d}"

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Work in hundredths internally so comparison is exact integer math.
        if level <= 1:
            # both one-place decimals (tenths)
            h1 = rng.randint(1, 9) * 10
            h2 = rng.randint(1, 9) * 10
            p1 = p2 = 1
        elif level == 2:
            h1 = rng.randint(1, 99)
            h2 = rng.randint(1, 99)
            p1 = 1 if h1 % 10 == 0 else 2
            p2 = 1 if h2 % 10 == 0 else 2
        else:
            # Tricky: one tenths value vs one hundredths value (e.g. 0.3 vs 0.27).
            tenths = rng.randint(1, 9)
            h1 = tenths * 10
            p1 = 1
            h2 = rng.randint(1, 99)
            p2 = 1 if h2 % 10 == 0 else 2
        left = self._decimal_text(h1, p1)
        right = self._decimal_text(h2, p2)
        sym = _compare_symbol(Fraction(h1, 100), Fraction(h2, 100))
        prompt = f"Compare the decimals. Type <, =, or >:  {left} ? {right}"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=ComparatorAnswer(sym),
            payload={"h1": h1, "h2": h2, "left": left, "right": right, "sym": sym},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        expected = _compare_symbol(Fraction(p["h1"], 100), Fraction(p["h2"], 100))
        return (
            problem.answer.value == expected
            and problem.answer.value in ("<", "=", ">")
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To compare decimals, line up the decimal points and compare place by place "
                "from the left. Give them the same number of places by adding a zero if needed: "
                "0.3 is the same as 0.30. Now 0.30 vs 0.27 — 30 hundredths beats 27 hundredths, "
                "so 0.3 > 0.27. Do not be fooled by 27 'looking' bigger than 3."
            ),
            strategy="Make the same number of decimal places, then compare like whole numbers.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Give both the same number of places by adding a zero (0.3 = 0.30).",
            "Then compare them as if they were whole numbers of hundredths.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"{p['left']} ? {p['right']}: that is {p['h1']} hundredths vs {p['h2']} "
            f"hundredths. Since {p['h1']} {p['sym']} {p['h2']}, the answer is {p['sym']}."
        )


register(EquivalentFractions())
register(CompareUnlikeFractions())
register(AddSubFractions())
register(FractionTimesWhole())
register(AddTenthsHundredths())
register(DecimalNotation())
register(CompareDecimals())
