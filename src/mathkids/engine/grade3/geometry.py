"""Grade 3 Geometry skills.

Covers categorizing shapes by shared attributes (3.G.A.1) — for example
recognizing that squares, rectangles, and rhombuses are all quadrilaterals —
and partitioning a shape into equal-area parts so that one part is the unit
fraction 1/b of the whole (3.G.A.2). The partition skill is Phase 2: it attaches
a ``fraction_bar`` image spec in ``payload["image"]`` for presentation, while the
answer is still computed in Python so grading never depends on the picture.
"""

from __future__ import annotations

import random
from fractions import Fraction

from mathkids.answers import FractionAnswer, IntegerAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_word

# Number of equal parts -> kid-facing part name + reasonable synonyms a kid types.
_SHARE_NAMES = {
    2: ("half", ("halves",)),
    3: ("third", ("thirds",)),
    4: ("fourth", ("fourths", "quarter", "quarters")),
    6: ("sixth", ("sixths",)),
    8: ("eighth", ("eighths",)),
}


class CategorizeShapes(Skill):
    id = "3.G.A.1"
    slug = "g3-categorize-shapes"
    grade = 3
    domain = "Geometry"
    title = "Categorize shapes"
    max_level = 2
    answer_type = "word"
    phase = 1

    def _make_special_quad(self, level: int, rng: random.Random) -> Problem:
        # A square/rectangle/rhombus is a special kind of quadrilateral.
        shape = rng.choice(("square", "rectangle", "rhombus"))
        prompt = f"A {shape} is a special kind of which 4-sided shape?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_word(
                rng,
                "quadrilateral",
                ("triangle", "pentagon", "hexagon"),
                aliases=("quadrilaterals",),
            ),
            payload={"variant": "special_quad", "shape": shape},
        )

    def _make_side_count(self, level: int, rng: random.Random) -> Problem:
        # How many sides does a named category have? Unambiguous whole-number answer.
        shape, sides = rng.choice(
            (("quadrilateral", 4), ("triangle", 3), ("pentagon", 5), ("hexagon", 6))
        )
        prompt = f"How many sides does a {shape} have? = ?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(sides),
            payload={"variant": "side_count", "shape": shape, "sides": sides},
        )

    def generate(self, level: int, rng: random.Random) -> Problem:
        # Level 1 sticks to the side-count question; higher levels mix in the
        # "special kind of quadrilateral" category question.
        if level <= 1:
            return self._make_side_count(level, rng)
        if rng.random() < 0.5:
            return self._make_special_quad(level, rng)
        return self._make_side_count(level, rng)

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        if p["variant"] == "side_count":
            ok = problem.answer.value == p["sides"] and p["sides"] >= 3
            return ok and super().invariant(problem)
        return p["shape"] in ("square", "rectangle", "rhombus") and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Shapes can be sorted into groups by what they have in common. Any closed "
                "shape with 4 straight sides is a quadrilateral. Squares, rectangles, and "
                "rhombuses all have 4 sides, so they are special kinds of quadrilaterals. "
                "Other groups are named by their side count too: 3 sides is a triangle, "
                "5 sides is a pentagon, and 6 sides is a hexagon."
            ),
            strategy="Count the sides to find the group; a 4-sided shape is a quadrilateral.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["variant"] == "special_quad":
            return [
                f"A {p['shape']} has 4 straight sides — count them.",
                "Every closed shape with 4 sides belongs to the quadrilateral family.",
            ]
        return [
            f"Picture a {p['shape']} and count its straight sides.",
            "Triangle = 3, quadrilateral = 4, pentagon = 5, hexagon = 6.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["variant"] == "special_quad":
            return (
                f"A {p['shape']} has 4 straight sides, and every 4-sided shape is a "
                "quadrilateral, so a {0} is a quadrilateral. Answer = quadrilateral.".format(
                    p["shape"]
                )
            )
        return (
            f"A {p['shape']} is named for its sides, so count them: a {p['shape']} has "
            f"{p['sides']} sides. Answer = {p['sides']}."
        )


class PartitionEqualAreas(Skill):
    id = "3.G.A.2"
    slug = "g3-partition-equal-areas"
    grade = 3
    domain = "Geometry"
    title = "Partition shapes into equal areas"
    max_level = 3
    answer_type = "fraction"
    phase = 2

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            b = rng.choice((2, 3, 4))
        elif level == 2:
            b = rng.choice((2, 3, 4, 6, 8))
        else:
            b = rng.choice((6, 8))
        name, _aliases = _SHARE_NAMES[b]
        value = Fraction(1, b)
        prompt = (
            f"A shape is split into {b} equal parts ({name}s). "
            f"What fraction of the whole shape is ONE part? = ?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=FractionAnswer(value),
            payload={
                "b": b,
                "name": name,
                "image": {"kind": "fraction_bar", "numerator": 1, "denominator": b},
            },
        )

    def invariant(self, problem: Problem) -> bool:
        b = problem.payload["b"]
        ok = b in (2, 3, 4, 6, 8) and problem.answer.value == Fraction(1, b)
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When a whole shape is cut into equal parts, every part covers the same "
                "amount of area. If the shape is split into b equal parts, then one part is "
                "1/b of the whole. Split a rectangle into 4 equal parts and one part is 1/4 "
                "of it; split it into 6 equal parts and one part is 1/6. The more equal "
                "parts you make, the smaller each part is."
            ),
            strategy="b equal parts means each part is 1/b of the whole.",
        )

    def hints(self, problem: Problem) -> list[str]:
        b = problem.payload["b"]
        return [
            f"The whole is cut into {b} equal parts, so the bottom number is {b}.",
            "One part is just 1 of those parts, so the fraction is 1/" + str(b) + ".",
        ]

    def worked_example(self, problem: Problem) -> str:
        b, name = problem.payload["b"], problem.payload["name"]
        return (
            f"The shape has {b} equal parts ({name}s), so each part is one of {b}: "
            f"that is 1/{b}. Answer = {problem.answer.display}."
        )


register(CategorizeShapes())
register(PartitionEqualAreas())
