"""Small-number story concepts, then gradual calculation and number-size gates."""
import random

from mathkids import learning as l

# Range and exchanging are separate demands. Each tier needs fresh evidence.
TIERS = {1: (3, 10, False), 2: (11, 20, False), 3: (21, 30, False),
         4: (31, 50, False), 5: (51, 100, False), 6: (11, 20, True),
         7: (21, 50, True), 8: (51, 100, True)}


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


def select(known, level, today):
    path = gates(level)
    # A later-day check is required before increasing either size or concept.
    for c, band in path:
        state = known.get((c, band), {})
        if state.get("stage") != "established":
            return c, band
        if state.get("due_at", 0) <= today:
            return c, band
    return None


def numbers(band, rng):
    low, high, exchange = TIERS[band]
    while True:
        total = rng.randint(low, high)
        part = rng.randint(1, total - 1)
        if (total % 10 < part % 10) == exchange and (band != 1 or total < 10):
            return total, part


def task(component, band, mode, seed):
    rng = random.Random(seed)
    total, change = numbers(band, rng)
    start = total - change
    name = rng.choice(["Tara", "Finn", "Maya", "Leo"])
    support = mode in {"guided", "faded"}
    feedback = f"The whole is {total}. Its two parts are {change} and {start}."
    diagram = f"Whole: {total} | Known part: {change} | Missing part: ?"
    answer = start
    if component == "story_take":
        prompt = (f"{name} has {total} buttons and gives away {change}. "
                  "How many buttons are left?")
        diagram = f"Start: {total} → Give away: {change} → Left: ?"
    elif component == "story_hidden":
        prompt = (f"There are {total} buttons altogether. You can see {change}. "
                  "How many buttons are covered?")
    elif component == "story_link":
        prompt = f"___ + {change} = {total}. What number is missing?"
    elif component == "story_calculate":
        prompt = f"{total} - {change} = ?"
    elif component == "story_start":
        prompt = (f"{name} got {change} more buttons and then had {total} buttons. "
                  f"How many buttons did {name} start with?")
        diagram = f"Start: ? → Added: {change} → Total: {total}"
    elif component == "story_start_take":
        prompt = (f"{name} gave away {change} buttons and had {start} left. "
                  f"How many buttons did {name} start with?")
        answer = total
        diagram = f"Start: ? → Gave away: {change} → Left: {start}"
    elif component == "story_change":
        prompt = (f"{name} had {change} buttons and got some more. Now there are {total}. "
                  "How many buttons were added?")
        diagram = f"Start: {change} → Added: ? → Total: {total}"
    else:
        prompt = (f"{name} had {total} buttons and gave some away. Now there are {change}. "
                  "How many buttons were given away?")
        diagram = f"Start: {total} → Gave away: ? → Left: {change}"
    steps = []
    if support:
        if mode == "guided" and component != "story_calculate":
            steps.append(l.step(f"{prompt} Which number tells us the whole, before it is split "
                                "into the two parts?" if component != "story_start_take" else
                                f"{prompt} How many buttons are left?",
                                total if component != "story_start_take" else start,
                                component, feedback if component != "story_start_take" else
                                f"The story says {start} buttons are left."))
        if component == "story_start_take":
            if band > 1:
                steps.extend(l.arithmetic_steps([start, change], "+", "add_parts", "faded"))
                for s in steps:
                    s["component"] = component
            else:
                steps.append(l.step(f"Put back the buttons given away: {start} + {change} = ?",
                                    total, component,
                                    "The starting amount includes both the buttons left and those given away."))
        elif component == "story_calculate" and band > 1:
            steps.extend(l.arithmetic_steps([total, change], "-", "sub_parts", "faded"))
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
            # Covered buttons stay hidden; the whole/visible counts supply the clue.
            steps[0]["picture"] = dict(kind=component, total=total, change=change)
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
    recovery = task(component, band, "guided", seed + 104729) if not support else None
    return dict(version=l.VERSION, component=component, band=band, mode=mode, seed=seed,
                prompt=prompt, explanation=explanation if mode == "guided" else "", model=[],
                steps=steps, recovery=recovery, columns="",
                remediation={c: l.smaller_example(c, seed + i) for i, c in enumerate(l.TITLES)})
