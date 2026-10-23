"""Fixes for the October stall: windowed checks, sticky mastery, reviews first with a
teaching cap, one-step-at-a-time teaching screens, and a retry before any lesson."""
import asyncio
import json
import random
from datetime import date

import pytest
from fastapi.testclient import TestClient

from mathkids import db, teaching
from mathkids import learning as l
from mathkids import word_learning as w
from mathkids.app import app
from mathkids.mastery import is_retained, recent_misses
from mathkids.scheduler import Slot, compose_blocks, compose_session, next_to_introduce


def run(coro):
    return asyncio.run(coro)


# --- teaching screens -------------------------------------------------------

@pytest.mark.parametrize("band", [2, 3, 4])
def test_decompose_asks_equations_ones_first(band):
    for seed in range(40):
        task = l.task("decompose", band, "guided", seed)
        prompts = [s["prompt"] for s in task["steps"][:-1]]
        assert all("___" in p and "part worth" not in p for p in prompts)
        places = [s["cell"][1] for s in task["steps"][:-1]]
        assert places == sorted(places)  # ones, then tens, then hundreds


def test_known_ingredients_are_shown_not_asked():
    # Samuel's add_parts lesson: decomposing 3-digit numbers is established.
    full = l.task("add_parts", 3, "guided", 5)
    short = l.task("add_parts", 3, "guided", 5, frozenset({"decompose"}))
    assert len(full["steps"]) == 10
    assert len(short["steps"]) == 4
    assert all(s["component"] != "decompose" for s in short["steps"])
    nums = [int(n) for n in short["prompt"].replace(" = ?", "").split(" + ")]
    given = {(g[0], g[1]): g[2] for g in short["table"]["given"]}
    for i, n in enumerate(nums):
        assert sum(v for (row, _), v in given.items() if row == i) == n


def test_the_idea_being_learned_is_never_prefilled():
    task = l.task("add_ones", 2, "guided", 9, frozenset({"decompose", "add_ones", "add_parts"}))
    assert any(s["component"] == "add_ones" for s in task["steps"])
    assert task["steps"][-1]["cell"] == ["answer", 0]


def test_new_ten_wording_shows_the_moved_ten_once():
    for seed in range(30):
        for s in l.task("add_many", 2, "guided", seed)["steps"]:
            assert not s["prompt"].startswith("Put 10 with")
    steps = l.arithmetic_steps([24, 19, 11], "+", "add_many", "faded")
    move = next(s for s in steps if "new ten" in s["prompt"])
    assert move["prompt"] == "Add the new ten to the tens: 40 + 10 = ?"
    assert move["answer"] == 50


def test_copying_the_previous_answer_gets_one_free_look():
    task = l.task("decompose", 3, "guided", 3)
    p = l.advance(task, l.initial_progress(task), True)
    previous = str(p["work"][-1]["answer"])
    if previous == str(p["steps"][p["index"]]["answer"]):
        pytest.skip("seed has equal adjacent answers")
    p = l.advance(task, p, False, previous)
    assert p["clean"] and p["copy_retry"] and "last step" in p["message"]
    p = l.advance(task, p, False, previous)
    assert not p["clean"]  # only once per activity


def test_table_grid_marks_only_the_current_cell():
    task = l.task("add_parts", 3, "guided", 5, frozenset({"decompose"}))
    progress = l.initial_progress(task)
    g = teaching.grid(task["table"], progress, progress["steps"][0])
    marked = [c for row in g["rows"] for c in row["cells"] if c["now"]]
    assert len(marked) == 1 and marked[0]["value"] is None
    assert g["rows"][-1]["label"] == "Total"


# --- retries before lessons ---------------------------------------------------

@pytest.mark.parametrize("component", ["decompose", "match", "add_parts", "sub_ones",
                                       "story_take", "story_calculate"])
def test_unaided_checks_carry_a_fresh_twin(component):
    for seed in range(10):
        task = l.task(component, 2, "probe", seed)
        assert task["steps"][0]["assess"] and task["twin"]["assess"]
        assert task["twin"]["seed"] == seed + l.TWIN_OFFSET
        assert task["twin"]["prompt"] != task["steps"][0]["prompt"] or seed == 0


