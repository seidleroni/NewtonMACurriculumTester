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
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_mc

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


# --- 4.G.A.1: points, lines, rays, segments, angles, line pairs ------------

_FIGURE_OPTIONS = {
    "point": "a point — one exact spot",
    "segment": "a line segment — straight, with two endpoints",
    "ray": "a ray — one endpoint, then it goes on forever in one direction",
    "line": "a line — it goes on forever in both directions",
}
_ANGLE_OPTIONS = {
    "acute": "an acute angle — smaller than a right angle",
    "right": "a right angle — a square corner (exactly 90°)",
    "obtuse": "an obtuse angle — bigger than a right angle",
}
_PAIR_OPTIONS = {
    "parallel": "parallel — they never cross",
    "perpendicular": "perpendicular — they cross at a square corner",
    "intersecting": "intersecting, but not perpendicular — they cross at a slant",
}
_ACUTE_DEGREES = (30, 40, 50, 60, 70)
_OBTUSE_DEGREES = (110, 120, 130, 140, 150)


class LinesRaysAngles(Skill):
    """4.G.A.1 — identify points, lines, line segments, rays, angle types, and
    parallel/perpendicular line pairs from a drawn figure (Phase-3 image + MC)."""

    id = "4.G.A.1"
    slug = "g4-lines-rays-angles"
    grade = 4
    domain = "Geometry"
    title = "Lines, rays & angles"
    max_level = 2
    answer_type = "multiple_choice"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            fig = rng.choice(tuple(_FIGURE_OPTIONS))
            correct = _FIGURE_OPTIONS[fig]
            distractors = tuple(v for k, v in _FIGURE_OPTIONS.items() if k != fig)
            prompt = "What does this figure show?"
            image = {"kind": "figure", "figure": fig}
            payload = {"variant": "figure", "figure": fig, "image": image}
        elif rng.random() < 0.5:
            cls = rng.choice(("acute", "right", "obtuse"))
            degrees = {
                "acute": rng.choice(_ACUTE_DEGREES),
                "right": 90,
                "obtuse": rng.choice(_OBTUSE_DEGREES),
            }[cls]
            correct = _ANGLE_OPTIONS[cls]
            distractors = tuple(v for k, v in _ANGLE_OPTIONS.items() if k != cls)
            prompt = "What kind of angle is this?"
            image = {"kind": "figure", "figure": "angle", "degrees": degrees}
            payload = {"variant": "angle", "class": cls, "degrees": degrees, "image": image}
        else:
            pair = rng.choice(("parallel", "perpendicular", "intersecting"))
            correct = _PAIR_OPTIONS[pair]
            distractors = tuple(v for k, v in _PAIR_OPTIONS.items() if k != pair)
            prompt = "How are these two lines related?"
            image = {"kind": "figure", "figure": pair}
            payload = {"variant": "pair", "pair": pair, "image": image}
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_mc(rng, correct, distractors),
            payload=payload,
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        ok = True
        if p["variant"] == "angle":
            deg = p["degrees"]
            ok = (
                (p["class"] == "acute" and 0 < deg < 90)
                or (p["class"] == "right" and deg == 90)
                or (p["class"] == "obtuse" and 90 < deg < 180)
            )
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Geometry has exact words for figures. A point is one spot. A line segment "
                "has two endpoints. A ray has one endpoint and an arrow — it goes on forever "
                "one way. A line has arrows on both ends. Two rays from the same endpoint "
                "make an angle: acute is smaller than a square corner, right IS a square "
                "corner (90°), obtuse is bigger. Lines that never cross are parallel; lines "
                "that cross at a square corner are perpendicular."
            ),
            strategy="Look at the ends (dots vs arrows) and at the corners (square or not).",
        )

    def hints(self, problem: Problem) -> list[str]:
        variant = problem.payload["variant"]
        if variant == "figure":
            return [
                "A dot is an endpoint; an arrow means it goes on forever.",
                "Count the endpoints: two = segment, one = ray, none = line.",
            ]
        if variant == "angle":
            return [
                "Compare it to a square corner, like the corner of a piece of paper.",
                "Smaller than the corner: acute. Exactly the corner: right. Bigger: obtuse.",
            ]
        return [
            "Do the lines cross? Parallel lines never do.",
            "If they cross, check the corner: a small square mark means perpendicular.",
        ]

    def worked_example(self, problem: Problem) -> str:
        correct = problem.answer.options[problem.answer.correct_index]
        return f"This figure shows {correct}."


# --- 4.G.A.2: classify triangles and quadrilaterals ------------------------
# Tick marks show equal sides (same count = same length); small squares show
# right angles. Option texts carry their definitions, so each choice is
# checkable against the picture and only one fits.

_SQUARE_OPT = "a square — 4 equal sides and 4 square corners"
_RECT_OPT = "a rectangle — 4 square corners, but not all sides equal"
_RHOMBUS_OPT = "a rhombus — 4 equal sides, but no square corners"
_PARA_OPT = "a parallelogram — opposite sides parallel, but no square corners and not all sides equal"
_TRAP_OPT = "a trapezoid — exactly one pair of parallel sides"
_EQUI_OPT = "equilateral — all three sides equal"
_ISO_OPT = "isosceles — exactly two sides equal"
_SCA_OPT = "scalene — no sides equal"
_RIGHT_TRI_OPT = "a right triangle"
_ACUTE_TRI_OPT = "an acute triangle"
_OBTUSE_TRI_OPT = "an obtuse triangle"

