"""Property-style sweep over every skill: each generated problem must self-grade,
respect its invariants, be deterministic, and ship teaching text.

This is the load-bearing test: it guards every skill we will ever add.
"""

import random

import pytest

from mathkids.answers import FractionAnswer, IntegerAnswer
from mathkids.engine import REGISTRY

SEEDS = range(400)
WRONG = "-987654"  # never a valid answer (all answers are non-negative)


def _all_skill_levels():
    for skill in REGISTRY.values():
        for level in range(1, skill.max_level + 1):
            yield skill, level


@pytest.mark.parametrize("skill,level", list(_all_skill_levels()), ids=lambda x: str(x))
def test_generated_problems_are_valid(skill, level):
    for seed in SEEDS:
        problem = skill.generate(level, random.Random(seed))

        # 1. The declared answer must grade itself correct.
        assert problem.answer.grade(problem.answer.canonical()).correct, (skill.id, level, seed)
        # 2. The skill's own invariant holds (ranges, non-negativity, etc.).
        assert skill.invariant(problem), (skill.id, level, seed)
        # 3. Answers in this curriculum are always non-negative.
        assert problem.answer.value >= 0, (skill.id, level, seed)
        # 4. A clearly wrong answer is rejected.
        assert not problem.answer.grade(WRONG).correct, (skill.id, level, seed)
        # 5. The prompt is a real question.
        assert problem.prompt and problem.prompt.strip().endswith("?")
        assert problem.skill_id == skill.id and problem.level == level


@pytest.mark.parametrize("skill,level", list(_all_skill_levels()), ids=lambda x: str(x))
def test_generation_is_deterministic(skill, level):
    for seed in (0, 7, 99, 256):
        p1 = skill.generate(level, random.Random(seed))
        p2 = skill.generate(level, random.Random(seed))
        assert p1.prompt == p2.prompt
        assert p1.answer.canonical() == p2.answer.canonical()


def test_every_skill_has_teaching_content():
    for skill in REGISTRY.values():
        lesson = skill.lesson()
        assert lesson.body.strip() and lesson.strategy.strip()
        problem = skill.generate(1, random.Random(0))
        assert isinstance(skill.hints(problem), list) and skill.hints(problem)
        assert skill.worked_example(problem).strip()


def test_expected_skills_are_registered():
    expected = {
        "2.OA.B.2", "2.NBT.A.1", "2.NBT.B.5",
        "4.OA.A.3.a", "4.NBT.B.5", "4.NF.B.3",
    }
    assert expected <= set(REGISTRY)


def test_answer_types_match_metadata():
    for skill in REGISTRY.values():
        problem = skill.generate(1, random.Random(1))
        if skill.answer_type == "integer":
            assert isinstance(problem.answer, IntegerAnswer)
        elif skill.answer_type == "fraction":
            assert isinstance(problem.answer, FractionAnswer)