def test_one_miss_is_not_a_lesson_two_are():
    state = l.empty_state("whole:4.NBT.B.4:1", 3)
    state = l.evidence_update(state, False, 100, 1, "probe", twin_pending=True)
    assert state["stage"] == "probe"
    state = l.evidence_update(state, True, 100, 2, "retry")
    assert state["stage"] == "probe"
    state = l.evidence_update(state, False, 101, 3, "probe", twin_pending=True)
    state = l.evidence_update(state, False, 101, 4, "retry")
    assert state["stage"] == "guided"


def test_whole_problems_forgive_a_single_unaided_miss():
    state = l.empty_state("whole:2.NBT.B.5:3", 2)
    state = l.evidence_update(state, False, 100, 1, "probe", lenient=True)
    assert state["stage"] == "probe"
    state = l.evidence_update(state, False, 101, 2, "probe", lenient=True)
    assert state["stage"] == "guided"


def test_missed_twin_without_a_lesson_shows_the_answer():
    task = l.task("add_parts", 3, "independent", 4)
    task["recovery"] = None  # tonight's lesson already happened
    p = l.advance(task, l.initial_progress(task), False)
    p = l.advance(task, p, False)
    assert p["outcome"] == "missed" and str(task["twin"]["answer"]) in p["message"].replace(",", "")


def test_old_snapshots_keep_their_original_flow():
    task = l.task("add_ones", 3, "probe", 10)
    old = dict(task, version=2, twin=None)
    for step in old["steps"]:
        step.pop("assess", None)
    p = l.advance(old, l.initial_progress(old), False, "123")
    assert p["recovery"]


def test_story_twin_uses_the_same_story_shape():
    task = w.task("story_hidden", 1, "probe", 12)
    assert "covered" in task["twin"]["prompt"]


# --- mastery and scheduling ---------------------------------------------------

def test_earned_mastery_survives_one_slip():
    answers = [(1, 4)] * 4 + [(0, 4)]
    assert is_retained(0.9, 4, 4, "2026-09-09", answers)
    assert not is_retained(0.9, 4, 4, "2026-09-09", answers + [(0, 4)])
    # A skill re-banded to a higher max_level keeps a badge earned before.
    assert is_retained(0.99, 4, 5, "2026-06-22", [(1, 4)] * 5)
    assert not is_retained(0.9, 4, 4, None, answers)


def test_recent_misses_can_look_at_one_level():
    answers = [(0, 1), (0, 1), (1, 2), (0, 2), (1, 2)]
    assert recent_misses(answers) == 3
    assert recent_misses(answers, 2) == 1


def slot(sid, due, attempts=5, mastered=False, score=0.5):
    return Slot(sid, 2, score, 3, due, mastered, attempts)


def test_reviews_come_first_most_overdue_first():
    seq = ["A", "B", "C", "D", "E", "F"]
    slots = {"A": slot("A", 200), "B": slot("B", 50, mastered=True),
             "C": slot("C", 10, mastered=True), "D": slot("D", 90, mastered=True),
             "E": slot("E", 100, attempts=0), "F": slot("F", 300)}
    reviews, rest = compose_blocks(slots, seq, 100, 12, checks=("A",))
    assert reviews[:3] == ["C", "B", "D"]
    assert "E" not in reviews  # introduced today: lesson first, not a review
    assert reviews[-1] == "A"  # the skill being taught gets an unaided check
    assert sorted(reviews + rest) == sorted(compose_session(slots, seq, 100, 12))


# --- through the app -----------------------------------------------------------

@pytest.fixture
def app_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MATHKIDS_DB", str(tmp_path / "u.db"))
    monkeypatch.setenv("MATHKIDS_TEACHING", "1")
    d = db.SqliteDB()
    run(db.init_db(d))
    run(db.create_kid(d, "Learner", 4, "L"))
    with TestClient(app) as c:
        yield c, d
    d.close()


def answer_rows(d, skill, results, level=1, day_offset=5):
    for i, ok in enumerate(results):
        run(db.record_attempt(d, 1, skill, None, level, f"q{i}", "1", "1" if ok else "2",
                              bool(ok), 9000, db.today_ordinal() - day_offset,
                              f"2026-01-0{day_offset % 9 + 1}T10:00:{i:02d}-05:00"))


def start_plan(d, plan, budget=12):
    run(db.create_session(d, 1, json.dumps(plan), db.today_ordinal(), db.now_iso(),
                          teaching_budget=budget))


def current(d):
    s = run(db.get_active_session(d, 1))
    return s, run(d.first("SELECT * FROM practice_activity WHERE session_id=? AND slot=?",
                          s["id"], s["answered"]))


