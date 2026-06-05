"""Grade 2 — Number & Operations in Base Ten skills."""

from __future__ import annotations

import random

from mathkids.answers import ComparatorAnswer, IntegerAnswer, SequenceAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_PLACE_VALUE = {"hundreds": 100, "tens": 10, "ones": 1}


class ThreeDigitPlaceValue(Skill):
    id = "2.NBT.A.1"
    slug = "g2-nbt-place-value-3"
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

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 900 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "In a 3-digit number, each digit sits in a place: hundreds, tens, ones. "
                "In 348 the 3 means 3 hundreds (300), the 4 means 4 tens (40), and the 8 "
                "means 8 ones (8). The same digit is worth different amounts in different "
                "columns."
            ),
            strategy="Find the column, then multiply the digit by 100, 10, or 1.",
        )

    def hints(self, problem: Problem) -> list[str]:
        place = problem.payload["place"]
        if problem.payload["mode"] == "digit":
            return [
                "The ones are on the far right, then tens, then hundreds.",
                f"Read off the single digit sitting in the {place} column.",
            ]
        return [
            f"First find the digit in the {place} column.",
            f"Then multiply it by {_PLACE_VALUE[place]} to get its value.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        place = problem.payload["place"]
        digit = problem.payload["digit"]
        if problem.payload["mode"] == "digit":
            return f"In {n}, the {place} digit is {digit}."
        pv = _PLACE_VALUE[place]
        return f"In {n}, the {place} digit is {digit}, worth {digit} × {pv} = {digit * pv}."


class SkipCount(Skill):
    id = "2.NBT.A.2"
    slug = "g2-nbt-skip-count"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Skip-count by 5s, 10s, 100s"
    max_level = 3
    answer_type = "sequence"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            step = rng.choice((5, 10))
        elif level == 2:
            step = rng.choice((5, 10, 100))
        else:
            step = 100
        # Pick a start that is a multiple of the step and keeps 3 terms within 0..1000.
        max_start = 1000 - 3 * step
        start = rng.randint(0, max_start // step) * step
        terms = (start + step, start + 2 * step, start + 3 * step)
        prompt = (
            f"Skip-count by {step}s. What are the next three numbers after {start}? "
            f"{start}, ___, ___, ___"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=SequenceAnswer(terms),
            payload={"start": start, "step": step, "terms": list(terms)},
        )

    def invariant(self, problem: Problem) -> bool:
        return all(0 <= t <= 1000 for t in problem.answer.values) and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Skip-counting means jumping by the same amount each time. By 5s: 5, 10, "
                "15, 20. By 10s: 30, 40, 50. By 100s: 200, 300, 400. Each jump adds the "
                "step to the number before it."
            ),
            strategy="Add the step over and over to get the next number each time.",
        )

    def hints(self, problem: Problem) -> list[str]:
        step = problem.payload["step"]
        start = problem.payload["start"]
        return [
            f"Each jump adds {step}.",
            f"Start at {start} and add {step}: {start} + {step} = {start + step}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        start = problem.payload["start"]
        step = problem.payload["step"]
        t1, t2, t3 = problem.payload["terms"]
        return (
            f"Add {step} each time: {start} + {step} = {t1}, {t1} + {step} = {t2}, "
            f"{t2} + {step} = {t3}."
        )


class ReadWriteNumbers(Skill):
    id = "2.NBT.A.3"
    slug = "g2-nbt-read-write"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Read & write numbers to 1,000"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        h = rng.randint(1, 9)
        t = rng.randint(0, 9)
        o = rng.randint(0, 9)
        n = h * 100 + t * 10 + o
        hp, tp, op_ = h * 100, t * 10, o
        if level <= 1:
            # Build the number from its expanded form.
            parts = [str(p) for p in (hp, tp, op_) if p != 0]
            expanded = " + ".join(parts)
            prompt = f"What number is {expanded}?"
            ans = n
            mode = "build"
        else:
            # Fill in one missing addend of the expanded form.
            idx = rng.randint(0, 2)
            pieces = [str(hp), str(tp), str(op_)]
            ans = (hp, tp, op_)[idx]
            pieces[idx] = "?"
            expanded = " + ".join(pieces)
            prompt = f"{n} = {expanded}"
            mode = "fill"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"n": n, "h": hp, "t": tp, "o": op_, "mode": mode},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 1000 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Expanded form breaks a number into its hundreds, tens, and ones added "
                "together. 562 = 500 + 60 + 2. To go the other way, add the parts back up: "
                "300 + 40 + 7 = 347."
            ),
            strategy="Hundreds + tens + ones. Add the parts to make the number.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["mode"] == "build":
            return [
                "Each part tells you a column: hundreds, tens, ones.",
                "Add all the parts together to make one number.",
            ]
        return [
            "The three parts are the hundreds, the tens, and the ones.",
            "Which place is missing? Read that digit of the number, then add its zeros.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        h = problem.payload["h"]
        t = problem.payload["t"]
        o = problem.payload["o"]
        if problem.payload["mode"] == "build":
            return f"{h} + {t} + {o} = {n}."
        missing = problem.answer.value
        return f"{n} breaks apart as {h} + {t} + {o}, so the missing part is {missing}."


class CompareThreeDigit(Skill):
    id = "2.NBT.A.4"
    slug = "g2-nbt-compare-3"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Compare three-digit numbers"
    max_level = 3
    answer_type = "comparator"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        a = rng.randint(100, 999)
        if rng.random() < 0.2:
            b = a  # occasionally equal
        elif level <= 1:
            # Differ in the hundreds digit so the comparison is clear.
            b = rng.randint(100, 999)
            while b // 100 == a // 100:
                b = rng.randint(100, 999)
        else:
            b = rng.randint(100, 999)
        sign = "<" if a < b else ">" if a > b else "="
        prompt = f"Compare with <, =, or >:  {a} ? {b}"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=ComparatorAnswer(sign),
            payload={"a": a, "b": b, "sign": sign},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To compare numbers, line them up by place value and check the biggest "
                "place first. Compare hundreds; if they tie, compare tens; if those tie, "
                "compare ones. The open mouth of < and > always points at the smaller "
                "number."
            ),
            strategy="Compare hundreds first, then tens, then ones.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Look at the hundreds digit of each number first.",
            "If the hundreds match, compare tens; the symbol points at the smaller number.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a = problem.payload["a"]
        b = problem.payload["b"]
        sign = problem.payload["sign"]
        if sign == "=":
            return f"{a} and {b} are the same, so {a} = {b}."
        bigger, smaller = (a, b) if a > b else (b, a)
        return f"Comparing place by place, {bigger} is larger, so {a} {sign} {b}."


