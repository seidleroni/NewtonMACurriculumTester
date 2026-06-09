"""Grade 4 Number & Operations in Base Ten skills.

Covers place-value structure (a digit is worth ten times the one to its right),
reading / writing / comparing numbers to 1,000,000, rounding to any place,
multi-digit addition and subtraction, multi-digit multiplication, and dividing a
multi-digit number by a single digit with a remainder.
"""

from __future__ import annotations

import random

from mathkids.answers import (
    ComparatorAnswer,
    IntegerAnswer,
    QuotientRemainderAnswer,
)
from mathkids.engine.base import Lesson, Problem, Skill, register

_PLACE_NAMES = {
    1: "ones",
    10: "tens",
    100: "hundreds",
    1000: "thousands",
    10000: "ten-thousands",
    100000: "hundred-thousands",
}


def _group(n: int) -> str:
    """Format an integer with thousands separators, e.g. 6250 -> '6,250'."""
    return f"{n:,}"


def _round_to(n: int, place: int) -> int:
    """Round n to the nearest `place` (a power of ten); a tie rounds up."""
    rem = n % place
    return n - rem if rem < place // 2 else n - rem + place


class DigitTenTimes(Skill):
    id = "4.NBT.A.1"
    slug = "g4-place-value-10x"
    grade = 4
    domain = "Number & Operations in Base Ten"
    title = "Digit is 10x the place to its right"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # How many digits / how big a place value to reach into.
        if level <= 1:
            places = (1, 10, 100)
        elif level == 2:
            places = (10, 100, 1000)
        else:
            places = (100, 1000, 10000, 100000)
        digit = rng.randint(1, 9)

        if rng.random() < 0.5:
            # "What is the value of the 6 in 6,250?" -> 6000
            place = rng.choice(places)
            others = self._wrap_digit(place, digit, rng)
            value = digit * place
            prompt = (
                f"What is the value of the {digit} in {_group(others)}?"
            )
            payload = {"kind": "value", "digit": digit, "place": place, "n": others}
        else:
            # "The 7 in the tens place is 10 times the 7 in which place?" -> ones
            # Asked numerically: value of the same digit one place to the right.
            # Only choose places that have a real place to their right (>= tens).
            place = rng.choice([p for p in places if p >= 10])
            right_place = place // 10
            value = digit * right_place
            prompt = (
                f"The {digit} in the {_PLACE_NAMES[place]} place is 10 times "
                f"{'an' if digit == 8 else 'a'} {digit} "
                f"in the {_PLACE_NAMES[right_place]} place. "
                f"What is the value of that {digit} in the "
                f"{_PLACE_NAMES[right_place]} place?"
            )
            payload = {
                "kind": "ten_times",
                "digit": digit,
                "place": place,
                "right_place": right_place,
            }
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(value),
            payload=payload,
        )

    @staticmethod
    def _wrap_digit(place: int, digit: int, rng: random.Random) -> int:
        """Build a number whose digit at `place` is exactly `digit` (and unique)."""
        n = digit * place
        # Fill the lower places with digits that are never equal to `digit`,
        # so the prompt is unambiguous about which `digit` is meant.
        p = place // 10
        while p >= 1:
            choices = [d for d in range(0, 10) if d != digit]
            n += rng.choice(choices) * p
            p //= 10
        return n

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "In our number system each place is worth ten times the place just to its "
                "right: ones, tens, hundreds, thousands, and so on. So the 6 in 6,250 sits "
                "in the thousands place and is worth 6 × 1,000 = 6,000, while the 5 sits in "
                "the tens place and is worth 5 × 10 = 50. Moving a digit one place left makes "
                "it ten times as big; one place right makes it one tenth as big."
            ),
            strategy="Name the place, then multiply the digit by that place value.",
        )

    def hints(self, problem: Problem) -> list[str]:
        digit = problem.payload["digit"]
        if problem.payload["kind"] == "value":
            place = problem.payload["place"]
            return [
                f"Find which place the {digit} sits in (ones, tens, hundreds, ...).",
                f"Multiply {digit} by the value of the {_PLACE_NAMES[place]} place.",
            ]
        right_place = problem.payload["right_place"]
        return [
            "Moving one place to the right makes a digit ten times smaller.",
            f"Multiply {digit} by the value of the {_PLACE_NAMES[right_place]} place.",
        ]

    def worked_example(self, problem: Problem) -> str:
        digit = problem.payload["digit"]
        if problem.payload["kind"] == "value":
            place = problem.payload["place"]
            n = problem.payload["n"]
            return (
                f"In {_group(n)}, the {digit} is in the {_PLACE_NAMES[place]} place, so its "
                f"value is {digit} × {_group(place)} = {_group(digit * place)}."
            )
        right_place = problem.payload["right_place"]
        return (
            f"A {digit} in the {_PLACE_NAMES[right_place]} place is worth "
            f"{digit} × {_group(right_place)} = {_group(digit * right_place)}."
        )


