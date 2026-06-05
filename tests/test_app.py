"""End-to-end: drive the real daily loop through HTTP against a temp database."""

import json

import pytest
from fastapi.testclient import TestClient

from mathkids import db
from mathkids.app import app, regenerate
from mathkids.engine import REGISTRY


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHKIDS_DB", str(tmp_path / "test.db"))
    conn = db.connect()
    db.init_db(conn)
    db.create_kid(conn, "Jacob", 2, "🦖", 12)
    conn.close()
    with TestClient(app) as c:
        yield c


def _current_item(kid_id):
    conn = db.connect()
    try:
        session = db.get_active_session(conn, kid_id)
        if session is None:
            return None
        plan = json.loads(session["plan"])
        idx = session["answered"]
        if idx >= len(plan):
            return None
        return idx, plan[idx]
    finally:
        conn.close()


def _lesson_seen(kid_id, skill_id):
    conn = db.connect()
    try:
        row = db.get_skill_state(conn, kid_id, skill_id)
        return row["lesson_seen"] if row else 0
    finally:
        conn.close()


def test_landing_page_lists_kid(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Jacob" in r.text


def test_full_daily_loop(client):
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
                f"/kid/{kid_id}/answer", data={"idx": idx, "answer": "-1", "ms": 1500}
            )
            assert rw.status_code == 200
            assert "Not quite" in rw.text
            wrong_checked = True
            continue

        rc = client.post(
            f"/kid/{kid_id}/answer",
            data={"idx": idx, "answer": problem.answer.canonical(), "ms": 1500},
        )
        assert rc.status_code == 200
        assert "Yes" in rc.text

    assert wrong_checked, "expected to exercise a wrong answer"

    # Finishing the plan finalizes the session and shows the summary.
    done = client.get(f"/kid/{kid_id}/play")
    assert done.status_code == 200
    assert "Nice work" in done.text

    # Dashboards render.
    assert client.get(f"/kid/{kid_id}").status_code == 200
    assert client.get("/parent").status_code == 200

    # State actually persisted.
    conn = db.connect()
    try:
        states = db.get_skill_states(conn, kid_id)
    finally:
        conn.close()
    assert states
    assert any(row["attempts"] > 0 for row in states.values())


def test_unknown_kid_redirects_home(client):
    r = client.get("/kid/999/play")
    assert r.status_code == 200
    assert "Math Time" in r.text  # redirected to the landing page
