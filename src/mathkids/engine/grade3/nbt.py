"""Grade 3 Number & Operations in Base Ten skills.

Covers rounding to the nearest 10/100, adding and subtracting within 1,000,
and multiplying one-digit numbers by multiples of 10.
"""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register


def _round_to(n: int, place: int) -> int:
    """Standard rounding of n to the nearest `place` (10 or 100); 5 rounds up."""
    rem = n % place
    return n - rem if rem < place // 2 else n - rem + place


class RoundTo10Or100(Skill):
    id = "3.NBT.A.1"
    slug = "g3-round-10-100"
    grade = 3
    domain = "Number & Operations in Base Ten"
    title = "Round to nearest 10 or 100"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            place = 10
            n = rng.randint(10, 99)
        elif level == 2:
            place = 100
            n = rng.randint(100, 999)
        else:
            place = rng.choice((10, 100))
            n = rng.randint(10, 999)
        place_word = "ten" if place == 10 else "hundred"
        ans = _round_to(n, place)
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"Round {n} to the nearest {place_word}. = ?",
            answer=IntegerAnswer(ans),
            payload={"n": n, "place": place, "place_word": place_word},
        )

    def invariant(self, problem: Problem) -> bool:
        place = problem.payload["place"]
        return problem.answer.value % place == 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To round, look at the digit just to the right of the place you are rounding to. "
                "If it is 5 or more, round up; if it is 4 or less, round down (keep the digit). "
                "Rounding 47 to the nearest ten: the ones digit is 7, so round up to 50. "
                "Rounding 312 to the nearest hundred: the tens digit is 1, so round down to 300."
            ),
            strategy="Check the next digit: 5 or more rounds up, 4 or less stays.",
        )

    def hints(self, problem: Problem) -> list[str]:
        place_word = problem.payload["place_word"]
        if place_word == "ten":
            return [
                "Look at the ones digit (the rightmost one).",
                "5 or more rounds the tens up; 4 or less keeps the tens the same.",
            ]
        return [
            "Look at the tens digit (the middle one).",
            "5 or more rounds the hundreds up; 4 or less keeps the hundreds the same.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        place = problem.payload["place"]
        place_word = problem.payload["place_word"]
        next_digit = (n % place) // (place // 10)
        direction = "up" if next_digit >= 5 else "down"
        return (
            f"Round {n} to the nearest {place_word}: the next digit is {next_digit}, "
            f"so round {direction}. Answer = {_round_to(n, place)}."
        )


class AddSubWithin1000(Skill):
    id = "3.NBT.A.2"
    slug = "g3-add-sub-1000"
    grade = 3
    domain = "Number & Operations in Base Ten"
    title = "Add & subtract within 1,000"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a = rng.randint(100, 500)
            b = rng.randint(10, 1000 - a)
            op, ans = "+", a + b
        elif level == 2:
            a = rng.randint(200, 999)
            b = rng.randint(10, a)
            op, ans = "-", a - b
        else:
            if rng.random() < 0.5:
                a = rng.randint(100, 800)
                b = rng.randint(50, 1000 - a)
                op, ans = "+", a + b
            else:
                a = rng.randint(300, 1000)
                b = rng.randint(50, a)
                op, ans = "-", a - b
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"{a} {op} {b} = ?",
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        ans = problem.answer.value
        return 0 <= ans <= 1000 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Line up the hundreds, tens, and ones. Work right to left. "
                "When a column adds past 9, carry to the next column. "
                "When you subtract and the top digit is too small, regroup: trade one from "
                "the next column for ten. 425 + 138: ones 5 + 8 = 13 (write 3, carry 1), "
                "tens 2 + 3 + 1 = 6, hundreds 4 + 1 = 5 -> 563."
            ),
            strategy="Stack by place value, work right to left, carry or regroup as needed.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Add the ones, then tens, then hundreds — one column at a time.",
                "If a column total is 10 or more, carry the extra to the next column.",
            ]
        return [
            "Subtract the ones, then tens, then hundreds — one column at a time.",
            "If the top digit is too small, regroup: borrow ten from the next column.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "+":
            return (
                f"{a} + {b}: add ones, then tens, then hundreds, carrying when a column "
                f"passes 9. Answer = {a + b}."
            )
        return (
            f"{a} - {b}: subtract ones, then tens, then hundreds, regrouping when the top "
            f"digit is too small. Answer = {a - b}."
        )


class MultiplyByMultiplesOf10(Skill):
    id = "3.NBT.A.3"
    slug = "g3-multiply-multiples-10"
    grade = 3
    domain = "Number & Operations in Base Ten"
    title = "Multiply by multiples of 10"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a = rng.randint(2, 5)
            tens = rng.randint(1, 5)
        elif level == 2:
            a = rng.randint(2, 9)
            tens = rng.randint(2, 9)
        else:
            a = rng.randint(6, 9)
            tens = rng.randint(5, 9)
        b = tens * 10
        ans = a * b
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"{a} × {b} = ?",
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "tens": tens},
        )

    def invariant(self, problem: Problem) -> bool:
        b = problem.payload["b"]
        return b % 10 == 0 and 10 <= b <= 90 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To multiply by a multiple of 10, use the basic fact and then attach a zero. "
                "For 6 × 40, first do 6 × 4 = 24, then multiply by 10 to get 240. "
                "It works because 40 is 4 tens, so 6 × 40 is 6 × 4 = 24 tens = 240."
            ),
            strategy="Multiply the single digits, then add one zero (× 10).",
        )

    def hints(self, problem: Problem) -> list[str]:
        a = problem.payload["a"]
        tens = problem.payload["tens"]
        return [
            f"Start with the easy fact: {a} × {tens}.",
            "Then multiply that answer by 10 — just put a zero on the end.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a = problem.payload["a"]
        b = problem.payload["b"]
        tens = problem.payload["tens"]
        return (
            f"{a} × {b}: first {a} × {tens} = {a * tens}, then × 10 gives "
            f"{a * tens}0 = {a * b}."
        )


register(RoundTo10Or100())
register(AddSubWithin1000())
register(MultiplyByMultiplesOf10())
