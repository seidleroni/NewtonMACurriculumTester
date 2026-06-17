"""Grade 3 Measurement & Data skills.

Time and elapsed time, one-step liquid-volume / mass problems, reading scaled
bar & picture graphs and line plots, and area & perimeter of rectangles.
Phase-2 skills attach an image spec in ``payload["image"]`` for presentation;
every answer is still computed in Python so grading never depends on the picture.
"""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer, TimeAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_VOLUME_MASS = (
    ("water", "L", "liters"),
    ("juice", "L", "liters"),
    ("flour", "g", "grams"),
    ("sugar", "g", "grams"),
    ("apples", "kg", "kilograms"),
    ("sand", "kg", "kilograms"),
)
_BAR_TOPICS = (
    ("Books Read", ("Mia", "Leo", "Ava", "Sam")),
    ("Cans Collected", ("Room A", "Room B", "Room C", "Room D")),
    ("Tickets Sold", ("Mon", "Tue", "Wed", "Thu")),
)
_LINE_PLOT_LABELS = (
    ("pencils", "inches"),
    ("ribbons", "centimeters"),
    ("seeds", "millimeters"),
    ("worms", "inches"),
)
_UNIT_SINGULAR = {"inches": "inch", "centimeters": "centimeter", "millimeters": "millimeter"}


def _fmt_time(hour: int, minute: int) -> str:
    return f"{hour}:{minute:02d}"