_SHAPE_CARDS = {
    # name -> (level, prompt, points, ticks, right_marks, correct, distractors)
    "right_triangle": (
        1, "Look at the marked corner. What kind of triangle is this?",
        [(0, 120), (160, 120), (0, 0)], None, [0],
        _RIGHT_TRI_OPT, (_ACUTE_TRI_OPT, _OBTUSE_TRI_OPT),
    ),
    "acute_triangle": (
        1, "Look at the corners. What kind of triangle is this?",
        [(20, 130), (180, 130), (90, 10)], None, None,
        _ACUTE_TRI_OPT, (_RIGHT_TRI_OPT, _OBTUSE_TRI_OPT),
    ),
    "obtuse_triangle": (
        1, "Look at the corners. What kind of triangle is this?",
        [(0, 130), (200, 130), (160, 90)], None, None,
        _OBTUSE_TRI_OPT, (_RIGHT_TRI_OPT, _ACUTE_TRI_OPT),
    ),
    "equilateral": (
        1, "The tick marks show equal sides. What kind of triangle is this?",
        [(0, 130), (150, 130), (75, 0)], [1, 1, 1], None,
        _EQUI_OPT, (_ISO_OPT, _SCA_OPT),
    ),
    "isosceles": (
        1, "The tick marks show equal sides. What kind of triangle is this?",
        [(0, 130), (160, 130), (80, 20)], [0, 1, 1], None,
        _ISO_OPT, (_EQUI_OPT, _SCA_OPT),
    ),
    "scalene": (
        1, "The tick marks show equal sides. What kind of triangle is this?",
        [(0, 130), (200, 130), (40, 30)], [1, 2, 3], None,
        _SCA_OPT, (_ISO_OPT, _EQUI_OPT),
    ),
    "square": (
        2, "Which name fits this shape best?",
        [(0, 0), (120, 0), (120, 120), (0, 120)], [1, 1, 1, 1], [0, 1, 2, 3],
        _SQUARE_OPT, (_RECT_OPT, _RHOMBUS_OPT, _TRAP_OPT),
    ),
    "rectangle": (
        2, "Which name fits this shape best?",
        [(0, 0), (170, 0), (170, 100), (0, 100)], [1, 2, 1, 2], [0, 1, 2, 3],
        _RECT_OPT, (_SQUARE_OPT, _RHOMBUS_OPT, _PARA_OPT),
    ),
    "rhombus": (
        2, "Which name fits this shape best?",
        [(0, 60), (80, 0), (160, 60), (80, 120)], [1, 1, 1, 1], None,
        _RHOMBUS_OPT, (_SQUARE_OPT, _RECT_OPT, _PARA_OPT),
    ),
    "parallelogram": (
        2, "Which name fits this shape best?",
        [(0, 100), (40, 0), (190, 0), (150, 100)], [1, 2, 1, 2], None,
        _PARA_OPT, (_RECT_OPT, _RHOMBUS_OPT, _TRAP_OPT),
    ),
    "trapezoid": (
        2, "Which name fits this shape best?",
        [(30, 0), (150, 0), (190, 100), (0, 100)], None, None,
        _TRAP_OPT, (_PARA_OPT, _RECT_OPT, _RHOMBUS_OPT),
    ),
}


class ClassifyShapes(Skill):
    """4.G.A.2 — classify triangles (level 1) and quadrilaterals (level 2)
    from a drawn, marked figure (Phase-3 image + MC)."""

    id = "4.G.A.2"
    slug = "g4-classify-shapes"
    grade = 4
    domain = "Geometry"
    title = "Classify shapes"
    max_level = 2
    answer_type = "multiple_choice"
    phase = 3

    def generate(self, level: int, rng: random.Random) -> Problem:
        names = [n for n, card in _SHAPE_CARDS.items() if card[0] == min(level, 2)]
        name = names[rng.randrange(len(names))]
        _, prompt, points, ticks, right_marks, correct, distractors = _SHAPE_CARDS[name]
        image = {"kind": "polygon", "points": points}
        if ticks:
            image["ticks"] = ticks
        if right_marks:
            image["right_marks"] = right_marks
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=shuffled_mc(rng, correct, distractors),
            payload={"shape": name, "image": image},
        )

    def invariant(self, problem: Problem) -> bool:
        name = problem.payload["shape"]
        card = _SHAPE_CARDS.get(name)
        ok = card is not None and problem.answer.options[problem.answer.correct_index] == card[5]
        return ok and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Shapes are named by their sides and corners. Triangles by corners: a right "
                "triangle has a square corner; acute means all corners are smaller; obtuse "
                "means one is bigger. Triangles by sides: equilateral (all 3 equal), "
                "isosceles (exactly 2 equal), scalene (none equal) — matching tick marks "
                "mean equal sides. Quadrilaterals: a square has 4 equal sides and 4 square "
                "corners; a rectangle has the corners but not all the sides; a rhombus has "
                "the sides but not the corners; a parallelogram has neither, just parallel "
                "opposite sides; a trapezoid has exactly one parallel pair."
            ),
            strategy="Check two things: which sides match (ticks) and which corners are square.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "Matching tick marks mean equal sides; a small square means a right angle.",
            "Test each name against the picture — only one fits exactly.",
        ]

    def worked_example(self, problem: Problem) -> str:
        correct = problem.answer.options[problem.answer.correct_index]
        return f"Counting equal sides and square corners, this shape is {correct}."


register(LinesOfSymmetryCount())
register(LinesRaysAngles())
register(ClassifyShapes())
