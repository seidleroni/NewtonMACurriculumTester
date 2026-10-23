"""Persistence and daily-loop integration for the arithmetic teaching engine."""
from __future__ import annotations

import json
import os
import random

from mathkids import db, learning
from mathkids.answers import IntegerAnswer
from mathkids.engine import REGISTRY
from mathkids.mastery import (
    MASTER_SCORE, MasteryState, apply_attempt, is_mastered, recent_misses,
)
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


def effective(known: dict, component: str, band: int) -> dict:
    """A component's state at `band`, borrowing from neighbouring bands of the same idea.

    An idea established on bigger numbers is not re-checked on smaller ones, and a new,
    bigger band starts at faded when the band below is established. Word-problem bands
    are number tiers with their own gates, and whole problems are per level: neither
    borrows."""
    state = known.get((component, band)) or learning.empty_state(component, band)
    if component.startswith(("story_", "whole:")) or state["stage"] == "established":
        return state
    if any(c == component and b > band and s["stage"] == "established"
           for (c, b), s in known.items()):
        return dict(state, stage="established")
    below = known.get((component, band - 1))
    if (component, band) not in known and below and below["stage"] == "established":
        return dict(state, stage="faded")
    return state


def ready(state: dict) -> bool:
    evidence = [e for e in state["evidence"] if e["mode"] not in {"guided", "faded"}][-3:]
    return state["stage"] == "established" or (
        len(evidence) == 3 and all(e["correct"] for e in evidence)
    )


REASONS = {
    "review": "Review: due for a check without help",
    "practice": "Practice: solving it without help",
    "recent_misses": "Checking a part, after 2 misses in the last 5 answers",
    "two_misses": "Learning the parts, after a missed problem and its retry",
    "parts_ready": "Whole problem: the parts it needs are confirmed",
    "spaced_review": "Spaced review of an idea learned earlier",
    "story_next": "Next word-problem step",
    "story_review": "Spaced review of an earlier word-problem step",
    "same_lesson": "More practice with tonight's lesson",
    "lesson_done": "Practice without help: tonight's lesson already happened",
}
CHECK_MISSES = 2  # misses among the last CHECK_WINDOW answers at a level that open teaching
CHECK_WINDOW = 5


async def needs_check(dbx, kid_id: int, skill_id: str, level: int) -> bool:
    """Recent unaided answers at this level choose ingredient checks; lifetime accuracy
    does not (one bad week in June must not decide October). Blank and duplicate
    submissions are excluded. They never certify independence either way."""
    answers = (await db.recent_answers(dbx, kid_id)).get(skill_id, [])
    return recent_misses(answers, level, CHECK_WINDOW) >= CHECK_MISSES


async def teaching_used(dbx, session_id: int) -> int:
    row = await dbx.first(
        """SELECT COUNT(*) AS n FROM step_response r JOIN practice_activity a
           ON a.id = r.activity_id WHERE a.session_id = ? AND r.mode IN ('guided','faded')""",
        session_id,
    )
    return row["n"]


def whole_snapshot(skill, item: dict, problem, band: int, mode: str, path: list[str],
                   review: bool) -> dict:
    component = f"whole:{skill.id}:{item['level']}"
    first = learning.step(problem.prompt, problem.answer.value, component,
                          "Let's check the parts of the problem together.")
    snapshot = dict(
        version=learning.VERSION, component=component, band=band, mode=mode,
        seed=item["seed"], prompt=problem.prompt, explanation="",
        steps=[dict(first, assess=True, seed=item["seed"])], model=[], twin=None,
        recovery=None, single_try=review,
        remediation={c: learning.smaller_example(c, item["seed"] + i)
                     for i, c in enumerate(learning.TITLES)},
    )
    if not review:
        twin_seed = item["seed"] + learning.TWIN_OFFSET
        twin = skill.generate(item["level"], random.Random(twin_seed))
        snapshot["twin"] = dict(learning.step(twin.prompt, twin.answer.value, component,
                                              "Let's check the parts of the problem together."),
                                assess=True, seed=twin_seed)
        snapshot["recovery"] = learning.task(
            "story_start" if skill.id == "2.OA.A.1" else path[0], band, "guided",
            item["seed"] + 104729,
        )
    return snapshot