class TimeAndElapsed(Skill):
    id = "3.MD.A.1"
    slug = "g3-time-elapsed"
    grade = 3
    domain = "Measurement & Data"
    title = "Time & elapsed time"
    max_level = 4
    answer_type = "time"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Find the end time after a duration (one answer type: TimeAnswer). Floor uses
        # 5-minute steps within the hour; then 1-minute steps; then crossing the hour
        # boundary (5-minute, then 1-minute) — the genuinely hard elapsed-time case.
        start_hour = rng.randint(1, 11)  # capped so a one-hour cross never passes 12
        if level <= 1:  # 5-minute steps, no hour crossing
            start_minute = rng.choice(range(0, 60, 5))
            max_steps = (55 - start_minute) // 5
            if max_steps < 1:
                start_minute, max_steps = 0, 11
            duration = 5 * rng.randint(1, max_steps)
        elif level == 2:  # 1-minute steps, no hour crossing
            start_minute = rng.randint(0, 58)
            duration = rng.randint(1, 59 - start_minute)
        elif level == 3:  # 5-minute steps, cross into the next hour
            start_minute = rng.choice(range(0, 60, 5))
            extra = 5 * rng.randint(0, 11)           # minutes into the next hour
            duration = (60 - start_minute) + extra    # total = 60 + extra -> crosses by 1 hour
        else:  # 1-minute steps, cross into the next hour
            start_minute = rng.randint(0, 59)
            extra = rng.randint(0, 59)
            duration = (60 - start_minute) + extra
        total = start_minute + duration
        end_hour = start_hour + total // 60
        end_minute = total % 60
        goes = "minute goes" if duration == 1 else "minutes go"
        prompt = (
            f"It is {_fmt_time(start_hour, start_minute)}. "
            f"{duration} {goes} by. What time is it now? (type it like H:MM)"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=TimeAnswer(end_hour, end_minute),
            payload={
                "start_hour": start_hour,
                "start_minute": start_minute,
                "end_hour": end_hour,
                "end_minute": end_minute,
                "duration": duration,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        total = p["start_minute"] + p["duration"]
        return (
            p["duration"] >= 1
            and 0 <= p["start_minute"] < 60
            and p["end_minute"] == total % 60
            and p["end_hour"] == p["start_hour"] + total // 60
            and 1 <= p["end_hour"] <= 12
            and super().invariant(problem)
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Adding time works like adding minutes on a clock. To find an end time, "
                "add the minutes that pass to the start time. To find how long something "
                "lasts, subtract the start time from the end time. 2:10 plus 20 minutes is "
                "2:30, and from 2:10 to 2:30 is 20 minutes."
            ),
            strategy="End time = start + minutes; length = end - start.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Add the minutes that pass to the start time.",
            "If you pass 60 minutes, move to the next hour and keep the leftover minutes.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        start = _fmt_time(p["start_hour"], p["start_minute"])
        end = _fmt_time(p["end_hour"], p["end_minute"])
        if p["end_hour"] == p["start_hour"]:
            return (
                f"Start at {start} and add {p['duration']} minutes: the minutes become "
                f"{p['start_minute']} + {p['duration']} = {p['end_minute']}, so it is {end}."
            )
        return (
            f"Start at {start} and add {p['duration']} minutes: that passes 60, so move to "
            f"the next hour with {p['end_minute']} minutes left over — it is {end}."
        )


class VolumeMassProblems(Skill):
    id = "3.MD.A.2"
    slug = "g3-volume-mass"
    grade = 3
    domain = "Measurement & Data"
    title = "Liquid volume & mass problems"
    max_level = 5
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        thing, unit, unit_word = rng.choice(_VOLUME_MASS)
        # Add one operation per band: add (small) -> add (bigger) -> +subtract ->
        # +multiply -> +divide. The floor is a single operation, no choice.
        if level <= 2:
            op = "+"
        elif level == 3:
            op = rng.choice(("+", "-"))
        elif level == 4:
            op = rng.choice(("+", "-", "×"))
        else:
            op = rng.choice(("+", "-", "×", "÷"))
        if op == "+":
            if level <= 1:  # gentle floor: single-digit, no carry
                a = rng.randint(2, 8)
                b = rng.randint(1, 9 - a)
            else:
                a, b = rng.randint(5, 60), rng.randint(5, 60)
            ans = a + b
            prompt = (
                f"A jug holds {a} {unit} of {thing} and another holds {b} {unit}. "
                f"How many {unit} of {thing} in all? = ?"
            )
        elif op == "-":
            a = rng.randint(20, 90)
            b = rng.randint(5, a - 1)
            ans = a - b
            prompt = (
                f"A container has {a} {unit} of {thing}. You pour out {b} {unit}. "
                f"How many {unit} of {thing} are left? = ?"
            )
        elif op == "×":
            a = rng.randint(2, 9)
            b = rng.randint(2, 12)
            ans = a * b
            prompt = (
                f"Each bag has {b} {unit} of {thing}. How many {unit} of {thing} "
                f"are in {a} bags? = ?"
            )
        else:  # ÷ — choose a clean whole-number split
            b = rng.randint(2, 9)
            q = rng.randint(2, 12)
            a = b * q
            ans = q
            prompt = (
                f"{a} {unit} of {thing} are shared equally into {b} containers. "
                f"How many {unit} of {thing} are in each container? = ?"
            )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"op": op, "unit": unit, "unit_word": unit_word, "thing": thing},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Volume and mass word problems are one-step problems. Combining amounts "
                "means add; pouring or taking away means subtract; equal groups mean "
                "multiply; sharing equally means divide. Both amounts use the same unit "
                "(grams, kilograms, or liters), so the answer keeps that unit."
            ),
            strategy="Pick add, subtract, multiply, or divide from the story; keep the unit.",
        )

    def hints(self, problem: Problem) -> list[str]:
        op = problem.payload["op"]
        word = {
            "+": "Combining amounts means you add.",
            "-": "Pouring some out means you subtract.",
            "×": "Equal groups (each bag the same) means you multiply.",
            "÷": "Sharing equally means you divide.",
        }[op]
        return [word, f"Keep the unit ({problem.payload['unit']}) on your answer."]

    def worked_example(self, problem: Problem) -> str:
        op = problem.payload["op"]
        unit = problem.payload["unit"]
        ans = problem.answer.value
        verb = {"+": "Add", "-": "Subtract", "×": "Multiply", "÷": "Divide"}[op]
        return f"{verb} the numbers in the story to get {ans} {unit}."