class ReadWriteCompare(Skill):
    id = "4.NBT.A.2"
    slug = "g4-read-write-compare"
    grade = 4
    domain = "Number & Operations in Base Ten"
    title = "Read/write/compare to 1,000,000"
    max_level = 3
    answer_type = "comparator"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = {1: 9999, 2: 99999}.get(level, 999999)
        lo = {1: 1000, 2: 10000}.get(level, 100000)

        if rng.random() < 0.5:
            # Compare two numbers -> ComparatorAnswer
            a = rng.randint(lo, hi)
            b = rng.randint(lo, hi)
            sign = "<" if a < b else (">" if a > b else "=")
            prompt = (
                f"Compare these numbers. Write <, =, or >:  "
                f"{_group(a)} ___ {_group(b)}"
            )
            return Problem(
                skill_id=self.id,
                level=level,
                prompt=prompt,
                answer=ComparatorAnswer(sign),
                payload={"kind": "compare", "a": a, "b": b},
            )

        # Expanded-form fill -> IntegerAnswer
        n = rng.randint(lo, hi)
        parts = self._expanded_parts(n)
        # Hide one nonzero part and ask for its value.
        nonzero = [p for p in parts if p > 0]
        hidden = rng.choice(nonzero)
        shown = [p for p in parts if p != hidden] or [0]
        # If the hidden value repeats (e.g. 5,005), only drop one occurrence.
        if shown == [p for p in parts if p > 0]:
            shown = list(parts)
            shown.remove(hidden)
            shown = [p for p in shown if p > 0] or [0]
        expr = " + ".join(_group(p) for p in shown)
        prompt = (
            f"Fill in the missing part of the expanded form:  "
            f"{expr} + ___ = {_group(n)}"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(hidden),
            payload={"kind": "expanded", "n": n, "hidden": hidden},
        )

    @staticmethod
    def _expanded_parts(n: int) -> list[int]:
        parts = []
        place = 1
        while place <= n:
            digit = (n // place) % 10
            if digit:
                parts.append(digit * place)
            place *= 10
        return parts or [0]

    def invariant(self, problem: Problem) -> bool:
        if problem.payload["kind"] == "compare":
            a, b = problem.payload["a"], problem.payload["b"]
            sign = problem.answer.value
            ok = (sign == "<" and a < b) or (sign == ">" and a > b) or (
                sign == "=" and a == b
            )
            return ok and super().invariant(problem)
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Read big numbers in groups of three from the right: thousands, then ones. "
                "240,135 is 'two hundred forty thousand, one hundred thirty-five'. To compare "
                "two numbers, line them up by place value and check the highest place first; "
                "the first place where the digits differ decides which is larger. Expanded form "
                "writes a number as the sum of each digit's value, e.g. 6,250 = 6,000 + 200 + 50."
            ),
            strategy="Compare from the biggest place down; the first different digit decides.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["kind"] == "compare":
            return [
                "Line the numbers up by place value and compare the leftmost digits first.",
                "The first place where the digits differ tells you which number is greater.",
            ]
        return [
            "Add up the parts you can see, place by place.",
            "The missing part fills the place that is left out of the sum.",
        ]

    def worked_example(self, problem: Problem) -> str:
        if problem.payload["kind"] == "compare":
            a, b = problem.payload["a"], problem.payload["b"]
            sign = problem.answer.value
            rel = {"<": "less than", ">": "greater than", "=": "equal to"}[sign]
            return (
                f"Compare {_group(a)} and {_group(b)} from the biggest place: "
                f"{_group(a)} is {rel} {_group(b)}, so the sign is {sign}."
            )
        n, hidden = problem.payload["n"], problem.payload["hidden"]
        return (
            f"The expanded parts of {_group(n)} must add back to {_group(n)}, "
            f"so the missing part is {_group(hidden)}."
        )


