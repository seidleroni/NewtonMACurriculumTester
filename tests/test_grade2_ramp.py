"""Guardrails for the grade-2 difficulty ramp.

The generic property sweep (test_generators.py) proves every band is *valid*; these
tests prove the redesigned bands are actually *gentle at the floor* and *get harder*,
so a future edit can't silently make level 1 hard again.
"""

import random

from mathkids.engine import REGISTRY

SEEDS = range(200)


def _probs(sid, level):
    sk = REGISTRY[sid]
    return [sk.generate(level, random.Random(s)) for s in SEEDS]


def test_facts_within_20_floor_never_crosses_ten():
    # 2.OA.B.2 level 1: addition only, both addends single-digit, sum stays <= 10.
    for p in _probs("2.OA.B.2", 1):
        a, b, op = p.payload["a"], p.payload["b"], p.payload["op"]
        assert op == "+" and a <= 9 and b <= 9 and a + b <= 10, p.prompt


def test_add_sub_within_100_floor_has_no_carry():
    # 2.NBT.B.5 level 1: two-digit + single-digit, ones never reach ten.
    for p in _probs("2.NBT.B.5", 1):
        a, b, op = p.payload["a"], p.payload["b"], p.payload["op"]
        assert op == "+" and b < 10 and (a % 10) + b <= 9, p.prompt


def test_add_sub_within_1000_floor_has_no_regrouping():
    # 2.NBT.B.7 level 1: addition where no column total exceeds 9 (was un-leveled).
    for p in _probs("2.NBT.B.7", 1):
        a, b, op = p.payload["a"], p.payload["b"], p.payload["op"]
        assert op == "+", p.prompt
        for place in (1, 10, 100):
            assert (a // place % 10) + (b // place % 10) <= 9, p.prompt


def test_word_problems_floor_is_small():
    # 2.OA.A.1 level 1: single-digit, no carry/borrow -> every answer is one digit.
    for p in _probs("2.OA.A.1", 1):
        assert p.answer.value <= 9, p.prompt


def test_facts_within_20_l4_is_all_bridging_addition():
    # The make-a-ten band must stay harder than the no-borrow subtraction below it.
    for p in _probs("2.OA.B.2", 4):
        a, b, op = p.payload["a"], p.payload["b"], p.payload["op"]
        assert op == "+" and a + b > 10, p.prompt


def test_add_sub_within_1000_top_band_forces_a_borrow():
    # 2.NBT.B.7 level 5 must actually force a borrow (ones of subtrahend > ones of minuend).
    for p in _probs("2.NBT.B.7", 5):
        a, b, op = p.payload["a"], p.payload["b"], p.payload["op"]
        assert op == "-" and (b % 10) > (a % 10), p.prompt


def test_read_write_fill_never_hides_a_zero():
    # 2.NBT.A.3 fill bands never ask the kid to type 0 into an expanded-form blank.
    for lvl in (3, 4):
        for p in _probs("2.NBT.A.3", lvl):
            if p.payload["mode"] == "fill":
                assert p.answer.value != 0, p.prompt


def test_number_line_floor_is_forward_only():
    # 2.MD.B.6 level 1 never produces a backward jump (even from start 100).
    for p in _probs("2.MD.B.6", 1):
        assert p.payload["op"] == "+", p.prompt


def test_length_word_floor_is_single_digit_addition():
    # 2.MD.B.5 level 1: single-digit addends, no carry across the ones.
    for p in _probs("2.MD.B.5", 1):
        a, b, op = p.payload["a"], p.payload["b"], p.payload["op"]
        assert op == "+" and a < 10 and b < 10 and (a % 10) + (b % 10) <= 9, p.prompt


def test_bar_graph_read_survives_past_the_floor_and_more_is_never_zero():
    # The pure-read mode should still appear at level 2 (no two-demand cliff)...
    assert "read" in {p.payload["mode"] for p in _probs("2.MD.D.10", 2)}
    # ...and a "how many more" question never has the confusing answer 0.
    sk = REGISTRY["2.MD.D.10"]
    for lvl in range(2, sk.max_level + 1):
        for p in _probs("2.MD.D.10", lvl):
            if p.payload["mode"] == "more":
                assert p.answer.value >= 1, p.prompt


def test_geometry_floors_only_show_introduced_names():
    # The gentle floor must not show buttons for shapes/shares not yet introduced.
    for p in _probs("2.G.A.1", 1):
        assert set(p.answer.choices) <= {"triangle", "quadrilateral"}, p.answer.choices
    for p in _probs("2.G.A.3", 1):
        assert set(p.answer.choices) <= {"half", "fourth"}, p.answer.choices


def test_bar_graph_floor_needs_no_arithmetic():
    # 2.MD.D.10 level 1: a single-bar read, no add/subtract.
    for p in _probs("2.MD.D.10", 1):
        assert p.payload["mode"] == "read", p.prompt


def test_money_floor_uses_at_most_two_coin_types():
    # 2.MD.C.8 level 1: only dimes and pennies (count tens and ones).
    for p in _probs("2.MD.C.8", 1):
        assert p.payload["nickels"] == 0 and p.payload["quarters"] == 0, p.prompt


def test_four_two_digit_addition_scales_up_monotonically():
    # 2.NBT.B.6 is pure addition, so the largest reachable answer must not shrink
    # as the level rises.
    sk = REGISTRY["2.NBT.B.6"]
    maxes = [max(p.answer.value for p in _probs("2.NBT.B.6", lvl))
             for lvl in range(1, sk.max_level + 1)]
    assert maxes == sorted(maxes), maxes


def test_steep_skills_have_five_bands():
    # The computation cluster the redesign targets should each have the full 5-band ramp.
    for sid in ("2.OA.B.2", "2.OA.A.1", "2.NBT.B.5", "2.NBT.B.6", "2.NBT.B.7"):
        assert REGISTRY[sid].max_level == 5, sid
