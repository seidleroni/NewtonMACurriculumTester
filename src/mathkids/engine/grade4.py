"""Grade 4 skills (Samuel's starting grade)."""

from __future__ import annotations

import random
from fractions import Fraction

from mathkids.answers import FractionAnswer, IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_FRACTION_DENOMS = (2, 3, 4, 5, 6, 8)


class FactsTo12(Skill):
    id = "4.OA.A.3.a"
    slug = "g4-facts-12"
    grade = 4
    domain = "Operations & Algebraic Thinking"
    title = "Multiplication & division facts to 12 × 12"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            prompt, ans, op = f"{a} × {b} = ?", a * b, "×"
        elif level == 2:
            a, b = rng.randint(2, 12), rng.randint(2, 12)
            prompt, ans, op = f"{a} × {b} = ?", a * b, "×"
        else:  # division facts
            a, b = rng.randint(2, 12), rng.randint(2, 12)
            product = a * b
            prompt, ans, op = f"{product} ÷ {a} = ?", b, "÷"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Knowing your times tables to 12 makes everything faster. Division is the "
                "flip side: 56 ÷ 8 asks 'what times 8 makes 56?' (answer 7)."
            ),
            strategy="Division? Ask: what times the divisor makes this number?",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "×":
            return [
                f"Skip-count by {a}, {b} times.",
                f"Or use a fact you know and adjust (e.g. {a}×{b} is {a}×{b - 1} plus {a}).",
            ]
        return [
            f"Ask: what number times {a} makes {a * b}?",
            f"Count up {a}, {a * 2}, {a * 3}… until you reach {a * b}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "×":
            return f"{a} × {b} = {a * b}."
        return f"{a * b} ÷ {a}: because {a} × {b} = {a * b}, the answer is {b}."


class MultiplyMultiDigit(Skill):
    id = "4.NBT.B.5"
    slug = "g4-multiply-multidigit"
    grade = 4
    domain = "Number & Operations in Base Ten"
    title = "Multi-digit multiplication"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(10, 99), rng.randint(2, 9)
        elif level == 2:
            a, b = rng.randint(100, 9999), rng.randint(2, 9)
        else:
            a, b = rng.randint(11, 99), rng.randint(11, 99)
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"{a} × {b} = ?",
            answer=IntegerAnswer(a * b),
            payload={"a": a, "b": b},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Break a big multiply into place-value pieces and add them up. "
                "47 × 6 = (40 × 6) + (7 × 6) = 240 + 42 = 282. "
                "For two 2-digit numbers, multiply by the tens and the ones, then add."
            ),
            strategy="Split into tens and ones, multiply each, then add.",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b = problem.payload["a"], problem.payload["b"]
        return [
            "Break the bigger number into hundreds/tens/ones and multiply each part.",
            f"Try ({(a // 10) * 10} × {b}) + ({a % 10} × {b}) and add them."
            if b < 10
            else f"Multiply {a} by the tens of {b}, then by the ones, then add.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b = problem.payload["a"], problem.payload["b"]
        if b < 10:
            tens = (a // 10) * 10
            ones = a % 10
            return f"{a} × {b} = ({tens} × {b}) + ({ones} × {b}) = {tens * b} + {ones * b} = {a * b}."
        return f"{a} × {b} = {a * b}."


class AddSubFractions(Skill):
    id = "4.NF.B.3"
    slug = "g4-add-sub-fractions"
    grade = 4
    domain = "Number & Operations—Fractions"
    title = "Add & subtract fractions (like denominators)"
    max_level = 3
    answer_type = "fraction"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        d = rng.choice(_FRACTION_DENOMS)
        if level <= 1:  # proper, result <= 1
            if d == 2 or rng.random() < 0.5:
                a = rng.randint(1, d - 1)
                b = rng.randint(1, d - a)
                op, value = "+", Fraction(a + b, d)
                prompt = f"{a}/{d} + {b}/{d} = ?"
            else:  # subtraction needs a >= 2, so d >= 3 here
                a = rng.randint(2, d - 1)
                b = rng.randint(1, a - 1)
                op, value = "-", Fraction(a - b, d)
                prompt = f"{a}/{d} - {b}/{d} = ?"
        elif level == 2:  # results may be greater than 1 (improper)
            a, b = rng.randint(1, d - 1), rng.randint(1, d - 1)
            op, value = "+", Fraction(a + b, d)
            prompt = f"{a}/{d} + {b}/{d} = ?"
        else:  # mixed numbers
            w1, w2 = rng.randint(1, 4), rng.randint(1, 4)
            a, b = rng.randint(1, d - 1), rng.randint(1, d - 1)
            op = "+"
            value = Fraction(w1 * d + a, d) + Fraction(w2 * d + b, d)
            prompt = f"{w1} {a}/{d} + {w2} {b}/{d} = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={"d": d, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When the bottom numbers (denominators) match, the pieces are the same size — "
                "so just add or subtract the top numbers and keep the bottom the same. "
                "2/5 + 1/5 = 3/5. For mixed numbers, add the whole parts and the fraction parts."
            ),
            strategy="Same bottom? Add/subtract the tops, keep the bottom.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "The denominators are the same, so the pieces are equal size — work with the top numbers.",
            "Add (or subtract) the numerators; keep the denominator. Then simplify if you can.",
        ]

    def worked_example(self, problem: Problem) -> str:
        return (
            "Same denominator, so combine the top numbers and keep the bottom. "
            f"The answer is {problem.answer.display}."
        )


register(FactsTo12())
register(MultiplyMultiDigit())
register(AddSubFractions())
