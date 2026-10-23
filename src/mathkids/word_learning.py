"""Small-number story concepts, then gradual calculation and number-size gates."""
import random

from mathkids import learning as l

# Range and exchanging are separate demands. Each tier needs fresh evidence.
TIERS = {1: (3, 10, False), 2: (11, 20, False), 3: (21, 30, False),
         4: (31, 50, False), 5: (51, 100, False), 6: (11, 20, True),
         7: (21, 50, True), 8: (51, 100, True)}


# Story names and objects vary; worked examples keep their fixed, vetted wording.
NAMES = ["Tara", "Finn", "Maya", "Leo", "Ava", "Omar", "Nina", "Ravi", "Lucy", "Theo"]
THINGS = ["buttons", "stickers", "marbles", "shells", "crayons", "beads", "acorns", "cards"]


def gates(level):
    result = [(c, 1) for c in ("story_take", "story_hidden", "story_link")]
    ceiling = 1 if level == 1 else 8
    for band in range(1, ceiling + 1):
        result.append(("story_calculate", band))
        result.append(("story_start", band))
        if level >= 3:
            result.append(("story_start_take", band))
        if level >= 5:
            result.extend((c, band) for c in ("story_change", "story_change_take"))
    return result


REVIEW_BACKLOG = 2  # due reviews that take precedence over the frontier


def select(known, level, today):
    """The frontier gate (first not yet established) comes first, so reviews of
    established gates cannot use up every story slot; a review is served first only
    when several are due. A later-day check is required before increasing either size
    or concept (establishing needs evidence on two days)."""
    path = gates(level)
    frontier = next(((c, band) for c, band in path
                     if known.get((c, band), {}).get("stage") != "established"), None)
    due = sorted((known[(c, band)].get("due_at", 0), i, (c, band)) for i, (c, band) in enumerate(path)
                 if (c, band) in known and known[(c, band)].get("stage") == "established"
                 and known[(c, band)].get("due_at", 0) <= today)
    if due and (frontier is None or len(due) >= REVIEW_BACKLOG):
        return due[0][2]
    return frontier


def numbers(band, rng):
    low, high, exchange = TIERS[band]
    while True:
        total = rng.randint(low, high)
        part = rng.randint(1, total - 1)
        if (total % 10 < part % 10) == exchange and (band != 1 or total < 10):
            return total, part


