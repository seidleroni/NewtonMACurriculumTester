"""Versioned, deterministic arithmetic teaching. No database or runtime AI.

Components describe ideas; bands describe digit counts; stages describe support.
Snapshots contain all prompts/answers, so an in-flight activity survives a deploy.
"""
from __future__ import annotations

import copy
import random

VERSION = 2
SUPPORTED = {"2.OA.A.1", "2.NBT.B.5", "2.NBT.B.6", "2.NBT.B.7", "3.NBT.A.2", "4.NBT.B.4"}
TITLES = {
    "decompose": "Break numbers into parts",
    "match": "Match hundreds, tens, and ones",
    "add_parts": "Add the parts and put them together",
    "add_ones": "Make a new ten",
    "add_tens": "Make a new hundred",
    "add_multi": "Regroup more than one place",
    "add_many": "Add several numbers in parts",
    "sub_parts": "Subtract matching parts",
    "sub_ones": "Exchange a ten for ones",
    "sub_tens": "Exchange a hundred for tens",
    "sub_multi": "Exchange in more than one place",
    "sub_zero": "Exchange across a zero",
    "story_take": "Take away and count what remains",
    "story_hidden": "Find the hidden part",
    "story_link": "Connect addition and subtraction",
    "story_calculate": "Subtract a little at a time",
    "story_start": "Find how many there were at the start",
    "story_start_take": "Find the start before some were given away",
    "story_change": "Find how many were added",
    "story_change_take": "Find how many were given away",
    "whole": "Solve it yourself",
}
STAGES = {"probe": "Checking independently", "guided": "Learning the steps",
          "faded": "Using fewer clues", "independent": "Practicing independently",
          "established": "Confirmed independently"}
PLACES = {1: "ones", 10: "tens", 100: "hundreds", 1000: "thousands",
          10000: "ten-thousands", 100000: "hundred-thousands", 1000000: "millions"}


def places(n: int) -> list[int]:
    return [10 ** i for i in reversed(range(max(2, len(str(n)))))]


