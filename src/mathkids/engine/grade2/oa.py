"""Grade 2 — Operations & Algebraic Thinking skills."""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer, WordAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_NAMES = (
    "Ava", "Ben", "Cara", "Diego", "Emma", "Finn", "Grace", "Hugo",
    "Iris", "Jack", "Kira", "Leo", "Maya", "Noah", "Omar", "Priya",
    "Quinn", "Rosa", "Sam", "Tara",
)
_ITEMS = (
    "stickers", "marbles", "crayons", "shells", "blocks", "apples",
    "buttons", "pennies", "cards", "beads",
)


class AddSubWordProblems(Skill):
    id = "2.OA.A.1"
    slug = "g2-word-problems"
    grade = 2
    domain = "Operations & Algebraic Thinking"
    title = "Add & subtract word problems within 100"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        name = rng.choice(_NAMES)
        item = rng.choice(_ITEMS)
        if level <= 1:
            # One-step join or take-from, result unknown.
            if rng.random() < 0.5:
                a = rng.randint(5, 45)
                b = rng.randint(5, 100 - a)
                ans = a + b
                prompt = (
                    f"{name} has {a} {item}. Then {name} gets {b} more {item}. "
                    f"How many {item} does {name} have now?"
                )
            else:
                a = rng.randint(20, 99)
                b = rng.randint(1, a)
                ans = a - b
                prompt = (
                    f"{name} has {a} {item}. {name} gives away {b} {item}. "
                    f"How many {item} are left?"
                )
            kind = "one_step"
        elif level == 2:
            # One-step with the start unknown (work backwards).
            if rng.random() < 0.5:
                start = rng.randint(5, 60)
                change = rng.randint(5, 100 - start)
                total = start + change
                ans = start
                prompt = (
                    f"{name} got {change} more {item} and then had {total} {item}. "
                    f"How many {item} did {name} start with?"
                )
                kind = "start_unknown_add"
            else:
                start = rng.randint(20, 99)
                change = rng.randint(1, start - 1)
                left = start - change
                ans = start
                prompt = (
                    f"{name} gave away {change} {item} and had {left} {item} left. "
                    f"How many {item} did {name} start with?"
                )
                kind = "start_unknown_sub"
        else:
            # Two-step story problem, total stays within 100.
            a = rng.randint(10, 40)
            b = rng.randint(5, 100 - a)
            c = rng.randint(1, a + b)
            ans = a + b - c
            prompt = (
                f"{name} had {a} {item}. {name} found {b} more {item}, "
                f"then used {c} {item}. How many {item} does {name} have now?"
            )
            kind = "two_step"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"kind": kind, "item": item, "name": name},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Read the story and decide if things are coming together (add) or going "
                "away (take away/subtract). Find the numbers, choose the operation, then "
                "solve. If the missing number is the start, work backwards: undo the "
                "change. Two-step problems: solve the first part, then use that answer in "
                "the second part."
            ),
            strategy="Decide add or subtract, then solve one step at a time.",
        )

    def hints(self, problem: Problem) -> list[str]:
        kind = problem.payload["kind"]
        if kind == "one_step":
            return [
                "Did the amount grow (add) or shrink (take away)?",
                "Pull out the two numbers and do that one operation.",
            ]
        if kind.startswith("start_unknown"):
            return [
                "The missing number is what we started with.",
                "Work backwards: undo the change to get back to the start.",
            ]
        return [
            "This is a two-step story — do the first change, then the second.",
            "Add what was found, then subtract what was used.",
        ]

    def worked_example(self, problem: Problem) -> str:
        return (
            f"Read carefully, choose add or subtract, and solve step by step. "
            f"The answer is {problem.answer.value}."
        )


