"""Grade 2 Measurement & Data skills.

Length comparison/word problems, number-line jumps, telling time, money,
and reading line plots / picture & bar graphs. Phase-2 skills attach an image
spec in ``payload["image"]`` for presentation; every answer is computed in
Python so grading never depends on the picture.
"""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer, MoneyAnswer, TimeAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_mc

_UNITS = ("cm", "inches", "feet", "meters")
_LINE_PLOT_LABELS = ("pencils", "books", "marbles", "stickers", "shells")
_GRAPH_TOPICS = (
    ("Favorite Pets", ("Dogs", "Cats", "Fish", "Birds")),
    ("Fruit Picked", ("Apples", "Pears", "Plums", "Grapes")),
    ("Stickers Earned", ("Stars", "Hearts", "Moons", "Suns")),
)


class HowMuchLonger(Skill):
    id = "2.MD.A.4"
    slug = "g2-how-much-longer"
    grade = 2
    domain = "Measurement & Data"
    title = "How much longer"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        unit = rng.choice(_UNITS)
        if level <= 1:
            longer = rng.randint(5, 20)
            shorter = rng.randint(1, longer - 1)
        elif level == 2:
            longer = rng.randint(20, 60)
            shorter = rng.randint(5, longer - 1)
        else:
            longer = rng.randint(50, 99)
            shorter = rng.randint(10, longer - 1)
        diff = longer - shorter
        prompt = (
            f"One ribbon is {longer} {unit} long and another is {shorter} {unit} long. "
            f"How much longer is the longer ribbon? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(diff),
            payload={"longer": longer, "shorter": shorter, "unit": unit},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "To find how much longer one length is than another, subtract the shorter "
                "length from the longer one. Both lengths use the same unit, so you can "
                "compare them directly. 12 cm and 8 cm differ by 12 - 8 = 4 cm."
            ),
            strategy="Subtract the shorter length from the longer length.",
        )

    def hints(self, problem: Problem) -> list[str]:
        longer = problem.payload["longer"]
        shorter = problem.payload["shorter"]
        return [
            "Both lengths use the same unit, so just compare the numbers.",
            f"Subtract: {longer} - {shorter} tells you how much longer it is.",
        ]

    def worked_example(self, problem: Problem) -> str:
        longer = problem.payload["longer"]
        shorter = problem.payload["shorter"]
        unit = problem.payload["unit"]
        return (
            f"The longer ribbon is {longer} {unit} and the shorter is {shorter} {unit}. "
            f"{longer} - {shorter} = {longer - shorter} {unit} longer."
        )