def task(component, band, mode, seed, with_twin=True):
    rng = random.Random(seed)
    total, change = numbers(band, rng)
    start = total - change
    name = rng.choice(NAMES)
    things = rng.choice(THINGS)
    support = mode in {"guided", "faded"}
    feedback = f"The whole is {total}. Its two parts are {change} and {start}."
    diagram = f"Whole: {total} | Known part: {change} | Missing part: ?"
    answer = start
    if component == "story_take":
        prompt = (f"{name} has {total} {things} and gives away {change}. "
                  f"How many {things} are left?")
        diagram = f"Start: {total} → Give away: {change} → Left: ?"
    elif component == "story_hidden":
        prompt = (f"There are {total} {things} altogether. You can see {change}. "
                  f"How many {things} are covered?")
    elif component == "story_link":
        prompt = f"___ + {change} = {total}. What number is missing?"
    elif component == "story_calculate":
        prompt = f"{total} - {change} = ?"
    elif component == "story_start":
        prompt = (f"{name} got {change} more {things} and then had {total} {things}. "
                  f"How many {things} did {name} start with?")
        diagram = f"Start: ? → Added: {change} → Total: {total}"
    elif component == "story_start_take":
        prompt = (f"{name} gave away {change} {things} and had {start} left. "
                  f"How many {things} did {name} start with?")
        answer = total
        diagram = f"Start: ? → Gave away: {change} → Left: {start}"
    elif component == "story_change":
        prompt = (f"{name} had {change} {things} and got some more. Now there are {total}. "
                  f"How many {things} were added?")
        diagram = f"Start: {change} → Added: ? → Total: {total}"
    else:
        prompt = (f"{name} had {total} {things} and gave some away. Now there are {change}. "
                  f"How many {things} were given away?")
        diagram = f"Start: {total} → Gave away: ? → Left: {change}"
    steps = []
    table = None
    if support:
        if mode == "guided" and component != "story_calculate":
            steps.append(l.step(f"{prompt} Which number tells us the whole, before it is split "
                                "into the two parts?" if component != "story_start_take" else
                                f"{prompt} How many {things} are left?",
                                total if component != "story_start_take" else start,
                                component, feedback if component != "story_start_take" else
                                f"The story says {start} {things} are left."))
        if component == "story_start_take":
            if band > 1:
                worked, table = l.prefill([start, change], "+", l.arithmetic_steps(
                    [start, change], "+", "add_parts", "faded"), "add_parts")
                steps.extend(worked)
                for s in steps:
                    s["component"] = component
            else:
                steps.append(l.step(f"Put back the {things} given away: {start} + {change} = ?",
                                    total, component,
                                    f"The starting amount includes both the {things} left and those given away."))
        elif component == "story_calculate" and band > 1:
            worked, table = l.prefill([total, change], "-", l.arithmetic_steps(
                [total, change], "-", "sub_parts", "faded"), "sub_parts")
            steps.extend(worked)
            # Story tiers must not certify unrelated digit-count arithmetic states.
            for s in steps:
                s["component"] = component
        else:
            steps.append(l.step(f"Remove the known part to find the missing part: "
                                f"{total} - {change} = ?", start, component, feedback))
    steps.append(l.step(prompt, answer, component, feedback))
    if support:
        for s in steps:
            s["diagram"] = diagram
        if band == 1 and component in {"story_take", "story_hidden"}:
            # Covered objects stay hidden; the whole/visible counts supply the clue.
            steps[0]["picture"] = dict(kind=component, total=total, change=change, things=things)
    explanation = (
        "Example: Tara got 3 more buttons and now has 7. The 7 includes the buttons "
        "she started with and the 3 new ones. Remove those 3: 7 - 3 = 4. She started with 4."
    )
    if component == "story_start_take":
        explanation = ("Example: Tara gave away 3 buttons and has 4 left. Put the 3 back: "
                       "4 + 3 = 7. She started with 7.")
    elif component == "story_take":
        explanation = "Example: Start with 7 buttons. Cross out 3 that go away. Count the 4 left."
    elif component == "story_hidden":
        explanation = "Example: 7 buttons altogether, 3 visible. The covered part is 7 - 3 = 4."
    elif component == "story_link":
        explanation = "Example: 4 + 3 = 7, so 7 - 3 = 4. Subtraction finds a missing part."
    elif component == "story_calculate":
        explanation = "Example: 27 - 13. Subtract ones: 7 - 3 = 4. Subtract tens: 20 - 10 = 10. Together: 14."
        if band == 1:
            explanation = "Example: 7 - 3. Count back three: 6, 5, 4. Four remain."
        elif TIERS[band][2]:
            explanation = ("Example: 23 - 15. Exchange one ten: 23 = 10 + 13. "
                           "Ones: 13 - 5 = 8. Tens: 10 - 10 = 0. Eight remain.")
    elif component == "story_change":
        explanation = ("Example: Tara had 3 buttons and got some more. Now she has 7. "
                       "The new buttons are the missing part: 7 - 3 = 4.")
    elif component == "story_change_take":
        explanation = ("Example: There were 7 buttons and now 3 are left. "
                       "The missing part is the buttons given away: 7 - 3 = 4.")
    recovery = twin = None
    if not support:
        recovery = task(component, band, "guided", seed + 104729)
        steps[0] = dict(steps[0], assess=True, seed=seed)
        if with_twin:
            twin = dict(task(component, band, mode, seed + l.TWIN_OFFSET, with_twin=False)["steps"][0],
                        seed=seed + l.TWIN_OFFSET)
    return dict(version=l.VERSION, component=component, band=band, mode=mode, seed=seed,
                prompt=prompt, explanation=explanation if mode == "guided" else "", model=[],
                steps=steps, recovery=recovery, twin=twin, columns="", table=table,
                remediation={c: l.smaller_example(c, seed + i) for i, c in enumerate(l.TITLES)})