class ReadScaledBarGraph(Skill):
    id = "3.MD.B.3"
    slug = "g3-scaled-bar-graph"
    grade = 3
    domain = "Measurement & Data"
    title = "Scaled bar/picture graphs (read)"
    max_level = 4
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        topic, labels = rng.choice(_BAR_TOPICS)
        # read one bar (scale 2) -> read one bar (bigger scales, 4 cats) -> compare two
        # bars (modest scales) -> compare two bars (large scales). The two-bar subtract
        # is the harder demand, reserved for the top bands.
        if level <= 1:
            scale, n_cats, max_units, ask_more = 2, 3, 5, False
        elif level == 2:
            scale, n_cats, max_units, ask_more = rng.choice((2, 5, 10)), 4, 6, False
        elif level == 3:
            scale, n_cats, max_units, ask_more = rng.choice((2, 5)), 4, 6, True
        else:
            scale, n_cats, max_units, ask_more = rng.choice((5, 10)), 4, 8, True
        cats = list(labels[:n_cats])
        # Each bar's value is a whole multiple of the scale (so the picture is clean).
        counts = {c: scale * rng.randint(1, max_units) for c in cats}
        if ask_more and len(set(counts.values())) == 1:
            # guarantee two different bars so "how many more" is never a trivial 0
            counts[rng.choice(cats)] += scale
        categories = [[c, counts[c]] for c in cats]
        if ask_more:
            a, b = rng.sample(cats, 2)
            while counts[a] == counts[b]:  # a distinct pair now always exists
                a, b = rng.sample(cats, 2)
            if counts[a] < counts[b]:
                a, b = b, a
            ans = counts[a] - counts[b]
            prompt = (
                f"This scaled bar graph shows {topic} (each square = {scale}). "
                f"How many more {a} than {b}? = ?"
            )
            mode = "more"
            extra = {"a": a, "b": b}
        else:
            target = rng.choice(cats)
            ans = counts[target]
            prompt = (
                f"This scaled bar graph shows {topic} (each square = {scale}). "
                f"How many for {target}? = ?"
            )
            mode = "value"
            extra = {"target": target}
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={
                "topic": topic,
                "scale": scale,
                "counts": counts,
                "mode": mode,
                "image": {"kind": "bar_graph", "categories": categories, "scale": scale},
                **extra,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "In a scaled graph each square or picture stands for more than one — the key "
                "tells you how many. Read a bar by counting its squares and multiplying by "
                "the scale. To find 'how many more', read both bars and subtract."
            ),
            strategy="Bar value = squares × scale; 'how many more' = subtract the two bars.",
        )

    def hints(self, problem: Problem) -> list[str]:
        scale = problem.payload["scale"]
        if problem.payload["mode"] == "more":
            a, b = problem.payload["a"], problem.payload["b"]
            return [
                f"Each square is worth {scale}, so read each bar's full value first.",
                f"Subtract the {b} value from the {a} value.",
            ]
        return [
            f"Each square is worth {scale}.",
            f"Count the squares for {problem.payload['target']} and multiply by {scale}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        counts = problem.payload["counts"]
        scale = problem.payload["scale"]
        if problem.payload["mode"] == "more":
            a, b = problem.payload["a"], problem.payload["b"]
            return (
                f"{a} reads {counts[a]} and {b} reads {counts[b]}: "
                f"{counts[a]} - {counts[b]} = {counts[a] - counts[b]} more."
            )
        target = problem.payload["target"]
        squares = counts[target] // scale
        return (
            f"{target} has {squares} squares and each square is {scale}: "
            f"{squares} × {scale} = {counts[target]}."
        )


class ReadLinePlot(Skill):
    id = "3.MD.B.4"
    slug = "g3-line-plot"
    grade = 3
    domain = "Measurement & Data"
    title = "Line plots (read)"
    max_level = 4
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        label, unit = rng.choice(_LINE_PLOT_LABELS)
        # read one stack (small) -> read one stack (bigger plot) -> total across all
        # stacks (small) -> total (bigger plot). Summing every stack is the harder step.
        if level <= 1:
            n_values, max_count, ask_total = 3, 3, False
        elif level == 2:
            n_values, max_count, ask_total = 5, 5, False
        elif level == 3:
            n_values, max_count, ask_total = 3, 3, True
        else:
            n_values, max_count, ask_total = 5, 5, True
        first = rng.randint(1, 4)
        values = [first + i for i in range(n_values)]
        counts = {v: rng.randint(0, max_count) for v in values}
        if sum(counts.values()) == 0:
            counts[values[0]] = 1
        categories = [[str(v), counts[v]] for v in values]
        if ask_total:
            ans = sum(counts.values())
            prompt = (
                f"This line plot shows the length of each of the {label} (in {unit}). "
                f"How many {label} were measured in all? = ?"
            )
            mode = "total"
            target = None
        else:
            # Prefer a value that actually has marks so the question is interesting.
            nonzero = [v for v in values if counts[v] > 0]
            target = rng.choice(nonzero if nonzero else values)
            ans = counts[target]
            unit_word = _UNIT_SINGULAR[unit] if target == 1 else unit
            prompt = (
                f"This line plot shows the length of each of the {label} (in {unit}). "
                f"How many {label} measured {target} {unit_word}? = ?"
            )
            mode = "at_value"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={
                "label": label,
                "unit": unit,
                "mode": mode,
                "target": target,
                "counts": {str(v): counts[v] for v in values},
                "image": {"kind": "bar_graph", "categories": categories, "scale": 1},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A line plot stacks one mark for each measurement above its number on a "
                "scale. To find 'how many measured X', count the marks above X. To find the "
                "total measured, count every mark on the whole plot."
            ),
            strategy="Count marks above one value, or count every mark for the total.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["mode"] == "total":
            return [
                "Every mark stands for one measurement.",
                "Count all the marks across the whole plot and add them up.",
            ]
        return [
            f"Find {problem.payload['target']} {problem.payload['unit']} along the bottom.",
            "Count just the marks stacked above that number.",
        ]

    def worked_example(self, problem: Problem) -> str:
        counts = problem.payload["counts"]
        label = problem.payload["label"]
        if problem.payload["mode"] == "total":
            pieces = " + ".join(str(v) for v in counts.values())
            total = sum(counts.values())
            return f"Add the marks above every value: {pieces} = {total} {label}."
        target = problem.payload["target"]
        unit = problem.payload["unit"]
        ans = problem.answer.value
        return (
            f"Count the marks above {target} {unit}: {ans} {label} measured {target} {unit}."
        )


class AreaUnitSquares(Skill):
    id = "3.MD.C.5"
    slug = "g3-area-unit-squares"
    grade = 3
    domain = "Measurement & Data"
    title = "Area as unit squares"
    max_level = 3
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        # A single strip (count one line) -> a small rectangle -> a large rectangle
        # where one-by-one counting is impractical.
        if level <= 1:
            if rng.random() < 0.5:
                rows, cols = 1, rng.randint(2, 6)
            else:
                rows, cols = rng.randint(2, 6), 1
        elif level == 2:
            rows, cols = rng.randint(2, 4), rng.randint(2, 5)
        else:
            rows, cols = rng.randint(3, 6), rng.randint(4, 8)
        area = rows * cols
        prompt = (
            "This figure is covered with unit squares (each one is 1 square unit). "
            "What is the area? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(area),
            payload={
                "rows": rows,
                "cols": cols,
                "image": {"kind": "grid", "rows": rows, "cols": cols},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        return problem.answer.value == p["rows"] * p["cols"] and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Area is the number of unit squares it takes to cover a flat shape with no "
                "gaps and no overlaps. Each unit square counts as 1 square unit, so the area "
                "is simply how many unit squares fill the figure."
            ),
            strategy="Count every unit square that covers the figure.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Each little square is 1 square unit.",
            "Count all the squares that cover the figure — that is the area.",
        ]

    def worked_example(self, problem: Problem) -> str:
        rows = problem.payload["rows"]
        cols = problem.payload["cols"]
        return (
            f"There are {rows} rows of {cols} squares, so counting them all gives "
            f"{rows} × {cols} = {rows * cols} square units."
        )


class MeasureAreaCounting(Skill):
    id = "3.MD.C.6"
    slug = "g3-measure-area-count"
    grade = 3
    domain = "Measurement & Data"
    title = "Measure area by counting squares"
    max_level = 3
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        # States the rows/columns (cues the multiply strategy). Small -> medium -> large.
        if level <= 1:
            rows, cols = rng.randint(2, 3), rng.randint(2, 4)
        elif level == 2:
            rows, cols = rng.randint(2, 5), rng.randint(3, 7)
        else:
            rows, cols = rng.randint(4, 7), rng.randint(5, 9)
        area = rows * cols
        prompt = f"This rectangle has {rows} rows of {cols} squares. How many squares cover it?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(area),
            payload={
                "rows": rows,
                "cols": cols,
                "image": {"kind": "grid", "rows": rows, "cols": cols},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        return problem.answer.value == p["rows"] * p["cols"] and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When a rectangle is tiled with unit squares, you can count the squares to "
                "find the area. Counting row by row, each row has the same number of squares, "
                "so the area is the number of rows times the squares in each row."
            ),
            strategy="Count the squares — rows × squares-per-row gives the area fast.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            f"Each row has {problem.payload['cols']} squares.",
            f"There are {problem.payload['rows']} rows, so skip-count by "
            f"{problem.payload['cols']}s.",
        ]

    def worked_example(self, problem: Problem) -> str:
        rows = problem.payload["rows"]
        cols = problem.payload["cols"]
        return (
            f"Counting {rows} rows of {cols} squares: {rows} × {cols} = {rows * cols} "
            "square units."
        )


