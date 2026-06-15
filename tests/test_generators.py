"""Property-style sweep over every registered skill: each generated problem must
self-grade, respect its invariants, be deterministic, ship teaching text, and use a
known answer type. Plus structural consistency between the registry and SEQUENCES.

This is the load-bearing test: it guards every skill we add. (It cannot catch math
that is wrong-but-self-consistent — an adversarial correctness audit covers that.)
"""

import random

import pytest

from mathkids.answers import ANSWER_TYPES, Answer
from mathkids.engine import REGISTRY, SEQUENCES

SEEDS = range(200)
WRONG = "-987654"  # never a valid answer in this curriculum


def _all_skill_levels():
    for skill in REGISTRY.values():
        for level in range(1, skill.max_level + 1):
            yield skill, level


@pytest.mark.parametrize("skill,level", list(_all_skill_levels()), ids=lambda x: f"{x}")
def test_generated_problems_are_valid(skill, level):
    for seed in SEEDS:
        problem = skill.generate(level, random.Random(seed))
        ctx = (skill.id, level, seed)

        # 1. The declared answer must grade itself correct.
        assert problem.answer.grade(problem.answer.canonical()).correct, ctx
        # 2. The skill's own invariant holds (ranges, etc.).
        assert skill.invariant(problem), ctx
        # 3. A clearly wrong answer is rejected.
        assert not problem.answer.grade(WRONG).correct, ctx
        # 4. The prompt is a non-empty question; metadata is consistent.
        assert problem.prompt and problem.prompt.strip(), ctx
        assert problem.skill_id == skill.id and problem.level == level, ctx
        # 5. The answer is a known, registered type.
        assert isinstance(problem.answer, Answer), ctx
        assert problem.answer.answer_type in ANSWER_TYPES, ctx


@pytest.mark.parametrize("skill,level", list(_all_skill_levels()), ids=lambda x: f"{x}")
def test_generation_is_deterministic(skill, level):
    for seed in (0, 7, 99, 150):
        p1 = skill.generate(level, random.Random(seed))
        p2 = skill.generate(level, random.Random(seed))
        assert p1.prompt == p2.prompt
        assert p1.answer.canonical() == p2.answer.canonical()


def test_every_skill_has_teaching_content():
    for skill in REGISTRY.values():
        lesson = skill.lesson()
        assert lesson.body.strip() and lesson.strategy.strip(), skill.id
        problem = skill.generate(1, random.Random(0))
        assert isinstance(skill.hints(problem), list) and skill.hints(problem), skill.id
        assert skill.worked_example(problem).strip(), skill.id


@pytest.mark.parametrize("skill,level", list(_all_skill_levels()), ids=lambda x: f"{x}")
def test_categorical_answers_are_selectable(skill, level):
    """Comparator and word answers are pick-one across every grade/subject: each
    must offer `choices` the kid taps (never a text box), with exactly one correct."""
    for seed in SEEDS:
        problem = skill.generate(level, random.Random(seed))
        answer = problem.answer
        if answer.answer_type not in ("comparator", "word"):
            continue
        ctx = (skill.id, level, seed, answer.choices)
        assert answer.choices, ctx
        correct = [c for c in answer.choices if answer.grade(c).correct]
        assert len(correct) == 1, ctx


def test_registry_and_sequences_are_consistent():
    seq_ids = {sid for ids in SEQUENCES.values() for sid in ids}
    reg_ids = set(REGISTRY)
    # Every sequenced skill is implemented...
    missing = seq_ids - reg_ids
    assert not missing, f"in SEQUENCES but not registered: {sorted(missing)}"
    # ...and every implemented skill is sequenced (so it can be introduced).
    orphan = reg_ids - seq_ids
    assert not orphan, f"registered but not in any SEQUENCE: {sorted(orphan)}"


def test_skill_grade_matches_sequence_grade():
    for grade, ids in SEQUENCES.items():
        for sid in ids:
            assert REGISTRY[sid].grade == grade, (sid, grade)