def step_data(a, answer):
    return dict(activity_id=a["id"], session_id=a["session_id"], revision=a["revision"],
                answer=str(answer), ms=5000)


def right(a):
    p = json.loads(a["progress"])
    return p["steps"][p["index"]]["answer"]


def test_recent_answers_ignore_blanks_and_duplicates(app_db):
    _, d = app_db
    answer_rows(d, "4.NBT.B.4", [1, 1])
    for _ in range(3):  # a triple submit of one answer, and two blanks
        run(db.record_attempt(d, 1, "4.NBT.B.4", 7, 1, "dup", "5", "4", False, 100,
                              db.today_ordinal(), "2026-10-01T10:00:00-04:00"))
    for i in range(2):
        run(db.record_attempt(d, 1, "4.NBT.B.4", 7, 1, f"b{i}", "5", "  ", False, 100,
                              db.today_ordinal(), f"2026-10-01T10:00:0{i + 1}-04:00"))
    assert run(db.recent_answers(d, 1))["4.NBT.B.4"] == [(1, 1), (1, 1), (0, 1)]


def test_blank_submissions_are_not_recorded(app_db):
    c, d = app_db
    run(db.introduce_skill(d, 1, "4.OA.A.1", db.today_ordinal(), db.now_iso()))
    run(db.save_skill_state(d, 1, "4.OA.A.1", lesson_seen=1))
    start_plan(d, [{"skill": "4.OA.A.1", "level": 1, "seed": 3}])
    sid = run(db.get_active_session(d, 1))["id"]
    page = c.post("/kid/1/answer", data=dict(idx=0, session_id=sid, answer="  ", ms=200))
    assert "Type your answer in the box first" in page.text
    assert run(db.total_attempts(d, 1)) == 0
    run(db.introduce_skill(d, 1, "4.NBT.B.4", db.today_ordinal(), db.now_iso()))
    run(db.end_session(d, sid, db.now_iso()))
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 3}])
    c.get("/kid/1/play")
    _, a = current(d)
    page = c.post("/kid/1/step", data=step_data(a, ""))
    assert "Type your answer in the box first" in page.text
    assert run(d.first("SELECT COUNT(*) AS n FROM step_response"))["n"] == 0


def test_one_old_slip_no_longer_opens_a_month_of_lessons(app_db):
    # Samuel: 3 right, then 260 + 210 = 370. Lifetime 75% used to force ingredient teaching.
    c, d = app_db
    run(db.introduce_skill(d, 1, "4.NBT.B.4", db.today_ordinal(), db.now_iso()))
    run(db.save_skill_state(d, 1, "4.NBT.B.4", attempts=4, correct=3))
    answer_rows(d, "4.NBT.B.4", [1, 1, 1, 0])
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 11}])
    c.get("/kid/1/play")
    _, a = current(d)
    assert a["component"] == "whole:4.NBT.B.4:1"
    answer_rows(d, "4.NBT.B.4", [0], day_offset=4)  # a second recent miss
    run(db.end_session(d, a["session_id"], db.now_iso()))
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 12}])
    c.get("/kid/1/play")
    assert current(d)[1]["component"] == "decompose"


def test_review_is_one_unaided_problem_even_while_teaching(app_db):
    c, d = app_db
    run(db.introduce_skill(d, 1, "4.NBT.B.4", db.today_ordinal(), db.now_iso()))
    answer_rows(d, "4.NBT.B.4", [0, 0, 1])
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 21, "review": True},
                   {"skill": "4.NBT.B.4", "level": 1, "seed": 22}])
    c.get("/kid/1/play")
    _, a = current(d)
    snap = json.loads(a["snapshot"])
    assert a["component"].startswith("whole:") and snap["single_try"] and not snap["recovery"]
    page = c.post("/kid/1/step", data=step_data(a, right(a) + 1))
    assert "The answer is" in page.text and "come back another day" in page.text
    assert run(d.first("SELECT outcome FROM practice_activity WHERE id=?", a["id"]))["outcome"] == "missed"
    c.get("/kid/1/play")
    assert current(d)[1]["component"] == "decompose"  # teaching follows in its own slot