async def get_activity(dbx, session: dict, item: dict, skill, problem):
    """Return the activity for the current slot, creating it if needed, or
    {"defer": True} when this slot's work does not fit what is left of the set."""
    slot, sid, kid_id = session["answered"], session["id"], session["kid_id"]
    existing = await dbx.first(
        "SELECT * FROM practice_activity WHERE session_id=? AND slot=?", sid, slot
    )
    if existing:
        return existing
    known = await states(dbx, kid_id)
    info = await session_info(dbx, sid)
    band, path = learning.requirements(skill.id, item["level"])
    requirements_band = band
    whole = f"whole:{skill.id}:{item['level']}"
    whole_state = known.get((whole, band), learning.empty_state(whole, band))
    review = bool(item.get("review"))
    component = whole
    # Why this problem: one of REASONS, shown to the parent under the activity.
    reason = "review" if review else "practice"
    if review:
        pass  # a review is one unaided whole problem, whatever is being taught
    elif whole_state["stage"] == "guided" or (
        await needs_check(dbx, kid_id, skill.id, item["level"]) and not ready(whole_state)
    ):
        reason = "two_misses" if whole_state["stage"] == "guided" else "recent_misses"
        component = next((c for c in path if not ready(effective(known, c, band))), whole)
    elif ready(whole_state):
        due = [c for c in path if (c, band) in known
               and known[(c, band)]["stage"] == "established"
               and known[(c, band)]["due_at"] <= db.today_ordinal()]
        if due:
            component = min(due, key=lambda c: known[(c, band)]["due_at"])
            reason = "spaced_review"
    if skill.id == "2.OA.A.1" and not review:
        from mathkids.word_learning import select
        target = select(known, item["level"], db.today_ordinal())
        component, band = target if target else (whole, band)
        reason = "story_review" if target and known.get(target, {}).get(
            "stage") == "established" else "story_next" if target else reason
    if component == whole and reason in {"two_misses", "recent_misses"}:
        reason = "parts_ready"
    state = effective(known, component, band)
    mode = state["stage"]
    if component == whole:
        mode = "independent" if mode == "guided" else mode
        snapshot = whole_snapshot(skill, item, problem, band, mode, path, review)
    else:
        introduced = info["introduced"]
        key = f"{component}:{band}"
        if mode in {"probe", "guided", "faded"} and introduced and introduced != key:
            taught, band_text = introduced.rsplit(":", 1)
            if taught in path and int(band_text) == band:
                # Practice the idea already taught in this set instead of piling on another.
                component = taught
                mode = effective(known, component, band)["stage"]
                reason = "same_lesson"
            elif mode in {"guided", "faded"}:
                # Another skill's idea is today's lesson: practice this one unaided.
                component, band, mode = whole, requirements_band, "practice"
                reason = "lesson_done"
        if mode != "practice":
            established = frozenset(
                c for c, _ in known if not c.startswith(("story_", "whole:")) and (
                    effective(known, c, band)["stage"] == "established"
                    or known.get((c, band - 1), {}).get("stage") == "established"))
            snapshot = learning.task(component, band, mode, item["seed"], established)
    spent = await teaching_used(dbx, sid)
    if mode in {"guided", "faded"} and spent > 0 and \
            spent + len(snapshot["steps"]) > info["budget"] // 2:
        # One lesson per set may run past the budget (it is bounded); further teaching
        # stays within about half the set, so reviews and other practice still happen.
        component, band, mode = whole, requirements_band, "practice"
        reason = "lesson_done"
    if mode == "practice":
        snapshot = whole_snapshot(skill, item, problem, band, "independent", path, True)
        mode = snapshot["mode"]
    elif spent > 0 and mode not in {"guided", "faded"}:
        # Tonight's lesson already happened: a missed check waits for the next set.
        snapshot["recovery"] = None
    first_lesson = mode in {"guided", "faded"} and spent == 0
    fits = len(snapshot["steps"]) <= info["budget"] - info["used"]
    if info["used"] > 0 and not first_lesson and not fits:
        return {"defer": True}
    snapshot["reason"] = reason
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