class RoundToAnyPlace(Skill):
    id = "4.NBT.A.3"
    slug = "g4-round-any-place"
    grade = 4
    domain = "Number & Operations in Base Ten"
    title = "Round to any place"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            n = rng.randint(100, 9999)
            place = rng.choice((10, 100))
        elif level == 2:
            n = rng.randint(1000, 99999)
            place = rng.choice((10, 100, 1000))
        else:
            n = rng.randint(10000, 999999)
            place = rng.choice((10, 100, 1000, 10000, 100000))
        ans = _round_to(n, place)
        place_word = {
            10: "ten",
            100: "hundred",
            1000: "thousand",
            10000: "ten thousand",
            100000: "hundred thousand",
        }[place]
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"Round {_group(n)} to the nearest {place_word}. = ?",
            answer=IntegerAnswer(ans),
            payload={"n": n, "place": place, "place_word": place_word},
        )

    def invariant(self, problem: Problem) -> bool:
        place = problem.payload["place"]
        return (
            problem.answer.value % place == 0
            and problem.answer.value >= 0
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To round to a place, look at the digit just to the right of that place. "
                "If it is 5 or more, round up; if it is 4 or less, keep the place digit the "
                "same. Then turn every digit to the right into a zero. Rounding 6,250 to the "
                "nearest hundred: the digit to the right of the hundreds is 5, so round up to "
                "6,300. Rounding 47,820 to the nearest thousand gives 48,000."
            ),
            strategy="Look one place to the right: 5 or more rounds up, 4 or less stays.",
        )

    def hints(self, problem: Problem) -> list[str]:
        place_word = problem.payload["place_word"]
        return [
            f"Find the {place_word}s place, then look at the digit just to its right.",
            "5 or more rounds up; 4 or less keeps it. Then zero out everything to the right.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        place = problem.payload["place"]
        place_word = problem.payload["place_word"]
        next_digit = (n % place) // (place // 10)
        direction = "up" if next_digit >= 5 else "down"
        return (
            f"Round {_group(n)} to the nearest {place_word}: the digit to the right of that "
            f"place is {next_digit}, so round {direction}. Answer = {_group(_round_to(n, place))}."
        )


class AddSubToMillion(Skill):
    id = "4.NBT.B.4"
    slug = "g4-add-sub-million"
    grade = 4
    domain = "Number & Operations in Base Ten"
    title = "Add & subtract to 1,000,000"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a = rng.randint(1000, 9000)
            b = rng.randint(100, 9999 - a) if a < 9999 else rng.randint(100, 999)
            op, ans = "+", a + b
        elif level == 2:
            a = rng.randint(10000, 99999)
            b = rng.randint(1000, a)
            op, ans = "-", a - b
        else:
            if rng.random() < 0.5:
                a = rng.randint(100000, 800000)
                b = rng.randint(1000, 1000000 - a)
                op, ans = "+", a + b
            else:
                a = rng.randint(200000, 999999)
                b = rng.randint(1000, a)
                op, ans = "-", a - b
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"{_group(a)} {op} {_group(b)} = ?",
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        ans = problem.answer.value
        return 0 <= ans <= 1000000 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Stack the numbers so the places line up and work from right to left. "
                "When a column adds to 10 or more, carry to the next column. When you subtract "
                "and the top digit is too small, regroup: trade one from the next column for ten. "
                "The same steps work whether the numbers are in the hundreds or the hundred-thousands."
            ),
            strategy="Line up by place value, work right to left, carry or regroup as needed.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Line up the places and add one column at a time, starting from the ones.",
                "Whenever a column reaches 10 or more, carry the extra to the next column.",
            ]
        return [
            "Line up the places and subtract one column at a time, starting from the ones.",
            "If the top digit is too small, regroup: borrow ten from the next column.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "+":
            return (
                f"{_group(a)} + {_group(b)}: add each column from the right, carrying when a "
                f"column passes 9. Answer = {_group(a + b)}."
            )
        return (
            f"{_group(a)} - {_group(b)}: subtract each column from the right, regrouping when "
            f"the top digit is too small. Answer = {_group(a - b)}."
        )


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
            prompt=f"{_group(a)} × {_group(b)} = ?",
            answer=IntegerAnswer(a * b),
            payload={"a": a, "b": b},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Break a big multiplication into place-value pieces and add them up. "
                "47 × 6 = (40 × 6) + (7 × 6) = 240 + 42 = 282. For a four-digit number times a "
                "single digit, multiply each place (ones, tens, hundreds, thousands) and add. "
                "For two 2-digit numbers, multiply by the tens and the ones, then add the parts."
            ),
            strategy="Split into place-value parts, multiply each, then add.",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b = problem.payload["a"], problem.payload["b"]
        if b < 10:
            return [
                "Break the bigger number into its place-value parts and multiply each.",
                f"Try ({(a // 10) * 10} × {b}) + ({a % 10} × {b}) and add them.",
            ]
        return [
            "Multiply the first number by the tens of the second, then by the ones.",
            "Add those two partial products together.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b = problem.payload["a"], problem.payload["b"]
        if b < 10:
            tens = (a // 10) * 10
            ones = a % 10
            return (
                f"{_group(a)} × {b} = ({tens} × {b}) + ({ones} × {b}) = "
                f"{_group(tens * b)} + {ones * b} = {_group(a * b)}."
            )
        bt = (b // 10) * 10
        bo = b % 10
        return (
            f"{a} × {b} = ({a} × {bt}) + ({a} × {bo}) = "
            f"{_group(a * bt)} + {_group(a * bo)} = {_group(a * b)}."
        )


class DivideFourByOne(Skill):
    id = "4.NBT.B.6"
    slug = "g4-divide-4by1"
    grade = 4
    domain = "Number & Operations in Base Ten"
    title = "Divide 4-digit by 1-digit (quotient & remainder)"
    max_level = 3
    answer_type = "quotient_remainder"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            dividend = rng.randint(20, 99)
        elif level == 2:
            dividend = rng.randint(100, 999)
        else:
            dividend = rng.randint(1000, 9999)
        divisor = rng.randint(2, 9)
        quotient, remainder = divmod(dividend, divisor)
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=(
                f"{_group(dividend)} ÷ {divisor} = ?  "
                f"(give the quotient and remainder, e.g. 123 R 4)"
            ),
            answer=QuotientRemainderAnswer(quotient, remainder),
            payload={"dividend": dividend, "divisor": divisor},
        )

    def invariant(self, problem: Problem) -> bool:
        q = problem.answer.quotient
        r = problem.answer.remainder
        d = problem.payload["divisor"]
        n = problem.payload["dividend"]
        return (
            q * d + r == n
            and 0 <= r < d
            and q >= 0
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Use long division: work from the leftmost digit. Ask how many times the "
                "divisor fits, write that digit of the quotient, subtract, and bring down the "
                "next digit. Keep going to the ones place; whatever is left over is the "
                "remainder. For 437 ÷ 6: 6 goes into 43 seven times (42), remainder 1; bring "
                "down 7 to make 17; 6 goes in twice (12), remainder 5. So 437 ÷ 6 = 72 R 5."
            ),
            strategy="Divide, multiply, subtract, bring down — repeat to the ones place.",
        )

    def hints(self, problem: Problem) -> list[str]:
        divisor = problem.payload["divisor"]
        return [
            f"Start at the left: how many times does {divisor} fit into the first digits?",
            "Subtract, bring down the next digit, and repeat. What is left over is the remainder.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["dividend"]
        d = problem.payload["divisor"]
        q, r = divmod(n, d)
        check = f"{q} × {d}"
        if r:
            return (
                f"{_group(n)} ÷ {d}: working left to right gives a quotient of {q} with "
                f"{r} left over, because {check} + {r} = {_group(n)}. Answer = {q} R {r}."
            )
        return (
            f"{_group(n)} ÷ {d}: it divides evenly into {q}, because {check} = {_group(n)}. "
            f"Answer = {q}."
        )


register(DigitTenTimes())
register(ReadWriteCompare())
register(RoundToAnyPlace())
register(AddSubToMillion())
register(MultiplyMultiDigit())
register(DivideFourByOne())