def test_second_lesson_in_a_set_becomes_unaided_practice(app_db):
    c, d = app_db
    run(db.introduce_skill(d, 1, "4.NBT.B.4", db.today_ordinal(), db.now_iso()))
    answer_rows(d, "4.NBT.B.4", [0, 0, 1])
    for comp in ("decompose", "match"):
        run(d.run("INSERT INTO learning_state (kid_id,component,band,stage) VALUES (1,?,3,'established')",
                  comp))
    run(d.run("INSERT INTO learning_state (kid_id,component,band,stage) VALUES (1,'add_parts',3,'guided')"))
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 30 + i} for i in range(4)])
    c.get("/kid/1/play")
    _, a = current(d)
    assert a["component"] == "add_parts" and a["mode"] == "guided"
    assert len(json.loads(a["snapshot"])["steps"]) == 4  # decomposing is shown, not asked
    page = c.get(f"/kid/1/activity/{a['id']}")
    assert 'class="placegrid"' in page.text and 'class="now"' in page.text
    for _ in range(10):
        s, a = current(d)
        if a is None or a["outcome"]:
            break
        c.post("/kid/1/step", data=step_data(a, right(a)))
    c.get("/kid/1/play")
    _, b = current(d)
    snap = json.loads(b["snapshot"])
    assert b["component"].startswith("whole:") and snap["single_try"]


def test_mastered_skill_with_one_slip_still_frees_a_new_skill(app_db):
    c, d = app_db
    seq = ["4.OA.A.3.a", "4.OA.A.1", "4.OA.A.2", "4.OA.A.3"]
    for sid in seq[:3]:
        run(db.introduce_skill(d, 1, sid, db.today_ordinal() - 30, db.now_iso()))
    run(db.save_skill_state(d, 1, "4.OA.A.3.a", level=5, score=0.9, mastered_at="2026-09-01"))
    run(db.save_skill_state(d, 1, "4.OA.A.1", level=4, score=0.97, mastered_at="2026-09-01"))
    run(db.save_skill_state(d, 1, "4.OA.A.2", level=2, score=0.4))
    answer_rows(d, "4.OA.A.3.a", [1, 1, 1, 1, 0])
    c.post("/kid/1/start")
    assert len(run(db.get_skill_states(d, 1))) == 4


def test_plan_starts_with_its_review_block(app_db):
    c, d = app_db
    for sid in ("4.OA.A.3.a", "4.OA.A.1"):
        run(db.introduce_skill(d, 1, sid, db.today_ordinal() - 40, db.now_iso()))
        run(db.save_skill_state(d, 1, sid, attempts=10, correct=10, due_at=db.today_ordinal() - 20,
                               level=2, score=0.6, lesson_seen=1))
    c.post("/kid/1/start")
    plan = json.loads(run(db.get_active_session(d, 1))["plan"])
    reviews = [p for p in plan if p.get("review")]
    assert reviews and plan[:len(reviews)] == reviews


# --- the whole loop -----------------------------------------------------------

def test_simulated_nights_keep_reviews_answers_and_lessons_in_balance(tmp_path, monkeypatch):
    from tools.simulate_teaching import simulate

    path = tmp_path / "sim-source.db"
    monkeypatch.setenv("MATHKIDS_DB", str(path))
    d = db.SqliteDB(str(path))
    run(db.init_db(d))
    run(db.create_kid(d, "G2", 2, "A"))
    run(db.create_kid(d, "G4", 4, "B"))
    rng = random.Random(4)
    for kid, skills in ((1, ["2.OA.B.2", "2.NBT.A.1", "2.NBT.B.5"]),
                        (2, ["4.OA.A.3.a", "4.NBT.A.1", "4.NBT.B.4"])):
        for sid in skills:
            run(db.introduce_skill(d, kid, sid, db.today_ordinal() - 60, db.now_iso()))
            run(db.save_skill_state(d, kid, sid, level=2, score=0.6, attempts=8, correct=6,
                                   lesson_seen=1, due_at=db.today_ordinal() - rng.randint(0, 20)))
    d.close()
    for slip in (0.0, 0.2):
        records, broken = simulate(path, nights=4, slip=slip, seed=2,
                                   start=date.fromordinal(db.today_ordinal() + 1))
        assert not broken, broken
        assert all(r.responses >= 8 for r in records)
        assert all(r.reviews for r in records)


# --- lanes ------------------------------------------------------------------------

def lane_slots(**levels):
    return {sid: Slot(sid, lv, 0.5, 2, 999, lv == 9, 5) for sid, lv in levels.items()}


