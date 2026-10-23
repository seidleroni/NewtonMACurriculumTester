"""Plain-sentence health checks for the parent view, one per invariant.

Each check reads stored rows and says something only when it is wrong, so an empty
list means all is well. Time is measured in practice nights (days with a finished
set), not calendar days, so a holiday is not mistaken for a stall. The September
teaching rollout broke the first three for weeks before anyone looked; these are the
same invariants tools/simulate_teaching.py checks before a change ships.
"""
from __future__ import annotations

import json
from datetime import date
from statistics import median

from mathkids import learning
from mathkids.engine import REGISTRY

REVIEW_NIGHTS = 4       # a due review waiting this many practice nights
NEW_SKILL_NIGHTS = 10   # practice nights without a new skill while some are locked
SHORT_SET = 8           # median answers per set below this
LESSON_NIGHTS = 10      # nights a skill may be taught without one unaided answer
BLANK_DAYS = 30


async def kid_health(dbx, kid_id: int, sequence: list[str], today: int) -> list[str]:
    sessions = await dbx.all(
        """SELECT s.id, s.day, s.plan, l.used FROM session s
           LEFT JOIN learning_session l ON l.session_id = s.id
           WHERE s.kid_id = ? AND s.ended_at IS NOT NULL AND s.answered > 0
           ORDER BY s.id""", kid_id)
    nights = sorted({s["day"] for s in sessions})
    states = {r["skill_id"]: r for r in await dbx.all(
        "SELECT * FROM skill_state WHERE kid_id = ?", kid_id)}
    attempts = await dbx.all(
        "SELECT skill_id, day, given FROM attempt WHERE kid_id = ?", kid_id)
    taught = await dbx.all(
        """SELECT DISTINCT a.skill_id, s.day FROM practice_activity a
           JOIN session s ON s.id = a.session_id
           WHERE a.kid_id = ? AND a.mode IN ('guided','faded')""", kid_id)
    warnings = []

    def nights_since(day: int) -> int:
        return sum(1 for n in nights if n >= day)

    due = [(nights_since(r["due_at"]), sid) for sid, r in states.items()
           if r["attempts"] and r["due_at"] <= today and sid in REGISTRY]
    if due:
        waited, sid = max(due)
        if waited >= REVIEW_NIGHTS:
            warnings.append(f"{REGISTRY[sid].title} ({sid}) has waited {waited} practice "
                            "nights for its review.")

    locked = [s for s in sequence if s not in states]
    introduced = [date.fromisoformat(r["introduced_at"][:10]).toordinal()
                  for r in states.values() if r["introduced_at"]]
    if locked and introduced:
        since = nights_since(max(introduced) + 1)
        if since >= NEW_SKILL_NIGHTS:
            warnings.append(f"No new skill in {since} practice nights.")

    recent = sessions[-5:]
    sizes = [s["used"] if s["used"] is not None else len(json.loads(s["plan"])) for s in recent]
    if len(sizes) >= 3 and median(sizes) < SHORT_SET:
        warnings.append(f"Recent sets were short: a median of {median(sizes):g} answers "
                        f"over the last {len(sizes)}.")

    window = set(nights[-LESSON_NIGHTS:])
    lessons = {r["skill_id"] for r in taught if r["day"] in window}
    unaided = {a["skill_id"] for a in attempts if a["day"] in window and (a["given"] or "").strip()}
    for sid in sorted(lessons - unaided):
        if sid in learning.SUPPORTED:
            warnings.append(f"{REGISTRY[sid].title} ({sid}) has had lessons but no problem "
                            f"solved without help in {len(window)} practice nights.")

    blanks = sum(1 for a in attempts
                 if a["day"] > today - BLANK_DAYS and not (a["given"] or "").strip())
    if blanks:
        warnings.append(f"{blanks} blank answer{'s' if blanks != 1 else ''} recorded in the "
                        f"last {BLANK_DAYS} days (no longer possible since the fix).")
    return warnings
