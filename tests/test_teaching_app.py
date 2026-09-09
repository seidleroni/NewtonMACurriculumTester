import asyncio
import json
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from mathkids import db, teaching
from mathkids.app import app


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def practice(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHKIDS_DB", str(tmp_path / "practice.db"))
    monkeypatch.setenv("MATHKIDS_TEACHING", "1")
    d = db.SqliteDB()
    run(db.init_db(d))
    run(db.create_kid(d, "Learner", 2, "L"))
    run(db.introduce_skill(d, 1, "2.NBT.B.7", db.today_ordinal(), db.now_iso()))
    run(db.save_skill_state(d, 1, "2.NBT.B.7", level=2, attempts=11, correct=7))
    plan = [{"skill": "2.NBT.B.7", "level": 2, "seed": i * 101 + 5} for i in range(12)]
    run(db.create_session(d, 1, json.dumps(plan), db.today_ordinal(), db.now_iso(), teaching_budget=12))
    with TestClient(app) as c:
        yield c, d
    d.close()


def active(d):
    session = run(db.get_active_session(d, 1))
    return run(d.first("SELECT * FROM practice_activity WHERE session_id=? AND slot=?",
                       session["id"], session["answered"]))


def data_for(activity, wrong=False):
    p = json.loads(activity["progress"])
    answer = p["steps"][p["index"]]["answer"]
    return dict(activity_id=activity["id"], session_id=activity["session_id"],
                revision=activity["revision"], answer=str(answer + 1 if wrong else answer), ms=10000)


def test_jacob_entry_check_automatic_teaching_and_history(practice):
    c, d = practice
    page = c.get("/kid/1/play")
    a = active(d)
    assert a["component"] == "decompose" and a["mode"] == "probe"
    assert "help" not in page.text.lower()
    wrong = data_for(a, True)
    page = c.post("/kid/1/step", data=wrong)
    assert "Let's find the part" in page.text or "Let&#39;s find the part" in page.text
    assert run(db.total_attempts(d, 1)) == 0
    assert run(db.get_skill_state(d, 1, "2.NBT.B.7"))["attempts"] == 11
    # Refresh has the same current question and does not reset the revision.
    a = active(d)
    revision = a["revision"]
    c.get("/kid/1/play")
    assert active(d)["revision"] == revision
    for _ in range(20):
        a = active(d)
        if a is None:
            break
        c.post("/kid/1/step", data=data_for(a))
    record = run(d.first("SELECT * FROM practice_activity ORDER BY id LIMIT 1"))
    assert record["outcome"] == "practiced"
    assert run(db.total_attempts(d, 1)) == 0
    hist = c.get("/parent/kid/1/history")
    assert hist.status_code == 200
    assert wrong["answer"] in hist.text
    assert "Incorrect" in hist.text and "Correct" in hist.text
    assert "Guided" in hist.text and "Independent" in hist.text
    assert "View questions and answers by day" in c.get("/parent").text


def test_confident_learner_stays_independent(practice):
    c, d = practice
    run(db.save_skill_state(d, 1, "2.NBT.B.7", attempts=12, correct=12))
    c.get("/kid/1/play")
    a = active(d)
    assert a["component"].startswith("whole:")
    assert len(json.loads(a["snapshot"])["steps"]) == 1
    c.post("/kid/1/step", data=data_for(a))
    assert run(db.total_attempts(d, 1)) == 1
    assert run(db.get_skill_state(d, 1, "2.NBT.B.7"))["correct"] == 13
    assert run(d.first("SELECT COUNT(*) AS n FROM step_response"))["n"] == 1


def test_whole_failure_is_recorded_once_even_after_guided_completion(practice):
    c, d = practice
    run(db.save_skill_state(d, 1, "2.NBT.B.7", attempts=12, correct=12))
    c.get("/kid/1/play")
    c.post("/kid/1/step", data=data_for(active(d), True))
    assert run(db.total_attempts(d, 1)) == 1
    for _ in range(20):
        a = active(d)
        if not a:
            break
        c.post("/kid/1/step", data=data_for(a))
    assert run(db.total_attempts(d, 1)) == 1
    assert run(d.first("SELECT correct FROM attempt"))["correct"] == 0
    summary = run(teaching.summary(d, run(db.get_active_session(d, 1))["id"]))
    assert summary == {"independent": 1, "correct": 0, "guided": 1, "checks": 0}


def test_component_checks_are_celebrated_without_counting_as_whole_answers(practice):
    c, d = practice
    run(d.run("UPDATE learning_session SET budget=1"))
    c.get("/kid/1/play")
    c.post("/kid/1/step", data=data_for(active(d)))
    page = c.get("/kid/1/play")
    assert "1 skill checks solved independently" in page.text
    assert "whole-problem answers correct" not in page.text


def test_abandoned_entry_check_preserves_need_for_teaching(practice):
    c, d = practice
    run(db.save_skill_state(d, 1, "2.NBT.B.7", attempts=100, correct=100))
    c.get("/kid/1/play")
    a = active(d)
    c.post("/kid/1/step", data=data_for(a, True))
    state = run(teaching.states(d, 1))[(a["component"], a["band"])]
    assert state["stage"] == "guided"
    run(db.end_session(d, a["session_id"], db.now_iso()))
    plan = json.dumps([{"skill": "2.NBT.B.7", "level": 2, "seed": 5678}])
    run(db.create_session(d, 1, plan, db.today_ordinal(), db.now_iso(), teaching_budget=12))
    c.get("/kid/1/play")
    assert active(d)["component"] == "decompose"


def test_history_uses_each_response_day_across_midnight(practice):
    from datetime import date

    c, d = practice
    c.get("/kid/1/play")
    a = active(d)
    c.post("/kid/1/step", data=data_for(a, True))
    yesterday = db.today_ordinal() - 1
    run(d.run("UPDATE session SET day=?", yesterday))
    run(d.run("UPDATE step_response SET day=?", yesterday))
    c.post("/kid/1/step", data=data_for(active(d)))
    old = c.get(f"/parent/kid/1/history?day={date.fromordinal(yesterday)}")
    new = c.get(f"/parent/kid/1/history?day={date.fromordinal(yesterday + 1)}")
    assert "1 teaching/check responses" in old.text
    assert "1 teaching/check responses" in new.text
    assert "Incorrect" in old.text and "Incorrect" not in new.text
    assert "Correct" in new.text


def test_reload_uses_original_activity_snapshot(practice, monkeypatch):
    from mathkids import learning

    c, d = practice
    c.get("/kid/1/play")
    before = active(d)

    def changed_generator(*args, **kwargs):
        raise AssertionError("An existing activity must not be regenerated")

    monkeypatch.setattr(learning, "task", changed_generator)
    assert c.get("/kid/1/play").status_code == 200
    assert active(d)["snapshot"] == before["snapshot"]


def test_new_mastery_requires_confirmation_on_a_later_day(practice):
    from mathkids.mastery import MASTER_SCORE

    c, d = practice
    run(db.save_skill_state(d, 1, "2.NBT.B.7", level=5, attempts=100, correct=100,
                           score=MASTER_SCORE - 0.001))
    session = run(db.get_active_session(d, 1))
    plan = json.loads(session["plan"])
    for item in plan:
        item["level"] = 5
    run(d.run("UPDATE session SET plan=? WHERE id=?", json.dumps(plan), session["id"]))
    c.get("/kid/1/play")
    c.post("/kid/1/step", data=data_for(active(d)))
    state = run(db.get_skill_state(d, 1, "2.NBT.B.7"))
    assert state["score"] < MASTER_SCORE
    assert state["mastered_at"] is None


def test_new_probe_does_not_start_second_guided_idea(practice):
    c, d = practice
    run(d.run("INSERT INTO learning_state (kid_id,component,band,stage) VALUES (1,'decompose',3,'established')"))
    run(d.run("UPDATE learning_session SET introduced='decompose:3'"))
    c.get("/kid/1/play")
    assert active(d)["component"] == "decompose"


def test_repeated_step_and_invalid_owner_do_not_change_progress(practice):
    c, d = practice
    c.get("/kid/1/play")
    a = active(d)
    data = data_for(a)
    c.post("/kid/999/step", data=data, follow_redirects=False)
    c.post("/kid/1/step", data=data, follow_redirects=False)
    c.post("/kid/1/step", data=data, follow_redirects=False)
    assert run(d.first("SELECT COUNT(*) AS n FROM step_response"))["n"] == 1


def test_step_transaction_rolls_back_on_response_failure(practice):
    c, d = practice
    c.get("/kid/1/play")
    before = active(d)
    run(d.run("""CREATE TRIGGER fail_response BEFORE INSERT ON step_response
                 BEGIN SELECT RAISE(ABORT, 'write failed'); END"""))
    with pytest.raises(sqlite3.IntegrityError, match="write failed"):
        c.post("/kid/1/step", data=data_for(before))
    assert active(d) == before
    assert run(d.first("SELECT used FROM learning_session"))["used"] == 0


def test_concurrent_steps_claim_one_revision(practice, monkeypatch):
    c, d = practice
    c.get("/kid/1/play")
    data = data_for(active(d))
    original = teaching.states

    async def race():
        gate = asyncio.Event()
        count = 0

        async def same_snapshot(*args):
            nonlocal count
            result = await original(*args)
            count += 1
            if count == 2:
                gate.set()
            await asyncio.wait_for(gate.wait(), 5)
            return result

        monkeypatch.setattr(teaching, "states", same_snapshot)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await asyncio.gather(client.post("/kid/1/step", data=data), client.post("/kid/1/step", data=data))
    run(race())
    assert run(d.first("SELECT COUNT(*) AS n FROM step_response"))["n"] == 1
    assert run(d.first("SELECT used FROM learning_session"))["used"] == 1


def test_budget_finishes_current_activity_then_ends_set(practice):
    c, d = practice
    run(d.run("UPDATE learning_session SET budget=1"))
    c.get("/kid/1/play")
    c.post("/kid/1/step", data=data_for(active(d), True))
    for _ in range(20):
        a = active(d)
        if not a:
            break
        c.post("/kid/1/step", data=data_for(a))
    page = c.get("/kid/1/play")
    assert "learning activities" in page.text
    assert run(db.get_active_session(d, 1)) is None


def test_activation_and_rollback_retire_incompatible_sessions(practice, monkeypatch):
    c, d = practice
    old = run(db.get_active_session(d, 1))
    monkeypatch.setenv("MATHKIDS_TEACHING", "0")
    c.post("/kid/1/start")
    replacement = run(db.get_active_session(d, 1))
    assert replacement["id"] != old["id"]
    assert run(teaching.session_info(d, replacement["id"])) is None
    assert run(d.first("SELECT ended_at FROM session WHERE id=?", old["id"]))["ended_at"]


def test_history_filters_days_and_retains_possible_duplicates(practice):
    c, d = practice
    today = db.today_ordinal()
    for _ in range(2):
        run(db.record_attempt(d, 1, "2.NBT.B.7", None, 2, "817 + 179 = ?", "996", "976",
                              False, 190000, today - 1, "2026-09-03T19:20:04-04:00"))
    from datetime import date
    old_day = date.fromordinal(today - 1).isoformat()
    page = c.get(f"/parent/kid/1/history?day={old_day}")
    assert page.text.count("817 + 179") == 2
    assert "Possible duplicate" in page.text
    assert "0 / 2" in page.text
    assert "817 + 179" not in c.get(f"/parent/kid/1/history?day={date.fromordinal(today)}").text
    assert c.get("/parent/kid/1/history?day=bad").status_code == 400
    assert c.get("/parent/kid/999/history", follow_redirects=False).status_code == 303


def test_parallel_start_keeps_one_complete_plan(practice):
    c, d = practice
    run(db.end_session(d, run(db.get_active_session(d, 1))["id"], db.now_iso()))

    async def start_twice():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await asyncio.gather(client.post("/kid/1/start"), client.post("/kid/1/start"))
    run(start_twice())
    assert run(d.first("SELECT COUNT(*) AS n FROM session WHERE ended_at IS NULL"))["n"] == 1
    current = run(db.get_active_session(d, 1))
    assert len(json.loads(current["plan"])) == 12
    assert run(teaching.session_info(d, current["id"])) is not None
