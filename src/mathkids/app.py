"""FastAPI app: the daily loop + dashboards, server-rendered (classic form posts)."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from mathkids import assets, db
from mathkids.engine import REGISTRY, SEQUENCES, Problem
from mathkids.mastery import MasteryState, apply_attempt, is_mastered, stars
from mathkids.scheduler import Slot, compose_session, next_due, next_to_introduce, update_box

FAST_MS = 8000  # answers quicker than this earn the speed bonus

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.globals["star_bar"] = lambda n: "★" * int(n) + "☆" * (5 - int(n))

@asynccontextmanager
async def lifespan(_app: "FastAPI"):
    conn = db.connect()
    db.init_db(conn)
    conn.close()
    yield


app = FastAPI(title="Newton Math", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


# --- helpers --------------------------------------------------------------

def grade_sequence(grade: int) -> list[str]:
    return SEQUENCES.get(grade, [])


def row_to_slot(row, skill) -> Slot:
    return Slot(
        skill_id=skill.id,
        level=row["level"],
        score=row["score"],
        box=row["box"],
        due_at=row["due_at"],
        mastered=is_mastered(row["score"], row["level"], skill.max_level),
    )


def build_slots(states: dict, sequence: list[str]) -> dict[str, Slot]:
    return {
        sid: row_to_slot(states[sid], REGISTRY[sid])
        for sid in sequence
        if sid in states and sid in REGISTRY
    }


def ensure_introductions(conn, kid_id: int, sequence: list[str], today: int, now: str) -> None:
    states = db.get_skill_states(conn, kid_id)
    if not states:
        for sid in sequence[:2]:
            db.introduce_skill(conn, kid_id, sid, today, now)
        return
    nxt = next_to_introduce(build_slots(states, sequence), sequence)
    if nxt:
        db.introduce_skill(conn, kid_id, nxt, today, now)


def regenerate(item: dict) -> Problem:
    skill = REGISTRY[item["skill"]]
    return skill.generate(item["level"], random.Random(item["seed"]))


# --- routes ---------------------------------------------------------------

@app.get("/")
def index(request: Request):
    conn = db.connect()
    try:
        kids = []
        for kid in db.get_kids(conn):
            started = len(db.get_skill_states(conn, kid["id"]))
            kids.append({"row": kid, "started": started})
        return templates.TemplateResponse(request, "index.html", {"kids": kids})
    finally:
        conn.close()


@app.post("/kid/{kid_id}/start")
def start(kid_id: int):
    conn = db.connect()
    try:
        kid = db.get_kid(conn, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        today, now = db.today_ordinal(), db.now_iso()
        active = db.get_active_session(conn, kid_id)
        if active is not None:
            # Resume today's unfinished set rather than discarding its progress;
            # a leftover set from a previous day is closed and replanned fresh.
            if active["day"] == today and active["answered"] < len(json.loads(active["plan"])):
                return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)
            db.end_session(conn, active["id"], now)
        sequence = grade_sequence(kid["grade"])
        ensure_introductions(conn, kid_id, sequence, today, now)
        states = db.get_skill_states(conn, kid_id)
        slots = build_slots(states, sequence)
        plan_ids = compose_session(slots, sequence, today, n=kid["daily_goal"])
        session_id = db.create_session(conn, kid_id, "[]", today, now)
        plan = [
            {"skill": sid, "level": slots[sid].level, "seed": session_id * 1000 + i}
            for i, sid in enumerate(plan_ids)
        ]
        db.update_session_plan(conn, session_id, json.dumps(plan))
        return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)
    finally:
        conn.close()


@app.get("/kid/{kid_id}/play")
def play(request: Request, kid_id: int):
    conn = db.connect()
    try:
        kid = db.get_kid(conn, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        session = db.get_active_session(conn, kid_id)
        if session is None:
            return RedirectResponse("/", status_code=303)
        plan = json.loads(session["plan"])
        idx = session["answered"]
        if idx >= len(plan):
            db.end_session(conn, session["id"], db.now_iso())
            return RedirectResponse(f"/kid/{kid_id}/done", status_code=303)

        item = plan[idx]
        skill = REGISTRY[item["skill"]]
        st = db.get_skill_state(conn, kid_id, skill.id)
        if st["lesson_seen"] == 0:
            return templates.TemplateResponse(
                request,
                "lesson.html",
                {"kid": kid, "skill": skill, "lesson": skill.lesson()},
            )

        problem = regenerate(item)
        image_uri = assets.data_uri(problem.payload["image"]) if problem.payload.get("image") else None
        return templates.TemplateResponse(
            request,
            "problem.html",
            {
                "kid": kid,
                "skill": skill,
                "problem": problem,
                "image_uri": image_uri,
                "idx": idx,
                "num": idx + 1,
                "total": len(plan),
                "stars": stars(st["score"]),
                "level": st["level"],
                "max_level": skill.max_level,
            },
        )
    finally:
        conn.close()


@app.post("/kid/{kid_id}/seen")
def seen(kid_id: int, skill_id: str = Form(...)):
    conn = db.connect()
    try:
        db.save_skill_state(conn, kid_id, skill_id, lesson_seen=1)
        return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)
    finally:
        conn.close()


@app.post("/kid/{kid_id}/answer")
def answer(
    request: Request,
    kid_id: int,
    idx: int = Form(...),
    answer: str = Form(""),
    ms: int = Form(0),
):
    conn = db.connect()
    try:
        kid = db.get_kid(conn, kid_id)
        session = db.get_active_session(conn, kid_id)
        if kid is None or session is None:
            return RedirectResponse("/", status_code=303)
        plan = json.loads(session["plan"])
        if idx != session["answered"] or idx >= len(plan):
            return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)

        item = plan[idx]
        skill = REGISTRY[item["skill"]]
        problem = regenerate(item)
        result = problem.answer.grade(answer)
        correct = result.correct
        fast = 0 < ms < FAST_MS

        st = db.get_skill_state(conn, kid_id, skill.id)
        ms_state = MasteryState(
            score=st["score"],
            level=st["level"],
            consec_correct=st["consec_correct"],
            recent=st["recent"],
        )
        upd = apply_attempt(ms_state, skill.max_level, correct, fast)
        new_box = update_box(st["box"], correct)
        now = db.now_iso()
        today = db.today_ordinal()
        db.save_skill_state(
            conn,
            kid_id,
            skill.id,
            score=upd.state.score,
            level=upd.state.level,
            consec_correct=upd.state.consec_correct,
            recent=upd.state.recent,
            box=new_box,
            due_at=next_due(today, new_box),
            attempts=st["attempts"] + 1,
            correct=st["correct"] + int(correct),
            last_seen_at=now,
            mastered_at=now if upd.mastered_now else st["mastered_at"],
        )
        db.record_attempt(
            conn, kid_id, skill.id, session["id"], item["level"], problem.prompt,
            result.expected_display, result.given_display, correct, ms, today, now,
        )
        db.advance_session(
            conn, session["id"], idx + 1, session["num_correct"] + int(correct)
        )

        return templates.TemplateResponse(
            request,
            "feedback.html",
            {
                "kid": kid,
                "skill": skill,
                "problem": problem,
                "correct": correct,
                "expected": result.expected_display,
                "given": result.given_display,
                "hints": [] if correct else skill.hints(problem)[:2],
                "worked": "" if correct else skill.worked_example(problem),
                "leveled_up": upd.leveled_up,
                "mastered_now": upd.mastered_now,
            },
        )
    finally:
        conn.close()


@app.get("/kid/{kid_id}/done")
def done(request: Request, kid_id: int):
    conn = db.connect()
    try:
        kid = db.get_kid(conn, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        session = db.get_latest_session(conn, kid_id)
        states = db.get_skill_states(conn, kid_id)
        sequence = grade_sequence(kid["grade"])
        nxt = next_to_introduce(build_slots(states, sequence), sequence)

        practiced = []
        if session:
            seen_ids: list[str] = []
            for it in json.loads(session["plan"]):
                if it["skill"] not in seen_ids:
                    seen_ids.append(it["skill"])
            for sid in seen_ids:
                sk = REGISTRY[sid]
                row = states.get(sid)
                practiced.append(
                    {
                        "title": sk.title,
                        "stars": stars(row["score"]) if row else 0,
                        "mastered": is_mastered(row["score"], row["level"], sk.max_level)
                        if row
                        else False,
                    }
                )
        return templates.TemplateResponse(
            request,
            "summary.html",
            {
                "kid": kid,
                "session": session,
                "practiced": practiced,
                "next_skill": REGISTRY[nxt].title if nxt else None,
            },
        )
    finally:
        conn.close()


@app.get("/kid/{kid_id}")
def kid_dashboard(request: Request, kid_id: int):
    conn = db.connect()
    try:
        kid = db.get_kid(conn, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        states = db.get_skill_states(conn, kid_id)
        sequence = grade_sequence(kid["grade"])
        skills = []
        for sid in sequence:
            sk = REGISTRY[sid]
            row = states.get(sid)
            if row:
                skills.append(
                    {
                        "title": sk.title,
                        "domain": sk.domain,
                        "introduced": True,
                        "stars": stars(row["score"]),
                        "level": row["level"],
                        "max_level": sk.max_level,
                        "mastered": is_mastered(row["score"], row["level"], sk.max_level),
                        "recent": db.recent_correctness(conn, kid_id, sid, 8),
                    }
                )
            else:
                skills.append({"title": sk.title, "domain": sk.domain, "introduced": False})
        return templates.TemplateResponse(
            request,
            "kid_dashboard.html",
            {
                "kid": kid,
                "skills": skills,
                "started": sum(1 for sid in sequence if sid in states),
            },
        )
    finally:
        conn.close()


@app.get("/parent")
def parent(request: Request):
    conn = db.connect()
    try:
        today = db.today_ordinal()
        kids_data = []
        for kid in db.get_kids(conn):
            states = db.get_skill_states(conn, kid["id"])
            sequence = grade_sequence(kid["grade"])
            introduced = [sid for sid in sequence if sid in states]

            by_domain: dict[str, list[int]] = defaultdict(list)
            for sid in introduced:
                by_domain[REGISTRY[sid].domain].append(stars(states[sid]["score"]))
            domains = [
                {"domain": d, "stars": round(sum(v) / len(v)) if v else 0}
                for d, v in by_domain.items()
            ]

            slots = build_slots(states, sequence)
            non_mastered = [sid for sid in sequence if sid in slots and not slots[sid].mastered]
            focus = REGISTRY[non_mastered[0]].title if non_mastered else None

            trouble = None
            worst = 2.0
            for sid in introduced:
                row = states[sid]
                if row["attempts"] >= 3:
                    acc = row["correct"] / row["attempts"]
                    if acc < worst:
                        worst, trouble = acc, (REGISTRY[sid].title, round(acc * 100))

            kids_data.append(
                {
                    "kid": kid,
                    "domains": domains,
                    "week": db.week_stats(conn, kid["id"], today),
                    "focus": focus,
                    "trouble": trouble,
                }
            )
        return templates.TemplateResponse(
            request, "parent_dashboard.html", {"kids_data": kids_data}
        )
    finally:
        conn.close()


def main() -> None:  # pragma: no cover - entry point
    import uvicorn

    uvicorn.run("mathkids.app:app", host="127.0.0.1", port=8000, reload=False)
