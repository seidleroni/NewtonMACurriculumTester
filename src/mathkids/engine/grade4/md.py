"""Grade 4 Measurement & Data skills.

Unit conversions from a larger unit to a smaller one, one-step measurement word
problems (money change, elapsed time, distance/volume arithmetic), area and
perimeter of rectangles (including an unknown side), reading a fractional line
plot, angles measured as fractions of a circle, and finding an unknown angle by
addition/subtraction. Every answer is computed in Python so grading never depends
on presentation.
"""

from __future__ import annotations

import random
from fractions import Fraction

from mathkids.answers import (
    FractionAnswer,
    IntegerAnswer,
    MoneyAnswer,
)
from mathkids.engine.base import Lesson, Problem, Skill, register

# 1 larger unit = factor smaller units.  (larger, smaller, factor)
_CONVERSIONS = {
    "ft_in": ("feet", "foot", "inches", 12),
    "hr_min": ("hours", "hour", "minutes", 60),
    "min_sec": ("minutes", "minute", "seconds", 60),
    "m_cm": ("meters", "meter", "centimeters", 100),
    "km_m": ("kilometers", "kilometer", "meters", 1000),
    "kg_g": ("kilograms", "kilogram", "grams", 1000),
    "day_hr": ("days", "day", "hours", 24),
    "lb_oz": ("pounds", "pound", "ounces", 16),
    "yd_ft": ("yards", "yard", "feet", 3),
    "L_mL": ("liters", "liter", "milliliters", 1000),
}

_LINE_PLOT_LABELS = (
    ("pencils", "inches"),
    ("ribbons", "inches"),
    ("worms", "inches"),
    ("nails", "inches"),
)


class UnitConversions(Skill):
    id = "4.MD.A.1"
    slug = "g4-unit-conversions"
    grade = 4
    domain = "Measurement & Data"
    title = "Unit conversions (larger to smaller)"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Laddered by the size of the multiplier: x3 -> x12/x16 -> x60/x24 -> x100/x1000.
        if level <= 1:
            keys = ("yd_ft",)
            qty = rng.randint(2, 5)
        elif level == 2:
            keys = ("yd_ft", "ft_in", "lb_oz")
            qty = rng.randint(2, 8)
        elif level == 3:
            keys = ("hr_min", "min_sec", "day_hr")
            qty = rng.randint(2, 9)
        else:
            keys = ("m_cm", "km_m", "kg_g", "L_mL")
            qty = rng.randint(2, 12)
        key = rng.choice(keys)
        plural, singular, smaller, factor = _CONVERSIONS[key]
        unit_word = singular if qty == 1 else plural
        ans = qty * factor
        prompt = (
            f"How many {smaller} are in {qty} {unit_word}? "
            f"({factor} {smaller} = 1 {singular}) = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"qty": qty, "factor": factor, "smaller": smaller, "singular": singular},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        return problem.answer.value == p["qty"] * p["factor"] and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Going from a bigger unit to a smaller one, each big unit is worth many small "
                "ones, so you multiply. There are 12 inches in 1 foot, so 3 feet is 3 × 12 = "
                "36 inches. The number of small units is always larger than the number of big "
                "units."
            ),
            strategy="Larger to smaller: multiply by how many small units fit in one big unit.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        return [
            f"Each {p['singular']} holds {p['factor']} {p['smaller']}.",
            f"Multiply: {p['qty']} × {p['factor']}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"There are {p['factor']} {p['smaller']} in 1 {p['singular']}, so {p['qty']} × "
            f"{p['factor']} = {problem.answer.value} {p['smaller']}."
        )


