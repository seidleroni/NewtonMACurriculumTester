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
    {"kind": "figure", "figure": "point"},
    {"kind": "figure", "figure": "segment"},
    {"kind": "figure", "figure": "ray"},
    {"kind": "figure", "figure": "line"},
    {"kind": "figure", "figure": "parallel"},
    {"kind": "figure", "figure": "perpendicular"},
    {"kind": "figure", "figure": "intersecting"},
    {"kind": "figure", "figure": "angle", "degrees": 40},
    {"kind": "figure", "figure": "angle", "degrees": 90},
    {"kind": "figure", "figure": "angle", "degrees": 135},
    {
        "kind": "polygon",
        "points": [[0, 0], [120, 0], [120, 120], [0, 120]],
        "ticks": [1, 1, 1, 1],
        "right_marks": [0, 1, 2, 3],
    },
    {"kind": "polygon", "points": [[0, 130], [200, 130], [160, 90]]},
    {"kind": "protractor", "angle": 60},
    {"kind": "protractor", "angle": 135},
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
