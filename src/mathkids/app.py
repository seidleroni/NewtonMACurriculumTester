"""FastAPI app: the daily loop + dashboards, server-rendered (classic form posts).

Runs in two environments: locally under uvicorn against sqlite (``uv run
mathkids``), and on Cloudflare Workers against D1 (``src/worker.py`` is the
entry point there; the D1 binding arrives per-request via request.scope["env"]).
"""

from __future__ import annotations

import json
import random
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import jinja2
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from mathkids import db
from mathkids.engine import REGISTRY, SEQUENCES, Problem
from mathkids.mastery import MasteryState, apply_attempt, is_mastered, stars
from mathkids.scheduler import Slot, compose_session, next_due, next_to_introduce, update_box

FAST_MS = 8000  # answers quicker than this earn the speed bonus

IS_WORKERS = sys.platform == "emscripten"  # Pyodide (the Workers runtime)

BASE = Path(__file__).parent


def _jinja_env() -> jinja2.Environment:
    # The Workers bundle carries only .py modules, so templates ship baked into
    # a generated module (tools/embed_templates.py, run by wrangler's build
    # hook). Local dev reads the live files.
    if IS_WORKERS:
        from mathkids._templates_embedded import TEMPLATES

        loader: jinja2.BaseLoader = jinja2.DictLoader(TEMPLATES)
    else:
        loader = jinja2.FileSystemLoader(str(BASE / "templates"))
    return jinja2.Environment(loader=loader, autoescape=True)


templates = Jinja2Templates(env=_jinja_env())
templates.env.globals["star_bar"] = lambda n: "★" * int(n) + "☆" * (5 - int(n))


@asynccontextmanager
async def lifespan(_app: "FastAPI"):
    if not IS_WORKERS:  # on Workers the schema comes from D1 migrations
        dbx = db.SqliteDB()
        await db.init_db(dbx)
        dbx.close()
    yield


app = FastAPI(title="Newton Math", lifespan=lifespan)

if not IS_WORKERS:  # on Workers, /static/* is served from the edge (wrangler assets)
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/static",
        StaticFiles(directory=str(BASE.parents[1] / "public" / "static")),
        name="static",
    )


# --- helpers --------------------------------------------------------------

def database(request: Request):
    """Pick the storage backend for this request: D1 on Workers, sqlite locally."""
    env = request.scope.get("env")
    if env is not None:
        return db.D1DB(env.DB)
    return db.SqliteDB()


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


async def ensure_introductions(dbx, kid_id: int, sequence: list[str], today: int, now: str) -> None:
    states = await db.get_skill_states(dbx, kid_id)
    if not states:
        for sid in sequence[:2]:
            await db.introduce_skill(dbx, kid_id, sid, today, now)
        return
    nxt = next_to_introduce(build_slots(states, sequence), sequence)
    if nxt:
        await db.introduce_skill(dbx, kid_id, nxt, today, now)


def regenerate(item: dict) -> Problem:
    skill = REGISTRY[item["skill"]]
    return skill.generate(item["level"], random.Random(item["seed"]))


def celebration_headline(num_correct: int, answered: int) -> tuple[str, str]:
    """(emoji, headline) for the summary page. Every tier celebrates —
    finishing the day's set is the achievement."""
    pct = 100 * num_correct / answered if answered else 0
    if pct == 100:
        return "💯", "Perfect day!"
    if pct >= 90:
        return "🌟", "Outstanding!"
    if pct >= 75:
        return "🎉", "Great job!"
    if pct >= 50:
        return "💪", "Strong work!"
    return "✅", "You finished it!"


# --- routes ---------------------------------------------------------------

@app.get("/")
async def index(request: Request):
    dbx = database(request)
    try:
        kids = []
        for kid in await db.get_kids(dbx):
            started = len(await db.get_skill_states(dbx, kid["id"]))
            kids.append({"row": kid, "started": started})
        return templates.TemplateResponse(request, "index.html", {"kids": kids})
    finally:
        dbx.close()