def parts(n: int) -> str:
    return " + ".join(str(n // p % 10 * p) for p in places(n))


def requirements(skill_id: str, level: int) -> tuple[int, list[str]]:
    """Explicit concept gates, independent of a lucky generated no-carry example."""
    if skill_id == "2.OA.A.1":
        from mathkids.word_learning import gates
        pairs = gates(level)
        return pairs[-1][1], list(dict.fromkeys(c for c, _ in pairs))
    band = 2 if skill_id in {"2.NBT.B.5", "2.NBT.B.6"} else 3
    path = ["decompose", "match", "add_parts"]
    if skill_id == "2.NBT.B.6":
        return band, path + ["add_ones", "add_many"]
    if skill_id == "2.NBT.B.5":
        if level >= 3:
            path += ["add_ones"]
        if level >= 5:
            path += ["sub_parts", "sub_ones"]
        return band, path
    if skill_id == "2.NBT.B.7":
        if level >= 2:
            path += ["add_ones"]
        if level >= 3:
            path += ["add_tens", "add_multi"]
        if level >= 4:
            path += ["sub_parts"]
        if level >= 5:
            path += ["sub_ones", "sub_tens", "sub_multi", "sub_zero"]
    elif skill_id == "3.NBT.A.2":
        if level >= 2:
            path += ["add_ones"]
        if level >= 3:
            path += ["sub_parts"]
        if level >= 4:
            path += ["sub_ones", "sub_tens", "sub_multi", "sub_zero"]
        if level >= 5:
            path += ["add_tens", "add_multi"]
    elif skill_id == "4.NBT.B.4":
        band = [3, 4, 4, 5, 6][level - 1]
        if level >= 2:
            path += ["add_ones", "add_tens", "add_multi"]
        if level >= 3:
            path += ["sub_parts"]
        if level >= 4:
            path += ["sub_ones", "sub_tens", "sub_multi", "sub_zero"]
    return band, path


def empty_state(component: str, band: int) -> dict:
    return dict(component=component, band=band, stage="probe", streak=0,
                evidence=[], due_at=0, revision=0)


def evidence_update(state: dict, correct: bool, day: int, seed: int, mode: str) -> dict:
    state = copy.deepcopy(state)
    history = state["evidence"]
    # A repeated seed cannot manufacture fresh evidence.
    if any(e["seed"] == seed for e in history):
        return state
    history.append(dict(correct=correct, day=day, seed=seed, mode=mode))
    state["evidence"] = history[-12:]
    stage = state["stage"]
    state["streak"] = state["streak"] + 1 if correct else 0
    if mode in {"guided", "faded"}:
        if stage == "probe":
            state["stage"] = mode
        if correct and state["streak"] >= 2 and stage in {"probe", "guided", "faded"}:
            state["stage"] = "faded" if mode == "guided" else "independent"
            state["streak"] = 0
    else:
        recent = [e for e in history if e["mode"] not in {"guided", "faded"}][-3:]
        if not correct and (stage == "probe" or sum(not e["correct"] for e in recent) >= 2):
            state["stage"] = "guided"
            state["streak"] = 0
        elif len(recent) == 3 and all(e["correct"] for e in recent):
            state["stage"] = (
                "established" if len({e["day"] for e in recent}) >= 2 else "independent"
            )
    state["due_at"] = day + (7 if state["stage"] == "established" else 1)
    state["revision"] += 1
    return state


def step(prompt: str, answer: int, component: str, feedback: str, *, choices=None) -> dict:
    return dict(prompt=prompt, answer=answer, component=component,
                feedback=feedback, choices=choices or [])


def smaller_example(component: str, seed: int) -> dict:
    """An authored, related prerequisite check, not a generic easy distraction."""
    rng = random.Random(seed)
    if component.startswith("story_"):
        return step("7 buttons have two parts: 3 and a hidden part. 7 - 3 = ?", 4,
                    component, "Count back three from seven: six, five, four. The hidden part is 4.")
    n = rng.randint(2, 8)
    if component in {"decompose", "match"}:
        return step(f"3 tens are worth 30. What are {n} tens worth?", n * 10, "decompose",
                    f"Count {n} groups of ten: " + " + ".join(["10"] * n) + f" = {n * 10}.")
    if component in {"add_ones", "add_tens", "add_multi", "add_many"}:
        return step(f"16 = 10 + 6. Break apart {10 + n}: {10 + n} = 10 + ?", n,
                    "add_ones", f"A teen number has one ten and some ones: {10+n} = 10 + {n}.")
    if component in {"sub_ones", "sub_tens", "sub_multi", "sub_zero"}:
        return step(f"30 = 20 + 10. Exchange one ten: {n * 10} = ___ + 10.", (n - 1) * 10,
                    "sub_ones", f"Keep the total the same: {n * 10} = {(n - 1) * 10} + 10.")
    if component == "sub_parts":
        return step(f"5 tens - 2 tens = 3 tens. {n * 10} - 10 = ?", (n - 1) * 10,
                    component, f"Removing one ten leaves {n - 1} tens, or {(n - 1) * 10}.")
    return step(f"2 tens + 1 ten = 3 tens. {n * 10} + 10 = ?", (n + 1) * 10,
                "add_parts", f"One more ten makes {n + 1} tens: {(n + 1) * 10}.")


def operands(component: str, band: int, rng: random.Random) -> tuple[list[int], str]:
    """Generate one conceptual demand at a time; each carry/exchange is forced."""
    width = 2 if component in {"add_ones", "sub_ones", "add_many"} else max(3, band)
    # Teach a new exchange on small numbers before extending to the requested band.
    width = min(width, band)
    while True:
        a = rng.randint(10 ** (width - 1), 10 ** width - 1)
        b = rng.randint(10, a if component.startswith("sub") else 10 ** width - 1)
        if component.startswith("sub"):
            if a <= b:
                continue
            borrow, sites, across_zero = 0, [], False
            for p in reversed(places(a)):
                ad, bd = a // p % 10 - borrow, b // p % 10
                needs = ad < bd
                if needs:
                    sites.append(p)
                    across_zero |= a // (p * 10) % 10 == 0
                borrow = int(needs)
            valid = {
                "sub_parts": not sites,
                "sub_ones": sites == [1],
                "sub_tens": sites == [10],
                "sub_multi": len(sites) >= 2 and not across_zero,
                "sub_zero": across_zero,
            }[component]
            if valid:
                return [a, b], "-"
        else:
            carry, sites = 0, []
            for p in reversed(places(max(a, b))):
                total = a // p % 10 + b // p % 10 + carry
                carry = total // 10
                if carry:
                    sites.append(p)
            if a + b >= 10 ** band:
                continue
            valid = {
                "add_parts": not sites,
                "add_ones": sites == [1],
                "add_tens": sites == [10],
                "add_multi": len(sites) >= 2,
                "add_many": True,
            }[component]
            if valid:
                nums = [a, b]
                if component == "add_many":
                    # Three, then four addends are separately exposed by examples.
                    nums = [rng.randint(10, 24) for _ in range(rng.choice([3, 4]))]
                return nums, "+"


def arithmetic_steps(nums: list[int], op: str, component: str, mode: str) -> list[dict]:
    """Construct a concrete solution, with value-preserving exchanges."""
    result = []
    ps = places(max(nums))
    if mode == "guided":
        for n in nums:
            for p in ps:
                result.append(step(
                    f"Break apart {n:,}. What is the {PLACES[p]} part worth?",
                    n // p % 10 * p, "decompose",
                    f"The {PLACES[p]} digit counts groups of {p:,}. {n:,} = {parts(n)}.",
                ))
    if op == "+":
        totals = {p: sum(n // p % 10 * p for n in nums) for p in ps}
        for p in ps:
            expr = " + ".join(str(n // p % 10 * p) for n in nums)
            result.append(step(f"Add the {PLACES[p]}: {expr} = ?", totals[p], "add_parts",
                               f"Add matching places. {expr} = {totals[p]}.",))
        for p in reversed(ps):
            if totals[p] >= 10 * p:
                exchange = totals[p] // (10 * p) * (10 * p)
                rest = totals[p] % (10 * p)
                result.append(step(
                    f"Break apart {totals[p]}: {totals[p]} = {exchange} + ?", rest,
                    component, f"Keep the value the same: {totals[p]} = {exchange} + {rest}.",
                ))
                totals[p] = rest
                totals[p * 10] = totals.get(p * 10, 0) + exchange
                result.append(step(
                    f"Put {exchange} with the {PLACES[p * 10]}: "
                    f"{totals[p * 10] - exchange} + {exchange} = ?", totals[p * 10], component,
                    "The extra group belongs with the matching place.",
                ))
        expr = " + ".join(str(totals[p]) for p in sorted(totals, reverse=True))
        result.append(step(f"Put your parts together: {expr} = ?", sum(nums), component,
                           f"Your parts name the total: {expr} = {sum(nums)}."))
    else:
        a, b = nums
        counts = {p: a // p % 10 for p in ps}
        differences = {}
        for p in reversed(ps):
            needed = b // p % 10
            if counts[p] < needed:
                donor = p * 10
                while counts.get(donor, 0) == 0:
                    donor *= 10
                while donor > p:
                    before = counts[donor] * donor
                    counts[donor] -= 1
                    result.append(step(
                        f"Exchange {donor:,} from {before:,}. How much stays in that place?",
                        counts[donor] * donor, component,
                        f"{before:,} = {counts[donor] * donor:,} + {donor:,}. "
                        "We move that group; we do not change the number.",
                    ))
                    lower = donor // 10
                    previous = counts.get(lower, 0) * lower
                    counts[lower] = counts.get(lower, 0) + 10
                    result.append(step(
                        f"Move it to the {PLACES[lower]}: {previous:,} + {donor:,} = ?",
                        counts[lower] * lower, component,
                        f"One group of {donor:,} is ten groups of {lower:,}.",
                    ))
                    donor = lower
            left, right = counts[p] * p, needed * p
            differences[p] = left - right
            result.append(step(f"Subtract the {PLACES[p]}: {left} - {right} = ?",
                               left - right, "sub_parts",
                               f"Subtract matching places: {left} - {right} = {left - right}."))
        expr = " + ".join(str(differences[p]) for p in ps)
        result.append(step(f"Put your remaining parts together: {expr} = ?", a - b,
                           component, f"{expr} = {a - b}."))
    return result


def task(component: str, band: int, mode: str, seed: int) -> dict:
    if component.startswith("story_"):
        from mathkids.word_learning import task as story_task
        return story_task(component, band, mode, seed)
    rng = random.Random(seed)
    explanation = ""
    model = []
    columns = ""
    if component == "decompose":
        n = rng.randint(10 ** (band - 1), 10 ** band - 1)
        ps = places(n)
        if mode == "guided":
            example = 56 if band == 2 else 356
            explanation = f"{example} = {parts(example)}. Each digit tells us the value of one part."
            steps = [step(f"Break apart {n:,}. What is the {PLACES[p]} part worth?",
                          n // p % 10 * p, component,
                          f"The digit {n // p % 10} counts groups of {p:,}. "
                          f"Each group is worth {p:,}.") for p in ps]
            steps.append(step(f"Put it back together: {parts(n)} = ?", n, component,
                              "The parts and the original number have the same value."))
        else:
            p = rng.choice(ps)
            expr = " + ".join("___" if q == p else str(n // q % 10 * q) for q in ps)
            steps = [step(f"{n:,} = {expr}. What is missing?", n // p % 10 * p,
                          component, f"The missing part is the value of the {PLACES[p]} digit.")]
        prompt = f"Break apart {n:,}"
    elif component == "match":
        n = rng.randint(10 ** (band - 1), 10 ** band - 1)
        p = rng.choice(places(n))
        value = n // p % 10 * p
        options = list(dict.fromkeys(n // q % 10 * q for q in places(n)))
        prompt = f"Find matching parts in {n:,}"
        example = "43 + 25" if band == 2 else "243 + 125"
        explanation = f"For {example}, 40 belongs with 20: they are both tens."
        steps = [step(f"Which part of {n:,} belongs with {2 * p:,}?", value, component,
                      f"Match {PLACES[p]} with {PLACES[p]}. {n:,} = {parts(n)}.",
                      choices=options if mode == "guided" else None)]
    else:
        nums, op = operands(component, band, rng)
        if component == "add_many":
            nums = nums[:3] if mode == "guided" else (nums + [rng.randint(10, 24)])[:4]
        prompt = f"{' + '.join(map(str, nums))} = ?" if op == "+" else f"{nums[0]} - {nums[1]} = ?"
        if band >= 4 and mode in {"guided", "faded"}:
            width = max(len(str(n)) for n in nums) + 2
            columns = "\n".join((" " if i == 0 else op) + str(n).rjust(width - 1)
                                for i, n in enumerate(nums)) + "\n" + "─" * width
        # A different, small worked example introduces the idea.
        models = {
            "add_parts": ([324, 152], "+"), "add_ones": ([247, 136], "+"),
            "add_tens": ([364, 172], "+"), "add_multi": ([368, 176], "+"),
            "add_many": ([12, 23, 14], "+"), "sub_parts": ([476, 152], "-"),
            "sub_ones": ([43, 17], "-"), "sub_tens": ([432, 170], "-"),
            "sub_multi": ([432, 178], "-"), "sub_zero": ([403, 178], "-"),
        }
        model_nums, model_op = models[component]
        if band == 2:
            model_nums = {"add_parts": [24, 52], "add_ones": [47, 36],
                          "sub_parts": [76, 52]}.get(component, model_nums)
        model = arithmetic_steps(model_nums, model_op, component, "faded")
        explanation = "Example: " + (" + " if model_op == "+" else " - ").join(map(str, model_nums))
        if mode == "guided":
            explanation += ". Watch how the parts keep the same total."
        if mode in {"guided", "faded"}:
            steps = arithmetic_steps(nums, op, component, mode)
        else:
            answer = sum(nums) if op == "+" else nums[0] - nums[1]
            steps = [step(prompt, answer, component,
                          "Break the numbers into place-value parts, then work with matching parts.")]
    # Immutable fallback tasks avoid re-generating any in-flight instruction.
    recovery = None
    if mode not in {"guided", "faded"}:
        recovery = task(component, band, "guided", seed + 104729)
    return dict(version=VERSION, component=component, band=band, mode=mode, seed=seed,
                prompt=prompt, explanation=explanation if mode == "guided" else "",
                model=model if mode == "guided" else [],
                steps=steps, recovery=recovery, columns=columns,
                remediation={c: smaller_example(c, seed + i) for i, c in enumerate(TITLES)})


def initial_progress(snapshot: dict) -> dict:
    return dict(index=0, work=[], misses=0, cycles=0, clean=True, message="",
                steps=copy.deepcopy(snapshot["steps"]), outcome=None, recovery=False,
                components={}, model=[])


def advance(snapshot: dict, progress: dict, correct: bool) -> dict:
    """Bounded automatic instruction. Each request advances one persisted revision."""
    p = copy.deepcopy(progress)
    current = p["steps"][p["index"]]
    c = current["component"]
    p["components"][c] = p["components"].get(c, True) and correct
    if correct:
        p["work"].append(dict(prompt=current["prompt"], answer=current["answer"]))
        p["index"] += 1
        p["misses"] = 0
        p["message"] = "Yes! Keep your parts together as you work."
        if p["index"] == len(p["steps"]):
            p["outcome"] = "independent" if snapshot["mode"] not in {
                "guided", "faded"
            } and p["clean"] else "practiced"
        return p
    p["clean"] = False
    p["misses"] += 1
    p["message"] = current["feedback"]
    if snapshot["recovery"] and not p["recovery"]:
        # A whole-answer miss does not diagnose a cause: inspect its ingredients.
        recovery = snapshot["recovery"]
        p.update(steps=copy.deepcopy(recovery["steps"]), index=0, recovery=True,
                 misses=0, model=recovery["model"],
                 message="Let's find the part to practice. " + recovery["explanation"])
    elif p["misses"] >= 2:
        p["cycles"] += 1
        if p["cycles"] >= 2:
            p["outcome"] = "revisit"
            p["message"] = "You worked on a new idea today. We'll practice this part again next time."
        else:
            recovery_step = copy.deepcopy(snapshot["remediation"].get(
                current["component"], snapshot["remediation"]["decompose"]
            ))
            p["message"] += " Let's try a smaller example, then come back to this step."
            p["steps"].insert(p["index"], recovery_step)
            p["misses"] = 0
    return p
