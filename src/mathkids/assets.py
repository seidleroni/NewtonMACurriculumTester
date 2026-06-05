"""Deterministic image rendering for Phase-2 (image-presented) skills.

A skill that needs a picture puts an image spec in ``Problem.payload["image"]``,
e.g. ``{"kind": "clock", "hour": 3, "minute": 40}``. The web layer calls
``data_uri(spec)`` to embed the rendered PNG inline in the page — no asset files,
no extra routes, no state. Rendering is pure: same spec -> same image.

The image is *presentation only*; the problem's answer is computed in Python from
the same spec, so grading never depends on the pixels.
"""

from __future__ import annotations

import base64
import io
import math

from PIL import Image, ImageDraw, ImageFont

WHITE = (255, 255, 255)
INK = (43, 36, 64)
ACCENT = (106, 78, 168)
SHADE = (180, 158, 224)
DOT = (138, 111, 208)


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _center_text(draw: ImageDraw.ImageDraw, xy, text, font, fill=INK):
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text((xy[0] - w / 2, xy[1] - h / 2), text, font=font, fill=fill)


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _clock(hour: int, minute: int) -> Image.Image:
    size = 240
    img = Image.new("RGB", (size, size), WHITE)
    d = ImageDraw.Draw(img)
    cx = cy = size // 2
    r = 100
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=4)
    font = _font(18)
    for n in range(1, 13):
        ang = math.radians(n * 30)
        x = cx + (r - 18) * math.sin(ang)
        y = cy - (r - 18) * math.cos(ang)
        _center_text(d, (x, y), str(n), font)
    # hour hand
    ha = math.radians((hour % 12) * 30 + minute * 0.5)
    d.line([cx, cy, cx + 52 * math.sin(ha), cy - 52 * math.cos(ha)], fill=INK, width=6)
    # minute hand
    ma = math.radians(minute * 6)
    d.line([cx, cy, cx + 82 * math.sin(ma), cy - 82 * math.cos(ma)], fill=ACCENT, width=4)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=INK)
    return img


def _number_line(start: int, end: int, step: int, mark) -> Image.Image:
    vals = list(range(start, end + 1, step))
    pad, gap, h = 40, 70, 120
    w = pad * 2 + gap * (len(vals) - 1)
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    y = 60
    d.line([pad, y, w - pad, y], fill=INK, width=3)
    font = _font(16)
    xs = {}
    for i, v in enumerate(vals):
        x = pad + i * gap
        xs[v] = x
        d.line([x, y - 7, x, y + 7], fill=INK, width=2)
        _center_text(d, (x, y + 22), str(v), font)
    if mark is not None and mark in xs:
        x = xs[mark]
        d.polygon([(x, y - 10), (x - 7, y - 26), (x + 7, y - 26)], fill=ACCENT)
    return img


def _fraction_number_line(denominator: int, mark: int) -> Image.Image:
    pad, gap, h = 40, 70, 110
    w = pad * 2 + gap * denominator
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    y = 55
    d.line([pad, y, w - pad, y], fill=INK, width=3)
    font = _font(16)
    for i in range(denominator + 1):
        x = pad + i * gap
        d.line([x, y - 7, x, y + 7], fill=INK, width=2)
        if i == 0:
            _center_text(d, (x, y + 22), "0", font)
        elif i == denominator:
            _center_text(d, (x, y + 22), "1", font)
    x = pad + mark * gap
    d.polygon([(x, y - 10), (x - 7, y - 28), (x + 7, y - 28)], fill=ACCENT)
    return img


def _array(rows: int, cols: int) -> Image.Image:
    pad, gap, rad = 26, 34, 9
    w = pad * 2 + gap * (cols - 1)
    h = pad * 2 + gap * (rows - 1)
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    for r in range(rows):
        for c in range(cols):
            cx = pad + c * gap
            cy = pad + r * gap
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=DOT)
    return img


def _grid(rows: int, cols: int, shaded: int = 0) -> Image.Image:
    cell, pad = 30, 12
    w = pad * 2 + cols * cell
    h = pad * 2 + rows * cell
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    k = 0
    for r in range(rows):
        for c in range(cols):
            x0, y0 = pad + c * cell, pad + r * cell
            fill = SHADE if k < shaded else WHITE
            d.rectangle([x0, y0, x0 + cell, y0 + cell], fill=fill, outline=INK, width=2)
            k += 1
    return img


def _fraction_bar(numerator: int, denominator: int) -> Image.Image:
    cell, h, pad = 44, 56, 12
    w = pad * 2 + denominator * cell
    img = Image.new("RGB", (w, h + pad * 2), WHITE)
    d = ImageDraw.Draw(img)
    for i in range(denominator):
        x0 = pad + i * cell
        fill = SHADE if i < numerator else WHITE
        d.rectangle([x0, pad, x0 + cell, pad + h], fill=fill, outline=INK, width=2)
    return img


def _bar_graph(categories: list, scale: int = 1) -> Image.Image:
    # categories: list of [label, value]
    bw, gap, base_y, top_pad, left_pad = 48, 26, 200, 24, 44
    n = len(categories)
    w = left_pad + n * (bw + gap) + 20
    h = base_y + 40
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    max_v = max([v for _, v in categories] + [1])
    unit = 160 / max(max_v, 1)
    font = _font(15)
    d.line([left_pad - 6, top_pad, left_pad - 6, base_y], fill=INK, width=2)
    d.line([left_pad - 6, base_y, w - 10, base_y], fill=INK, width=2)
    # y ticks at multiples of scale
    tick = max(scale, 1)
    v = 0
    while v <= max_v:
        y = base_y - v * unit
        d.line([left_pad - 10, y, left_pad - 6, y], fill=INK, width=2)
        _center_text(d, (left_pad - 20, y), str(v), font)
        v += tick
    for i, (label, value) in enumerate(categories):
        x0 = left_pad + i * (bw + gap)
        y0 = base_y - value * unit
        d.rectangle([x0, y0, x0 + bw, base_y], fill=ACCENT, outline=INK, width=2)
        _center_text(d, (x0 + bw / 2, base_y + 16), str(label), font)
    return img


_RENDERERS = {
    "clock": lambda s: _clock(s["hour"], s["minute"]),
    "number_line": lambda s: _number_line(s["start"], s["end"], s.get("step", 1), s.get("mark")),
    "fraction_number_line": lambda s: _fraction_number_line(s["denominator"], s["mark"]),
    "array": lambda s: _array(s["rows"], s["cols"]),
    "grid": lambda s: _grid(s["rows"], s["cols"], s.get("shaded", 0)),
    "fraction_bar": lambda s: _fraction_bar(s["numerator"], s["denominator"]),
    "bar_graph": lambda s: _bar_graph(s["categories"], s.get("scale", 1)),
}


def render(spec: dict) -> bytes:
    """Render an image spec to PNG bytes. Raises KeyError on an unknown kind."""
    return _png(_RENDERERS[spec["kind"]](spec))


def data_uri(spec: dict) -> str:
    return "data:image/png;base64," + base64.b64encode(render(spec)).decode("ascii")