class LengthWordProblems(Skill):
    id = "2.MD.B.5"
    slug = "g2-length-word-problems"
    grade = 2
    domain = "Measurement & Data"
    title = "Length word problems"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        unit = rng.choice(_UNITS)
        add = level <= 1 or (level == 2 and rng.random() < 0.5)
        if add:
            if level <= 1:
                a, b = rng.randint(5, 25), rng.randint(5, 25)
            else:
                a, b = rng.randint(10, 49), rng.randint(10, 50)
            total = a + b
            ans = total
            prompt = (
                f"A walk to the park is {a} {unit} and the walk home is {b} {unit}. "
                f"How many {unit} is the whole trip? = ?"
            )
            op = "+"
        else:
            if level == 2:
                whole = rng.randint(30, 90)
            else:
                whole = rng.randint(40, 99)
            part = rng.randint(5, whole - 1)
            ans = whole - part
            prompt = (
                f"A rope is {whole} {unit} long. You cut off {part} {unit}. "
                f"How many {unit} of rope are left? = ?"
            )
            op = "-"
            a, b = whole, part
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op, "unit": unit},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Length word problems are addition or subtraction in disguise. Putting "
                "two lengths together (a whole trip) means add. Taking some length away "
                "(cutting a rope) means subtract. Keep the same unit the whole time."
            ),
            strategy="Putting together? Add. Taking away? Subtract.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "The two lengths join together, so this is an addition problem.",
                f"Add the two lengths: {problem.payload['a']} + {problem.payload['b']}.",
            ]
        return [
            "Some length is taken away, so this is a subtraction problem.",
            f"Subtract: {problem.payload['a']} - {problem.payload['b']}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a = problem.payload["a"]
        b = problem.payload["b"]
        op = problem.payload["op"]
        unit = problem.payload["unit"]
        if op == "+":
            return f"Add the lengths: {a} + {b} = {a + b} {unit}."
        return f"Subtract what is removed: {a} - {b} = {a - b} {unit}."


class NumberLineJumps(Skill):
    id = "2.MD.B.6"
    slug = "g2-number-line-jumps"
    grade = 2
    domain = "Measurement & Data"
    title = "Sums & differences on a number line"
    max_level = 3
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        ticks = list(range(0, 101, 10))
        start = rng.choice(ticks)
        if level <= 1:
            jump = rng.randint(1, 9)
            up = start + jump <= 100
        elif level == 2:
            jump = rng.choice((10, 20, 30))
            up = rng.random() < 0.5
        else:
            jump = rng.randint(11, 35)
            up = rng.random() < 0.5
        # Keep the result inside 0..100 by choosing a feasible direction.
        if up and start + jump > 100:
            up = False
        if not up and start - jump < 0:
            up = True
        if up:
            result = start + jump
            prompt = (
                f"Start at {start} on the number line and jump forward {jump}. "
                f"Where do you land? = ?"
            )
            op = "+"
        else:
            result = start - jump
            prompt = (
                f"Start at {start} on the number line and jump back {jump}. "
                f"Where do you land? = ?"
            )
            op = "-"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(result),
            payload={
                "start": start,
                "jump": jump,
                "op": op,
                "image": {"kind": "number_line", "start": 0, "end": 100, "step": 10, "mark": start},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A number line turns adding and subtracting into hops. To add, hop to the "
                "right (forward). To subtract, hop to the left (backward). The number you "
                "land on is the answer. Start at 30 and jump forward 20 to land on 50."
            ),
            strategy="Add = hop right, subtract = hop left; read where you land.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["op"] == "+":
            return [
                "Find the start, then hop forward (to the right).",
                f"Count {problem.payload['jump']} forward from {problem.payload['start']}.",
            ]
        return [
            "Find the start, then hop backward (to the left).",
            f"Count {problem.payload['jump']} back from {problem.payload['start']}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        start = problem.payload["start"]
        jump = problem.payload["jump"]
        op = problem.payload["op"]
        result = start + jump if op == "+" else start - jump
        word = "forward" if op == "+" else "back"
        return (
            f"From {start}, hop {word} {jump}: {start} {op} {jump} = {result}. "
            f"You land on {result}."
        )


class TellTime(Skill):
    id = "2.MD.C.7"
    slug = "g2-time"
    grade = 2
    domain = "Measurement & Data"
    title = "Tell time to 5 minutes"
    max_level = 3
    answer_type = "time"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        hour = rng.randint(1, 12)
        choices = (
            [0, 15, 30, 45]
            if level <= 1
            else [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
        )
        minute = rng.choice(choices)
        return Problem(
            skill_id=self.id,
            level=level,
            prompt="What time does the clock show? (type it like H:MM)",
            answer=TimeAnswer(hour, minute),
            payload={"image": {"kind": "clock", "hour": hour, "minute": minute}},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "The short hand points to the hour. The long hand points to the minutes — "
                "count by 5s around the clock (1->5, 2->10, ...)."
            ),
            strategy="Short hand = hour, long hand = minutes (count by 5s).",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Which hand is short? That's the hour.",
            "Count the long hand by 5s to get the minutes.",
        ]

    def worked_example(self, problem: Problem) -> str:
        return (
            "The short hand gives the hour and the long hand the minutes: "
            f"{problem.answer.canonical()}."
        )


class CountMoney(Skill):
    id = "2.MD.C.8"
    slug = "g2-money"
    grade = 2
    domain = "Measurement & Data"
    title = "Money"
    max_level = 3
    answer_type = "money"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            pennies = rng.randint(0, 4)
            nickels = rng.randint(0, 3)
            dimes = rng.randint(0, 4)
            quarters = rng.randint(0, 2)
        elif level == 2:
            pennies = rng.randint(0, 6)
            nickels = rng.randint(0, 5)
            dimes = rng.randint(0, 8)
            quarters = rng.randint(0, 8)
        else:
            pennies = rng.randint(0, 9)
            nickels = rng.randint(0, 9)
            dimes = rng.randint(0, 15)
            quarters = rng.randint(0, 20)
        total = pennies * 1 + nickels * 5 + dimes * 10 + quarters * 25
        # Total must stay under $10 (1000 cents); the level caps already ensure this.
        parts = []
        for count, name in (
            (quarters, "quarter"),
            (dimes, "dime"),
            (nickels, "nickel"),
            (pennies, "penny"),
        ):
            if count:
                if name == "penny":
                    plural = "penny" if count == 1 else "pennies"
                else:
                    plural = name if count == 1 else name + "s"
                parts.append(f"{count} {plural}")
        if not parts:
            parts.append("1 penny")
            pennies, total = 1, 1
        coin_text = ", ".join(parts)
        prompt = f"How much money is this: {coin_text}? = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=MoneyAnswer(total),
            payload={
                "pennies": pennies,
                "nickels": nickels,
                "dimes": dimes,
                "quarters": quarters,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 < problem.answer.cents < 1000 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Each coin is worth a set number of cents: penny 1, nickel 5, dime 10, "
                "quarter 25. To find the total, count the biggest coins first, then add the "
                "rest. Write the total as dollars and cents, like $1.04."
            ),
            strategy="Count quarters, then dimes, nickels, and pennies; add them up.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Remember: penny = 1c, nickel = 5c, dime = 10c, quarter = 25c.",
            "Add the value of each coin, then write it as dollars and cents.",
        ]

    def worked_example(self, problem: Problem) -> str:
        q = problem.payload["quarters"]
        d = problem.payload["dimes"]
        n = problem.payload["nickels"]
        p = problem.payload["pennies"]
        total = q * 25 + d * 10 + n * 5 + p
        return (
            f"{q}x25 + {d}x10 + {n}x5 + {p}x1 = "
            f"{q * 25} + {d * 10} + {n * 5} + {p} = {total} cents = "
            f"{MoneyAnswer(total).canonical()}."
        )


class ReadLinePlot(Skill):
    id = "2.MD.D.9"
    slug = "g2-line-plot-read"
    grade = 2
    domain = "Measurement & Data"
    title = "Line plots (read)"
    max_level = 3
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        label = rng.choice(_LINE_PLOT_LABELS)
        n_values = 3 if level <= 1 else (4 if level == 2 else 5)
        first = rng.randint(1, 4)
        values = [first + i for i in range(n_values)]
        max_count = 3 if level <= 1 else (5 if level == 2 else 7)
        counts = {v: rng.randint(0, max_count) for v in values}
        if all(c == 0 for c in counts.values()):
            counts[values[0]] = 1
        target = rng.choice(values)
        answer = counts[target]
        categories = [[str(v), counts[v]] for v in values]
        prompt = (
            f"This line plot shows how long each of the {label} measured (in inches). "
            f"How many {label} measured {target} inches? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={
                "label": label,
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
                "scale. To answer 'how many measured X?', find X on the bottom and count "
                "the marks stacked above it."
            ),
            strategy="Find the value on the scale, then count the marks above it.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            f"Find {problem.payload['target']} along the bottom of the plot.",
            "Count how many marks are stacked above that number.",
        ]

    def worked_example(self, problem: Problem) -> str:
        target = problem.payload["target"]
        label = problem.payload["label"]
        answer = problem.answer.value
        return (
            f"Look above {target} inches on the line plot and count the marks: "
            f"{answer} {label} measured {target} inches."
        )


