"""Recompute mastery without blank or duplicate submissions, as a reviewable diff.

Usage:
    uv run python -m tools.rebuild_state SNAPSHOT.db            # report only
    uv run python -m tools.rebuild_state SNAPSHOT.db --emit-sql out.sql

Blank submits (fixed in the app: they are no longer recorded) and double-submitted
answers depressed some skill scores, Leitner boxes and the `recent` window. This
replays each affected skill's attempts through the current mastery rules twice:

1. faithfully, blanks included. If that reproduces the stored state, the replay
   models this skill's history and the correction can be trusted;
2. without blank/duplicate rows. The difference is the proposed correction.

Skills whose faithful replay does not reproduce the stored row (their history crosses
a rule change, such as the July re-banding or teaching-mode gating) are reported and
left alone. Nothing is written to any database; --emit-sql writes UPDATE statements
for review, to be applied with `npx wrangler d1 execute mathkids --remote --file ...`.
Attempt rows themselves are never deleted: history keeps every submission.
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date
from pathlib import Path

from mathkids import learning
from mathkids.engine import REGISTRY
from mathkids.mastery import MasteryState, apply_attempt, is_mastered
from mathkids.scheduler import next_due, update_box

FAST_MS = 8000
FIELDS = ("score", "level", "consec_correct", "recent", "box", "due_at", "attempts", "correct")
TEACHING_START = date(2026, 9, 9).toordinal()


def is_blank(row) -> bool:
    return not (row["given"] or "").strip()


def replay(rows: list, max_level: int, skill_id: str, start_level: int = 1) -> dict:
    st = MasteryState(level=start_level)
    box, due, n, ok = 1, 0, 0, 0
    for r in rows:
        correct = bool(r["correct"])
        fast = 0 < r["response_ms"] < FAST_MS and not (
            skill_id in learning.SUPPORTED and r["day"] >= TEACHING_START)
        st = apply_attempt(st, max_level, correct, fast, attempt_index=n).state
        box = update_box(box, correct)
        due = next_due(r["day"], box)
        n += 1
        ok += int(correct)
    return dict(score=st.score, level=st.level, consec_correct=st.consec_correct,
                recent=st.recent, box=box, due_at=due, attempts=n, correct=ok)


def same(a: dict, b: dict) -> bool:
    return all(abs(a[k] - b[k]) < 1e-9 if isinstance(a[k], float) else a[k] == b[k]
               for k in FIELDS)


def analyse(path: str) -> tuple[list[dict], list[str]]:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    kids = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM kid")}
    fixes, skipped = [], []
    for st in con.execute("SELECT * FROM skill_state ORDER BY kid_id, skill_id").fetchall():
        rows = con.execute("SELECT * FROM attempt WHERE kid_id=? AND skill_id=? ORDER BY id",
                           (st["kid_id"], st["skill_id"])).fetchall()
        seen, clean = set(), []
        for r in rows:
            key = (r["session_id"], r["prompt"], r["given"], r["created_at"])
            if is_blank(r) or key in seen:
                continue
            seen.add(key)
            clean.append(r)
        if len(clean) == len(rows):
            continue
        skill = REGISTRY[st["skill_id"]]
        label = f"{kids[st['kid_id']]} {st['skill_id']}"
        stored = {k: st[k] for k in FIELDS}
        removed = len(rows) - len(clean)
        if same(replay(rows, skill.max_level, skill.id), stored):
            new, how = replay(clean, skill.max_level, skill.id), "full replay"
        else:
            new, how = undo_tail(rows, clean, stored), "undo trailing blank misses"
        if new is None:
            skipped.append(f"{label}: {removed} blank/duplicate rows, but later answers have "
                           "superseded them and the history does not replay under today's "
                           "rules; left unchanged (the app now ignores them anyway)")
            continue
        fixes.append(dict(kid_id=st["kid_id"], skill_id=st["skill_id"], label=label, how=how,
                          removed=removed, before=stored, after=new,
                          mastered=is_mastered(new["score"], new["level"], skill.max_level)))
    con.close()
    return fixes, skipped


def undo_tail(rows: list, clean: list, stored: dict) -> dict | None:
    """Reverse blank misses that are a skill's most recent answers.

    A miss only scales the score by (1 - ALPHA * PENALTY), so k trailing blank misses
    are undone exactly by dividing k times. The level returns to the level the first
    blank was asked at (blanks are what demoted it). `recent` and the streak are
    rebuilt from the kept answers. The Leitner box cannot be recovered exactly after it
    reached 1, so it is set no higher than it provably was (and reviews come soon).
    Returns None when other rows are involved."""
    kept_ids = {r["id"] for r in clean}
    last_kept = max((i for i, r in enumerate(rows) if r["id"] in kept_ids), default=-1)
    tail = rows[last_kept + 1:]
    if not tail or len(rows) - len(clean) != len(tail) or any(r["correct"] for r in tail):
        return None
    from mathkids.mastery import ALPHA, PENALTY, RECENT_WINDOW
    score = min(1.0, stored["score"] / (1 - ALPHA * PENALTY) ** len(tail))
    level = tail[0]["level"]
    streak = 0
    for r in reversed(clean):
        if not r["correct"] or r["level"] != level:
            break
        streak += 1
    box = min(5, stored["box"] + len(tail)) if stored["box"] > 1 else 2
    last_day = clean[-1]["day"] if clean else rows[0]["day"]
    return dict(score=score, level=level, consec_correct=streak,
                recent="".join(str(r["correct"]) for r in clean[-RECENT_WINDOW:]),
                box=box, due_at=next_due(last_day, box), attempts=stored["attempts"] - len(tail),
                correct=stored["correct"])


def to_sql(fix: dict) -> str:
    sets = ", ".join(f"{k} = {fix['after'][k]!r}" if k != "recent" else f"recent = '{fix['after'][k]}'"
                     for k in FIELDS)
    guard = " AND ".join(
        f"{k} = {fix['before'][k]!r}" if k != "recent" else f"recent = '{fix['before'][k]}'"
        for k in ("attempts", "correct", "level", "recent"))
    # Guarded on the old values: if the kid practised since the snapshot, nothing changes.
    return (f"UPDATE skill_state SET {sets} WHERE kid_id = {fix['kid_id']} "
            f"AND skill_id = '{fix['skill_id']}' AND {guard};")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("snapshot")
    parser.add_argument("--emit-sql", type=Path)
    args = parser.parse_args()
    fixes, skipped = analyse(args.snapshot)
    for f in fixes:
        print(f"{f['label']}: {f['removed']} blank/duplicate rows dropped ({f['how']})")
        for k in FIELDS:
            if f["before"][k] != f["after"][k]:
                print(f"    {k}: {f['before'][k]!r} -> {f['after'][k]!r}")
    for s in skipped:
        print("SKIPPED", s)
    if args.emit_sql:
        args.emit_sql.write_text("\n".join(to_sql(f) for f in fixes) + "\n", encoding="utf-8")
        print(f"wrote {len(fixes)} statements to {args.emit_sql}")


if __name__ == "__main__":
    main()