class AreaLengthTimesWidth(Skill):
    id = "3.MD.C.7"
    slug = "g3-area-length-width"
    grade = 3
    domain = "Measurement & Data"
    title = "Area = length × width"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # small direct -> larger direct -> distributive split (always) -> distributive
        # with large factors. The split lands only on bands where length >= 6.
        if level <= 1:
            length, width, distributive = rng.randint(2, 6), rng.randint(2, 6), False
        elif level == 2:
            length, width, distributive = rng.randint(5, 12), rng.randint(3, 9), False
        elif level == 3:
            length, width, distributive = rng.randint(6, 12), rng.randint(3, 9), True
        else:
            length, width, distributive = rng.randint(10, 15), rng.randint(5, 12), True
        area = length * width
        if distributive:
            # Split the length as (b + c), both parts >= 2 (length >= 6 here).
            b = rng.randint(2, length - 2)
            c = length - b
            prompt = (
                f"A rectangle is {length} units long and {width} units wide. Break the "
                f"length into {b} + {c}: the area is {width}×{b} + {width}×{c}. "
                "What is the total area? = ?"
            )
            mode = "distributive"
            extra = {"b": b, "c": c}
        else:
            prompt = (
                f"A rectangle is {length} units long and {width} units wide. "
                "What is its area? = ?"
            )
            mode = "direct"
            extra = {}
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(area),
            payload={"length": length, "width": width, "mode": mode, **extra},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        return problem.answer.value == p["length"] * p["width"] and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "For a rectangle, area = length × width, because the rows of unit squares "
                "are length long and there are width of them. You can also split one side: "
                "a 7-wide rectangle equals a 4-wide piece plus a 3-wide piece (the "
                "distributive property)."
            ),
            strategy="Multiply length × width; you can split a side and add the parts.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["mode"] == "distributive":
            return [
                "Find each smaller rectangle's area, then add them.",
                f"{p['width']}×{p['b']} plus {p['width']}×{p['c']} gives the whole area.",
            ]
        return [
            "Area of a rectangle is length times width.",
            f"Multiply {p['length']} × {p['width']}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        length, width = p["length"], p["width"]
        if p["mode"] == "distributive":
            b, c = p["b"], p["c"]
            return (
                f"{width}×{b} + {width}×{c} = {width * b} + {width * c} = "
                f"{length * width} square units, the same as {length} × {width}."
            )
        return f"Area = length × width = {length} × {width} = {length * width} square units."


class Perimeter(Skill):
    id = "3.MD.D.8"
    slug = "g3-perimeter"
    grade = 3
    domain = "Measurement & Data"
    title = "Perimeter"
    max_level = 4
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # forward (small) -> forward (larger) -> reverse "find the other side" (always)
        # -> reverse with large numbers. The reverse task is the harder demand.
        if level <= 1:
            length, width, reverse = rng.randint(2, 7), rng.randint(2, 7), False
        elif level == 2:
            length, width, reverse = rng.randint(6, 18), rng.randint(3, 15), False
        elif level == 3:
            length, width, reverse = rng.randint(3, 12), rng.randint(2, 10), True
        else:
            length, width, reverse = rng.randint(8, 25), rng.randint(3, 20), True
        perimeter = 2 * (length + width)
        if reverse:
            # Give the perimeter and one side; ask for the other side.
            ans = width
            prompt = (
                f"A rectangle has a perimeter of {perimeter} units. One side is {length} "
                "units long. How long is the side next to it? = ?"
            )
            mode = "reverse"
        else:
            ans = perimeter
            prompt = (
                f"A rectangle is {length} units long and {width} units wide. "
                "What is its perimeter? = ?"
            )
            mode = "forward"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={
                "length": length,
                "width": width,
                "perimeter": perimeter,
                "mode": mode,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        ok = p["perimeter"] == 2 * (p["length"] + p["width"])
        return ok and problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Perimeter is the distance all the way around a shape. A rectangle has two "
                "lengths and two widths, so perimeter = 2 × (length + width). If you already "
                "know the perimeter and one side, take half the perimeter (length + width) "
                "and subtract the known side to find the other."
            ),
            strategy="Perimeter = 2 × (length + width); reverse it with half-perimeter minus a side.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["mode"] == "reverse":
            half = p["perimeter"] // 2
            return [
                "Half the perimeter equals one length plus one width.",
                f"Half of {p['perimeter']} is {half}; subtract the side you know.",
            ]
        return [
            "Add a length and a width, then double it.",
            f"2 × ({p['length']} + {p['width']}) gives the perimeter.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        length, width, perimeter = p["length"], p["width"], p["perimeter"]
        if p["mode"] == "reverse":
            half = perimeter // 2
            return (
                f"Half the perimeter is {perimeter} ÷ 2 = {half}, which is one length plus "
                f"one width. So the other side is {half} - {length} = {width} units."
            )
        return (
            f"Perimeter = 2 × ({length} + {width}) = 2 × {length + width} = {perimeter} units."
        )


register(TimeAndElapsed())
register(VolumeMassProblems())
register(ReadScaledBarGraph())
register(ReadLinePlot())
register(AreaUnitSquares())
register(MeasureAreaCounting())
register(AreaLengthTimesWidth())
register(Perimeter())
