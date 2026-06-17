"""Grade 2 — Number & Operations in Base Ten skills."""

from __future__ import annotations

import random

from mathkids.answers import ComparatorAnswer, IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_mc

_PLACE_VALUE = {"hundreds": 100, "tens": 10, "ones": 1}


class ThreeDigitPlaceValue(Skill):
    id = "2.NBT.A.1"
    slug = "g2-nbt-place-value-3"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Three-digit place value"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        n = rng.randint(100, 999)
        # Bands: name the ones digit -> name any digit -> worth (tens/ones) -> worth (any).
        if level <= 1:
            place = "ones"
        elif level == 2:
            place = rng.choice(["hundreds", "tens", "ones"])
        elif level == 3:
            place = rng.choice(["tens", "ones"])
        else:
            place = rng.choice(["hundreds", "tens", "ones"])
        digit = (n // _PLACE_VALUE[place]) % 10
        if level <= 2:
            prompt = f"What digit is in the {place} place of {n}?"
            ans = digit
            mode = "digit"
        else:
            prompt = f"In {n}, how much is the digit in the {place} place worth?"
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
            f"Then multiply it by {_PLACE_VALUE[place]} to see how much it is worth.",
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
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # By 10s (easiest) -> add 5s -> add 100s (must spot which step is in play).
        if level <= 1:
            step = 10
        elif level == 2:
            step = rng.choice((5, 10))
        else:
            step = rng.choice((5, 10, 100))
        # Pick a start that is a multiple of the step and keeps 4 terms within 0..1000.
        max_start = 1000 - 4 * step
        start = rng.randint(0, max_start // step) * step
        shown = (start, start + step, start + 2 * step, start + 3 * step)
        ans = start + 4 * step
        shown_str = ", ".join(str(v) for v in shown)
        prompt = (
            f"Skip-count by {step}s: {shown_str}, ___. What number comes next?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"start": start, "step": step, "shown": list(shown)},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 1000 and super().invariant(problem)

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
        last = problem.payload["shown"][-1]
        return [
            f"Each jump adds {step}.",
            f"Add {step} to the last number, {last}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        step = problem.payload["step"]
        last = problem.payload["shown"][-1]
        return f"Add {step} to the last number: {last} + {step} = {last + step}."


class ReadWriteNumbers(Skill):
    id = "2.NBT.A.3"
    slug = "g2-nbt-read-write"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Read & write numbers to 1,000"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        h = rng.randint(1, 9)
        # Level 1 keeps every place non-zero (no dropped columns to puzzle over);
        # higher levels allow zeros.
        if level <= 1:
            t = rng.randint(1, 9)
            o = rng.randint(1, 9)
        else:
            t = rng.randint(0, 9)
            o = rng.randint(0, 9)
        if level <= 2:
            # Build the number from its expanded form.
            n = h * 100 + t * 10 + o
            hp, tp, op_ = h * 100, t * 10, o
            parts = [str(p) for p in (hp, tp, op_) if p != 0]
            expanded = " + ".join(parts)
            prompt = f"What number is {expanded}?"
            ans = n
            mode = "build"
        else:
            # Fill in one missing addend of the expanded form. Level 3 only hides the
            # tens or ones; level 4 can hide any place (including the hundreds). Never
            # hide a zero place (typing "0" into an expanded-form blank is confusing),
            # so bump the chosen place to a real digit if it came up zero.
            idx = rng.choice([1, 2] if level == 3 else [0, 1, 2])
            digits = [h, t, o]
            if digits[idx] == 0:
                digits[idx] = rng.randint(1, 9)
            h, t, o = digits
            n = h * 100 + t * 10 + o
            hp, tp, op_ = h * 100, t * 10, o
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
            # Differ in the hundreds digit so the comparison is clear at a glance.
            b = rng.randint(100, 999)
            while b // 100 == a // 100:
                b = rng.randint(100, 999)
        elif level == 2:
            # Same hundreds, different tens: the answer is decided at the tens place.
            at = (a // 10) % 10
            bt = rng.choice([d for d in range(10) if d != at])
            b = (a // 100) * 100 + bt * 10 + rng.randint(0, 9)
        else:
            # Any pair — may require comparing all the way down to the ones.
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
    max_level = 5
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:  # two-digit + one-digit, no regrouping
            ao = rng.randint(0, 8)
            at = rng.randint(1, 8)
            b = rng.randint(1, 9 - ao)  # single-digit, ones never reach 10
            a = at * 10 + ao
            op, ans = "+", a + b
        elif level == 2:  # two-digit + two-digit, no regrouping (the old level 1)
            ao = rng.randint(0, 4)
            bo = rng.randint(0, 9 - ao)
            at = rng.randint(1, 7)
            bt = rng.randint(1, 8 - at)
            a, b = at * 10 + ao, bt * 10 + bo
            op, ans = "+", a + b
        elif level == 3:  # addition where the ones MIGHT carry (not forced)
            ao = rng.randint(0, 9)
            bo = rng.randint(0, 9)
            at = rng.randint(1, 4)
            bt = rng.randint(1, 4)
            a, b = at * 10 + ao, bt * 10 + bo
            op, ans = "+", a + b
        elif level == 4:  # addition with FORCED regrouping (the old level 2)
            ao = rng.randint(1, 9)
            bo = rng.randint(10 - ao, 9)
            at = rng.randint(1, 7)
            bt = rng.randint(1, 8 - at)
            a, b = at * 10 + ao, bt * 10 + bo
            op, ans = "+", a + b
        else:  # subtraction with borrowing (the old level 3)
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
    max_level = 5
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Ease in the count of addends and their size: 2 small -> 3 small -> 3 bigger
        # -> 4 bigger -> 4 biggest.
        if level <= 1:
            count, hi = 2, 19
        elif level == 2:
            count, hi = 3, 19
        elif level == 3:
            count, hi = 3, 25
        elif level == 4:
            count, hi = 4, 25
        else:
            count, hi = 4, 30
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
    max_level = 5
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # A real ramp (the old version ignored `level` entirely): no-regroup addition
        # -> addition where only the ones carry -> full addition -> no-borrow
        # subtraction -> subtraction with borrowing.
        if level <= 1:
            h1 = rng.randint(1, 8); h2 = rng.randint(1, 9 - h1)
            t1 = rng.randint(0, 9); t2 = rng.randint(0, 9 - t1)
            o1 = rng.randint(0, 9); o2 = rng.randint(0, 9 - o1)
            a, b = h1 * 100 + t1 * 10 + o1, h2 * 100 + t2 * 10 + o2
            op, ans = "+", a + b
        elif level == 2:
            h1 = rng.randint(1, 8); h2 = rng.randint(1, 9 - h1)
            t1 = rng.randint(0, 4); t2 = rng.randint(0, 8 - t1)  # tens stay safe even with a carry
            o1 = rng.randint(0, 9); o2 = rng.randint(0, 9)        # ones may pass 9
            a, b = h1 * 100 + t1 * 10 + o1, h2 * 100 + t2 * 10 + o2
            op, ans = "+", a + b
        elif level == 3:
            # Full addition, regrouping unconstrained.
            a = rng.randint(100, 800)
            b = rng.randint(100, 1000 - a)
            op, ans = "+", a + b
        elif level == 4:
            # Subtraction, no borrowing; hundreds strictly greater so a > b (never a
            # trivial zero) and every minuend column >= its subtrahend column.
            hs = rng.randint(1, 8); ts = rng.randint(0, 9); os_ = rng.randint(0, 9)
            hm = rng.randint(hs + 1, 9); tm = rng.randint(ts, 9); om = rng.randint(os_, 9)
            a, b = hm * 100 + tm * 10 + om, hs * 100 + ts * 10 + os_
            op, ans = "-", a - b
        else:
            # Subtraction that FORCES a borrow (the hardest): the subtrahend's ones digit
            # is larger than the minuend's, and its hundreds digit is smaller so a > b.
            hm = rng.randint(2, 9); tm = rng.randint(0, 9); om = rng.randint(0, 8)
            hs = rng.randint(1, hm - 1); ts = rng.randint(0, 9); os_ = rng.randint(om + 1, 9)
            a, b = hm * 100 + tm * 10 + om, hs * 100 + ts * 10 + os_
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
        # Single +/-10 -> single +/-100 -> mixed (kid must spot which column to change).
        if level <= 1:
            step = 10
        elif level == 2:
            step = 100
        else:
            step = rng.choice((10, 100))
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


class ExplainStrategy(Skill):
    """2.NBT.B.9 — explain *why* an add/subtract strategy works (Phase-3
    multiple-choice reframe of an open-reasoning standard)."""

    id = "2.NBT.B.9"
    slug = "g2-nbt-explain-strategy"
    grade = 2
    domain = "Number & Operations in Base Ten"
    title = "Why strategies work"
    max_level = 2
    answer_type = "multiple_choice"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            variant = rng.choice(("break_apart", "compensation"))
        else:
            variant = rng.choice(("count_up", "same_change"))
        return getattr(self, f"_{variant}")(rng)

    def _break_apart(self, rng: random.Random) -> Problem:
        a = rng.randint(21, 78)
        b = rng.randint(21, 78)
        ta, oa = a // 10 * 10, a % 10
        tb, ob = b // 10 * 10, b % 10
        prompt = (
            f"To add {a} + {b}, Maya first adds the tens: {ta} + {tb} = {ta + tb}. "
            f"Then the ones: {oa} + {ob} = {oa + ob}. Last she adds "
            f"{ta + tb} + {oa + ob}. Why does her way work?"
        )
        answer = shuffled_mc(
            rng,
            "Splitting each number into tens and ones keeps the same total — "
            "every ten and every one still gets added.",
            (
                "Adding the tens first makes the answer bigger.",
                "It only works when the ones add up to less than 10.",
                "Tens are worth more than ones, so the ones do not matter.",
            ),
        )
        return Problem(
            skill_id=self.id, level=1, prompt=prompt, answer=answer,
            payload={"variant": "break_apart", "a": a, "b": b},
        )

    def _compensation(self, rng: random.Random) -> Problem:
        a = rng.randint(25, 75)
        b = rng.choice((18, 19, 28, 29, 38, 39, 48, 49))
        b_round = (b // 10 + 1) * 10
        diff = b_round - b
        prompt = (
            f"To add {a} + {b}, Leo adds {a} + {b_round} = {a + b_round}, "
            f"then subtracts {diff}. Why does he subtract {diff}?"
        )
        answer = shuffled_mc(
            rng,
            f"{b_round} is {diff} more than {b}, so his sum is {diff} too big — "
            f"taking {diff} away fixes it.",
            (
                f"{b_round} is {diff} less than {b}, so he should add {diff} more instead.",
                "You always subtract after you add.",
                f"Subtracting {diff} makes the answer end in zero.",
            ),
        )
        return Problem(
            skill_id=self.id, level=1, prompt=prompt, answer=answer,
            payload={"variant": "compensation", "a": a, "b": b, "diff": diff},
        )

    def _count_up(self, rng: random.Random) -> Problem:
        d = rng.randint(38, 79)
        gap = rng.choice((4, 5, 6, 7, 8, 9, 11, 12, 13))  # never a multiple of 10
        c = d + gap
        prompt = (
            f"To find {c} − {d}, Ana starts at {d} and counts up to {c}. "
            f"She counted up {gap}. Why is {gap} the answer to {c} − {d}?"
        )
        answer = shuffled_mc(
            rng,
            f"Subtraction finds the gap between two numbers, and counting up "
            f"from {d} to {c} measures that gap.",
            (
                "Counting up always gives a bigger answer than subtracting.",
                "It only works when both numbers end in the same digit.",
                "Adding and subtracting are the same thing.",
            ),
        )
        return Problem(
            skill_id=self.id, level=2, prompt=prompt, answer=answer,
            payload={"variant": "count_up", "c": c, "d": d, "gap": gap},
        )

    def _same_change(self, rng: random.Random) -> Problem:
        d = rng.choice((28, 29, 38, 39, 48, 49, 58, 59))
        c = d + rng.randint(15, 35)
        k = 10 - d % 10
        prompt = (
            f"To find {c} − {d}, Sam changes it to {c + k} − {d + k}. "
            f"Why is the answer still the same?"
        )
        answer = shuffled_mc(
            rng,
            f"He added {k} to both numbers, and moving both up by the same "
            f"amount keeps the gap between them the same.",
            (
                f"Adding {k} to both numbers makes the answer {2 * k} bigger.",
                f"It works because {d + k} ends in zero, and zeros do not count.",
                "You may change one number as long as it is the smaller one.",
            ),
        )
        return Problem(
            skill_id=self.id, level=2, prompt=prompt, answer=answer,
            payload={"variant": "same_change", "c": c, "d": d, "k": k},
        )

    def invariant(self, problem: Problem) -> bool:
        opts = problem.answer.options
        ok = len(set(opts)) == len(opts) and 0 <= problem.answer.correct_index < len(opts)
        p = problem.payload
        if p["variant"] == "compensation":
            ok = ok and (p["b"] + p["diff"]) % 10 == 0
        if p["variant"] == "count_up":
            ok = ok and p["c"] - p["d"] == p["gap"] and p["gap"] % 10 != 0
        if p["variant"] == "same_change":
            ok = ok and (p["d"] + p["k"]) % 10 == 0
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Good adding and subtracting tricks all work for a reason. You can split "
                "numbers into tens and ones, because every part still gets counted. You can "
                "round a number up to make it friendly, as long as you take the extra back "
                "off. And a subtraction is really the gap between two numbers — sliding both "
                "numbers up or down together never changes that gap."
            ),
            strategy="Ask: did every part still get counted, and did the gap stay the same?",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "A strategy is fair if the total (or the gap) never changes.",
            "Check each choice: would the answer come out the same, or different?",
        ]

    def worked_example(self, problem: Problem) -> str:
        correct = problem.answer.options[problem.answer.correct_index]
        return f"The right reason: {correct}"


register(ThreeDigitPlaceValue())
register(SkipCount())
register(ReadWriteNumbers())
register(CompareThreeDigit())
register(AddSubWithin100())
register(AddFourTwoDigit())
register(AddSubWithin1000())
register(AddSubTenHundred())
register(ExplainStrategy())