class MeasurementWordProblems(Skill):
    id = "4.MD.A.2"
    slug = "g4-measurement-word-problems"
    grade = 4
    domain = "Measurement & Data"
    title = "Measurement word problems"
    max_level = 3
    answer_type = "money"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Money change, one new demand per band: change from a dollar (no borrow past
        # $1) -> change from a larger bill -> two-step (buy two items, then make change).
        if level <= 1:
            cost = rng.randint(20, 95)
            paid = 100
            change = paid - cost
            prompt = (
                f"A toy costs {MoneyAnswer.display_of(cost)}. You pay with "
                f"{MoneyAnswer.display_of(paid)}. How much change do you get back?"
            )
            payload = {"variant": "change", "cost": cost, "paid": paid, "change": change}
        elif level == 2:
            cost = rng.randint(105, 480)
            paid = rng.choice((500, 1000))
            change = paid - cost
            prompt = (
                f"A book costs {MoneyAnswer.display_of(cost)}. You pay with "
                f"{MoneyAnswer.display_of(paid)}. How much change do you get back?"
            )
            payload = {"variant": "change", "cost": cost, "paid": paid, "change": change}
        else:
            item_a = rng.randint(75, 260)
            item_b = rng.randint(75, 260)
            subtotal = item_a + item_b
            paid = 1000 if subtotal >= 500 else rng.choice((500, 1000))
            change = paid - subtotal
            prompt = (
                f"A pen costs {MoneyAnswer.display_of(item_a)} and a notebook costs "
                f"{MoneyAnswer.display_of(item_b)}. You pay with "
                f"{MoneyAnswer.display_of(paid)}. How much change do you get back?"
            )
            payload = {
                "variant": "two_step", "item_a": item_a, "item_b": item_b,
                "paid": paid, "change": change,
            }
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=MoneyAnswer(change),
            payload=payload,
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        if p["variant"] == "two_step":
            ok = p["change"] == p["paid"] - p["item_a"] - p["item_b"]
        else:
            ok = p["change"] == p["paid"] - p["cost"]
        return ok and p["change"] >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Making change is a subtraction story: the change is the money you handed "
                "over minus what it cost. When you buy more than one thing, first add the "
                "costs to get the subtotal, then subtract that from the bill you paid. Keep "
                "your answer in dollars and cents."
            ),
            strategy="Add the costs if there are several, then subtract from what you paid.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["variant"] == "two_step":
            return [
                f"First add the two prices: {MoneyAnswer.display_of(p['item_a'])} + "
                f"{MoneyAnswer.display_of(p['item_b'])}.",
                "Then subtract that subtotal from the money you paid.",
            ]
        return [
            "Change is the money you handed over minus what it cost.",
            "Subtract the cost from the amount you paid.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["variant"] == "two_step":
            subtotal = p["item_a"] + p["item_b"]
            return (
                f"Subtotal = {MoneyAnswer.display_of(p['item_a'])} + "
                f"{MoneyAnswer.display_of(p['item_b'])} = {MoneyAnswer.display_of(subtotal)}. "
                f"Change = {MoneyAnswer.display_of(p['paid'])} - "
                f"{MoneyAnswer.display_of(subtotal)} = {MoneyAnswer.display_of(p['change'])}."
            )
        return (
            f"Change = paid - cost = {MoneyAnswer.display_of(p['paid'])} - "
            f"{MoneyAnswer.display_of(p['cost'])} = {MoneyAnswer.display_of(p['change'])}."
        )


class AreaPerimeter(Skill):
    id = "4.MD.A.3"
    slug = "g4-area-perimeter"
    grade = 4
    domain = "Measurement & Data"
    title = "Area & perimeter of rectangles"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # area only -> add the perimeter formula (choice) -> add the inverse (unknown
        # side) -> larger two-digit sides (multi-digit multiply / longer division).
        if level <= 1:
            length, width, mode = rng.randint(2, 9), rng.randint(2, 9), "area"
        elif level == 2:
            length = rng.randint(2, 9)
            width = rng.randint(2, 9)
            mode = rng.choice(("area", "perimeter"))
        elif level == 3:
            length = rng.randint(3, 12)
            width = rng.randint(3, 12)
            mode = rng.choice(("area", "perimeter", "unknown"))
        else:
            length = rng.randint(10, 25)
            width = rng.randint(6, 20)
            mode = rng.choice(("area", "perimeter", "unknown"))
        area = length * width
        perimeter = 2 * (length + width)
        if mode == "area":
            ans = area
            prompt = (
                f"A rectangle is {length} units long and {width} units wide. "
                "What is its area? = ?"
            )
        elif mode == "perimeter":
            ans = perimeter
            prompt = (
                f"A rectangle is {length} units long and {width} units wide. "
                "What is its perimeter? = ?"
            )
        else:  # unknown side from area and one side (divides evenly: area = length × width)
            ans = width
            prompt = (
                f"A rectangle has an area of {area} square units. One side is {length} units "
                "long. How long is the other side? = ?"
            )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={
                "length": length,
                "width": width,
                "area": area,
                "perimeter": perimeter,
                "mode": mode,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        ok = p["area"] == p["length"] * p["width"] and p["perimeter"] == 2 * (
            p["length"] + p["width"]
        )
        return ok and problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Area is the space inside a rectangle: area = length × width. Perimeter is the "
                "distance around it: perimeter = 2 × (length + width). If you know the area and "
                "one side, divide the area by that side to find the missing side, because "
                "length × width = area."
            ),
            strategy="Area = length × width; perimeter = 2 × (length + width); side = area ÷ side.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["mode"] == "area":
            return [
                "Area is the space inside — multiply the two sides.",
                f"Multiply {p['length']} × {p['width']}.",
            ]
        if p["mode"] == "perimeter":
            return [
                "Perimeter goes all the way around: two lengths and two widths.",
                f"Add {p['length']} + {p['width']}, then double it.",
            ]
        return [
            "Area = one side × the other side, so the missing side is area ÷ known side.",
            f"Divide {p['area']} ÷ {p['length']}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        length, width = p["length"], p["width"]
        if p["mode"] == "area":
            return f"Area = length × width = {length} × {width} = {p['area']} square units."
        if p["mode"] == "perimeter":
            return (
                f"Perimeter = 2 × ({length} + {width}) = 2 × {length + width} = "
                f"{p['perimeter']} units."
            )
        return (
            f"The other side = area ÷ known side = {p['area']} ÷ {length} = {width} units, "
            f"because {length} × {width} = {p['area']}."
        )


class LinePlotFractions(Skill):
    id = "4.MD.B.4"
    slug = "g4-line-plot-fractions"
    grade = 4
    domain = "Measurement & Data"
    title = "Line plots with fractions (read)"
    max_level = 4
    answer_type = "fraction"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # read the longest -> like-denominator difference (values <= 1) -> eighths with
        # mixed numbers -> a difference across UNLIKE denominators (quarters and eighths).
        label, unit = rng.choice(_LINE_PLOT_LABELS)
        if level >= 4:
            # Guarantee the extremes have UNLIKE denominators: the shortest is a quarter
            # and the longest is a true eighth, so the difference needs a common bottom.
            lo = Fraction(rng.choice((1, 2)), 4)    # 1/4 or 1/2 (denominator 4 or 2)
            hi = Fraction(rng.choice((13, 15)), 8)  # 13/8 or 15/8 (denominator 8), > 1 > lo
            mid: set[Fraction] = set()
            while len(mid) < 4:  # four more marks strictly between the extremes
                d = rng.choice((4, 8))
                v = Fraction(rng.randint(1, 2 * d), d)
                if lo < v < hi:
                    mid.add(v)
            values = sorted({lo, hi} | mid)
            mode = "difference"
        else:
            if level <= 1:
                denom, n_marks, hi, mode = 4, 3, 4, "longest"
            elif level == 2:
                denom, n_marks, hi, mode = 4, 3, 4, "difference"
            else:  # level 3: eighths, values up to 2
                denom, n_marks, hi, mode = 8, 4, 16, "difference"
            numers = rng.sample(range(1, hi + 1), n_marks)
            values = sorted(Fraction(k, denom) for k in numers)
        diff = values[-1] - values[0]
        data = ", ".join(_frac_text(v) for v in values)
        if mode == "difference":
            answer = FractionAnswer(diff)
            prompt = (
                f"A line plot shows the lengths of {len(values)} {label} (in {unit}): "
                f"{data}. What is the difference in length between the longest and the "
                "shortest? = ?"
            )
        else:
            answer = FractionAnswer(values[-1])
            prompt = (
                f"A line plot shows the lengths of {len(values)} {label} (in {unit}): "
                f"{data}. What is the length of the longest one? = ?"
            )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=answer,
            payload={
                "label": label,
                "unit": unit,
                "shortest": _frac_text(values[0]),
                "longest": _frac_text(values[-1]),
                "mode": mode,
                "unlike": values[0].denominator != values[-1].denominator,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A line plot marks each measurement above its value on a number line, and the "
                "values can be fractions like 1/2, 1/4, or 3/8. To compare lengths, line the "
                "fractions up by their size. The difference between the longest and shortest is "
                "the longest fraction minus the shortest fraction."
            ),
            strategy="Find the biggest and smallest values, then subtract: longest - shortest.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["mode"] == "difference":
            if p.get("unlike"):
                return [
                    "First spot the longest and the shortest measurement.",
                    f"The bottoms are different, so rename to a common bottom (e.g. eighths) "
                    f"before subtracting {p['longest']} - {p['shortest']}.",
                ]
            return [
                "First spot the longest and the shortest measurement in the list.",
                f"Subtract {p['longest']} - {p['shortest']}; the bottoms match, so work the tops.",
            ]
        return [
            "Compare the fractions to find the biggest one.",
            "The longest is the largest fraction in the list.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["mode"] == "difference":
            return (
                f"The longest is {p['longest']} and the shortest is {p['shortest']}, so the "
                f"difference is {p['longest']} - {p['shortest']} = {problem.answer.display}."
            )
        return f"Comparing the fractions, the longest measurement is {problem.answer.display}."


class AngleFractionsOfCircle(Skill):
    id = "4.MD.C.5"
    slug = "g4-angle-fractions-circle"
    grade = 4
    domain = "Measurement & Data"
    title = "Angles as fractions of a circle"
    max_level = 3
    answer_type = "fraction"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # A D-degree angle is D/360 of a circle. Laddered by how hard D/360 is to
        # simplify: easy unit fractions -> other simple fractions -> non-obvious ones.
        if level <= 1:
            degrees = rng.choice((90, 180))       # -> 1/4, 1/2
        elif level == 2:
            degrees = rng.choice((60, 120, 270))  # -> 1/6, 1/3, 3/4
        else:
            degrees = rng.choice((30, 45, 135, 150))  # -> 1/12, 1/8, 3/8, 5/12
        value = Fraction(degrees, 360)
        prompt = (
            f"What fraction of a full circle (360°) is a {degrees}° angle? "
            "(give a fraction) = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={"variant": "fraction", "degrees": degrees},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        return (
            problem.answer.value == Fraction(p["degrees"], 360) and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A full circle is 360 degrees. A D-degree angle is D out of 360 of the circle, "
                "which is the fraction D/360 — then simplify. A right angle of 90° is "
                "90/360 = 1/4 of a circle; a 60° angle is 60/360 = 1/6 of a circle."
            ),
            strategy="Put the angle over 360, then simplify: a D° angle is D/360 of a turn.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        return [
            "A full circle is 360 degrees, so put the angle over 360.",
            f"Write {p['degrees']}/360, then simplify.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        return (
            f"A full circle is 360°, so a {p['degrees']}° angle is {p['degrees']}/360 = "
            f"{problem.answer.display} of the circle."
        )


class UnknownAngle(Skill):
    id = "4.MD.C.7"
    slug = "g4-unknown-angle"
    grade = 4
    domain = "Measurement & Data"
    title = "Angle addition (find unknown angle)"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # right-angle two-part split -> straight angle -> full turn -> three-part (the
        # only level that needs adding the two known parts before subtracting).
        if level == 4:
            whole = rng.choice((180, 360))
            p1 = rng.randint(20, whole // 2 - 10)
            p2 = rng.randint(20, whole - p1 - 10)
            missing = whole - p1 - p2
            prompt = (
                f"Three angles together make {whole}°. Two of them measure {p1}° and {p2}°. "
                "What is the third angle? = ?"
            )
            return Problem(
                skill_id=self.id,
                level=level,
                prompt=prompt,
                answer=IntegerAnswer(missing),
                payload={"whole": whole, "parts": (p1, p2), "missing": missing},
            )
        if level <= 1:
            whole, part = 90, rng.randint(10, 80)
        elif level == 2:
            whole, part = 180, rng.randint(15, 165)
        else:
            whole, part = 360, rng.randint(20, 340)
        missing = whole - part
        prompt = (
            f"A {whole}° angle is split into two parts. One part is {part}°. "
            "What is the other part? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(missing),
            payload={"whole": whole, "parts": (part,), "missing": missing},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        ok = p["missing"] == p["whole"] - sum(p["parts"]) and p["missing"] >= 0
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When a big angle is split into smaller angles, the parts add up to the whole. "
                "To find a missing part, subtract the parts you know from the whole angle. If a "
                "90° angle splits into 30° and a mystery part, the mystery part is 90 - 30 = 60°."
            ),
            strategy="Parts add to the whole, so missing part = whole - (known parts).",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        known = " + ".join(f"{x}°" for x in p["parts"])
        return [
            "All the parts add up to the whole angle.",
            f"Subtract the known parts ({known}) from {p['whole']}°.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        known_sum = sum(p["parts"])
        known = " + ".join(f"{x}" for x in p["parts"])
        if len(p["parts"]) > 1:
            return (
                f"The parts add to the whole, so the third angle is {p['whole']} - ({known}) = "
                f"{p['whole']} - {known_sum} = {p['missing']}°."
            )
        return (
            f"The two parts add to {p['whole']}°, so the other part is {p['whole']} - "
            f"{known_sum} = {p['missing']}°."
        )


def _frac_text(value: Fraction) -> str:
    """Display a non-negative Fraction as a kid-friendly mixed/simple string."""
    if value.denominator == 1:
        return str(value.numerator)
    if value.numerator < value.denominator:
        return f"{value.numerator}/{value.denominator}"
    whole = value.numerator // value.denominator
    rem = value - whole
    if rem == 0:
        return str(whole)
    return f"{whole} {rem.numerator}/{rem.denominator}"


class ReadProtractor(Skill):
    """4.MD.C.6 — read an angle's measure off a drawn protractor (Phase-3
    image skill; sketching angles stays a paper-and-pencil activity)."""

    id = "4.MD.C.6"
    slug = "g4-read-protractor"
    grade = 4
    domain = "Measurement & Data"
    title = "Read a protractor"
    max_level = 3
    answer_type = "integer"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            angle = rng.randrange(20, 91, 10)   # acute, on a labeled tens tick
        elif level == 2:
            angle = rng.randrange(20, 161, 10)  # adds obtuse, still on tens
        else:
            angle = rng.randrange(15, 166, 5)   # may land between the marked tens (+5)
        prompt = (
            "One ray of the angle points at 0° on the right. Read the scale where the "
            "slanted ray crosses it: how many degrees is this angle?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(angle),
            payload={"angle": angle, "image": {"kind": "protractor", "angle": angle}},
        )

    def invariant(self, problem: Problem) -> bool:
        a = problem.payload["angle"]
        ok = 0 < a < 180 and a % 5 == 0 and problem.answer.value == a
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A protractor measures angles in degrees. Put the center dot on the angle's "
                "corner and line up one ray with 0°. Then read the number where the other "
                "ray crosses the scale. On our protractor 0° is on the right, and the "
                "numbers grow counterclockwise to 180°. Small tick marks count by 10; if "
                "the ray lands halfway between two ticks, add 5."
            ),
            strategy="Start at 0° on one ray, follow the scale around to the other ray.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "One ray sits on 0°. Follow the curved scale up from 0 toward the other ray.",
            "Big ticks are 30s, small ticks are 10s; halfway between small ticks adds 5.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a = problem.payload["angle"]
        tens = a // 10 * 10
        if a % 10 == 0:
            return (
                f"Counting up the scale from 0° by tens, the slanted ray crosses at "
                f"{a}, so the angle measures {a}°."
            )
        return (
            f"The slanted ray lands halfway between {tens} and {tens + 10}, so the "
            f"angle measures {tens} + 5 = {a}°."
        )


register(UnitConversions())
register(ReadProtractor())
register(MeasurementWordProblems())
register(AreaPerimeter())
register(LinePlotFractions())
register(AngleFractionsOfCircle())
register(UnknownAngle())