def grid(table: dict, progress: dict, current: dict | None) -> dict:
    """Rows of place-value cells for the screen: given cells, answered cells, and the
    one cell the current question fills (marked so it stands out)."""
    values = {(str(r), p): v for r, p, v in table["given"]}
    for w in progress["work"]:
        if w.get("cell"):
            values[(str(w["cell"][0]), w["cell"][1])] = w["answer"]
    now = (str(current["cell"][0]), current["cell"][1]) if current and current.get("cell") else None
    sign = {"+": "Total", "-": "Left"}.get(table["op"], "")
    labels = [(str(i), f"{table['op'] if i and table['op'] else ''} {n:,}".strip())
              for i, n in enumerate(table["nums"])]
    if table["op"]:
        labels.append(("sum", sign))

    def cells(row):
        return [dict(value=values.get((row, p)), now=now == (row, p)) for p in table["places"]]

    return dict(
        heads=[learning.PLACES[p].capitalize() for p in table["places"]],
        rows=[dict(label=label, cells=cells(row), total=row == "sum") for row, label in labels],
        answer=values.get(("answer", 0)), answer_now=now == ("answer", 0),
    )


def page_context(activity: dict, kid: dict, skill, info: dict, empty: bool = False) -> dict:
    snapshot = json.loads(activity["snapshot"])
    progress = json.loads(activity["progress"])
    current = None if progress["outcome"] else progress["steps"][progress["index"]]
    source = snapshot["recovery"] if progress["recovery"] and snapshot.get("recovery") else snapshot
    table = source.get("table")
    return dict(
        kid=kid, skill=skill, activity=activity, snapshot=snapshot, progress=progress,
        current=current, empty=empty,
        # The retry problem is a plain whole problem; the table returns with a lesson.
        grid=grid(table, progress, current) if table and (
            progress["recovery"] or not progress.get("twin")) else None,
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
    after = learning.advance(snapshot, before, correct, raw)
    done = after["outcome"] is not None
    kid_id, sid, aid = session["kid_id"], session["id"], activity["id"]
    now, today = db.now_iso(), db.today_ordinal()
    known = await states(dbx, kid_id)
    state = known[(activity["component"], activity["band"])]
    whole = activity["component"].startswith("whole:")
    # Unaided answers (the first try and its one retry) are evidence the moment they are
    # given, even if the child stops mid-lesson. Older snapshots mark only revision 0.
    copied = bool(after.get("copy_retry")) and not before.get("copy_retry")
    checked = bool(current.get("assess", whole and activity["revision"] == 0)) and not copied
    assessment = whole and checked
    if checked:
        retry = bool(before.get("twin"))
        new_state = learning.evidence_update(
            state, correct, today, current.get("seed", snapshot["seed"]),
            "retry" if retry else activity["mode"], lenient=whole,
            twin_pending=not correct and not retry and bool(snapshot.get("twin")),
        )
    elif done:
        # The idea being learned is judged by its own steps; a slip on an
        # ingredient step is recorded against that ingredient instead.
        clean = after["components"].get(activity["component"], after["clean"])
        new_state = learning.evidence_update(
            state, clean, today, snapshot["seed"], activity["mode"], lenient=whole,
        )
    else:
        new_state = state
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
        """SELECT COUNT(*) AS completed, COALESCE(SUM(outcome NOT IN ('independent','missed')),0) AS guided
           , COALESCE(SUM(outcome='independent' AND component NOT LIKE 'whole:%'),0) AS checks
           FROM practice_activity WHERE session_id=? AND outcome IS NOT NULL""", session_id,
    )
    return dict(independent=assessment["total"], correct=assessment["correct"],
                guided=practice["guided"], checks=practice["checks"])


async def parent_progress(dbx, kid_id: int) -> list[dict]:
    from mathkids.word_learning import TIERS

    rows = list((await states(dbx, kid_id)).values())
    return [dict(title=learning.TITLES.get(r["component"],
                    f"{REGISTRY[r['component'].split(':')[1]].title}, level "
                    f"{r['component'].split(':')[2]}"
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