class ReadGraph(Skill):
    id = "2.MD.D.10"
    slug = "g2-bar-graph-read"
    grade = 2
    domain = "Measurement & Data"
    title = "Picture & bar graphs (read)"
    max_level = 3
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        topic, labels = rng.choice(_GRAPH_TOPICS)
        n_cats = 3 if level <= 1 else 4
        cats = list(labels[:n_cats])
        max_count = 6 if level <= 1 else (9 if level == 2 else 12)
        counts = {c: rng.randint(1, max_count) for c in cats}
        categories = [[c, counts[c]] for c in cats]
        ask_more = rng.random() < 0.5
        if ask_more:
            a, b = rng.sample(cats, 2)
            if counts[a] < counts[b]:
                a, b = b, a
            answer = counts[a] - counts[b]
            prompt = f"This graph shows {topic}. How many more {a} than {b}? = ?"
            mode = "more"
            payload_extra = {"a": a, "b": b}
        else:
            answer = sum(counts.values())
            prompt = f"This graph shows {topic}. How many in all? = ?"
            mode = "all"
            payload_extra = {}
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={
                "topic": topic,
                "counts": counts,
                "mode": mode,
                "image": {"kind": "bar_graph", "categories": categories, "scale": 1},
                **payload_extra,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Each bar's height tells how many are in that category. To compare two "
                "categories ('how many more A than B'), subtract the smaller bar from the "
                "bigger bar. To find 'how many in all', add every bar together."
            ),
            strategy="'How many more' = subtract bars; 'in all' = add every bar.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["mode"] == "more":
            a = problem.payload["a"]
            b = problem.payload["b"]
            return [
                f"Read the height of the {a} bar and the {b} bar.",
                f"Subtract the shorter from the taller to compare {a} and {b}.",
            ]
        return [
            "Read the height of every bar on the graph.",
            "Add all the bar heights together to find the total.",
        ]

    def worked_example(self, problem: Problem) -> str:
        counts = problem.payload["counts"]
        if problem.payload["mode"] == "more":
            a = problem.payload["a"]
            b = problem.payload["b"]
            return (
                f"{a} has {counts[a]} and {b} has {counts[b]}: "
                f"{counts[a]} - {counts[b]} = {counts[a] - counts[b]} more."
            )
        total = sum(counts.values())
        pieces = " + ".join(str(v) for v in counts.values())
        return f"Add every bar: {pieces} = {total} in all."


