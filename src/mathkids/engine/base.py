"""Skill engine core: Problem / Lesson / Skill abstractions + a global registry.

Determinism is mandatory: Skill.generate(level, rng) must use *only* the injected
random.Random, so the same (skill, level, seed) always yields the identical problem.
That is what lets app.py regenerate a problem at grading time, and what lets the test
suite verify thousands of generated problems.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from mathkids.answers import Answer, MultipleChoiceAnswer


@dataclass(frozen=True)
class Lesson:
    title: str
    body: str
    strategy: str


@dataclass(frozen=True)
class Problem:
    skill_id: str
    level: int
    prompt: str
    answer: Answer
    payload: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Tidy a redundant trailing "= ?" when the prompt is already a worded
        # question (e.g. "How much longer...? = ?" -> "How much longer...?").
        p = self.prompt.rstrip()
        if p.endswith("= ?") and "?" in p[:-3]:
            object.__setattr__(self, "prompt", p[:-3].rstrip())


def shuffled_mc(
    rng: random.Random, correct: str, distractors: tuple[str, ...]
) -> MultipleChoiceAnswer:
    """Build a MultipleChoiceAnswer with deterministically shuffled options."""
    opts = [correct, *distractors]
    if len(set(opts)) != len(opts):
        raise ValueError(f"duplicate options: {opts}")
    rng.shuffle(opts)
    return MultipleChoiceAnswer(tuple(opts), opts.index(correct))


class Skill:
    """A single teachable/testable skill. Concrete skills subclass and set metadata."""

    id: str = ""
    slug: str = ""
    grade: int = 0
    domain: str = ""
    title: str = ""
    max_level: int = 3
    answer_type: str = "integer"
    prereqs: tuple[str, ...] = ()
    phase: int = 1

    def generate(self, level: int, rng: random.Random) -> Problem:  # pragma: no cover
        raise NotImplementedError

    def lesson(self) -> Lesson:  # pragma: no cover - overridden by concrete skills
        return Lesson(title=self.title, body="", strategy="")

    def hints(self, problem: Problem) -> list[str]:
        return []

    def worked_example(self, problem: Problem) -> str:
        return ""

    def invariant(self, problem: Problem) -> bool:
        """Return False if a generated problem violates the skill's constraints.

        Used by the property tests. Default: re-grading the canonical answer succeeds.
        """
        return problem.answer.grade(problem.answer.canonical()).correct


# Ordered skill-introduction sequence per grade (roughly prerequisite order).
# New skills are unlocked in this order as a kid progresses; the first two are
# introduced when a kid is created (see seed.py).
SEQUENCES: dict[int, list[str]] = {
    2: [
        "2.OA.B.2", "2.NBT.A.1", "2.NBT.A.2", "2.NBT.A.3", "2.NBT.A.4",
        "2.OA.A.1", "2.NBT.B.5", "2.NBT.B.6", "2.NBT.B.7", "2.NBT.B.8",
        "2.NBT.B.9", "2.OA.C.3", "2.OA.C.4", "2.MD.C.7", "2.MD.C.8",
        "2.MD.A.1", "2.MD.A.2", "2.MD.A.3", "2.MD.A.4",
        "2.MD.B.5", "2.MD.B.6", "2.MD.D.9", "2.MD.D.10",
        "2.G.A.1", "2.G.A.2", "2.G.A.3",
    ],
    3: [
        "3.OA.A.1", "3.OA.A.2", "3.OA.A.3", "3.OA.A.4", "3.OA.B.5", "3.OA.B.6",
        "3.OA.C.7", "3.OA.D.8", "3.OA.D.9", "3.NBT.A.1", "3.NBT.A.2", "3.NBT.A.3",
        "3.NF.A.1", "3.NF.A.2", "3.NF.A.3", "3.MD.A.1", "3.MD.A.2", "3.MD.B.3",
        "3.MD.B.4", "3.MD.C.5", "3.MD.C.6", "3.MD.C.7", "3.MD.D.8",
        "3.G.A.1", "3.G.A.2",
    ],
    4: [
        "4.OA.A.3.a", "4.OA.A.1", "4.OA.A.2", "4.OA.A.3", "4.OA.B.4", "4.OA.C.5",
        "4.NBT.A.1", "4.NBT.A.2", "4.NBT.A.3", "4.NBT.B.4", "4.NBT.B.5", "4.NBT.B.6",
        "4.NF.A.1", "4.NF.A.2", "4.NF.B.3", "4.NF.B.4", "4.NF.C.5", "4.NF.C.6",
        "4.NF.C.7", "4.MD.A.1", "4.MD.A.2", "4.MD.A.3", "4.MD.B.4", "4.MD.C.5",
        "4.MD.C.6", "4.MD.C.7", "4.G.A.1", "4.G.A.2", "4.G.A.3",
    ],
}


REGISTRY: dict[str, Skill] = {}


def register(skill: Skill) -> Skill:
    if not skill.id:
        raise ValueError("skill.id must be set before registering")
    if skill.id in REGISTRY:
        raise ValueError(f"duplicate skill id: {skill.id}")
    REGISTRY[skill.id] = skill
    return skill


def skills_for_grade(grade: int) -> list[Skill]:
    return [s for s in REGISTRY.values() if s.grade == grade]
