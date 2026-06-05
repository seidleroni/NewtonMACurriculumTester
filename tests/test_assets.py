"""Image renderer: every kind produces a valid, deterministic PNG."""

import pytest

from mathkids import assets

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

SPECS = [
    {"kind": "clock", "hour": 3, "minute": 40},
    {"kind": "clock", "hour": 12, "minute": 0},
    {"kind": "number_line", "start": 0, "end": 100, "step": 10, "mark": 30},
    {"kind": "fraction_number_line", "denominator": 4, "mark": 3},
    {"kind": "array", "rows": 4, "cols": 3},
    {"kind": "grid", "rows": 3, "cols": 5, "shaded": 4},
    {"kind": "fraction_bar", "numerator": 3, "denominator": 8},
    {"kind": "bar_graph", "categories": [["Dogs", 5], ["Cats", 3], ["Fish", 2]], "scale": 1},
]


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s["kind"])
def test_renders_valid_png(spec):
    png = assets.render(spec)
    assert png.startswith(PNG_MAGIC)
    assert len(png) > 200  # not a degenerate/blank image


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s["kind"])
def test_render_is_deterministic(spec):
    assert assets.render(spec) == assets.render(spec)


def test_data_uri_prefix():
    uri = assets.data_uri(SPECS[0])
    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 100


def test_unknown_kind_raises():
    with pytest.raises(KeyError):
        assets.render({"kind": "nope"})