def test_a_stuck_lane_does_not_block_other_domains():
    seq = ["N1", "N2", "F1", "M1"]
    domains = {"N1": "nbt", "N2": "nbt", "F1": "nf", "M1": "md"}
    slots = lane_slots(N1=1)  # stuck on its floor, like 4.NBT.B.4 in October
    assert next_to_introduce(slots, seq) is None  # the old single-lane gate
    assert next_to_introduce(slots, seq, domains=domains) == "F1"
    slots = lane_slots(N1=1, F1=1)
    assert next_to_introduce(slots, seq, domains=domains) == "M1"
    slots = lane_slots(N1=1, F1=1, M1=1)  # the global cap still holds
    assert next_to_introduce(slots, seq, domains=domains) is None


def test_cross_lane_prerequisites_wait_for_their_skill():
    seq = ["N1", "N2", "M1"]
    domains = {"N1": "nbt", "N2": "nbt", "M1": "md"}
    prereqs = {"M1": ("N2",)}
    slots = lane_slots(N1=9)
    assert next_to_introduce(slots, seq, domains=domains, prereqs=prereqs) == "N2"
    slots = lane_slots(N1=9, N2=1)
    assert next_to_introduce(slots, seq, domains=domains, prereqs=prereqs) is None
    slots = lane_slots(N1=9, N2=2)
    assert next_to_introduce(slots, seq, domains=domains, prereqs=prereqs) == "M1"


def test_every_prerequisite_is_a_real_earlier_or_other_lane_skill():
    from mathkids.engine import REGISTRY, SEQUENCES
    from mathkids.engine.base import LANE_PREREQS

    for skill, needs in LANE_PREREQS.items():
        seq = SEQUENCES[REGISTRY[skill].grade]
        for need in needs:
            assert need in seq and REGISTRY[need].domain != REGISTRY[skill].domain


# --- spacing and bands ------------------------------------------------------------

def test_reviews_of_established_ideas_spread_out():
    state = l.empty_state("add_ones", 3)
    days = []
    for i, day in enumerate((100, 100, 101, 108, 122, 152, 212)):
        state = l.evidence_update(state, True, day, i, "independent")
        days.append(state["due_at"] - day)
    assert days[2:] == [7, 14, 30, 60, 60]
    state = l.evidence_update(state, False, 300, 99, "established")
    state = l.evidence_update(state, True, 300, 100, "established")
    assert state["due_at"] - 300 == 7  # a miss starts the spacing over


def test_story_frontier_comes_before_a_single_due_review():
    known = {}
    gates = w.gates(4)
    for pair in gates[:3]:
        known[pair] = dict(stage="established", due_at=90)
    assert w.select(known, 4, 100) == gates[0]  # three due: catch up first
    known[gates[0]]["due_at"] = known[gates[1]]["due_at"] = 200
    assert w.select(known, 4, 100) == gates[3]  # one due: the frontier wins


def test_bands_borrow_established_evidence():
    known = {("add_ones", 4): dict(l.empty_state("add_ones", 4), stage="established"),
             ("match", 2): dict(l.empty_state("match", 2), stage="established")}
    assert teaching.effective(known, "add_ones", 3)["stage"] == "established"
    assert teaching.effective(known, "match", 3)["stage"] == "faded"
    assert teaching.effective(known, "match", 4)["stage"] == "probe"
    story = {("story_take", 2): dict(l.empty_state("story_take", 2), stage="established")}
    assert teaching.effective(story, "story_take", 1)["stage"] == "probe"


# --- parent view ----------------------------------------------------------------

@pytest.mark.parametrize("expected,given,ms,previous,kind", [
    ("20", "10", 6000, None, "place_name"),          # Jacob: "tens part worth?"
    ("800000", "100000", 9000, None, "place_name"),  # Samuel: value of the 8
    ("853", "953", 9000, None, "one_off"),
    ("1", "40", 5000, "40", "copy"),
    ("50", "", 9000, None, "blank"),
    ("50", "7", 300, None, "blank"),
    ("864", "721", 9000, None, None),
    ("100", "100", 9000, None, None),
])
def test_mistake_patterns(expected, given, ms, previous, kind):
    from mathkids.misconceptions import classify

    assert classify(expected, given, ms, previous) == kind