class FactsWithin20(Skill):
    id = "2.OA.B.2"
    slug = "g2-oa-facts-20"
    grade = 2
    domain = "Operations & Algebraic Thinking"
    title = "Add & subtract facts within 20"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(1, 9), rng.randint(1, 9)
            op, ans = "+", a + b
        elif level == 2:
            if rng.random() < 0.5:
                a, b = rng.randint(1, 9), rng.randint(1, 9)
                op, ans = "+", a + b
            else:
                a = rng.randint(2, 20)
                b = rng.randint(1, a)
                op, ans = "-", a - b
        else:  # bridging-ten facts (the tricky ones)
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

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 20 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "These are the add and subtract facts up to 20 — worth knowing by heart. "
                "For the tricky ones, make a ten: 8 + 7 is 8 + 2 (that makes 10) and 5 more "
                "= 15. To subtract across ten, count up: 13 - 6 is 6 up to 10 (that's 4), "
                "then 3 more = 7."
            ),
            strategy="Make a ten, then add or count up the rest.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Can you make a 10 first? Take from one number to round the other up to 10.",
                f"Try: {problem.payload['a']} + {problem.payload['b']} — fill up to 10, "
                "then add what's left.",
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


class OddEven(Skill):
    id = "2.OA.C.3"
    slug = "g2-odd-even"
    grade = 2
    domain = "Operations & Algebraic Thinking"
    title = "Odd & even numbers"
    max_level = 2
    answer_type = "word"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1 or rng.random() < 0.6:
            n = rng.randint(1, 20)
            word = "even" if n % 2 == 0 else "odd"
            return Problem(
                skill_id=self.id,
                level=level,
                prompt=f"Is {n} odd or even?",
                answer=WordAnswer(word),
                payload={"kind": "odd_even", "n": n},
            )
        # Doubles / halving variant: half of an even number.
        half = rng.randint(1, 10)
        n = half * 2
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"What is half of {n}?",
            answer=IntegerAnswer(half),
            payload={"kind": "half", "n": n, "half": half},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "An even number can be split into two equal groups with nothing left over "
                "(2, 4, 6, 8...). An odd number always has one left over (1, 3, 5, 7...). "
                "A quick check: look at the last digit — 0, 2, 4, 6, 8 means even. Even "
                "numbers are doubles, so half of an even number is a whole number."
            ),
            strategy="Even = splits in two evenly; check the last digit.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["kind"] == "half":
            n = problem.payload["n"]
            return [
                f"Split {n} into two equal groups.",
                "Half means one of two equal parts — what doubles to make this number?",
            ]
        return [
            "Try to split the number into two equal groups.",
            "Look at the last digit: 0, 2, 4, 6, 8 is even; 1, 3, 5, 7, 9 is odd.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        if problem.payload["kind"] == "half":
            half = problem.payload["half"]
            return f"{n} splits into {half} and {half}, so half of {n} = {half}."
        word = problem.answer.value
        if word == "even":
            return f"{n} splits into two equal groups with none left over, so {n} is even."
        return f"{n} leaves one left over when split in two, so {n} is odd."


class ArraysRepeatedAddition(Skill):
    id = "2.OA.C.4"
    slug = "g2-arrays"
    grade = 2
    domain = "Operations & Algebraic Thinking"
    title = "Repeated addition with arrays"
    max_level = 3
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        low = 1 if level <= 1 else 2
        rows = rng.randint(low, 5)
        cols = rng.randint(low, 5)
        total = rows * cols
        if level >= 3 and rng.random() < 0.5:
            prompt = (
                f"This array has {rows} rows of {cols}. Write it as repeated addition "
                f"and find the total. How many dots in all?"
            )
        else:
            prompt = (
                f"Look at the array: {rows} rows with {cols} in each row. "
                f"How many dots are there in all?"
            )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(total),
            payload={
                "rows": rows,
                "cols": cols,
                "image": {"kind": "array", "rows": rows, "cols": cols},
            },
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "An array is rows and columns of objects. Each row has the same number, so "
                "you can add that number once for each row. 3 rows of 4 means 4 + 4 + 4 = "
                "12. Repeated addition like this is the start of multiplication."
            ),
            strategy="Add the row amount once for each row.",
        )

    def hints(self, problem: Problem) -> list[str]:
        rows, cols = problem.payload["rows"], problem.payload["cols"]
        return [
            f"Each of the {rows} rows has {cols} dots.",
            f"Add {cols} a total of {rows} times (skip-count by {cols}).",
        ]

    def worked_example(self, problem: Problem) -> str:
        rows, cols = problem.payload["rows"], problem.payload["cols"]
        terms = " + ".join([str(cols)] * rows)
        return f"{rows} rows of {cols}: {terms} = {rows * cols} dots."


register(AddSubWordProblems())
register(FactsWithin20())
register(OddEven())
register(ArraysRepeatedAddition())
