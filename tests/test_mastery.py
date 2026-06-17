"""Mastery scoring: ceiling-by-difficulty, promotion, demotion, mastery, stars."""

from mathkids.mastery import (
    MasteryState,
    apply_attempt,
    is_mastered,
    level_ceiling,
    stars,
    update_score,
)


def test_score_is_capped_by_level_ceiling():
    # Only-easy success can never approach mastery: the bottom band caps at 0.5.
    score = 0.0
    for _ in range(500):
        score = update_score(score, level=1, max_level=3, correct=True)
    assert score <= level_ceiling(1, 3) + 1e-9
    assert score > 0.45  # it does climb toward the 0.5 ceiling


def test_ceiling_curve_is_independent_of_band_count():
    # Bottom band always 0.5, top band always 1.0, regardless of how many bands.
    for ml in (2, 3, 4, 5):
        assert level_ceiling(1, ml) == 0.5
        assert level_ceiling(ml, ml) == 1.0
    # ...and evenly spaced in between (a 5-band skill's middle band).
    assert level_ceiling(3, 5) == 0.75
    # A single-band skill caps at 1.0.
    assert level_ceiling(1, 1) == 1.0


def test_mid_level_ceiling():
    score = 0.0
    for _ in range(500):
        score = update_score(score, level=2, max_level=3, correct=True)
    assert score <= level_ceiling(2, 3) + 1e-9
    assert score < 0.95  # cannot be "mastered" while below the top level


def test_wrong_answers_reduce_score_gently_but_never_below_zero():
    score = 0.6
    new = update_score(score, level=2, max_level=3, correct=False)
    assert 0 < new < score
    for _ in range(50):
        new = update_score(new, level=2, max_level=3, correct=False)
    assert new >= 0.0


def test_promotion_after_a_correct_streak():
    state = MasteryState()
    level_reached = 1
    for _ in range(40):
        upd = apply_attempt(state, max_level=3, correct=True, fast=True)
        state = upd.state
        level_reached = max(level_reached, state.level)
    assert level_reached == 3
    assert is_mastered(state.score, state.level, 3)


def test_no_mastery_below_top_level():
    assert not is_mastered(0.99, 1, 3)
    assert not is_mastered(0.99, 2, 3)
    assert is_mastered(0.96, 3, 3)


def test_demotion_after_a_bad_run():
    state = MasteryState(score=0.6, level=2, consec_correct=0, recent="11111")
    leveled_down = False
    for _ in range(5):
        upd = apply_attempt(state, max_level=3, correct=False)
        state = upd.state
        leveled_down = leveled_down or upd.leveled_down
    assert leveled_down
    assert state.level == 1


def test_placement_probe_promotes_after_acing_first_attempts():
    # The probe now needs a clean run of PROBE_WINDOW (4) correct answers, and only
    # steps up one band (to level 2) — it never vaults further.
    state = MasteryState()
    upd = apply_attempt(state, max_level=3, correct=True, attempt_index=0)
    upd = apply_attempt(upd.state, max_level=3, correct=True, attempt_index=1)
    upd = apply_attempt(upd.state, max_level=3, correct=True, attempt_index=2)
    assert upd.state.level == 1  # not yet — only 3 in a row
    upd = apply_attempt(upd.state, max_level=3, correct=True, attempt_index=3)
    assert upd.state.level == 2
    assert upd.leveled_up


def test_placement_probe_requires_every_probe_attempt_correct():
    state = MasteryState()
    upd = apply_attempt(state, max_level=3, correct=False, attempt_index=0)
    for i in (1, 2, 3):
        upd = apply_attempt(upd.state, max_level=3, correct=True, attempt_index=i)
    assert upd.state.level == 1  # the early miss disqualifies the probe


def test_placement_probe_never_fires_later():
    # A correct pair anywhere past the first attempts is just normal progress.
    state = MasteryState(recent="11")
    upd = apply_attempt(state, max_level=3, correct=True, attempt_index=5)
    assert upd.state.level == 1


def test_placement_probe_off_without_attempt_index():
    state = MasteryState(consec_correct=1, recent="1")
    upd = apply_attempt(state, max_level=3, correct=True)
    assert upd.state.level == 1


def test_stars_mapping():
    assert stars(0.0) == 0
    assert stars(0.2) == 1
    assert stars(0.39) == 1
    assert stars(0.4) == 2
    assert stars(0.94) == 4
    assert stars(1.0) == 5


def test_fifth_star_unlocks_at_mastery():
    # The score EMA asymptotes below 1.0, so the 5th star must unlock at the
    # mastery threshold or it could never be earned.
    state = MasteryState()
    for _ in range(40):
        state = apply_attempt(state, max_level=3, correct=True, fast=True).state
    assert is_mastered(state.score, state.level, 3)
    assert stars(state.score) == 5


def test_stars_cannot_reach_five_at_low_level():
    # Highest reachable score at the bottom band is 0.5 -> at most 2 stars; the 5th
    # star still requires top-level mastery.
    score = 0.0
    for _ in range(500):
        score = update_score(score, level=1, max_level=3, correct=True)
    assert stars(score) <= 2
    assert stars(score) < 5
