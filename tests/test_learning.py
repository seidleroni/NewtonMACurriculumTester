"""Concept progression, not merely arithmetic answers grading themselves."""
import random
import re

import pytest

from mathkids import learning as l


@pytest.mark.parametrize("component", list(l.TITLES)[:-1])
def test_snapshot_math_and_bounded_recovery(component):
    for seed in range(30):
        snapshot = l.task(component, 3, "guided", seed)
        for step in snapshot["steps"]:
            # Independently solve the arithmetic expressions actually shown to the child.
            match = re.search(r"([\d,]+(?: [+-] [\d,]+)+) = \?", step["prompt"])
            if match:
                tokens = match[1].replace(",", "").split()
                value = int(tokens[0])
                for i in range(1, len(tokens), 2):
                    value += int(tokens[i+1]) * (1 if tokens[i] == "+" else -1)
                assert value == step["answer"], step
        progress = l.initial_progress(snapshot)
        for _ in range(6):
            if progress["outcome"]:
                break
            progress = l.advance(snapshot, progress, False)
        assert progress["outcome"] == "revisit"


@pytest.mark.parametrize("band", [2, 3, 4, 5, 6])
def test_decomposition_includes_zeros_and_reconstructs(band):
    saw_zero = False
    for seed in range(30):
        task = l.task("decompose", band, "guided", seed)
        values = [s["answer"] for s in task["steps"]]
        assert sum(values[:-1]) == values[-1]
        saw_zero |= 0 in values[:-1]
    assert saw_zero


def test_exchange_preserves_number_across_zero():
    steps = l.arithmetic_steps([403, 178], "-", "sub_zero", "faded")
    assert steps[0]["answer"] == 300  # 400 -> 300 + 100
    assert steps[1]["answer"] == 100  # 0 tens + 100
    assert steps[2]["answer"] == 90   # 100 -> 90 + 10
    assert steps[3]["answer"] == 13   # 3 ones + 10
    assert steps[-1]["answer"] == 225


def test_single_regrouping_bands_do_not_add_another_demand():
    for seed in range(50):
        nums, _ = l.operands("add_ones", 3, random.Random(seed))
        assert sum(n % 10 for n in nums) >= 10
        assert sum(n // 10 % 10 for n in nums) + 1 < 10
        nums, _ = l.operands("add_tens", 3, random.Random(seed))
        assert sum(n % 10 for n in nums) < 10
        assert sum(n // 10 % 10 for n in nums) >= 10


def test_support_fades_and_independence_needs_another_day():
    state = l.empty_state("decompose", 3)
    state = l.evidence_update(state, False, 100, 1, "probe")
    assert state["stage"] == "guided"
    for seed in (2, 3):
        state = l.evidence_update(state, True, 100, seed, "guided")
    assert state["stage"] == "faded"
    for seed in (4, 5):
        state = l.evidence_update(state, True, 100, seed, "faded")
    assert state["stage"] == "independent"
    for seed in (6, 7, 8):
        state = l.evidence_update(state, True, 100, seed, "independent")
    assert state["stage"] == "independent"
    state = l.evidence_update(state, True, 101, 9, "independent")
    assert state["stage"] == "established"
    repeated = l.evidence_update(state, True, 102, 9, "independent")
    assert repeated == state


def test_two_independent_misses_reopen_only_that_state():
    state = l.empty_state("add_ones", 3)
    state["stage"] = "established"
    state = l.evidence_update(state, False, 100, 1, "established")
    assert state["stage"] == "established"
    state = l.evidence_update(state, True, 100, 2, "established")
    state = l.evidence_update(state, False, 100, 3, "established")
    assert state["stage"] == "guided"


def test_wrong_probe_opens_instruction_without_claiming_success():
    task = l.task("add_ones", 3, "probe", 10)
    progress = l.advance(task, l.initial_progress(task), False)
    assert progress["recovery"] and not progress["clean"]
    while not progress["outcome"]:
        progress = l.advance(task, progress, True)
    assert progress["outcome"] == "practiced"


def test_snapshot_is_immutable_during_transition():
    task = l.task("decompose", 3, "guided", 1)
    before = l.initial_progress(task)
    after = l.advance(task, before, False)
    assert before["clean"] and not after["clean"]
    assert before["misses"] == 0


def test_guided_ingredient_practice_does_not_demote_established_knowledge():
    state = l.empty_state("decompose", 3)
    state.update(stage="established", streak=5)
    state = l.evidence_update(state, True, 100, 1, "guided")
    assert state["stage"] == "established"
def test_large_number_column_bridge_does_not_show_answer():
    from mathkids import learning

    for mode in ("guided", "faded"):
        snapshot = learning.task("add_multi", 5, mode, 123)
        rows = snapshot["columns"].splitlines()
        assert len(rows) == 3
        assert len({len(row) for row in rows}) == 1
        assert rows[1].startswith("+")
    assert learning.task("add_multi", 5, "independent", 123)["columns"] == ""
