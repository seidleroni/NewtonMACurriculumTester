"""Grade 4 Geometry skills.

Covers recognizing a line of symmetry for a two-dimensional figure and counting
how many such lines a well-known regular or named shape has (4.G.A.3). A line of
symmetry folds a shape so the two halves match exactly. The answer is a plain
whole number looked up from a fixed table of familiar shapes, so the math never
depends on a picture and grading stays deterministic.
"""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

# Well-known shapes -> number of lines of symmetry. Values are standard facts:
# a square folds 4 ways, a (non-square) rectangle 2, an equilateral triangle 3,
# a regular pentagon 5, a regular hexagon 6, and an isosceles triangle just 1.
def _article(noun: str) -> str:
    return "an" if noun[0] in "aeiou" else "a"


_SYMMETRY_LINES = {
    "square": 4,
    "rectangle": 2,
    "equilateral triangle": 3,
    "regular pentagon": 5,
    "regular hexagon": 6,
    "isosceles triangle": 1,
}


class LinesOfSymmetryCount(Skill):
    id = "4.G.A.3"
    slug = "g4-lines-of-symmetry"
    grade = 4
    domain = "Geometry"
    title = "Lines of symmetry (count)"
    max_level = 2
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Level 1 keeps to shapes whose symmetry lines match their side/equal-side
        # count or are easy to picture; level 2 opens up to every listed shape.
        if level <= 1:
            shapes = ("square", "rectangle", "equilateral triangle", "isosceles triangle")
        else:
            shapes = tuple(_SYMMETRY_LINES)
        shape = rng.choice(shapes)
        lines = _SYMMETRY_LINES[shape]
        prompt = f"How many lines of symmetry does {_article(shape)} {shape} have? = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(lines),
            payload={"shape": shape, "lines": lines},
        )

    def invariant(self, problem: Problem) -> bool:
        shape = problem.payload["shape"]
        ok = (
            shape in _SYMMETRY_LINES
            and problem.answer.value == _SYMMETRY_LINES[shape]
            and problem.answer.value >= 1
        )
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A line of symmetry is a fold line: if you fold the shape along it, the two "
                "halves land exactly on top of each other. A shape can have more than one. A "
                "square folds 4 ways (top-bottom, side-to-side, and both diagonals), so it has "
                "4 lines of symmetry. A rectangle that is not a square folds only 2 ways. An "
                "equilateral triangle has 3, a regular pentagon has 5, and a regular hexagon "
                "has 6 — a regular shape with n equal sides has n lines of symmetry. An "
                "isosceles triangle has just 1, straight down from its tip."
            ),
            strategy="Count the fold lines that make the two halves match exactly.",
        )

    def hints(self, problem: Problem) -> list[str]:
        shape = problem.payload["shape"]
        return [
            f"Imagine folding the {shape} so the two halves line up perfectly.",
            "Count every different fold that makes the halves match — that is the number "
            "of lines of symmetry.",
        ]

    def worked_example(self, problem: Problem) -> str:
        shape = problem.payload["shape"]
        lines = problem.payload["lines"]
        an = _article(shape)
        return (
            f"Picture {an} {shape} and find every fold that makes the two halves match. "
            f"{an.capitalize()} {shape} has "
            f"{lines} such {'line' if lines == 1 else 'lines'} of symmetry. Answer = {lines}."
        )


register(LinesOfSymmetryCount())
