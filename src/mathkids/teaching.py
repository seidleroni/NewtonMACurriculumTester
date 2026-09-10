"""Persistence and daily-loop integration for the arithmetic teaching engine."""
from __future__ import annotations

import json
import os

from mathkids import db, learning
from mathkids.answers import IntegerAnswer
from mathkids.engine import REGISTRY
from mathkids.mastery import MASTER_SCORE, MasteryState, apply_attempt, is_mastered
from mathkids.scheduler import next_due, update_box


def enabled(request) -> bool:
    env = request.scope.get("env")
    value = getattr(env, "MATHKIDS_TEACHING", "0") if env is not None else os.getenv(
        "MATHKIDS_TEACHING", "0"
    )
    return str(value).lower() in {"1", "true"}


async def session_info(dbx, session_id: int):
    return await dbx.first("SELECT * FROM learning_session WHERE session_id=?", session_id)


async def states(dbx, kid_id: int) -> dict:
    rows = await dbx.all("SELECT * FROM learning_state WHERE kid_id=?", kid_id)
    for row in rows:
        row["evidence"] = json.loads(row["evidence"])
    return {(row["component"], row["band"]): row for row in rows}


def ready(state: dict) -> bool:
    evidence = [e for e in state["evidence"] if e["mode"] not in {"guided", "faded"}][-3:]
    return state["stage"] == "established" or (
        len(evidence) == 3 and all(e["correct"] for e in evidence)
    )


async def get_activity(dbx, session: dict, item: dict, skill, problem):
    slot, sid, kid_id = session["answered"], session["id"], session["kid_id"]
    existing = await dbx.first(
        "SELECT * FROM practice_activity WHERE session_id=? AND slot=?", sid, slot
    )
    if existing:
        return existing
    known = await states(dbx, kid_id)
    info = await session_info(dbx, sid)
    band, path = learning.requirements(skill.id, item["level"])
    whole = f"whole:{skill.id}:{item['level']}"
    whole_state = known.get((whole, band), learning.empty_state(whole, band))
    legacy = await db.get_skill_state(dbx, kid_id, skill.id)
    # Historical outcomes select a starting check; they never certify independence.
    needs_check = legacy["attempts"] >= 3 and legacy["correct"] / legacy["attempts"] < 0.85
    component = whole
    if whole_state["stage"] == "guided" or (needs_check and not ready(whole_state)):
        component = next((c for c in path if not ready(
            known.get((c, band), learning.empty_state(c, band))
        )), whole)
    elif ready(whole_state):
        due = [c for c in path if (c, band) in known
               and known[(c, band)]["stage"] == "established"
               and known[(c, band)]["due_at"] <= db.today_ordinal()]
        if due:
            component = min(due, key=lambda c: known[(c, band)]["due_at"])
    if skill.id == "2.OA.A.1":
        from mathkids.word_learning import select
        target = select(known, item["level"], db.today_ordinal())
        component, band = target if target else (whole, band)
    state = known.get((component, band), learning.empty_state(component, band))
    mode = state["stage"]
    if component == whole:
        mode = "independent" if mode == "guided" else mode
        snapshot = dict(
            version=learning.VERSION, component=component, band=band, mode=mode,
            seed=item["seed"], prompt=problem.prompt, explanation="",
            steps=[learning.step(problem.prompt, problem.answer.value, component,
                                 "Let's check the parts of the problem together.")],
            recovery=learning.task("story_start" if skill.id == "2.OA.A.1" else path[0],
                                   band, "guided", item["seed"] + 104729),
            model=[], remediation={c: learning.smaller_example(c, item["seed"] + i)
                                   for i, c in enumerate(learning.TITLES)},
        )
    else:
        introduced = info["introduced"]
        key = f"{component}:{band}"
        if mode in {"probe", "guided", "faded"} and introduced and introduced != key:
            # Practice the idea already taught in this set instead of piling on another.
            component, band_text = introduced.rsplit(":", 1)
            band = int(band_text)
            state = known.get((component, band), learning.empty_state(component, band))
            mode = state["stage"]
        snapshot = learning.task(component, band, mode, item["seed"])
    if info["used"] > 0 and len(snapshot["steps"]) > info["budget"] - info["used"]:
        return {"budget_end": True}
    await dbx.run(
        "INSERT OR IGNORE INTO learning_state (kid_id,component,band) VALUES (?,?,?)",
        kid_id, component, band,
    )
    await dbx.run(
        """INSERT OR IGNORE INTO practice_activity
           (session_id,slot,kid_id,skill_id,component,band,mode,snapshot,progress,started_at)
           SELECT ?,?,?,?,?,?,?,?,?,? WHERE EXISTS
           (SELECT 1 FROM session WHERE id=? AND ended_at IS NULL AND answered=?)""",
        sid, slot, kid_id, skill.id, component, band, mode, json.dumps(snapshot),
        json.dumps(learning.initial_progress(snapshot)), db.now_iso(), sid, slot,
    )
    if mode in {"guided", "faded"}:
        await dbx.run(
            "UPDATE learning_session SET introduced=COALESCE(introduced,?) WHERE session_id=?",
            f"{component}:{band}", sid,
        )
    return await dbx.first("SELECT * FROM practice_activity WHERE session_id=? AND slot=?", sid, slot)


