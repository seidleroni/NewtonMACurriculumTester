"""Guardrails for the grade-3 difficulty ramp.

Locks the gentle floors, the audit fixes, and the answer-type/kid-wording rules the
property tests can't see. The cross-grade "no dead/flat level" structural guard lives
in test_grade4_ramp.py and now covers grades 2, 3, and 4.
"""

import random
from fractions import Fraction

from mathkids.engine import REGISTRY

SEEDS = range(200)
_ITEM_PLURALS = ("apples", "marbles", "stickers", "cookies", "crayons", "pencils", "books")


def _probs(sid, level):
    sk = REGISTRY[sid]
    return [sk.generate(level, random.Random(s)) for s in SEEDS]


def _carries(a: int, b: int) -> bool:
    while a or b:
        if a % 10 + b % 10 >= 10:
            return True
        a, b = a // 10, b // 10
    return False


def _borrows(a: int, b: int) -> bool:
    while b:
        if a % 10 < b % 10:
            return True
        a, b = a // 10, b // 10
    return False


def test_add_sub_within_1000_forces_carry_then_borrow():
    # 3.NBT.A.2: L2 ("carry") and L4 ("borrow") must always exercise the regrouping.
    for p in _probs("3.NBT.A.2", 2):
        assert p.payload["op"] == "+" and _carries(p.payload["a"], p.payload["b"]), p.prompt
    for p in _probs("3.NBT.A.2", 4):
        assert p.payload["op"] == "-" and _borrows(p.payload["a"], p.payload["b"]), p.prompt


def test_add_sub_within_1000_floor_has_no_carry():
    for p in _probs("3.NBT.A.2", 1):
        assert p.payload["op"] == "+" and not _carries(p.payload["a"], p.payload["b"]), p.prompt


def test_two_step_has_no_singular_plural_bug():
    # 3.OA.D.8: never "gives away 1 stickers" / "eats 1 crayons".
    sk = REGISTRY["3.OA.D.8"]
    for lvl in range(1, sk.max_level + 1):
        for p in _probs("3.OA.D.8", lvl):
            assert not any(f" 1 {n}" in p.prompt for n in _ITEM_PLURALS), p.prompt


def test_time_is_time_only_with_singular_minute():
    # 3.MD.A.1: one answer type (time), and "1 minute goes by" (not "1 minutes go by").
    sk = REGISTRY["3.MD.A.1"]
    for lvl in range(1, sk.max_level + 1):
        for p in _probs("3.MD.A.1", lvl):
            assert p.answer.answer_type == "time", (p.prompt, p.answer.answer_type)
            if p.payload["duration"] == 1:
                assert "1 minute goes by" in p.prompt, p.prompt


def test_time_top_band_crosses_the_hour():
    # 3.MD.A.1 level 4 always crosses into the next hour (the genuinely hard case).
    for p in _probs("3.MD.A.1", 4):
        assert p.payload["end_hour"] > p.payload["start_hour"], p.prompt
        assert p.payload["end_hour"] <= 12, p.prompt


def test_line_plot_unit_singular_and_compare_never_zero():
    for lvl in range(1, REGISTRY["3.MD.B.4"].max_level + 1):
        for p in _probs("3.MD.B.4", lvl):
            assert not any(
                f"measured 1 {u}" in p.prompt for u in ("inches", "centimeters", "millimeters")
            ), p.prompt
    for lvl in (3, 4):  # 3.MD.B.3 "how many more" is never a trivial 0
        for p in _probs("3.MD.B.3", lvl):
            if p.payload.get("mode") == "more":
                assert p.answer.value >= 1, p.prompt


def test_fraction_floors_are_unit_fractions():
    # 3.NF.A.1 and 3.NF.A.2 level 1 are unit fractions 1/d.
    for sid in ("3.NF.A.1", "3.NF.A.2"):
        for p in _probs(sid, 1):
            assert p.answer.value.numerator == 1, p.prompt


def test_understand_fractions_top_band_is_not_the_floor():
    # 3.NF.A.1 level 4 (whole / near-whole) never regresses to the 1/2 floor.
    for p in _probs("3.NF.A.1", 4):
        assert p.answer.value != Fraction(1, 2), p.prompt


def test_compare_fractions_top_band_is_unlike():
    # 3.NF.A.3 level 4 has different numerators (so it can't collapse into L3's
    # like-numerator task).
    import re

    for p in _probs("3.NF.A.3", 4):
        nums = re.findall(r"(\d+)/(\d+)", p.prompt)
        assert len(nums) == 2 and nums[0][0] != nums[1][0], p.prompt


def test_partition_uses_correct_plurals():
    sk = REGISTRY["3.G.A.2"]
    for lvl in range(1, sk.max_level + 1):
        for p in _probs("3.G.A.2", lvl):
            assert "halfs" not in p.prompt, p.prompt


def test_steep_grade3_skills_have_five_bands():
    for sid in ("3.OA.C.7", "3.OA.D.8", "3.NBT.A.2", "3.MD.A.2"):
        assert REGISTRY[sid].max_level == 5, sid