# What to measure -> the best tool. Phrases read as the object of "measure ...".
# Each entry: (what, correct tool). The non-length distractors make level 1 easy;
# level 2 offers all three length tools, so the kid must pick the right one.
_TOOL_BANK = (
    ("the length of a crayon", "a ruler"),
    ("the length of an eraser", "a ruler"),
    ("the length of your shoe", "a ruler"),
    ("the length of a book", "a ruler"),
    ("the length of your classroom", "a meter stick"),
    ("the length of the school hallway", "a meter stick"),
    ("the height of a door", "a meter stick"),
    ("the length of a long rug", "a meter stick"),
    ("the distance around your wrist", "a measuring tape"),
    ("the distance around a basketball", "a measuring tape"),
    ("the distance around a tree trunk", "a measuring tape"),
)
_LENGTH_TOOLS = ("a ruler", "a meter stick", "a measuring tape")
_NON_LENGTH_TOOLS = ("a kitchen scale", "a measuring cup", "a clock", "a thermometer")


class ChooseMeasuringTool(Skill):
    """2.MD.A.1 — choose the appropriate measuring tool (Phase-3 MC reframe;
    actually using the tool stays a hands-on family activity)."""

    id = "2.MD.A.1"
    slug = "g2-md-choose-tool"
    grade = 2
    domain = "Measurement & Data"
    title = "Pick the measuring tool"
    max_level = 2
    answer_type = "multiple_choice"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        what, correct = _TOOL_BANK[rng.randrange(len(_TOOL_BANK))]
        if level <= 1:
            distractors = tuple(rng.sample(_NON_LENGTH_TOOLS, 2))
        else:
            others = tuple(t for t in _LENGTH_TOOLS if t != correct)
            distractors = others + (rng.choice(_NON_LENGTH_TOOLS),)
        prompt = f"Which tool is best to measure {what}?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_mc(rng, correct, distractors),
            payload={"what": what, "correct": correct},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        ok = (p["what"], p["correct"]) in _TOOL_BANK
        ok = ok and problem.answer.options[problem.answer.correct_index] == p["correct"]
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Different tools fit different jobs. A ruler is short and flat — great for "
                "small things like a crayon. A meter stick is long and straight — great for "
                "big straight things like a doorway or a room. A measuring tape bends — "
                "perfect for going around curved things like a ball or your wrist."
            ),
            strategy="Small and flat: ruler. Long and straight: meter stick. Curved: tape.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Is the thing small, long, or curved?",
            "Rulers for small, meter sticks for long and straight, tape for around things.",
        ]

    def worked_example(self, problem: Problem) -> str:
        return (
            f"To measure {problem.payload['what']}, the best tool is "
            f"{problem.payload['correct']}."
        )


