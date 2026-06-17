"""Mastery scoring: a 0..1 proficiency per (kid, skill), with level-ups.

Key guarantee (the spec's most opinionated piece): a correct answer pulls the score
toward a *ceiling that depends on the difficulty level*. So you can never reach the
"mastered" threshold by only answering easy (low-level) problems — only sustained
success at the *top* level can push the score to 1.0. Wrong answers apply a gentle
proportional penalty.

The ceiling curve is `0.5 + 0.5 * (level-1)/(max_level-1)`: the bottom band always
caps at 0.5 and the top band at 1.0, evenly spaced in between, *independent of how
many bands a skill has*. This decoupling is deliberate — it lets us split a skill into
many fine bands for a gentle ramp without quietly compressing its whole score/star
scale (a naive `level/max_level` would push a level-1-of-5 band down to 0.2).

The ramp is intentionally gradual: a kid dwells on each band for several reps (low
learning rate + a 4-correct promotion streak) and the placement probe only nudges one
band after a clean opening run, so difficulty rises in small, earned steps.
"""

from __future__ import annotations

from dataclasses import dataclass

ALPHA = 0.20          # base learning rate (low on purpose: more reps per band)
FAST_MULT = 1.2       # bonus rate when answered quickly
ALPHA_CAP = 0.5
PENALTY = 0.5         # wrong-answer penalty factor (gentle)
PROMOTE_STREAK = 4    # consecutive correct needed to consider a level-up
PROMOTE_EPS = 0.05    # how close to the ceiling counts as "ready"
MASTER_SCORE = 0.95
RECENT_WINDOW = 5
DEMOTE_MIN_CORRECT = 2  # < this many correct in the last RECENT_WINDOW -> demote
PROBE_WINDOW = 4      # ace the first PROBE_WINDOW answers on a fresh skill -> nudge up
PROBE_LEVEL = 2       # the probe only steps to band 2 (one earned step, never a vault)


@dataclass
class MasteryState:
    score: float = 0.0
    level: int = 1
    consec_correct: int = 0
    recent: str = ""  # up to RECENT_WINDOW chars of '1'/'0', most recent last


@dataclass
class MasteryUpdate:
    state: MasteryState
    leveled_up: bool
    leveled_down: bool
    mastered_now: bool


def level_ceiling(level: int, max_level: int) -> float:
    """Score cap for a given band. Bottom band caps at 0.5, top band at 1.0, evenly
    spaced — independent of how many bands the skill has, so splitting a skill into
    more (gentler) bands does not compress its score/star scale. A single-band skill
    caps at 1.0."""
    if max_level <= 1:
        return 1.0
    return 0.5 + 0.5 * (level - 1) / (max_level - 1)


def _alpha(fast: bool) -> float:
    return min(ALPHA_CAP, ALPHA * (FAST_MULT if fast else 1.0))


def update_score(score: float, level: int, max_level: int, correct: bool, fast: bool = False) -> float:
    if correct:
        target = level_ceiling(level, max_level)
        if target > score:  # never pushes the score above the current level's ceiling
            score = score + _alpha(fast) * (target - score)
    else:
        score = score - ALPHA * PENALTY * score
    return min(1.0, max(0.0, score))


def stars(score: float) -> int:
    """Whole stars earned, 0..5 (floor). The 5th star unlocks at the mastery
    threshold — the EMA never quite reaches 1.0, so flooring alone would make
    it unattainable. Score >= MASTER_SCORE still requires top-level success
    (the ceiling-by-difficulty caps lower levels well below it)."""
    if score >= MASTER_SCORE:
        return 5
    return max(0, min(5, int(score * 5 + 1e-9)))


def is_mastered(score: float, level: int, max_level: int) -> bool:
    return level >= max_level and score >= MASTER_SCORE


def apply_attempt(
    state: MasteryState, max_level: int, correct: bool, fast: bool = False,
    attempt_index: int | None = None,
) -> MasteryUpdate:
    """Apply one attempt. `attempt_index` is the 0-based count of prior attempts
    on this skill; when provided, acing the first PROBE_WINDOW attempts acts as a
    placement probe — a kid who clearly already knows the skill skips to
    PROBE_LEVEL instead of grinding up from level 1 (DESIGN §7.4)."""
    was_mastered = is_mastered(state.score, state.level, max_level)
    new_score = update_score(state.score, state.level, max_level, correct, fast)
    recent = (state.recent + ("1" if correct else "0"))[-RECENT_WINDOW:]
    consec = state.consec_correct + 1 if correct else 0
    level = state.level
    leveled_up = leveled_down = False

    if (
        correct
        and attempt_index is not None
        and attempt_index == PROBE_WINDOW - 1
        and consec >= PROBE_WINDOW  # every probe attempt was correct
        and level < min(PROBE_LEVEL, max_level)
    ):
        level = min(PROBE_LEVEL, max_level)
        consec = 0
        leveled_up = True
    elif correct and consec >= PROMOTE_STREAK and level < max_level:
        if new_score >= level_ceiling(level, max_level) - PROMOTE_EPS:
            level += 1
            consec = 0
            leveled_up = True
    elif (
        not correct
        and level > 1
        and len(recent) >= RECENT_WINDOW
        and recent.count("1") < DEMOTE_MIN_CORRECT
    ):
        level -= 1
        leveled_down = True

    new_state = MasteryState(score=new_score, level=level, consec_correct=consec, recent=recent)
    mastered_now = (not was_mastered) and is_mastered(new_score, level, max_level)
    return MasteryUpdate(
        state=new_state,
        leveled_up=leveled_up,
        leveled_down=leveled_down,
        mastered_now=mastered_now,
    )
