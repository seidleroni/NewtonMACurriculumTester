"""Grade 2 geometry skills: shape names, partitioning rectangles, equal shares."""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_word

# polygon side-count -> kid-facing name (square/rectangle are NOT accepted for 4)
_POLYGON_NAMES = {
    3: "triangle",
    4: "quadrilateral",
    5: "pentagon",
    6: "hexagon",
}

# equal-share part name + the synonyms a kid might reasonably type
_SHARE_NAMES = {
    2: ("half", ("halves",)),
    3: ("third", ("thirds",)),
    4: ("fourth", ("fourths", "quarter", "quarters")),
}


class NameShapesByAttributes(Skill):
    id = "2.G.A.1"
    slug = "g2-name-shapes"
    grade = 2
    domain = "Geometry"
    title = "Name shapes by attributes"
    max_level = 2
    answer_type = "word"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        sides = rng.choice((3, 4) if level <= 1 else (3, 4, 5, 6))
        name = _POLYGON_NAMES[sides]
        distractors = tuple(nm for nm in _POLYGON_NAMES.values() if nm != name)
        prompt = f"A polygon with {sides} sides is called a ___?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_word(rng, name, distractors),
            payload={"sides": sides, "name": name},
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A polygon is a closed shape made of straight sides. We name many polygons by "
                "how many sides they have: 3 sides is a triangle, 4 sides is a quadrilateral, "
                "5 sides is a pentagon, and 6 sides is a hexagon."
            ),
            strategy="Count the sides, then match the count to the shape's name.",
        )

    def hints(self, problem: Problem) -> list[str]:
        sides = problem.payload["sides"]
        return [
            f"Count the sides: this shape has {sides} of them.",
            "Match the number of sides to its name (3 triangle, 4 quadrilateral, "
            "5 pentagon, 6 hexagon).",
        ]

    def worked_example(self, problem: Problem) -> str:
        sides, name = problem.payload["sides"], problem.payload["name"]
        return f"A polygon with {sides} sides is a {name}."


class PartitionRectangleIntoSquares(Skill):
    id = "2.G.A.2"
    slug = "g2-partition-rectangle"
    grade = 2
    domain = "Geometry"
    title = "Partition a rectangle into squares"
    max_level = 2
    answer_type = "integer"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = 4 if level <= 1 else 6
        rows = rng.randint(1, hi)
        cols = rng.randint(1, hi)
        total = rows * cols
        prompt = (
            f"This rectangle is split into {rows} rows and {cols} columns of equal "
            "squares. How many squares are there in all?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(total),
            payload={
                "rows": rows,
                "cols": cols,
                "image": {"kind": "grid", "rows": rows, "cols": cols},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When a rectangle is cut into equal squares lined up in rows and columns, "
                "every row has the same number of squares. You can skip-count the squares in "
                "each row, or multiply the number of rows by the number of columns to count "
                "them all."
            ),
            strategy="Count squares per row, then add up the rows (rows × columns).",
        )

    def hints(self, problem: Problem) -> list[str]:
        rows, cols = problem.payload["rows"], problem.payload["cols"]
        return [
            f"Each row has {cols} squares. How many rows are there?",
            f"Add {cols} for each of the {rows} rows, or multiply {rows} × {cols}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        rows, cols = problem.payload["rows"], problem.payload["cols"]
        return f"{rows} rows of {cols} squares: {rows} × {cols} = {rows * cols} squares."


class EqualShares(Skill):
    id = "2.G.A.3"
    slug = "g2-equal-shares"
    grade = 2
    domain = "Geometry"
    title = "Equal shares (halves, thirds, fourths)"
    max_level = 2
    answer_type = "word"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        parts = rng.choice((2, 4) if level <= 1 else (2, 3, 4))
        name, aliases = _SHARE_NAMES[parts]
        distractors = tuple(nm for nm, _al in _SHARE_NAMES.values() if nm != name)
        prompt = f"One of {parts} equal parts of a whole is called a ___?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_word(rng, name, distractors, aliases=aliases),
            payload={
                "parts": parts,
                "name": name,
                "image": {"kind": "fraction_bar", "numerator": 1, "denominator": parts},
            },
        )

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When we split a whole into equal parts, the parts get special names. "
                "Two equal parts are halves, three equal parts are thirds, and four equal "
                "parts are fourths (also called quarters). One piece is one of those parts."
            ),
            strategy="Count the equal parts: 2 = halves, 3 = thirds, 4 = fourths.",
        )

    def hints(self, problem: Problem) -> list[str]:
        parts = problem.payload["parts"]
        return [
            f"The whole is split into {parts} equal parts.",
            "2 parts are halves, 3 parts are thirds, 4 parts are fourths (quarters).",
        ]

    def worked_example(self, problem: Problem) -> str:
        parts, name = problem.payload["parts"], problem.payload["name"]
        return f"A whole cut into {parts} equal parts: one part is a {name}."


register(NameShapesByAttributes())
register(PartitionRectangleIntoSquares())
register(EqualShares())