def test_health_names_a_stall_and_is_quiet_when_well(app_db):
    from mathkids import health

    _, d = app_db
    today = db.today_ordinal()
    seq = ["4.OA.A.3.a", "4.OA.A.1", "4.NBT.B.4"]
    run(db.introduce_skill(d, 1, "4.NBT.B.4", today - 40, "2026-09-01T10:00:00-04:00"))
    run(db.save_skill_state(d, 1, "4.NBT.B.4", attempts=4, due_at=today - 30))
    for i in range(10):  # ten short nights of lessons and nothing else
        day = today - 20 + i
        run(d.run("INSERT INTO session (kid_id,plan,day,started_at,ended_at,answered) "
                  "VALUES (1,'[]',?,?,?,2)", day, "t", "t"))
        sid = run(d.first("SELECT MAX(id) AS id FROM session"))["id"]
        run(d.run("INSERT INTO learning_session (session_id,version,budget,used) VALUES (?,1,12,3)", sid))
        run(d.run("INSERT INTO practice_activity (session_id,slot,kid_id,skill_id,component,band,"
                  "mode,snapshot,progress,started_at) VALUES (?,0,1,'4.NBT.B.4','add_parts',3,"
                  "'guided','{}','{}','t')", sid))
    text = " ".join(run(health.kid_health(d, 1, seq, today)))
    assert "waited 10 practice nights" in text
    assert "No new skill in 10 practice nights" in text
    assert "median of 3 answers" in text
    assert "no problem solved without help" in text
    run(d.run("DELETE FROM session"))
    run(d.run("UPDATE skill_state SET due_at=?", today + 3))
    assert run(health.kid_health(d, 1, seq, today)) == []


def test_history_explains_choices_and_lists_what_was_not_reached(app_db):
    c, d = app_db
    run(db.introduce_skill(d, 1, "4.NBT.B.4", db.today_ordinal(), db.now_iso()))
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 41, "review": True},
                   {"skill": "4.OA.A.1", "level": 1, "seed": 42}])
    c.get("/kid/1/play")
    _, a = current(d)
    c.post("/kid/1/step", data=step_data(a, right(a)))
    run(db.end_session(d, a["session_id"], db.now_iso()))
    page = c.get("/parent/kid/1/history").text
    assert "Why this problem: Review" in page
    assert "Not reached in this set: " in page and "4.OA" not in page.split("Not reached")[0][-5:]
    page = c.get("/parent").text
    assert "Needs a look" in page or "Practice is on track" in page


def test_stories_vary_their_names_and_objects():
    pairs = set()
    for seed in range(60):
        prompt = w.task("story_take", 2, "independent", seed)["prompt"]
        name = prompt.split()[0]
        thing = next(t for t in w.THINGS if t in prompt)
        assert prompt.count(thing) == 2  # the object stays the same within a story
        pairs.add((name, thing))
    assert len(pairs) >= 12


def test_prompt_report_flags_a_tricky_wording(tmp_path):
    from tools.prompt_report import report, template

    assert template("Round 27,704 to the nearest ten.") == "Round # to the nearest ten."
    path = tmp_path / "r.db"
    d = db.SqliteDB(str(path))
    run(db.init_db(d))
    for i in range(12):
        tricky = i % 2 == 0
        run(db.record_attempt(d, 1, "x", 1, 1, f"Put {i} with the tens: 40 + 10 = ?" if tricky
                              else f"{i} + 1 = ?", "1", "2" if tricky and i % 4 == 0 else "1",
                              not (tricky and i % 4 == 0), 5000, 100 + i % 3, "t"))
    d.close()
    rows = {r["template"]: r for r in report(str(path))}
    assert rows["Put # with the tens: # + # = ?"]["flag"]
    assert not rows["# + # = ?"]["flag"]


def test_lesson_after_a_missed_retry_keeps_its_table(app_db):
    c, d = app_db
    run(db.introduce_skill(d, 1, "4.NBT.B.4", db.today_ordinal(), db.now_iso()))
    start_plan(d, [{"skill": "4.NBT.B.4", "level": 1, "seed": 51}])
    c.get("/kid/1/play")
    _, a = current(d)
    assert a["component"].startswith("whole:")
    c.post("/kid/1/step", data=step_data(a, right(a) + 1))
    _, a = current(d)
    page = c.post("/kid/1/step", data=step_data(a, right(a) + 1))
    assert "find the part to practice" in page.text.replace("&#39;", "'")
    assert 'class="placegrid"' in page.text
