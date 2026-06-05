"""Spaced repetition (Leitner) + daily session composition.

All functions are pure so they can be unit-tested without a database. The app maps
SQLite rows into `Slot`s, calls these, and writes the results back.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

LEITNER_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15}  # box -> days until next review


def update_box(box: int, correct: bool) -> int:
    return min(5, box + 1) if correct else max(1, box - 1)


def next_due(today_ordinal: int, box: int) -> int:
    return today_ordinal + LEITNER_INTERVALS.get(box, 1)


@dataclass
class Slot:
    skill_id: str
    level: int
    score: float
    box: int
    due_at: int
    mastered: bool


def _interleave(plan: list[str]) -> list[str]:
    """Spread repeated skills apart so the same one isn't back-to-back when avoidable."""
    remaining = Counter(plan)
    result: list[str] = []
    last: str | None = None
    while sum(remaining.values()) > 0:
        candidates = sorted(
            (s for s in remaining if remaining[s] > 0),
            key=lambda s: (-remaining[s], s),
        )
        choice = next((s for s in candidates if s != last), candidates[0])
        result.append(choice)
        remaining[choice] -= 1
        last = choice
    return result


def compose_session(
    slots: dict[str, Slot], sequence: list[str], today_ordinal: int, n: int = 12
) -> list[str]:
    """Return an ordered list of skill ids (length <= n) for today's session."""
    active = [sid for sid in sequence if sid in slots]
    if not active:
        return []
    non_mastered = [sid for sid in active if not slots[sid].mastered] or active

    due = sorted(
        (sid for sid in non_mastered if slots[sid].due_at <= today_ordinal),
        key=lambda s: (slots[s].due_at, slots[s].score),
    )
    focus = non_mastered[0]

    plan: list[str] = [sid for sid in due[:5] if sid != focus]
    plan += [focus] * 5
    stretch = next((s for s in non_mastered if s != focus), None)
    if stretch:
        plan.append(stretch)

    weak = sorted(non_mastered, key=lambda s: (slots[s].score, s))
    i = 0
    while len(plan) < n and weak:
        plan.append(weak[i % len(weak)])
        i += 1

    return _interleave(plan[:n])


def next_to_introduce(
    slots: dict[str, Slot], sequence: list[str], max_active_unmastered: int = 4
) -> str | None:
    """Return the next locked skill to introduce, or None if it's not time yet."""
    introduced = set(slots)
    locked = [s for s in sequence if s not in introduced]
    if not locked:
        return None
    active_unmastered = [s for s in introduced if not slots[s].mastered]
    if len(active_unmastered) >= max_active_unmastered:
        return None
    ready = all(
        (slots[s].level >= 2 or slots[s].score >= 0.5 or slots[s].mastered)
        for s in active_unmastered
    )
    if active_unmastered and not ready:
        return None
    return locked[0]
