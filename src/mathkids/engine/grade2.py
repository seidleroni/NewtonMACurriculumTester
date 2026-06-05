"""Grade 2 skills (Jacob's starting grade)."""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_PLACE_VALUE = {"hundreds": 100, "tens": 10, "ones": 1}


class FactsWithin20(Skill):
    id = "2.OA.B.2"
    slug = "g2-facts-20"
    grade = 2
    domain = "Operations & Algebraic Thinking"
    title = "Add & subtract facts within 20"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            op, ans = "+", a + b
        elif level == 2:
            a = rng.randint(6, 18)
            b = rng.randint(1, a)
            op, ans = "-", a - b
        else:  # bridging-ten facts (the hard ones)
            if rng.random() < 0.5:
                a = rng.randint(6, 9)
                b = rng.randint(11 - a, 9)
                op, ans = "+", a + b
            else:
                a = rng.randint(11, 18)
                b = rng.randint(a - 9, 9)
                op, ans = "-", a - b
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"{a} {op} {b} = ?",
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "These are the add and subtract facts up to 20 — the ones worth just knowing. "
                "For the tricky ones, make a ten: 8 + 7 is 8 + 2 (that's 10) and 5 more = 15."
            ),
            strategy="Make a ten, then add the rest.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Can you make a 10 first? Take from one number to round the other up to 10.",
                f"Try: {problem.payload['a']} + {problem.payload['b']} — fill up to 10, then add what's left.",
            ]
        return [
            "Count up from the smaller number to the bigger one.",
            "Or think of the matching addition fact: what plus the second number makes the first?",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "+":
            to_ten = 10 - a if a < 10 else 0
            if 0 < to_ten <= b:
                return f"{a} + {b}: {a} + {to_ten} = 10, then 10 + {b - to_ten} = {a + b}."
            return f"{a} + {b} = {a + b}."
        return f"{a} - {b}: count up from {b} to {a}, that's {a - b}. So {a} - {b} = {a - b}."


class ThreeDigitPlaceValue(Skill):
    id = "2.NBT.A.1"
    slug = "g2-place-value-3"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Three-digit place value"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        n = rng.randint(100, 999)
        place = rng.choice(["hundreds", "tens", "ones"])
        digit = (n // _PLACE_VALUE[place]) % 10
        if level <= 1:
            prompt = f"What digit is in the {place} place of {n}?"
            ans = digit
            mode = "digit"
        else:
            prompt = f"What is the value of the {place} digit in {n}?"
            ans = digit * _PLACE_VALUE[place]
            mode = "value"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"n": n, "place": place, "digit": digit, "mode": mode},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "In a 3-digit number, each digit has a place: hundreds, tens, ones. "
                "In 348, the 3 means 3 hundreds (300), the 4 means 4 tens (40), the 8 means 8 ones (8)."
            ),
            strategy="Find the column, then multiply the digit by 100, 10, or 1.",
        )

    def hints(self, problem: Problem) -> list[str]:
        place = problem.payload["place"]
        return [
            f"Find the {place} column. The ones are on the right, then tens, then hundreds.",
            (
                f"The {place} digit is {problem.payload['digit']}."
                if problem.payload["mode"] == "value"
                else f"Look at the {place} spot and read off the digit."
            ),
        ]

    def worked_example(self, problem: Problem) -> str:
        n, place, digit = problem.payload["n"], problem.payload["place"], problem.payload["digit"]
        if problem.payload["mode"] == "digit":
            return f"In {n}, the {place} digit is {digit}."
        pv = _PLACE_VALUE[place]
        return f"In {n}, the {place} digit is {digit}, worth {digit} × {pv} = {digit * pv}."


class AddSubWithin100(Skill):
    id = "2.NBT.B.5"
    slug = "g2-add-sub-100"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Add & subtract within 100"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:  # addition, no regrouping
            ao = rng.randint(0, 4)
            bo = rng.randint(0, 9 - ao)
            at = rng.randint(1, 7)
            bt = rng.randint(1, 8 - at)
            a, b = at * 10 + ao, bt * 10 + bo
            op, ans = "+", a + b
        elif level == 2:  # addition with regrouping
            ao = rng.randint(1, 9)
            bo = rng.randint(10 - ao, 9)
            at = rng.randint(1, 7)
            bt = rng.randint(1, 8 - at)
            a, b = at * 10 + ao, bt * 10 + bo
            op, ans = "+", a + b
        else:  # subtraction with borrowing
            mo = rng.randint(0, 8)
            so = rng.randint(mo + 1, 9)
            mt = rng.randint(2, 9)
            st = rng.randint(1, mt - 1)
            a, b = mt * 10 + mo, st * 10 + so
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
        return 0 <= ans <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Stack the tens and ones. When you add and the ones go past 9, carry a ten. "
                "When you subtract and the top ones are too small, regroup: trade 1 ten for 10 ones. "
                "Example 62 - 47: 2 - 7 won't work, so 6 becomes 5 and 2 becomes 12; 12 - 7 = 5, "
                "5 - 4 = 1 → 15."
            ),
            strategy="Not enough ones? Trade a ten for ten ones.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Add the ones first. If they make 10 or more, carry a ten to the tens column.",
                "Then add the tens (plus any carry).",
            ]
        return [
            "Look at the ones first. Is the top digit big enough to subtract?",
            "If not, borrow 1 ten: shrink the tens digit by 1 and add 10 to the ones.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "+":
            return (
                f"{a} + {b}: ones {a % 10} + {b % 10} = {a % 10 + b % 10}, "
                f"tens {a // 10} + {b // 10}. Total = {a + b}."
            )
        return (
            f"{a} - {b}: trade a ten so the ones become {a % 10 + 10}; "
            f"{a % 10 + 10} - {b % 10} = {a % 10 + 10 - b % 10}. Answer = {a - b}."
        )


register(FactsWithin20())
register(ThreeDigitPlaceValue())
register(AddSubWithin100())
