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
    attempts: int = 0


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
        (sid for sid in active if slots[sid].due_at <= today_ordinal),
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


MAX_REVIEWS = 4  # due reviews served first in a set
MAX_BLOCK = 5    # reviews plus unaided checks of skills being taught


def compose_blocks(
    slots: dict[str, Slot], sequence: list[str], today_ordinal: int, n: int = 12,
    checks: tuple[str, ...] = (),
) -> tuple[list[str], list[str]]:
    """The same set as `compose_session`, split into a review block served first and the
    rest. Reviews are the most overdue due skills; `checks` (skills being taught) each
    get one slot in the block too, so an unaided answer keeps their mastery moving
    while teaching runs. Teaching and new work can then never crowd out reviews."""
    plan = compose_session(slots, sequence, today_ordinal, n)
    due = sorted(
        (s for s in dict.fromkeys(plan)
         if slots[s].due_at <= today_ordinal and slots[s].attempts > 0),
        key=lambda s: (slots[s].due_at, slots[s].score, s),
    )
    block = due[:MAX_REVIEWS]
    block += [s for s in dict.fromkeys(checks) if s in plan and s not in block]
    block = block[:MAX_BLOCK]
    rest = list(plan)
    for s in block:
        rest.remove(s)
    return block, rest


def _off_the_floor(slot: Slot) -> bool:
    """A skill is 'settled enough' to let a new sibling unlock once it is mastered or
    has climbed at least one band off its trivial entry floor (level >= 2). The deeper
    pacing comes from the load cap plus the deliberately slow per-band leveling in
    mastery.py; this gate just refuses to pile a brand-new skill on a kid who hasn't
    even gotten off the floor of the skills already in play."""
    return slot.mastered or slot.level >= 2


PER_DOMAIN = 2  # unmastered skills in play at once within one domain (lane)


def next_to_introduce(
    slots: dict[str, Slot], sequence: list[str], max_active_unmastered: int = 3,
    domains: dict[str, str] | None = None, prereqs: dict[str, tuple[str, ...]] | None = None,
) -> str | None:
    """Return the next locked skill to introduce, or None if it's not time yet.

    New skills are paced deliberately: never more than `max_active_unmastered` in play
    at once. Without `domains`, a new one unlocks only when every current unmastered
    skill has climbed off its entry floor (see `_off_the_floor`).

    With `domains` (skill -> Common Core domain), each domain is a lane in sequence
    order: a lane's next skill unlocks when that lane's unmastered skills are off the
    floor (at most PER_DOMAIN of them), so one hard area cannot block clocks or shapes
    that do not depend on it. `prereqs` names cross-lane dependencies, which must be
    introduced and off the floor first. Among ready lanes the least loaded wins, then
    curriculum order."""
    introduced = set(slots)
    locked = [s for s in sequence if s not in introduced]
    if not locked:
        return None
    active_unmastered = [s for s in introduced if not slots[s].mastered]
    if len(active_unmastered) >= max_active_unmastered:
        return None
    if domains is None:
        ready = all(_off_the_floor(slots[s]) for s in active_unmastered)
        if active_unmastered and not ready:
            return None
        return locked[0]
    prereqs = prereqs or {}
    candidates = []
    for lane in dict.fromkeys(domains[s] for s in locked):
        skill = next(s for s in locked if domains[s] == lane)
        busy = [s for s in active_unmastered if domains.get(s) == lane]
        if len(busy) >= PER_DOMAIN or not all(_off_the_floor(slots[s]) for s in busy):
            continue
        if not all(p in slots and _off_the_floor(slots[p]) for p in prereqs.get(skill, ())):
            continue
        candidates.append((len(busy), sequence.index(skill), skill))
    return min(candidates)[2] if candidates else None
