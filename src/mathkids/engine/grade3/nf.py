"""Grade 3 Number & Operations—Fractions skills.

Introduces the meaning of a unit/non-unit fraction a/b (parts of a whole),
locating fractions on a 0..1 number line, and reasoning about equivalent and
comparable fractions. Phase-2 skills attach an image spec in ``payload["image"]``
for presentation; every answer is still computed in Python so grading never
depends on the picture.
"""

from __future__ import annotations

import random
from fractions import Fraction

from mathkids.answers import ComparatorAnswer, FractionAnswer, IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_DENOMS = (2, 3, 4, 6, 8)
_DENOM_WORDS = {
    2: "halves",
    3: "thirds",
    4: "fourths",
    6: "sixths",
    8: "eighths",
}


class UnderstandFractions(Skill):
    id = "3.NF.A.1"
    slug = "g3-understand-fractions"
    grade = 3
    domain = "Number & Operations—Fractions"
    title = "Understand fractions a/b"
    max_level = 3
    answer_type = "fraction"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            b = rng.choice((2, 3, 4))
            a = rng.randint(1, b)
        elif level == 2:
            b = rng.choice(_DENOMS)
            a = rng.randint(1, b)
        else:
            b = rng.choice((6, 8))
            a = rng.randint(1, b)
        value = Fraction(a, b)
        word = _DENOM_WORDS[b]
        prompt = (
            f"A whole is split into {b} equal parts ({word}). "
            f"{a} of those parts is shaded. What fraction is shaded? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={
                "a": a,
                "b": b,
                "word": word,
                "image": {"kind": "fraction_bar", "numerator": a, "denominator": b},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        a, b = problem.payload["a"], problem.payload["b"]
        return 1 <= a <= b and problem.answer.value == Fraction(a, b) and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A fraction a/b names equal parts of one whole. The bottom number, b, "
                "tells how many equal parts the whole is split into. The top number, a, "
                "tells how many of those parts you are counting. If a bar is cut into 4 "
                "equal parts and 3 are shaded, that is 3/4 — three of the four equal pieces."
            ),
            strategy="Bottom = how many equal parts; top = how many you count.",
        )

    def hints(self, problem: Problem) -> list[str]:
        b = problem.payload["b"]
        return [
            f"Count the total equal parts — that is the bottom number ({b}).",
            "Count the shaded parts — that is the top number. Write top/bottom.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b = problem.payload["a"], problem.payload["b"]
        return (
            f"The whole has {b} equal parts (the bottom), and {a} are shaded (the top), "
            f"so the fraction is {a}/{b}. Answer = {problem.answer.display}."
        )


class FractionsOnNumberLine(Skill):
    id = "3.NF.A.2"
    slug = "g3-fractions-number-line"
    grade = 3
    domain = "Number & Operations—Fractions"
    title = "Fractions on a number line"
    max_level = 3
    answer_type = "fraction"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            d = rng.choice((2, 3, 4))
        elif level == 2:
            d = rng.choice(_DENOMS)
        else:
            d = rng.choice((6, 8))
        k = rng.randint(1, d - 1)
        value = Fraction(k, d)
        prompt = (
            "The number line from 0 to 1 is split into equal parts. "
            "What fraction does the marked tick show? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={
                "d": d,
                "k": k,
                "image": {"kind": "fraction_number_line", "denominator": d, "mark": k},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        d, k = problem.payload["d"], problem.payload["k"]
        ok = 1 <= k < d and 0 <= problem.answer.value <= 1
        return ok and problem.answer.value == Fraction(k, d) and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "On a number line from 0 to 1, the whole distance is split into equal "
                "jumps. If there are d equal jumps, each jump is 1/d. Count jumps from 0 "
                "to the mark — that count is the top number. Split 0 to 1 into 4 equal "
                "parts and land on the third tick: that is 3/4."
            ),
            strategy="Count equal jumps in the whole (bottom); count jumps to the mark (top).",
        )

    def hints(self, problem: Problem) -> list[str]:
        d = problem.payload["d"]
        return [
            f"Count how many equal jumps fit between 0 and 1 — that is the bottom ({d}).",
            "Count the jumps from 0 up to the arrow — that is the top number.",
        ]

    def worked_example(self, problem: Problem) -> str:
        d, k = problem.payload["d"], problem.payload["k"]
        return (
            f"0 to 1 is split into {d} equal jumps, so each jump is 1/{d}. The mark is "
            f"{k} jumps from 0, so it is {k}/{d}. Answer = {problem.answer.display}."
        )


