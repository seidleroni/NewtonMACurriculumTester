"""Replay future practice nights through the real app, on a copy of a database.

Usage:
    uv run python -m tools.simulate_teaching backups/d1-snapshot-20261023.db
    uv run python -m tools.simulate_teaching SNAPSHOT --nights 12 --slip 0.05 --seed 3
    uv run python -m tools.simulate_teaching SNAPSHOT --nights 1 --show   # tomorrow's sets

Unlike tools/simulate_ramp.py (pure mastery/scheduler math), this drives the actual
routes (start, play, answer, step) with a simulated calendar, so the teaching engine,
budget and scheduler interact exactly as they do for the kids. The source file is
never modified. Each night prints, per kid: answers given, minutes-equivalent (answers),
reviews served, deferred slots, new skills, and what was taught.

Invariants checked (and listed at the end when broken):
  * every night serves the kid's most overdue review, if any was due;
  * a night has at least MIN_RESPONSES answers unless the plan ran out;
  * a skill being taught gets at least one unaided whole problem every night.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

MIN_RESPONSES = 8
ANSWER_FIELDS = re.compile(r'name="(\w+)" value="([^"]*)"')


@dataclass
class Night:
    kid: str
    day: str
    responses: int = 0
    whole: int = 0
    reviews: list[str] = field(default_factory=list)
    deferred: list[str] = field(default_factory=list)
    taught: list[str] = field(default_factory=list)
    new_skills: list[str] = field(default_factory=list)
    most_overdue: str | None = None
    shown: list[str] = field(default_factory=list)  # every question asked, in order


def practice_days(start: date, nights: int, weekdays: set[int]) -> list[date]:
    days, d = [], start
    while len(days) < nights:
        if d.weekday() in weekdays:
            days.append(d)
        d += timedelta(days=1)
    return days


def simulate(source: str | Path, nights: int = 10, slip: float = 0.0, seed: int = 1,
             weekdays: set[int] = frozenset({0, 1, 2, 3}), start: date | None = None,
             kids: list[int] | None = None) -> tuple[list[Night], list[str]]:
    """Run `nights` practice nights for each kid. Returns per-night records and a list of
    broken invariants (empty when everything held)."""
    tmp = Path(tempfile.mkdtemp()) / "sim.db"
    shutil.copy(source, tmp)
    old_env = {k: os.environ.get(k) for k in ("MATHKIDS_DB", "MATHKIDS_TEACHING")}
    os.environ.update(MATHKIDS_DB=str(tmp), MATHKIDS_TEACHING="1")
    from fastapi.testclient import TestClient

    from mathkids import app as app_module
    from mathkids import db
    from mathkids.engine import REGISTRY

    clock = {"day": date.today()}
    real = (db.today_ordinal, db.now_iso)
    db.today_ordinal = lambda: clock["day"].toordinal()
    db.now_iso = lambda: datetime.combine(clock["day"], datetime.min.time()).replace(
        hour=19).isoformat(timespec="seconds") + "-04:00"
    rng = random.Random(seed)
    records: list[Night] = []
    broken: list[str] = []
    try:
        with TestClient(app_module.app) as c:
            dbx = db.SqliteDB(str(tmp))
            kid_rows = [k for k in dbx._conn.execute("SELECT * FROM kid").fetchall()
                        if kids is None or k["id"] in kids]
            last = dbx._conn.execute("SELECT MAX(day) FROM session").fetchone()[0]
            first = start or (date.fromordinal(last) + timedelta(days=1) if last else date.today())
            for day in practice_days(first, nights, set(weekdays)):
                clock["day"] = day
                for kid in kid_rows:
                    records.append(night(c, dbx, kid, day, rng, slip, REGISTRY, app_module, broken))
            dbx.close()
    finally:
        db.today_ordinal, db.now_iso = real
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp.parent, ignore_errors=True)
    return records, broken


def night(c, dbx, kid, day, rng, slip, registry, app_module, broken) -> Night:
    kid_id = kid["id"]
    today = day.toordinal()
    rec = Night(kid=kid["name"], day=day.isoformat())
    before = {r["skill_id"] for r in dbx._conn.execute(
        "SELECT skill_id FROM skill_state WHERE kid_id=?", (kid_id,))}
    due = dbx._conn.execute(
        "SELECT skill_id FROM skill_state WHERE kid_id=? AND due_at<=? ORDER BY due_at, score",
        (kid_id, today)).fetchall()
    rec.most_overdue = due[0]["skill_id"] if due else None
    page = c.post(f"/kid/{kid_id}/start")
    sid = dbx._conn.execute("SELECT MAX(id) FROM session WHERE kid_id=?", (kid_id,)).fetchone()[0]
    for _ in range(200):
        text = page.text
        if f'action="/kid/{kid_id}/seen"' in text:
            skill = re.search(r'name="skill_id" value="([^"]+)"', text)[1]
            page = c.post(f"/kid/{kid_id}/seen", data={"skill_id": skill})
        elif f'action="/kid/{kid_id}/answer"' in text:
            fields = dict(ANSWER_FIELDS.findall(text))
            plan = json.loads(dbx._conn.execute("SELECT plan FROM session WHERE id=?",
                                                (sid,)).fetchone()[0])
            problem = app_module.regenerate(plan[int(fields["idx"])])
            answer = problem.answer.canonical()
            if rng.random() < slip:
                answer = "999999" if problem.answer.answer_type != "multiple_choice" else "Z"
            page = c.post(f"/kid/{kid_id}/answer", data=dict(
                idx=fields["idx"], session_id=fields["session_id"], answer=answer, ms=9000))
            page = c.get(f"/kid/{kid_id}/play")
        elif f'action="/kid/{kid_id}/step"' in text:
            fields = dict(ANSWER_FIELDS.findall(text))
            act = dbx._conn.execute("SELECT progress FROM practice_activity WHERE id=?",
                                    (int(fields["activity_id"]),)).fetchone()
            progress = json.loads(act["progress"])
            answer = str(progress["steps"][progress["index"]]["answer"])
            if rng.random() < slip:
                answer = "999999"
            page = c.post(f"/kid/{kid_id}/step", data=dict(
                activity_id=fields["activity_id"], session_id=fields["session_id"],
                revision=fields["revision"], answer=answer, ms=9000))
        elif f'id="next" href="/kid/{kid_id}/play"' in text:
            page = c.get(f"/kid/{kid_id}/play")
        else:
            break
    session = dict(dbx._conn.execute("SELECT * FROM session WHERE id=?", (sid,)).fetchone())
    plan = json.loads(session["plan"])
    rec.responses = dbx._conn.execute(
        "SELECT used FROM learning_session WHERE session_id=?", (sid,)).fetchone()[0]
    rec.whole = dbx._conn.execute("SELECT COUNT(*) FROM attempt WHERE session_id=?",
                                  (sid,)).fetchone()[0]
    rec.reviews = [p["skill"] for p in plan if p.get("review")]
    rec.deferred = [p["skill"] for p in plan if p.get("deferred")]
    rec.taught = [f"{r['component']}:{r['band']}/{r['mode']}" for r in dbx._conn.execute(
        "SELECT component, band, mode FROM practice_activity WHERE session_id=? "
        "AND mode IN ('guided','faded')", (sid,))]
    legacy = iter(dbx._conn.execute(
        "SELECT * FROM attempt WHERE session_id=? ORDER BY id", (sid,)).fetchall())
    for slot, item in enumerate(plan[:session["answered"]]):
        act = dbx._conn.execute("SELECT * FROM practice_activity WHERE session_id=? AND slot=?",
                                (sid, slot)).fetchone()
        tag = "review" if item.get("review") else "deferred" if item.get("deferred") else ""
        if act is None:
            if not item.get("deferred"):
                a = next(legacy, None)
                if a:
                    rec.shown.append(f"[{item['skill']}{' ' + tag if tag else ''}] {a['prompt']}")
            continue
        snap = json.loads(act["snapshot"])
        head = f"[{item['skill']} {act['component']}/{act['mode']}{' ' + tag if tag else ''}]"
        why = snap.get("reason", "")
        for r in dbx._conn.execute("SELECT * FROM step_response WHERE activity_id=? ORDER BY revision",
                                   (act["id"],)):
            rec.shown.append(f"{head} {r['prompt']} -> {r['expected']}"
                             f"{'' if r['correct'] else ' (answered ' + r['raw_input'] + ')'}"
                             f"{'  <' + why + '>' if why and r['revision'] == 0 else ''}")
        if act["attempt_id"]:  # whole problems also wrote an attempt row
            next(legacy, None)
    after = {r["skill_id"] for r in dbx._conn.execute(
        "SELECT skill_id FROM skill_state WHERE kid_id=?", (kid_id,))}
    rec.new_skills = sorted(after - before)
    if rec.most_overdue and rec.most_overdue not in [p["skill"] for p in plan
                                                     if not p.get("deferred")]:
        broken.append(f"{rec.day} {rec.kid}: most overdue review {rec.most_overdue} not served")
    if rec.responses < MIN_RESPONSES and session["answered"] < len(plan):
        broken.append(f"{rec.day} {rec.kid}: only {rec.responses} answers")
    taught_skills = {r["skill_id"] for r in dbx._conn.execute(
        "SELECT skill_id FROM practice_activity WHERE session_id=? AND mode IN ('guided','faded')",
        (sid,))}
    unaided = {r["skill_id"] for r in dbx._conn.execute(
        "SELECT skill_id FROM attempt WHERE session_id=?", (sid,))}
    for skill in taught_skills - unaided:
        broken.append(f"{rec.day} {rec.kid}: {skill} taught with no unaided whole problem")
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("snapshot")
    parser.add_argument("--nights", type=int, default=10)
    parser.add_argument("--slip", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--show", action="store_true", help="print every question asked")
    args = parser.parse_args()
    records, broken = simulate(args.snapshot, args.nights, args.slip, args.seed)
    for r in records:
        print(f"{r.day} {r.kid:7} answers={r.responses:2} whole={r.whole:2} "
              f"reviews={','.join(r.reviews) or '-'} deferred={len(r.deferred)} "
              f"taught={','.join(dict.fromkeys(r.taught)) or '-'} "
              f"new={','.join(r.new_skills) or '-'}")
        if args.show:
            for line in r.shown:
                print("      ", line)
    print("\nInvariants:", "all held" if not broken else "")
    for b in broken:
        print("  BROKEN", b)


if __name__ == "__main__":
    main()
