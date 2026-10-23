"""What a kid's recent mistakes have in common, for the parent. Display only: these
patterns never feed scheduling or teaching, and anything that matches none of them is
shown as a plain example instead of being guessed at."""
from __future__ import annotations

WINDOW_DAYS = 30
FAST_MS = 1500

PATTERNS = {
    "place_name": dict(
        title="Gave the place's name instead of the digit's value",
        tip="Try at dinner: point at one digit and ask what it is worth. "
            "In 47, the 4 is worth 40, not \"ten\".",
    ),
    "digit": dict(
        title="Gave the digit instead of its value",
        tip="Try at dinner: in 34, the 3 is in the tens place, so it is worth 30.",
    ),
    "one_off": dict(
        title="One place off by one",
        tip="Try at dinner: after an answer, check it one place at a time out loud.",
    ),
    "copy": dict(
        title="Repeated the previous step's answer",
        tip="A screen slip, not a math mistake. Nothing to practise.",
    ),
    "blank": dict(
        title="Blank or answered in under 1.5 seconds",
        tip="Probably clicked through. Not a math mistake.",
    ),
}


def digits(text: str) -> str:
    return (text or "").replace(",", "").replace(" ", "")


PLACE_QUESTION = ("worth", "value", "___", "part")


def classify(expected: str, given: str, ms: int, previous: str | None = None,
             prompt: str = "") -> str | None:
    e, g = digits(expected), digits(given)
    if not g or 0 < ms < FAST_MS:
        return "blank"
    about_place = any(word in prompt for word in PLACE_QUESTION) or not prompt
    if e.isdigit() and g.isdigit() and len(e) >= 2 and about_place:
        nonzero = e.rstrip("0")
        if len(nonzero) == 1 and g == "1" + "0" * (len(e) - 1) and g != e:
            return "place_name"
        if len(nonzero) == 1 and g == nonzero and g != e:
            return "digit"
    if previous is not None and g == digits(previous) and g != e:
        return "copy"
    if e.isdigit() and g.isdigit() and len(e) >= 2:
        if len(e) == len(g):
            diff = [(a, b) for a, b in zip(e, g) if a != b]
            if len(diff) == 1 and abs(int(diff[0][0]) - int(diff[0][1])) == 1:
                return "one_off"
    return None


def summarize(mistakes: list[dict]) -> dict:
    """`mistakes`: dicts with prompt, expected, given, ms and optional previous (the
    answer to the step before, for teaching steps). Returns matched patterns, most
    frequent first, and up to three unmatched examples."""
    found: dict[str, list[dict]] = {}
    other = []
    for m in mistakes:
        kind = classify(m["expected"], m["given"], m["ms"], m.get("previous"), m["prompt"])
        if kind:
            found.setdefault(kind, []).append(m)
        else:
            other.append(m)

    def distinct(rows):
        unique = {(r["prompt"], r["given"]): r for r in rows}
        return list(unique.values())

    other = distinct(other)
    patterns = [dict(PATTERNS[k], kind=k, count=len(v), examples=distinct(v)[-3:])
                for k, v in sorted(found.items(), key=lambda kv: -len(kv[1]))]
    return dict(patterns=patterns, other=other[-3:], total=len(mistakes))


async def recent_mistakes(dbx, kid_id: int, today: int) -> list[dict]:
    since = today - WINDOW_DAYS
    rows = await dbx.all(
        """SELECT prompt, expected, given, response_ms AS ms, id FROM attempt
           WHERE kid_id = ? AND day >= ? AND correct = 0 ORDER BY id""", kid_id, since)
    mistakes = [dict(r, given=r["given"] or "") for r in rows]
    steps = await dbx.all(
        """SELECT r.activity_id, r.revision, r.prompt, r.expected, r.raw_input, r.correct,
                  r.response_ms AS ms, a.attempt_id
           FROM step_response r JOIN practice_activity a ON a.id = r.activity_id
           WHERE a.kid_id = ? AND r.day >= ? ORDER BY r.activity_id, r.revision""",
        kid_id, since)
    whole_prompts = {(m["prompt"], m["given"]) for m in mistakes}
    previous: dict[int, str] = {}
    for s in steps:
        if not s["correct"] and (s["prompt"], s["raw_input"]) not in whole_prompts:
            mistakes.append(dict(prompt=s["prompt"], expected=s["expected"],
                                 given=s["raw_input"], ms=s["ms"],
                                 previous=previous.get(s["activity_id"])))
        if s["correct"]:
            previous[s["activity_id"]] = s["expected"]
    return mistakes
