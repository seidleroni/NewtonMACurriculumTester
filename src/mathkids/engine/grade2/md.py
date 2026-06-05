"""Grade 2 Measurement & Data skills.

Length comparison/word problems, number-line jumps, telling time, money,
and reading line plots / picture & bar graphs. Phase-2 skills attach an image
spec in ``payload["image"]`` for presentation; every answer is computed in
Python so grading never depends on the picture.
"""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer, MoneyAnswer, TimeAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

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


register(HowMuchLonger())
register(LengthWordProblems())
register(NumberLineJumps())
register(TellTime())
register(CountMoney())
register(ReadLinePlot())
register(ReadGraph())
