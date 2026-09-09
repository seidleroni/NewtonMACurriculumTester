"""End-to-end: drive the real daily loop through HTTP against a temp database."""

import asyncio
import json

import pytest
import httpx
from fastapi.testclient import TestClient

from mathkids import db
from mathkids.app import app, celebration_headline, regenerate
from mathkids.engine import REGISTRY


def run(coro):
    """Drive the async db helpers from sync test code."""
    return asyncio.run(coro)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHKIDS_DB", str(tmp_path / "test.db"))
    dbx = db.SqliteDB()
    run(db.init_db(dbx))
    run(db.create_kid(dbx, "Jacob", 2, "🦖", 12))
    dbx.close()
    with TestClient(app) as c:
        yield c


def _session_id(kid_id):
    dbx = db.SqliteDB()
    try:
        return run(db.get_active_session(dbx, kid_id))["id"]
    finally:
        dbx.close()


def _current_item(kid_id):
    dbx = db.SqliteDB()
    try:
        session = run(db.get_active_session(dbx, kid_id))
        if session is None:
            return None
        plan = json.loads(session["plan"])
        idx = session["answered"]
        if idx >= len(plan):
            return None
        return idx, plan[idx]
    finally:
        dbx.close()


def _lesson_seen(kid_id, skill_id):
    dbx = db.SqliteDB()
    try:
        row = run(db.get_skill_state(dbx, kid_id, skill_id))
        return row["lesson_seen"] if row else 0
    finally:
        dbx.close()