_UNIT_PAIRS = (
    # (bigger unit plural, singular, smaller unit plural, singular, factor)
    ("feet", "foot", "inches", "inch", 12),
    ("meters", "meter", "centimeters", "centimeter", 100),
    ("yards", "yard", "feet", "foot", 3),
)


class MeasureTwiceTwoUnits(Skill):
    """2.MD.A.2 — measure the same object in two units and relate the counts
    (Phase-3 MC reframe of the hands-on standard)."""

    id = "2.MD.A.2"
    slug = "g2-md-two-units"
    grade = 2
    domain = "Measurement & Data"
    title = "Measuring with two units"
    max_level = 2
    answer_type = "multiple_choice"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        big, big_s, small, small_s, factor = _UNIT_PAIRS[rng.randrange(len(_UNIT_PAIRS))]
        thing = rng.choice(("a rug", "a rope", "a table", "a whiteboard", "a bench"))
        if level <= 1:
            prompt = (
                f"Maya measures {thing} in {big}, then measures it again in {small}. "
                f"Which is true about the two numbers she gets?"
            )
            answer = shuffled_mc(
                rng,
                f"The number of {small} is bigger, because each {small_s} is shorter "
                f"so it takes more of them.",
                (
                    f"The number of {small} is smaller, because each {small_s} is shorter.",
                    "The two numbers are exactly the same.",
                    f"You cannot measure {thing} in {small}.",
                ),
            )
            payload = {"variant": "which_bigger", "big": big, "small": small}
        else:
            n_big = rng.randint(2, 9)
            n_small = n_big * factor
            prompt = (
                f"A rope is {n_big} {big} long. Measured again in {small}, the same rope "
                f"is {n_small} {small}. Why is {n_small} a bigger number than {n_big}?"
            )
            answer = shuffled_mc(
                rng,
                f"Each {big_s} holds {factor} {small}, so the shorter unit needs a "
                f"bigger count for the same length.",
                (
                    "The rope stretched between the two measurements.",
                    f"{small.capitalize()} are longer than {big}.",
                    "The second measurement must be a mistake.",
                ),
            )
            payload = {
                "variant": "explain_factor",
                "big": big,
                "big_s": big_s,
                "small": small,
                "factor": factor,
                "n_big": n_big,
                "n_small": n_small,
            }
        return Problem(
            skill_id=self.id, level=level, prompt=prompt, answer=answer, payload=payload
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        ok = True
        if p["variant"] == "explain_factor":
            ok = p["n_small"] == p["n_big"] * p["factor"]
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "The same object can be measured in different units. The length doesn't "
                "change — only the count does. Smaller units (like inches) need a bigger "
                "count; bigger units (like feet) need a smaller count. A 3-foot table is "
                "36 inches: same table, different units."
            ),
            strategy="Smaller unit, bigger number. Bigger unit, smaller number.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "The object stays the same size — only the measuring unit changes.",
            "Shorter units take more of them to cover the same length.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["variant"] == "explain_factor":
            return (
                f"1 {p['big_s']} = {p['factor']} {p['small']}, so "
                f"{p['n_big']} × {p['factor']} = {p['n_small']} — a bigger count of a "
                f"smaller unit, same length."
            )
        return (
            f"Each {p['small']} is shorter than each {p['big']}, so measuring in "
            f"{p['small']} gives a bigger number for the same length."
        )