@app.post("/kid/{kid_id}/start")
async def start(request: Request, kid_id: int):
    dbx = database(request)
    try:
        kid = await db.get_kid(dbx, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        today, now = db.today_ordinal(), db.now_iso()
        active = await db.get_active_session(dbx, kid_id)
        if active is not None:
            # Resume today's unfinished set rather than discarding its progress;
            # a leftover set from a previous day is closed and replanned fresh.
            if active["day"] == today and active["answered"] < len(json.loads(active["plan"])):
                return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)
            await db.end_session(dbx, active["id"], now)
        sequence = grade_sequence(kid["grade"])
        await ensure_introductions(dbx, kid_id, sequence, today, now)
        states = await db.get_skill_states(dbx, kid_id)
        slots = build_slots(states, sequence)
        plan_ids = compose_session(slots, sequence, today, n=kid["daily_goal"])
        session_id = await db.create_session(dbx, kid_id, "[]", today, now)
        plan = [
            {"skill": sid, "level": slots[sid].level, "seed": session_id * 1000 + i}
            for i, sid in enumerate(plan_ids)
        ]
        await db.update_session_plan(dbx, session_id, json.dumps(plan))
        return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)
    finally:
        dbx.close()


@app.get("/kid/{kid_id}/play")
async def play(request: Request, kid_id: int):
    dbx = database(request)
    try:
        kid = await db.get_kid(dbx, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        session = await db.get_active_session(dbx, kid_id)
        if session is None:
            return RedirectResponse("/", status_code=303)
        plan = json.loads(session["plan"])
        idx = session["answered"]
        if idx >= len(plan):
            await db.end_session(dbx, session["id"], db.now_iso())
            return RedirectResponse(f"/kid/{kid_id}/done", status_code=303)

        item = plan[idx]
        skill = REGISTRY[item["skill"]]
        st = await db.get_skill_state(dbx, kid_id, skill.id)
        if st["lesson_seen"] == 0:
            return templates.TemplateResponse(
                request,
                "lesson.html",
                {"kid": kid, "skill": skill, "lesson": skill.lesson()},
            )

        problem = regenerate(item)
        image_spec = (
            json.dumps(problem.payload["image"]) if problem.payload.get("image") else None
        )
        return templates.TemplateResponse(
            request,
            "problem.html",
            {
                "kid": kid,
                "skill": skill,
                "problem": problem,
                "image_spec": image_spec,
                "idx": idx,
                "num": idx + 1,
                "total": len(plan),
                "stars": stars(st["score"]),
                "level": st["level"],
                "max_level": skill.max_level,
            },
        )
    finally:
        dbx.close()


@app.post("/kid/{kid_id}/seen")
async def seen(request: Request, kid_id: int, skill_id: str = Form(...)):
    dbx = database(request)
    try:
        await db.save_skill_state(dbx, kid_id, skill_id, lesson_seen=1)
        return RedirectResponse(f"/kid/{kid_id}/play", status_code=303)
    finally:
        dbx.close()


@app.post("/kid/{kid_id}/answer")
async def answer(
    request: Request,
    kid_id: int,
    idx: int = Form(...),
    answer: str = Form(""),
    ms: int = Form(0),
):
    dbx = database(request)
    try:
        kid = await db.get_kid(dbx, kid_id)
        session = await db.get_active_session(dbx, kid_id)
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

        st = await db.get_skill_state(dbx, kid_id, skill.id)
        ms_state = MasteryState(
            score=st["score"],
            level=st["level"],
            consec_correct=st["consec_correct"],
            recent=st["recent"],
        )
        upd = apply_attempt(
            ms_state, skill.max_level, correct, fast, attempt_index=st["attempts"]
        )
        if upd.state.level != st["level"]:
            # Within-session adaptivity (DESIGN §7.3): the rest of today's plan
            # for this skill follows the kid to the new level immediately.
            for it in plan[idx + 1 :]:
                if it["skill"] == skill.id:
                    it["level"] = upd.state.level
            await db.update_session_plan(dbx, session["id"], json.dumps(plan))
        new_box = update_box(st["box"], correct)
        now = db.now_iso()
        today = db.today_ordinal()
        await db.save_skill_state(
            dbx,
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
        await db.record_attempt(
            dbx, kid_id, skill.id, session["id"], item["level"], problem.prompt,
            result.expected_display, result.given_display, correct, ms, today, now,
        )
        await db.advance_session(
            dbx, session["id"], idx + 1, session["num_correct"] + int(correct)
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
        dbx.close()


@app.get("/kid/{kid_id}/done")
async def done(request: Request, kid_id: int):
    dbx = database(request)
    try:
        kid = await db.get_kid(dbx, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        session = await db.get_latest_session(dbx, kid_id)
        states = await db.get_skill_states(dbx, kid_id)
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
        emoji, headline = celebration_headline(
            session["num_correct"] if session else 0,
            session["answered"] if session else 0,
        )
        today_prefix = db.now_iso()[:10]
        mastered_today = [
            REGISTRY[sid].title
            for sid, row in states.items()
            if sid in REGISTRY
            and row["mastered_at"]
            and row["mastered_at"].startswith(today_prefix)
        ]
        # All-time century milestone (only-up signal): did this session push the
        # kid's lifetime total past a multiple of 100?
        milestone = None
        if session:
            total = await db.total_attempts(dbx, kid_id)
            before = total - session["answered"]
            if total >= 100 and total // 100 > before // 100:
                milestone = total // 100 * 100

        return templates.TemplateResponse(
            request,
            "summary.html",
            {
                "kid": kid,
                "session": session,
                "practiced": practiced,
                "next_skill": REGISTRY[nxt].title if nxt else None,
                "emoji": emoji,
                "headline": headline,
                "mastered_today": mastered_today,
                "milestone": milestone,
            },
        )
    finally:
        dbx.close()


async def domain_groups(dbx, kid_id: int, states: dict, sequence: list[str]) -> list[dict]:
    """Group a kid's skill sequence by Common Core domain, in curriculum order."""
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for sid in sequence:
        sk = REGISTRY[sid]
        g = by_name.get(sk.domain)
        if g is None:
            g = {"domain": sk.domain, "skills": [], "started": 0}
            by_name[sk.domain] = g
            groups.append(g)
        row = states.get(sid)
        if row:
            g["started"] += 1
            g["skills"].append(
                {
                    "title": sk.title,
                    "introduced": True,
                    "stars": stars(row["score"]),
                    "level": row["level"],
                    "max_level": sk.max_level,
                    "mastered": is_mastered(row["score"], row["level"], sk.max_level),
                    "recent": await db.recent_correctness(dbx, kid_id, sid, 8),
                }
            )
        else:
            g["skills"].append({"title": sk.title, "introduced": False})
    for g in groups:
        vals = [s["stars"] for s in g["skills"] if s["introduced"]]
        g["avg_stars"] = round(sum(vals) / len(vals)) if vals else 0
    return groups


@app.get("/kid/{kid_id}")
async def kid_dashboard(request: Request, kid_id: int):
    dbx = database(request)
    try:
        kid = await db.get_kid(dbx, kid_id)
        if kid is None:
            return RedirectResponse("/", status_code=303)
        states = await db.get_skill_states(dbx, kid_id)
        sequence = grade_sequence(kid["grade"])
        return templates.TemplateResponse(
            request,
            "kid_dashboard.html",
            {
                "kid": kid,
                "groups": await domain_groups(dbx, kid_id, states, sequence),
                "started": sum(1 for sid in sequence if sid in states),
            },
        )
    finally:
        dbx.close()


@app.get("/parent")
async def parent(request: Request):
    dbx = database(request)
    try:
        today = db.today_ordinal()
        kids_data = []
        for kid in await db.get_kids(dbx):
            states = await db.get_skill_states(dbx, kid["id"])
            sequence = grade_sequence(kid["grade"])
            introduced = [sid for sid in sequence if sid in states]

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
                    "groups": await domain_groups(dbx, kid["id"], states, sequence),
                    "week": await db.week_stats(dbx, kid["id"], today),
                    "focus": focus,
                    "trouble": trouble,
                }
            )
        return templates.TemplateResponse(
            request, "parent_dashboard.html", {"kids_data": kids_data}
        )
    finally:
        dbx.close()


def main() -> None:  # pragma: no cover - entry point
    import uvicorn

    uvicorn.run("mathkids.app:app", host="127.0.0.1", port=8000, reload=False)
