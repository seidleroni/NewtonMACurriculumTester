"""Read-only practice history. Days come from responses, not the server timezone."""
from __future__ import annotations

import json
from collections import Counter
from datetime import date


async def daily_history(dbx, kid_id: int, selected: str | None) -> dict:
    days = await dbx.all(
        """SELECT day FROM attempt WHERE kid_id=?
           UNION SELECT r.day FROM step_response r JOIN practice_activity a ON a.id=r.activity_id
                 WHERE a.kid_id=?
           UNION SELECT day FROM session WHERE kid_id=? ORDER BY day DESC""",
        kid_id, kid_id, kid_id,
    )
    ordinals = [r["day"] for r in days]
    chosen = date.fromisoformat(selected).toordinal() if selected else (
        ordinals[0] if ordinals else date.today().toordinal()
    )
    attempts = await dbx.all(
        "SELECT * FROM attempt WHERE kid_id=? AND day=? ORDER BY id", kid_id, chosen
    )
    sessions = await dbx.all(
        """SELECT DISTINCT s.* FROM session s WHERE s.kid_id=? AND
           (s.day=? OR s.id IN (SELECT session_id FROM attempt WHERE kid_id=? AND day=?)
            OR s.id IN (SELECT a.session_id FROM practice_activity a JOIN step_response r
                        ON r.activity_id=a.id WHERE a.kid_id=? AND r.day=?)) ORDER BY s.id""",
        kid_id, chosen, kid_id, chosen, kid_id, chosen,
    )
    responses = await dbx.all(
        """SELECT r.*,a.session_id,a.slot,a.snapshot,a.outcome,a.attempt_id,a.mode AS activity_mode
           FROM step_response r JOIN practice_activity a ON a.id=r.activity_id
           WHERE a.kid_id=? AND r.day=? ORDER BY r.id""", kid_id, chosen,
    )
    linked = {r["attempt_id"] for r in responses if r["attempt_id"] is not None}
    repeats = Counter((a["session_id"], a["skill_id"], a["prompt"], a["given"],
                       a["expected"], a["created_at"]) for a in attempts)
    groups = {s["id"]: dict(session=s, entries=[]) for s in sessions}
    activities = {}
    for r in responses:
        aid = r["activity_id"]
        if aid not in activities:
            snap = json.loads(r["snapshot"])
            entry = dict(kind="activity", prompt=snap["prompt"], steps=[], time=r["created_at"],
                         outcome=r["outcome"], mode=r["activity_mode"])
            activities[aid] = entry
            groups.setdefault(r["session_id"], dict(session=None, entries=[]))["entries"].append(entry)
        activities[aid]["steps"].append(r)
    for a in attempts:
        if a["id"] in linked:
            continue
        entry = dict(kind="attempt", row=a, time=a["created_at"],
                     repeated=repeats[(a["session_id"], a["skill_id"], a["prompt"], a["given"],
                                       a["expected"], a["created_at"])] > 1)
        groups.setdefault(a["session_id"], dict(session=None, entries=[]))["entries"].append(entry)
    for group in groups.values():
        group["entries"].sort(key=lambda e: e["time"])
    return dict(
        selected=date.fromordinal(chosen).isoformat(),
        days=[date.fromordinal(d).isoformat() for d in ordinals], groups=list(groups.values()),
        total=len(attempts), correct=sum(a["correct"] for a in attempts), steps=len(responses),
        older=next((date.fromordinal(d).isoformat() for d in ordinals if d < chosen), None),
        newer=next((date.fromordinal(d).isoformat() for d in reversed(ordinals) if d > chosen), None),
    )
