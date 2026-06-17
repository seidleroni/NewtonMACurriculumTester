"""Leitner spacing + daily session composition + skill introduction gate."""

from collections import Counter

from mathkids.scheduler import (
    LEITNER_INTERVALS,
    Slot,
    compose_session,
    next_due,
    next_to_introduce,
    update_box,
)

SEQ = ["A", "B", "C"]


def slot(skill_id, *, level=1, score=0.0, box=1, due_at=0, mastered=False):
    return Slot(skill_id, level, score, box, due_at, mastered)


def test_update_box():
    assert update_box(1, True) == 2
    assert update_box(5, True) == 5
    assert update_box(3, False) == 2
    assert update_box(1, False) == 1


def test_next_due_uses_interval_table():
    assert next_due(100, 1) == 100 + LEITNER_INTERVALS[1]
    assert next_due(100, 5) == 100 + LEITNER_INTERVALS[5]


def test_compose_session_length_and_focus():
    slots = {s: slot(s, due_at=0) for s in SEQ}
    plan = compose_session(slots, SEQ, today_ordinal=100, n=12)
    assert len(plan) == 12
    assert "A" in plan  # focus = first non-mastered in sequence
    assert set(plan) <= set(SEQ)
    assert len(set(plan)) >= 2  # interleaved across skills


def test_compose_session_interleaves_optimally():
    # With few skills the focus skill is necessarily over-represented, so some
    # adjacency can be unavoidable; assert the interleaver hits the theoretical
    # minimum number of back-to-back repeats: max(0, 2*maxcount - n - 1).
    slots = {s: slot(s, due_at=0) for s in SEQ}
    plan = compose_session(slots, SEQ, today_ordinal=100, n=12)
    back_to_back = sum(1 for i in range(len(plan) - 1) if plan[i] == plan[i + 1])
    maxc = max(Counter(plan).values())
    optimal = max(0, 2 * maxc - len(plan) - 1)
    assert back_to_back == optimal


def test_compose_session_prefers_due_reviews():
    slots = {
        "A": slot("A", due_at=100, score=0.6),  # focus
        "B": slot("B", due_at=90, score=0.3),   # overdue review
        "C": slot("C", due_at=200, score=0.9),  # not due
    }
    plan = compose_session(slots, SEQ, today_ordinal=100, n=12)
    assert "B" in plan


def test_compose_session_handles_all_mastered():
    slots = {s: slot(s, mastered=True, score=1.0) for s in SEQ}
    plan = compose_session(slots, SEQ, today_ordinal=100, n=6)
    assert len(plan) == 6  # light maintenance still produces a session


def test_next_to_introduce_when_ready():
    # "Settled enough" = off the entry floor (level >= 2), regardless of score.
    slots = {"A": slot("A", level=2)}
    assert next_to_introduce(slots, SEQ) == "B"


def test_next_to_introduce_blocks_on_floor():
    # Still on the bottom band (level 1) — even a decent score does not unlock a sibling.
    slots = {"A": slot("A", score=0.49, level=1)}
    assert next_to_introduce(slots, SEQ) is None


def test_next_to_introduce_none_when_all_introduced():
    slots = {s: slot(s, level=2) for s in SEQ}
    assert next_to_introduce(slots, SEQ) is None


def test_next_to_introduce_respects_active_load_cap():
    seq = ["A", "B", "C", "D", "E", "F"]
    slots = {s: slot(s, level=2) for s in seq[:3]}  # 3 active unmastered (the new default cap)
    assert next_to_introduce(slots, seq) is None
    # ...and an explicit higher cap still lets one through.
    assert next_to_introduce(slots, seq, max_active_unmastered=4) == "D"
