"""Measure the difficulty ramp WITHOUT a database — pure mastery/scheduler functions.

Two views:
  * climb_one_skill: how many correct-ish answers it takes to step up each band and
    to master a single skill of a given max_level (within-skill dwell time).
  * simulate_sequence: walk a kid through a whole grade's unlock sequence and record
    at which question-count each new skill is introduced and each skill is mastered
    (new-skill cadence).

Run before and after tuning to see the effect:
    .venv/Scripts/python.exe -m tools.simulate_ramp
"""

from __future__ import annotations

import dataclasses
import random

from mathkids.engine import REGISTRY, SEQUENCES
from mathkids.mastery import MasteryState, apply_attempt, is_mastered
from mathkids.scheduler import Slot, compose_session, next_due, next_to_introduce, update_box

# Proposed grade-2 max_level tiering (the generator re-banding lands in a later phase;
# passing this as an override lets us preview the cadence now).
STEEP = ["2.OA.B.2", "2.OA.A.1", "2.NBT.B.5", "2.NBT.B.6", "2.NBT.B.7"]
MEDIUM = [
    "2.NBT.A.1", "2.NBT.A.2", "2.NBT.A.3", "2.NBT.A.4", "2.NBT.B.8",
    "2.OA.C.4", "2.MD.C.7", "2.MD.C.8", "2.MD.A.4", "2.MD.B.5",
    "2.MD.B.6", "2.MD.D.9", "2.MD.D.10",
]
TIER_G2 = {**{s: 5 for s in STEEP}, **{s: 4 for s in MEDIUM}}

_SLOT_FIELDS = {f.name for f in dataclasses.fields(Slot)}


def _slot(sid, **kw):
    """Build a Slot, silently dropping fields this Slot version doesn't have
    (so the same sim runs against both the old and new Slot signature)."""
    return Slot(skill_id=sid, **{k: v for k, v in kw.items() if k in _SLOT_FIELDS})


def climb_one_skill(max_level: int, p: float, fast_p: float, seed: int = 0, cap: int = 4000):
    """Return (level_up_at, mastered_at): question index of each promotion and of mastery."""
    rng = random.Random(seed)
    st = MasteryState()
    level_up_at: dict[int, int] = {}
    mastered_at = None
    attempts = 0
    while attempts < cap:
        correct = rng.random() < p
        fast = correct and rng.random() < fast_p
        upd = apply_attempt(st, max_level, correct, fast, attempt_index=attempts)
        attempts += 1
        if upd.leveled_up and upd.state.level not in level_up_at:
            level_up_at[upd.state.level] = attempts
        if upd.mastered_now:
            mastered_at = attempts
        st = upd.state
        if mastered_at:
            break
    return level_up_at, mastered_at


def simulate_sequence(grade=2, p=0.85, fast_p=0.7, daily_goal=12, max_sessions=200,
                      override: dict | None = None, seed=0):
    rng = random.Random(seed)
    sequence = SEQUENCES[grade]

    def mlevel(sid):
        if override and sid in override:
            return override[sid]
        return REGISTRY[sid].max_level

    states: dict[str, dict] = {}
    total = 0          # cumulative questions answered
    today = 0
    introduced_at: dict[str, int] = {}   # sid -> cumulative question index when introduced
    mastered_at: dict[str, int] = {}

    def introduce(sid):
        states[sid] = dict(score=0.0, level=1, consec=0, recent="", box=1,
                           due_at=today, attempts=0, correct=0)
        introduced_at[sid] = total

    def slots():
        return {
            sid: _slot(sid, level=s["level"], score=s["score"], box=s["box"],
                       due_at=s["due_at"],
                       mastered=is_mastered(s["score"], s["level"], mlevel(sid)),
                       max_level=mlevel(sid))
            for sid, s in states.items()
        }

    for sid in sequence[:2]:
        introduce(sid)

    sessions_used = 0
    for session in range(max_sessions):
        sessions_used = session + 1
        today = session
        nxt = next_to_introduce(slots(), sequence)
        if nxt:
            introduce(nxt)
        plan = compose_session(slots(), sequence, today, n=daily_goal)
        for sid in plan:
            s = states[sid]
            ml = mlevel(sid)
            correct = rng.random() < p
            fast = correct and rng.random() < fast_p
            ms = MasteryState(score=s["score"], level=s["level"],
                              consec_correct=s["consec"], recent=s["recent"])
            upd = apply_attempt(ms, ml, correct, fast, attempt_index=s["attempts"])
            s["score"] = upd.state.score
            s["level"] = upd.state.level
            s["consec"] = upd.state.consec_correct
            s["recent"] = upd.state.recent
            s["box"] = update_box(s["box"], correct)
            s["due_at"] = next_due(today, s["box"])
            s["attempts"] += 1
            s["correct"] += int(correct)
            total += 1
            if upd.mastered_now and sid not in mastered_at:
                mastered_at[sid] = total
        if len(states) == len(sequence) and all(
            is_mastered(st["score"], st["level"], mlevel(sid)) for sid, st in states.items()
        ):
            break

    return dict(sequence=sequence, introduced_at=introduced_at, mastered_at=mastered_at,
                sessions=sessions_used, total=total, states=states, mlevel=mlevel)


def _fmt_climb(label, max_level, p, fast_p):
    ups, mastered = climb_one_skill(max_level, p, fast_p)
    steps = " ".join(f"L{lv}@{ups[lv]}" for lv in sorted(ups))
    return f"  {label:18} max_level={max_level}: {steps or '(no promotions)'}  mastered@{mastered}"


def main():
    print("=" * 78)
    print("WITHIN-SKILL DWELL TIME  (question index at each promotion / at mastery)")
    print("=" * 78)
    for p, fast_p, label in [(0.95, 0.85, "strong p=.95"), (0.85, 0.6, "average p=.85"),
                             (0.7, 0.4, "struggling p=.70")]:
        print(f"\n {label}")
        print(_fmt_climb("3-level skill", 3, p, fast_p))
        print(_fmt_climb("4-level skill", 4, p, fast_p))
        print(_fmt_climb("5-level skill", 5, p, fast_p))

    print("\n" + "=" * 78)
    print("SEQUENCE CADENCE  (cumulative questions answered when each skill unlocks)")
    print("  override=None reads the live (re-banded) class max_levels.")
    print("=" * 78)
    for p in (0.95, 0.85, 0.7):
        r = simulate_sequence(grade=2, p=p, override=None)
        seq = r["sequence"]
        intro = r["introduced_at"]
        order = [s for s in seq if s in intro]
        milestones = {3: order[2] if len(order) > 2 else None,
                      5: order[4] if len(order) > 4 else None,
                      8: order[7] if len(order) > 7 else None}
        line = ", ".join(f"#{k}skill@{intro[v]}q" for k, v in milestones.items() if v)
        print(f"\n live re-banded  p={p}")
        print(f"   skills unlocked: {len(intro)}/{len(seq)} in {r['sessions']} sessions "
              f"({r['total']} questions)")
        print(f"   {line}")
        print(f"   skills mastered: {len(r['mastered_at'])}/{len(seq)}")


if __name__ == "__main__":
    main()
