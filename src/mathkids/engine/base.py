"""Skill engine core: Problem / Lesson / Skill abstractions + a global registry.

Determinism is mandatory: Skill.generate(level, rng) must use *only* the injected
random.Random, so the same (skill, level, seed) always yields the identical problem.
That is what lets app.py regenerate a problem at grading time, and what lets the test
suite verify thousands of generated problems.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from mathkids.answers import Answer


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
    2: ["2.OA.B.2", "2.NBT.A.1", "2.NBT.B.5"],
    4: ["4.OA.A.3.a", "4.NBT.B.5", "4.NF.B.3"],
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
