import random

import pytest

from mathkids import learning as l
from mathkids import word_learning as w


@pytest.mark.parametrize("band", w.TIERS)
def test_ranges_and_exchange_are_separate(band):
    low, high, exchange = w.TIERS[band]
    for seed in range(200):
        total, part = w.numbers(band, random.Random(seed))
        assert low <= total <= high
        assert 0 < part < total
        assert (total % 10 < part % 10) == exchange
        if band == 1:
            assert total < 10


def test_number_growth_requires_confirmation_not_same_day_or_guided_success():
    known = {}
    for component, band in w.gates(4):
        assert w.select(known, 4, 100) == (component, band)
        state = l.empty_state(component, band)
        for seed in range(3):
            state = l.evidence_update(state, True, 100, seed, "probe")
        known[(component, band)] = state
        assert w.select(known, 4, 100) == (component, band)
        state = l.evidence_update(state, True, 101, 10, "independent")
        assert state["stage"] == "established"
        known[(component, band)] = state
    assert w.select(known, 4, 101) is None
    first = w.gates(4)[0]
    known[first] = l.evidence_update(known[first], False, 102, 11, "independent")
    known[first] = l.evidence_update(known[first], False, 102, 12, "independent")
    assert w.select(known, 4, 102) == first


@pytest.mark.parametrize("component", [c for c in l.TITLES if c.startswith("story_")])
@pytest.mark.parametrize("band", w.TIERS)
def test_story_answers_and_support_fading(component, band):
    for seed in range(15):
        total, part = w.numbers(band, random.Random(seed))
        expected = total if component == "story_start_take" else total - part
        independent = w.task(component, band, "independent", seed)
        assert len(independent["steps"]) == 1
        assert independent["steps"][0]["answer"] == expected
        assert "diagram" not in independent["steps"][0]
        assert not independent["explanation"]
        faded = w.task(component, band, "faded", seed)
        guided = w.task(component, band, "guided", seed)
        assert guided["steps"][-1]["answer"] == faded["steps"][-1]["answer"] == expected
        assert len(guided["steps"]) >= len(faded["steps"])
        assert guided["explanation"] and not faded["explanation"]
        assert all(s["component"] == component for s in guided["steps"])


def test_new_tiers_do_not_inherit_prior_tier_evidence():
    known = {pair: dict(stage="established", due_at=200) for pair in w.gates(4)
             if pair[1] == 1}
    assert w.select(known, 4, 100) == ("story_calculate", 2)
    known[("story_calculate", 2)] = dict(stage="independent", evidence=[])
    assert w.select(known, 4, 100) == ("story_calculate", 2)