# (what, good estimate, two way-off estimates). Estimates are everyday sizes a
# 2nd grader can picture; the distractors are absurd for the object.
_ESTIMATE_BANK_EASY = (
    ("a new pencil", "7 inches", ("7 feet", "7 meters")),
    ("the height of a classroom door", "7 feet", ("7 inches", "70 feet")),
    ("a paper clip", "1 inch", ("1 foot", "1 meter")),
    ("your math book", "30 centimeters", ("30 meters", "3 centimeters")),
    ("a bed", "6 feet", ("6 inches", "60 feet")),
)
_ESTIMATE_BANK_HARD = (
    ("a school bus", "35 feet", ("35 inches", "3 feet")),
    ("a fingernail", "1 centimeter", ("1 meter", "30 centimeters")),
    ("a soccer field", "100 meters", ("100 centimeters", "1 meter")),
    ("a drinking straw", "15 centimeters", ("15 meters", "150 centimeters")),
    ("the height of a 2nd grader", "4 feet", ("4 inches", "40 feet")),
)


class EstimateLength(Skill):
    """2.MD.A.3 — pick the most reasonable length estimate (Phase-3 MC reframe;
    estimation has no single typed right answer)."""

    id = "2.MD.A.3"
    slug = "g2-md-estimate-length"
    grade = 2
    domain = "Measurement & Data"
    title = "Estimate lengths"
    max_level = 2
    answer_type = "multiple_choice"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        bank = _ESTIMATE_BANK_EASY if level <= 1 else _ESTIMATE_BANK_HARD
        what, correct, distractors = bank[rng.randrange(len(bank))]
        prompt = f"About how long is {what}?"
        if what.startswith("the height"):
            prompt = f"About how tall is {what.removeprefix('the height of ')}?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_mc(rng, correct, distractors),
            payload={"what": what, "correct": correct},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        bank = _ESTIMATE_BANK_EASY + _ESTIMATE_BANK_HARD
        ok = any(w == p["what"] and c == p["correct"] for w, c, _ in bank)
        ok = ok and problem.answer.options[problem.answer.correct_index] == p["correct"]
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Estimating means making a smart guess using sizes you know. Your finger "
                "is about as wide as a centimeter. A ruler is about a foot. A big step is "
                "about a meter or a yard. Compare the object to one of those: a pencil is "
                "several finger-widths long, so inches or centimeters make sense — not feet "
                "or meters."
            ),
            strategy="Compare to a size you know: finger = cm, ruler = foot, big step = meter.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Picture the object next to a ruler or next to your own body.",
            "Toss out the silly choices: would it really be that tiny or that huge?",
        ]

    def worked_example(self, problem: Problem) -> str:
        return (
            f"{problem.payload['what'].capitalize()} is about "
            f"{problem.payload['correct']} — the other choices are far too big or "
            f"far too small."
        )


register(HowMuchLonger())
register(LengthWordProblems())
register(NumberLineJumps())
register(TellTime())
register(CountMoney())
register(ReadLinePlot())
register(ReadGraph())
register(ChooseMeasuringTool())
register(MeasureTwiceTwoUnits())
register(EstimateLength())