def test_landing_page_lists_kid(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Jacob" in r.text


def test_full_daily_loop(client, tmp_path):
    kid_id = 1
    r = client.post(f"/kid/{kid_id}/start")
    assert r.status_code == 200  # followed redirect into play (lesson or problem)

    wrong_checked = False
    for _ in range(80):  # safety bound (>> a 12-problem session + lessons)
        item = _current_item(kid_id)
        if item is None:
            break
        idx, it = item
        skill = REGISTRY[it["skill"]]

        if _lesson_seen(kid_id, skill.id) == 0:
            rr = client.post(f"/kid/{kid_id}/seen", data={"skill_id": skill.id})
            assert rr.status_code == 200
            continue

        problem = regenerate(it)
        if not wrong_checked:
            rw = client.post(
                f"/kid/{kid_id}/answer", data={"session_id": _session_id(kid_id), "idx": idx, "answer": "-1", "ms": 1500}
            )
            assert rw.status_code == 200
            assert "Not quite" in rw.text
            wrong_checked = True
            continue

        rc = client.post(
            f"/kid/{kid_id}/answer",
            data={"session_id": _session_id(kid_id), "idx": idx, "answer": problem.answer.canonical(), "ms": 1500},
        )
        assert rc.status_code == 200
        assert "Yes" in rc.text

    assert wrong_checked, "expected to exercise a wrong answer"

    # Finishing the plan finalizes the session and shows the celebration summary.
    done = client.get(f"/kid/{kid_id}/play")
    assert done.status_code == 200
    assert "Nice work" in done.text
    assert 'id="celebrate"' in done.text

    # Dashboards render.
    assert client.get(f"/kid/{kid_id}").status_code == 200
    assert client.get("/parent").status_code == 200

    # State actually persisted.
    dbx = db.SqliteDB()
    try:
        states = run(db.get_skill_states(dbx, kid_id))
    finally:
        dbx.close()
    assert states
    assert any(row["attempts"] > 0 for row in states.values())


def test_probe_promotes_and_updates_remaining_plan_items(client):
    """Acing the first two attempts on a fresh skill triggers the placement
    probe; the rest of today's plan for that skill must follow to level 2."""
    kid_id = 1
    client.post(f"/kid/{kid_id}/start")
    promoted = None
    for _ in range(30):
        item = _current_item(kid_id)
        if item is None:
            break
        idx, it = item
        skill_id = it["skill"]
        if _lesson_seen(kid_id, skill_id) == 0:
            client.post(f"/kid/{kid_id}/seen", data={"skill_id": skill_id})
            continue
        problem = regenerate(it)
        client.post(
            f"/kid/{kid_id}/answer",
            data={"session_id": _session_id(kid_id), "idx": idx, "answer": problem.answer.canonical(), "ms": 1500},
        )
        dbx = db.SqliteDB()
        try:
            st = run(db.get_skill_state(dbx, kid_id, skill_id))
            session = run(db.get_active_session(dbx, kid_id))
        finally:
            dbx.close()
        if st["level"] == 2:
            promoted = skill_id
            plan = json.loads(session["plan"])
            remaining = [p for p in plan[session["answered"] :] if p["skill"] == skill_id]
            assert remaining, "expected more planned items for the promoted skill"
            assert all(p["level"] == 2 for p in remaining)
            break
    assert promoted, "expected the placement probe to promote a skill to level 2"


def test_start_resumes_same_day_session(client):
    kid_id = 1
    client.post(f"/kid/{kid_id}/start")

    # Answer one problem (skipping past any lesson screens first).
    for _ in range(10):
        idx, it = _current_item(kid_id)
        skill_id = it["skill"]
        if _lesson_seen(kid_id, skill_id) == 0:
            client.post(f"/kid/{kid_id}/seen", data={"skill_id": skill_id})
            continue
        problem = regenerate(it)
        client.post(
            f"/kid/{kid_id}/answer",
            data={"session_id": _session_id(kid_id), "idx": idx, "answer": problem.answer.canonical(), "ms": 1500},
        )
        break

    dbx = db.SqliteDB()
    try:
        before = run(db.get_active_session(dbx, kid_id))
    finally:
        dbx.close()
    assert before["answered"] == 1

    # Clicking "Start" again must resume the same session, not discard progress.
    r = client.post(f"/kid/{kid_id}/start")
    assert r.status_code == 200
    dbx = db.SqliteDB()
    try:
        after = run(db.get_active_session(dbx, kid_id))
    finally:
        dbx.close()
    assert after["id"] == before["id"]
    assert after["answered"] == 1


def test_start_replans_stale_previous_day_session(client):
    kid_id = 1
    client.post(f"/kid/{kid_id}/start")
    dbx = db.SqliteDB()
    try:
        first = run(db.get_active_session(dbx, kid_id))
        # Simulate the unfinished session being from yesterday.
        run(dbx.run("UPDATE session SET day = day - 1 WHERE id = ?", first["id"]))
    finally:
        dbx.close()

    r = client.post(f"/kid/{kid_id}/start")
    assert r.status_code == 200
    dbx = db.SqliteDB()
    try:
        active = run(db.get_active_session(dbx, kid_id))
        stale = run(dbx.first("SELECT * FROM session WHERE id = ?", first["id"]))
    finally:
        dbx.close()
    assert active["id"] != first["id"]
    assert stale["ended_at"] is not None


def test_multiple_choice_problem_renders_and_grades(client):
    """A Phase-3 MC skill shows radio options and grades the posted letter."""
    kid_id = 1
    dbx = db.SqliteDB()
    try:
        today, now = db.today_ordinal(), db.now_iso()
        run(db.introduce_skill(dbx, kid_id, "2.MD.A.1", today, now))
        run(db.save_skill_state(dbx, kid_id, "2.MD.A.1", lesson_seen=1))
        session_id = run(db.create_session(dbx, kid_id, "[]", today, now))
        plan = [{"skill": "2.MD.A.1", "level": 1, "seed": session_id * 1000}]
        run(db.update_session_plan(dbx, session_id, json.dumps(plan)))
    finally:
        dbx.close()

    page = client.get(f"/kid/{kid_id}/play")
    assert page.status_code == 200
    assert 'type="radio"' in page.text
    assert "Which tool is best to measure" in page.text

    problem = regenerate(plan[0])
    r = client.post(
        f"/kid/{kid_id}/answer",
        data={"session_id": _session_id(kid_id), "idx": 0, "answer": problem.answer.canonical(), "ms": 1500},
    )
    assert r.status_code == 200
    assert "Yes" in r.text


def test_comparator_problem_renders_as_buttons_and_grades(client):
    """Compare-with-<,=,> shows tappable sign buttons (no text box) and grades
    the posted symbol."""
    kid_id = 1
    dbx = db.SqliteDB()
    try:
        today, now = db.today_ordinal(), db.now_iso()
        run(db.introduce_skill(dbx, kid_id, "2.NBT.A.4", today, now))
        run(db.save_skill_state(dbx, kid_id, "2.NBT.A.4", lesson_seen=1))
        session_id = run(db.create_session(dbx, kid_id, "[]", today, now))
        plan = [{"skill": "2.NBT.A.4", "level": 1, "seed": session_id * 1000}]
        run(db.update_session_plan(dbx, session_id, json.dumps(plan)))
    finally:
        dbx.close()

    page = client.get(f"/kid/{kid_id}/play")
    assert page.status_code == 200
    assert 'type="radio"' in page.text
    assert 'value="="' in page.text  # the "=" sign is a pickable option
    assert 'class="answer"' not in page.text  # no free-text input

    problem = regenerate(plan[0])
    r = client.post(
        f"/kid/{kid_id}/answer",
        data={"session_id": _session_id(kid_id), "idx": 0, "answer": problem.answer.canonical(), "ms": 1500},
    )
    assert r.status_code == 200
    assert "Yes" in r.text


def test_celebration_headline_tiers():
    assert celebration_headline(12, 12) == ("💯", "Perfect day!")
    assert celebration_headline(11, 12)[1] == "Outstanding!"
    assert celebration_headline(9, 12)[1] == "Great job!"
    assert celebration_headline(6, 12)[1] == "Strong work!"
    assert celebration_headline(2, 12)[1] == "You finished it!"
    assert celebration_headline(0, 0)[1] == "You finished it!"


def test_summary_shows_mastery_and_century_milestone(client):
    kid_id = 1
    dbx = db.SqliteDB()
    try:
        today, now = db.today_ordinal(), db.now_iso()
        # 98 attempts before today, then a finished 5-problem session today:
        # lifetime total 103 crosses the 100 mark during this session.
        for _ in range(98):
            run(db.record_attempt(
                dbx, kid_id, "2.OA.B.2", None, 1, "p", "1", "1", True, 900,
                today - 1, now,
            ))
        session_id = run(db.create_session(dbx, kid_id, "[]", today, now))
        for _ in range(5):
            run(db.record_attempt(
                dbx, kid_id, "2.OA.B.2", session_id, 1, "p", "1", "1", True, 900,
                today, now,
            ))
        run(db.advance_session(dbx, session_id, 5, 4))
        run(db.end_session(dbx, session_id, now))
        # ...and a skill mastered today.
        run(db.introduce_skill(dbx, kid_id, "2.OA.B.2", today, now))
        run(db.save_skill_state(dbx, kid_id, "2.OA.B.2", mastered_at=now))
    finally:
        dbx.close()

    r = client.get(f"/kid/{kid_id}/done")
    assert r.status_code == 200
    assert "MASTERED" in r.text
    assert "100 problems" in r.text


def test_unknown_kid_redirects_home(client):
    r = client.get("/kid/999/play")
    assert r.status_code == 200
    assert "Math Time" in r.text  # redirected to the landing page


def test_problem_form_contains_session_identity(client):
    client.post("/kid/1/start")
    _, item = _current_item(1)
    page = client.post("/kid/1/seen", data={"skill_id": item["skill"]})
    assert f'name="session_id" value="{_session_id(1)}"' in page.text


def test_old_or_missing_session_identity_does_not_record_answer(client):
    client.post("/kid/1/start")
    old_id = _session_id(1)
    dbx = db.SqliteDB()
    try:
        run(dbx.run("UPDATE session SET day = day - 1 WHERE id = ?", old_id))
        client.post("/kid/1/start")
        assert _session_id(1) != old_id
        for data in ({"idx": 0, "session_id": old_id}, {"idx": 0}):
            response = client.post("/kid/1/answer", data={**data, "answer": "5"},
                                   follow_redirects=False)
            assert response.status_code == 303
        assert run(db.total_attempts(dbx, 1)) == 0
        assert run(db.get_active_session(dbx, 1))["answered"] == 0
    finally:
        dbx.close()


def test_concurrent_duplicate_answers_only_commit_once(client, monkeypatch):
    client.post("/kid/1/start")
    idx, item = _current_item(1)
    data = {"idx": idx, "session_id": _session_id(1),
            "answer": regenerate(item).answer.canonical()}
    original = db.get_skill_state

    async def race():
        gate = asyncio.Event()
        readers = 0

        async def read_same_snapshot(*args):
            nonlocal readers
            row = await original(*args)
            readers += 1
            if readers == 2:
                gate.set()
            await asyncio.wait_for(gate.wait(), timeout=5)
            return row

        monkeypatch.setattr(db, "get_skill_state", read_same_snapshot)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://test") as c:
            responses = await asyncio.gather(
                c.post("/kid/1/answer", data=data), c.post("/kid/1/answer", data=data)
            )
        assert sorted(r.status_code for r in responses) == [200, 303]

    run(race())
    dbx = db.SqliteDB()
    try:
        assert run(db.total_attempts(dbx, 1)) == 1
        session = run(db.get_active_session(dbx, 1))
        assert (session["answered"], session["num_correct"]) == (1, 1)
        state = run(original(dbx, 1, item["skill"]))
        assert (state["attempts"], state["correct"]) == (1, 1)
    finally:
        dbx.close()


def test_answer_failure_rolls_back_mastery_plan_and_progress(client):
    client.post("/kid/1/start")
    idx, item = _current_item(1)
    dbx = db.SqliteDB()
    try:
        # The next correct answer promotes this skill and rewrites the plan.
        run(db.save_skill_state(dbx, 1, item["skill"], attempts=3, consec_correct=3))
        before_session = run(db.get_active_session(dbx, 1))
        before_state = run(db.get_skill_state(dbx, 1, item["skill"]))
        run(dbx.run("""CREATE TRIGGER fail_attempt BEFORE INSERT ON attempt
                       BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END"""))
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError, match="simulated write failure"):
            client.post("/kid/1/answer", data={
                "idx": idx, "session_id": before_session["id"],
                "answer": regenerate(item).answer.canonical(),
            })
        assert run(db.get_active_session(dbx, 1)) == before_session
        assert run(db.get_skill_state(dbx, 1, item["skill"])) == before_state
        assert run(db.total_attempts(dbx, 1)) == 0
    finally:
        dbx.close()