class AddSubWithin100(Skill):
    id = "2.NBT.B.5"
    slug = "g2-nbt-add-sub-100"
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
        return 0 <= problem.answer.value <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Stack the tens and ones. When you add and the ones go past 9, carry a ten. "
                "When you subtract and the top ones are too small, regroup: trade 1 ten for "
                "10 ones. Example 62 - 47: 2 - 7 won't work, so 6 becomes 5 and 2 becomes "
                "12; 12 - 7 = 5, 5 - 4 = 1 → 15."
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


class AddFourTwoDigit(Skill):
    id = "2.NBT.B.6"
    slug = "g2-nbt-add-four-2digit"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Add up to four two-digit numbers"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        count = 3 if level <= 1 else 4
        # Cap each addend so 4 numbers stay well within grade range.
        hi = 24 if level <= 1 else 24 if level == 2 else 30
        nums = [rng.randint(10, hi) for _ in range(count)]
        ans = sum(nums)
        prompt = " + ".join(str(x) for x in nums) + " = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"nums": nums},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 200 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To add several numbers, you can group them to make friendly tens, then add "
                "the rest. You can also add the tens of every number, then add all the ones, "
                "then combine. Order doesn't change the total."
            ),
            strategy="Make tens where you can, then add what's left.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Look for two numbers whose ones add up to 10 — add those first.",
            "Add the numbers two at a time, keeping a running total.",
        ]

    def worked_example(self, problem: Problem) -> str:
        nums = problem.payload["nums"]
        running = nums[0]
        steps = [str(nums[0])]
        for x in nums[1:]:
            running += x
            steps.append(f"+ {x} = {running}")
        return f"Add step by step: {' '.join(steps)}."


class AddSubWithin1000(Skill):
    id = "2.NBT.B.7"
    slug = "g2-nbt-add-sub-1000"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Add & subtract within 1,000"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if rng.random() < 0.5:
            # Addition: keep the sum within 1000.
            a = rng.randint(100, 800)
            b = rng.randint(10, 1000 - a)
            op, ans = "+", a + b
        else:
            # Subtraction: minuend >= subtrahend, non-negative result.
            a = rng.randint(150, 999)
            b = rng.randint(10, a)
            op, ans = "-", a - b
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=f"{a} {op} {b} = ?",
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 1000 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Work one place at a time: ones, then tens, then hundreds. Carry a group of "
                "ten or a group of a hundred when a column overflows. When subtracting, "
                "regroup from the next column to the left if the top digit is too small."
            ),
            strategy="Line up the places; carry or regroup one column at a time.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Add ones, then tens, then hundreds; carry whenever a column passes 9.",
                "Keep the columns lined up so each place adds with its match.",
            ]
        return [
            "Start at the ones. If the top is too small, regroup from the tens.",
            "Work left across the places, regrouping a hundred if the tens run short.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        ans = a + b if op == "+" else a - b
        return f"{a} {op} {b}: work the ones, then tens, then hundreds. Answer = {ans}."


class AddSubTenHundred(Skill):
    id = "2.NBT.B.8"
    slug = "g2-nbt-add-sub-10-100"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Mentally add/subtract 10 or 100"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        n = rng.randint(100, 900)
        if level <= 1:
            step = 10
        elif level == 2:
            step = rng.choice((10, 100))
        else:
            step = 100
        # Choose +/- so the result stays in 0..1000.
        options = []
        if n + step <= 1000:
            options.append("+")
        if n - step >= 0:
            options.append("-")
        op = rng.choice(options)
        ans = n + step if op == "+" else n - step
        prompt = f"{n} {op} {step} = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"n": n, "step": step, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 1000 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Adding or subtracting 10 changes only the tens digit by 1. Adding or "
                "subtracting 100 changes only the hundreds digit by 1. The other digits "
                "stay the same. 342 + 10 = 352; 342 + 100 = 442."
            ),
            strategy="Change only the tens digit for 10, or the hundreds digit for 100.",
        )

    def hints(self, problem: Problem) -> list[str]:
        step = problem.payload["step"]
        which = "tens" if step == 10 else "hundreds"
        return [
            f"You only need to change the {which} digit.",
            f"The other digits do not change — just go up or down by 1 in the {which} place.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        step = problem.payload["step"]
        op = problem.payload["op"]
        which = "tens" if step == 10 else "hundreds"
        direction = "up" if op == "+" else "down"
        ans = n + step if op == "+" else n - step
        return f"{n} {op} {step}: move the {which} digit {direction} by 1 → {ans}."


register(ThreeDigitPlaceValue())
register(SkipCount())
register(ReadWriteNumbers())
register(CompareThreeDigit())
register(AddSubWithin100())
register(AddFourTwoDigit())
register(AddSubWithin1000())
register(AddSubTenHundred())