def page_context(activity: dict, kid: dict, skill, info: dict) -> dict:
    snapshot = json.loads(activity["snapshot"])
    progress = json.loads(activity["progress"])
    return dict(
        kid=kid, skill=skill, activity=activity, snapshot=snapshot, progress=progress,
        current=None if progress["outcome"] else progress["steps"][progress["index"]],
        stage=learning.STAGES[activity["mode"]],
        title=learning.TITLES.get(activity["component"], "Try it yourself"),
        remaining=max(0, info["budget"] - info["used"]),
    )


async def submit(dbx, session: dict, activity: dict, raw: str, ms: int, skill) -> bool:
    """All effects of a step commit together, using the activity revision as a claim."""
    snapshot = json.loads(activity["snapshot"])
    before = json.loads(activity["progress"])
    if before["outcome"]:
        return False
    current = before["steps"][before["index"]]
    correct = IntegerAnswer(current["answer"]).grade(raw).correct
    after = learning.advance(snapshot, before, correct)
    done = after["outcome"] is not None
    kid_id, sid, aid = session["kid_id"], session["id"], activity["id"]
    now, today = db.now_iso(), db.today_ordinal()
    known = await states(dbx, kid_id)
    state = known[(activity["component"], activity["band"])]
    # Persist a failed entry check immediately, even if the child stops mid-lesson.
    assessment = activity["component"].startswith("whole:") and activity["revision"] == 0
    new_state = learning.evidence_update(
        state, after["clean"], today, snapshot["seed"], activity["mode"]
    ) if done or assessment else state
    # Record the FIRST whole-problem answer, even if automatic teaching follows.
    st = await db.get_skill_state(dbx, kid_id, skill.id)
    fields = None
    new_plan = json.loads(session["plan"])
    if assessment:
        upd = apply_attempt(MasteryState(st["score"], st["level"], st["consec_correct"], st["recent"]),
                            skill.max_level, correct, False, st["attempts"])
        confirmed = (
            new_state["stage"] == "established"
            or all(known.get((c, activity["band"]), {}).get("stage") == "established"
                   for c in learning.requirements(skill.id, st["level"])[1])
            or is_mastered(st["score"], st["level"], skill.max_level)
        )
        if skill.id == "2.OA.A.1":
            from mathkids.word_learning import gates
            confirmed = all(known.get(pair, {}).get("stage") == "established"
                            for pair in gates(st["level"]))
        if upd.leveled_up and not confirmed:
            upd.state.level = st["level"]
            upd.state.consec_correct = st["consec_correct"] + int(correct)
        if upd.mastered_now and not confirmed:
            upd.state.score = min(upd.state.score, MASTER_SCORE - 0.001)
            upd.mastered_now = False
        box = update_box(st["box"], correct)
        fields = dict(score=upd.state.score, level=upd.state.level,
                      consec_correct=upd.state.consec_correct, recent=upd.state.recent,
                      box=box, due_at=next_due(today, box), attempts=st["attempts"] + 1,
                      correct=st["correct"] + int(correct), last_seen_at=now,
                      mastered_at=now if upd.mastered_now else st["mastered_at"])
        for item in new_plan[session["answered"] + 1:]:
            if item["skill"] == skill.id:
                item["level"] = upd.state.level
    statements = [(
        """UPDATE practice_activity SET progress=?,revision=revision+1,outcome=?,ended_at=?
           WHERE id=? AND revision=? AND outcome IS NULL
             AND EXISTS (SELECT 1 FROM session WHERE id=? AND answered=? AND ended_at IS NULL)
             AND EXISTS (SELECT 1 FROM learning_state WHERE kid_id=? AND component=?
                         AND band=? AND revision=?)
             AND EXISTS (SELECT 1 FROM skill_state WHERE kid_id=? AND skill_id=? AND attempts=?)""",
        (json.dumps(after), after["outcome"], now if done else None, aid, activity["revision"],
         sid, session["answered"], kid_id, activity["component"], activity["band"],
         state["revision"], kid_id, skill.id, st["attempts"]),
    ), (
        """INSERT INTO step_response
           (activity_id,revision,step_key,component,mode,raw_input,prompt,expected,correct,
            response_ms,day,created_at)
           SELECT ?,?,?,?,?,?,?,?,?,?,?,? WHERE changes()=1""",
        (aid, activity["revision"], str(before["index"]), current["component"],
         "guided" if before["recovery"] else activity["mode"], raw, current["prompt"],
         str(current["answer"]), int(correct), max(0, ms), today, now),
    ), (
        """UPDATE learning_state SET stage=?,streak=?,evidence=?,due_at=?,revision=?
           WHERE kid_id=? AND component=? AND band=? AND changes()=1""",
        (new_state["stage"], new_state["streak"], json.dumps(new_state["evidence"]),
         new_state["due_at"], new_state["revision"], kid_id, activity["component"], activity["band"]),
    ), (
        "UPDATE learning_session SET used=used+1,revision=revision+1, "
        "introduced=COALESCE(introduced,?) WHERE session_id=? AND changes()=1",
        (f"{snapshot['recovery']['component']}:{activity['band']}"
         if after["recovery"] and snapshot["recovery"] else None, sid),
    ), (
        """UPDATE session SET answered=answered+?,num_correct=num_correct+?,plan=?
           WHERE id=? AND changes()=1""",
        (int(done), int(assessment and correct), json.dumps(new_plan), sid),
    )]
    if done:
        # Keep evidence about ingredients separate from the full problem's result.
        # Prompted steps cannot establish independent mastery of those ingredients.
        for component, clean in after["components"].items():
            if component == activity["component"]:
                continue
            previous = known.get((component, activity["band"]),
                                 learning.empty_state(component, activity["band"]))
            updated = learning.evidence_update(previous, clean, today, snapshot["seed"], "guided")
            statements.append((
                """INSERT INTO learning_state
                   (kid_id,component,band,stage,streak,evidence,due_at,revision)
                   SELECT ?,?,?,?,?,?,?,? WHERE changes()=1
                   ON CONFLICT(kid_id,component,band) DO UPDATE SET
                   stage=excluded.stage,streak=excluded.streak,evidence=excluded.evidence,
                   due_at=excluded.due_at,revision=excluded.revision""",
                (kid_id, component, activity["band"], updated["stage"], updated["streak"],
                 json.dumps(updated["evidence"]), updated["due_at"], updated["revision"]),
            ))
    if fields is not None:
        statements += [(
            "UPDATE skill_state SET " + ",".join(f"{k}=?" for k in fields)
            + " WHERE kid_id=? AND skill_id=? AND changes()=1",
            (*fields.values(), kid_id, skill.id),
        ), (
            """INSERT INTO attempt
               (kid_id,skill_id,session_id,level,prompt,expected,given,correct,response_ms,day,created_at)
               SELECT ?,?,?,?,?,?,?,?,?,?,? WHERE changes()=1""",
            (kid_id, skill.id, sid, json.loads(session["plan"])[session["answered"]]["level"],
             current["prompt"], str(current["answer"]), raw, int(correct), max(0, ms), today, now),
        ), (
            "UPDATE practice_activity SET attempt_id=last_insert_rowid() WHERE id=? AND changes()=1",
            (aid,),
        )]
    changes = await dbx.batch(statements)
    return changes[0] == 1


