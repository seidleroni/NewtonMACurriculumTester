"""Grade 2 — Operations & Algebraic Thinking skills."""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_word

_NAMES = (
    "Ava", "Ben", "Cara", "Diego", "Emma", "Finn", "Grace", "Hugo",
    "Iris", "Jack", "Kira", "Leo", "Maya", "Noah", "Omar", "Priya",
    "Quinn", "Rosa", "Sam", "Tara",
)
_ITEMS = (
    "stickers", "marbles", "crayons", "shells", "blocks", "apples",
    "buttons", "pennies", "cards", "beads",
)
_ITEM_SINGULAR = {"pennies": "penny"}  # the rest just drop the trailing "s"


def _noun(n: int, item: str) -> str:
    """The item word agreeing with a count of n (so "1 crayon", not "1 crayons")."""
    if n == 1:
        return _ITEM_SINGULAR.get(item, item[:-1])
    return item


class AddSubWordProblems(Skill):
    id = "2.OA.A.1"
    slug = "g2-word-problems"
    grade = 2
    domain = "Operations & Algebraic Thinking"
    title = "Add & subtract word problems within 100"
    max_level = 5
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        name = rng.choice(_NAMES)
        item = rng.choice(_ITEMS)
        if level <= 2:
            # One-step join or take-from, result unknown. Level 1 is a genuine gentle
            # floor: single-digit numbers with NO carrying or borrowing, so the focus is
            # reading the story and picking the operation. Level 2 opens to within 100.
            if level <= 1:
                join_a = rng.randint(1, 8)
                join_b = rng.randint(1, 9 - join_a)  # sum <= 9, no carry
                take_a = rng.randint(3, 9)           # single-digit minuend, no borrow
            else:
                join_a = rng.randint(5, 45)
                join_b = rng.randint(5, 100 - join_a)
                take_a = rng.randint(20, 99)
            if rng.random() < 0.5:
                a, b = join_a, join_b
                ans = a + b
                prompt = (
                    f"{name} has {a} {item}. Then {name} gets {b} more {_noun(b, item)}. "
                    f"How many {item} does {name} have now?"
                )
            else:
                a = take_a
                b = rng.randint(1, a)
                ans = a - b
                prompt = (
                    f"{name} has {a} {item}. {name} gives away {b} {_noun(b, item)}. "
                    f"How many {item} are left?"
                )
            kind = "one_step"
        elif level <= 4:
            # One-step with the start unknown (work backwards). Level 3 eases in with
            # small numbers; level 4 uses the full within-100 range.
            small = level <= 3
            if rng.random() < 0.5:
                start = rng.randint(2, 9) if small else rng.randint(5, 60)
                change = rng.randint(1, 9) if small else rng.randint(5, 100 - start)
                total = start + change
                ans = start
                prompt = (
                    f"{name} got {change} more {_noun(change, item)} and then had "
                    f"{total} {item}. How many {item} did {name} start with?"
                )
                kind = "start_unknown_add"
            else:
                start = rng.randint(5, 18) if small else rng.randint(20, 99)
                change = rng.randint(1, start - 1)
                left = start - change
                ans = start
                prompt = (
                    f"{name} gave away {change} {_noun(change, item)} and had "
                    f"{left} {_noun(left, item)} left. "
                    f"How many {item} did {name} start with?"
                )
                kind = "start_unknown_sub"
        else:
            # One-step with the *change* unknown (one operation, full range to 100).
            if rng.random() < 0.5:
                start = rng.randint(10, 70)
                total = rng.randint(start + 1, 100)
                ans = total - start  # how many more were added
                prompt = (
                    f"{name} had {start} {item}. {name} got some more {item} and "
                    f"now has {total} {item}. How many {item} did {name} get?"
                )
                kind = "change_unknown_add"
            else:
                start = rng.randint(20, 100)
                left = rng.randint(0, start - 1)
                ans = start - left  # how many were given away
                prompt = (
                    f"{name} had {start} {item} and now has {left} {_noun(left, item)} "
                    f"left. How many {item} did {name} give away?"
                )
                kind = "change_unknown_sub"
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
                "change. If the missing number is the change (how many were added or taken "
                "away), find the gap between the starting and ending amounts."
            ),
            strategy="Decide add or subtract, then solve in one step.",
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
            "The missing number is the change — how many were added or taken away.",
            "Find the gap between the starting amount and the ending amount.",
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
    max_level = 5
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            # Small single-digit addition; the sum never reaches past ten.
            a = rng.randint(1, 5)
            b = rng.randint(1, 9 - a)
            op, ans = "+", a + b
        elif level == 2:
            # Full single-digit addition, still no crossing ten (sum <= 10).
            a = rng.randint(1, 9)
            b = rng.randint(1, 10 - a)
            op, ans = "+", a + b
        elif level == 3:
            # Subtraction without borrowing: a teen minus its ones (e.g. 17 - 5).
            # Comes before make-a-ten addition because no-borrow subtraction is the
            # easier new step.
            a = rng.randint(11, 19)
            b = rng.randint(1, a - 10)
            op, ans = "-", a - b
        elif level == 4:
            # Make-a-ten addition: every sum crosses ten (the harder add facts).
            a = rng.randint(6, 9)
            b = rng.randint(11 - a, 9)
            op, ans = "+", a + b
        else:  # bridging-ten facts both ways (the trickiest)
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
    max_level = 3
    answer_type = "word"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # The halving variant only appears at the top band; lower bands are the
        # classify task, with small numbers at level 1 and the full 1-20 range above.
        if level < 3 or rng.random() < 0.6:
            n = rng.randint(1, 10 if level <= 1 else 20)
            word = "even" if n % 2 == 0 else "odd"
            other = "odd" if word == "even" else "even"
            return Problem(
                skill_id=self.id,
                level=level,
                prompt=f"Is {n} odd or even?",
                answer=shuffled_word(rng, word, (other,)),
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
    max_level = 4
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Grids grow gently: tiny (countable) -> up to 5x5 -> no trivial single rows ->
        # repeated-addition framing.
        if level <= 1:
            low, high = 1, 3
        elif level == 2:
            low, high = 1, 4
        elif level == 3:
            low, high = 2, 5
        else:
            low, high = 2, 6
        rows = rng.randint(low, high)
        cols = rng.randint(low, high)
        total = rows * cols
        row_word = "row" if rows == 1 else "rows"
        if level >= 4 and rng.random() < 0.5:
            prompt = (
                f"This array has {rows} {row_word} of {cols}. Write it as repeated "
                f"addition and find the total. How many dots in all?"
            )
        else:
            prompt = (
                f"Look at the array: {rows} {row_word} with {cols} in each row. "
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
