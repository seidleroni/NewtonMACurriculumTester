"""Guardrails for the grade-4 difficulty ramp + a structural check across the
re-banded grades (2 and 4).

The generic property sweep proves every band is *valid*; these prove the bands are
*gentle at the floor*, *monotonic*, and *single-typed*, and that no skill has a dead
(identical-to-its-neighbour) or ignored level — the defects the adversarial audit
caught that the property tests could not.
"""

import random

from mathkids.engine import REGISTRY, skills_for_grade

SEEDS = range(200)


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


def _carry_count(a: int, b: int) -> int:
    count = carry = 0
    while a or b or carry:
        carry = int(a % 10 + b % 10 + carry >= 10)
        count += carry
        a, b = a // 10, b // 10
    return count


def test_add_sub_to_million_forces_carry_then_borrow():
    # 4.NBT.B.4: L4 ("carry add") and L6 ("borrow subtract") must always exercise
    # their regrouping, not leave it to chance.
    for p in _probs("4.NBT.B.4", 4):
        assert p.payload["op"] == "+" and _carries(p.payload["a"], p.payload["b"]), p.prompt
    for p in _probs("4.NBT.B.4", 6):
        assert p.payload["op"] == "-" and _borrows(p.payload["a"], p.payload["b"]), p.prompt


def test_add_sub_to_million_floor_has_no_carry():
    for p in _probs("4.NBT.B.4", 1):
        assert p.payload["op"] == "+" and not _carries(p.payload["a"], p.payload["b"]), p.prompt


def test_add_sub_to_million_steps_up_with_exactly_one_carry():
    # The November 2026 rungs between the no-carry floor and 4-digit carrying: exactly
    # one carry, from either low place, and the sum keeps the addends' digit count.
    for level, digits in ((2, 3), (3, 4)):
        sites = set()
        for p in _probs("4.NBT.B.4", level):
            a, b = p.payload["a"], p.payload["b"]
            assert p.payload["op"] == "+", p.prompt
            assert len(str(a)) == len(str(b)) == len(str(a + b)) == digits, p.prompt
            assert _carry_count(a, b) == 1, p.prompt
            sites.add(next(i for i in range(digits) if a // 10**i % 10 + b // 10**i % 10 >= 10))
        assert sites == set(range(digits - 1)), (level, sites)  # every place below the top


def test_add_sub_to_million_teaching_gates_follow_the_ladder():
    from mathkids.learning import requirements

    base = ["decompose", "match", "add_parts"]
    single = base + ["add_ones", "add_tens"]
    multi = single + ["add_multi"]
    borrow = multi + ["sub_parts", "sub_ones", "sub_tens", "sub_multi", "sub_zero"]
    expected = {1: base, 2: single, 3: single, 4: multi, 5: multi + ["sub_parts"],
                6: borrow, 7: borrow}
    for level, path in expected.items():
        band, got = requirements("4.NBT.B.4", level)
        assert got == path, level
        assert {len(str(p.payload["a"])) for p in _probs("4.NBT.B.4", level)} == {band}, level


def test_add_sub_to_million_renumbering_keeps_stored_problems():
    # Level 1 is unchanged and old levels 2-5 moved up by two, so a stored (level, seed)
    # regenerates exactly what the kid saw (values recorded before the change).
    sk = REGISTRY["4.NBT.B.4"]
    seen = {(1, 0): "708 + 241 = ?", (1, 1): "311 + 547 = ?", (1, 7): "661 + 108 = ?",
            (4, 0): "7,087 + 7,479 = ?", (4, 7): "6,612 + 3,089 = ?",
            (5, 1): "7,117 - 2,117 = ?", (6, 0): "96,474 - 70,868 = ?",
            (7, 1): "166,172 + 268,459 = ?", (7, 7): "258,176 + 415,002 = ?"}
    for (level, seed), prompt in seen.items():
        assert sk.generate(level, random.Random(seed)).prompt == prompt


def test_line_plot_top_band_is_unlike_denominators():
    # 4.MD.B.4 level 4 must require finding a common denominator (extremes differ).
    for p in _probs("4.MD.B.4", 4):
        assert p.payload.get("unlike"), p.prompt


def test_multiplicative_comparison_floor_is_small_and_forward():
    # 4.OA.A.1 / 4.OA.A.2 level 1: forward multiply with small factors.
    for sid in ("4.OA.A.1", "4.OA.A.2"):
        for p in _probs(sid, 1):
            assert p.answer.value <= 25, p.prompt


def test_equivalent_fractions_floor_is_unit_fraction():
    # 4.NF.A.1 level 1 is a unit fraction (1/b) doubled.
    for p in _probs("4.NF.A.1", 1):
        assert p.payload["a"] == 1 and p.payload["mult"] == 2, p.prompt


def test_add_tenths_hundredths_prompt_drops_the_misleading_over_100():
    # 4.NF.C.5 must not demand "?/100" while feedback shows the reduced form.
    for lvl in range(1, REGISTRY["4.NF.C.5"].max_level + 1):
        for p in _probs("4.NF.C.5", lvl):
            assert "?/100" not in p.prompt, p.prompt


def test_money_word_problems_are_money_only():
    # 4.MD.A.2 was collapsed to a single money answer type (no time/distance).
    sk = REGISTRY["4.MD.A.2"]
    for lvl in range(1, sk.max_level + 1):
        for p in _probs("4.MD.A.2", lvl):
            assert p.answer.answer_type == "money", (p.prompt, p.answer.answer_type)


def test_angle_fractions_are_fraction_only():
    # 4.MD.C.5 dropped the trivial integer "count" variant.
    sk = REGISTRY["4.MD.C.5"]
    for lvl in range(1, sk.max_level + 1):
        for p in _probs("4.MD.C.5", lvl):
            assert p.answer.answer_type == "fraction", (p.prompt, p.answer.answer_type)


def test_steep_grade4_skills_have_five_bands():
    for sid in ("4.OA.A.3.a", "4.NF.B.4"):
        assert REGISTRY[sid].max_level == 5, sid
    assert REGISTRY["4.NBT.B.4"].max_level == 7  # two one-carry rungs added November 2026


def _sig(sk, level, seed):
    # A signature richer than the prompt text: many image / multiple-choice skills
    # reuse a fixed question stem ("What time does the clock show?") while the image,
    # answer, or choices change by level, so compare those too.
    p = sk.generate(level, random.Random(seed))
    choices = tuple(getattr(p.answer, "choices", None) or ())
    return (p.prompt, p.answer.canonical(), choices)


def _identical(sk, l1, l2, n=80):
    return all(_sig(sk, l1, s) == _sig(sk, l2, s) for s in range(n))


def test_rebanded_grades_have_no_dead_or_ignored_levels():
    # Structural guard for the re-banded grades (2, 3, 4): no two adjacent levels are
    # identical for every seed (a dead level), and the floor differs from the top (no
    # skill that ignores its level argument).
    offenders = []
    for grade in (2, 3, 4):
        for sk in skills_for_grade(grade):
            ml = sk.max_level
            if ml < 2:
                continue
            for k in range(1, ml):
                if _identical(sk, k, k + 1):
                    offenders.append(f"{sk.id}: L{k}==L{k+1}")
            if _identical(sk, 1, ml):
                offenders.append(f"{sk.id}: L1==L{ml} (level ignored?)")
    assert not offenders, offenders