class EquivalentAndCompareFractions(Skill):
    id = "3.NF.A.3"
    slug = "g3-equivalent-compare-fractions"
    grade = 3
    domain = "Number & Operations—Fractions"
    title = "Equivalent & compare fractions"
    max_level = 3
    answer_type = "comparator"
    phase = 1

    def _make_equivalence(self, level: int, rng: random.Random) -> Problem:
        # Choose base a/b and a whole-number multiplier so b*mult is a valid denominator.
        pairs = [(1, 2, 4), (1, 2, 6), (1, 2, 8), (1, 3, 6), (2, 3, 6), (1, 4, 8), (3, 4, 8)]
        if level <= 1:
            pairs = [(1, 2, 4), (1, 2, 6), (1, 3, 6)]
        a, b, big = rng.choice(pairs)
        mult = big // b
        num = a * mult
        prompt = f"Fill in the missing number: {a}/{b} = ?/{big}"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(num),
            payload={"variant": "equivalence", "a": a, "b": b, "big": big, "num": num},
        )

    def _make_compare(self, level: int, rng: random.Random) -> Problem:
        same = rng.choice(("denominator", "numerator"))
        if same == "denominator":
            d = rng.choice(_DENOMS)
            n1, n2 = rng.sample(range(1, d), 2) if d > 2 else (1, 1)
            if n1 == n2:
                n2 = n1 + 1 if n1 + 1 < d else n1
            f1, f2 = Fraction(n1, d), Fraction(n2, d)
            left, right = f"{n1}/{d}", f"{n2}/{d}"
        else:
            n = 1 if rng.random() < 0.5 else rng.choice((2, 3))
            d1, d2 = rng.sample([d for d in _DENOMS if d > n], 2)
            f1, f2 = Fraction(n, d1), Fraction(n, d2)
            left, right = f"{n}/{d1}", f"{n}/{d2}"
        sym = "<" if f1 < f2 else (">" if f1 > f2 else "=")
        prompt = f"Compare the fractions. Type <, =, or >:  {left} ? {right}"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=ComparatorAnswer(sym),
            payload={"variant": "compare", "same": same, "left": left, "right": right, "sym": sym},
        )

    def generate(self, level: int, rng: random.Random) -> Problem:
        if rng.random() < 0.5:
            return self._make_equivalence(level, rng)
        return self._make_compare(level, rng)

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        if p["variant"] == "equivalence":
            ok = Fraction(p["a"], p["b"]) == Fraction(p["num"], p["big"])
            return ok and problem.answer.value == p["num"] and super().invariant(problem)
        return problem.answer.value in ("<", "=", ">") and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Equivalent fractions name the same amount: 1/2 = 2/4 because multiplying "
                "the top and bottom by the same number keeps the value. To compare with the "
                "SAME bottom number, the bigger top is bigger: 3/8 > 1/8. To compare with "
                "the SAME top number, the smaller bottom is bigger because the pieces are "
                "larger: 1/3 > 1/6."
            ),
            strategy="Same bottom? bigger top wins. Same top? smaller bottom wins.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["variant"] == "equivalence":
            mult = p["big"] // p["b"]
            return [
                f"How many times bigger is the new bottom? {p['big']} ÷ {p['b']} = {mult}.",
                "Multiply the top by that same number to keep the fraction equal.",
            ]
        if p["same"] == "denominator":
            return [
                "The bottoms match, so the pieces are the same size.",
                "More pieces (bigger top) means a bigger fraction.",
            ]
        return [
            "The tops match, so you have the same number of pieces.",
            "Smaller bottom means bigger pieces, so that fraction is larger.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["variant"] == "equivalence":
            mult = p["big"] // p["b"]
            return (
                f"{p['a']}/{p['b']} = ?/{p['big']}: the bottom grew ×{mult}, so the top "
                f"grows ×{mult} too: {p['a']} × {mult} = {p['num']}. Answer = {p['num']}."
            )
        reason = (
            "same bottoms, so compare the tops"
            if p["same"] == "denominator"
            else "same tops, so the smaller bottom is the bigger fraction"
        )
        return (
            f"{p['left']} ? {p['right']}: {reason}. "
            f"Answer = {p['sym']}."
        )


register(UnderstandFractions())
register(FractionsOnNumberLine())
register(EquivalentAndCompareFractions())