async def summary(dbx, session_id: int) -> dict | None:
    if not await session_info(dbx, session_id):
        return None
    assessment = await dbx.first(
        "SELECT COUNT(*) AS total, COALESCE(SUM(correct),0) AS correct FROM attempt WHERE session_id=?",
        session_id,
    )
    practice = await dbx.first(
        """SELECT COUNT(*) AS completed, COALESCE(SUM(outcome!='independent'),0) AS guided
           , COALESCE(SUM(outcome='independent' AND component NOT LIKE 'whole:%'),0) AS checks
           FROM practice_activity WHERE session_id=? AND outcome IS NOT NULL""", session_id,
    )
    return dict(independent=assessment["total"], correct=assessment["correct"],
                guided=practice["guided"], checks=practice["checks"])


async def parent_progress(dbx, kid_id: int) -> list[dict]:
    from mathkids.word_learning import TIERS

    rows = list((await states(dbx, kid_id)).values())
    return [dict(title=learning.TITLES.get(r["component"],
                    REGISTRY[r["component"].split(":")[1]].title
                    if r["component"].startswith("whole:") else r["component"]),
                 band=r["band"],
                 range_label=(
                     ("Below 10" if r["band"] == 1 else f"Within {TIERS[r['band']][1]}")
                     + (", exchanging" if TIERS[r["band"]][2] else ", no exchanging")
                     if r["component"].startswith(("story_", "whole:2.OA.A.1:"))
                     else f"{r['band']}-digit"
                 ),
                 stage=learning.STAGES[r["stage"]], due_at=r["due_at"])
            for r in rows]
