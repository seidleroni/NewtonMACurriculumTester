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


def _arrow_head(d: ImageDraw.ImageDraw, tip, away_from, color=INK, width=3):
    """Small open arrow head at `tip`, pointing away from `away_from`."""
    ang = math.atan2(tip[1] - away_from[1], tip[0] - away_from[0])
    for da in (math.radians(150), math.radians(-150)):
        d.line(
            [tip, (tip[0] + 13 * math.cos(ang + da), tip[1] + 13 * math.sin(ang + da))],
            fill=color,
            width=width,
        )


def _endpoint_dot(d: ImageDraw.ImageDraw, p, color=INK):
    d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=color)


def _right_angle_mark(d: ImageDraw.ImageDraw, vertex, p1, p2, size=14):
    """Small square at `vertex` between the directions of p1 and p2."""
    u1 = _unit(vertex, p1)
    u2 = _unit(vertex, p2)
    a = (vertex[0] + size * u1[0], vertex[1] + size * u1[1])
    b = (a[0] + size * u2[0], a[1] + size * u2[1])
    c = (vertex[0] + size * u2[0], vertex[1] + size * u2[1])
    d.line([a, b, c], fill=ACCENT, width=2)


def _unit(p_from, p_to):
    dx, dy = p_to[0] - p_from[0], p_to[1] - p_from[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _figure(figure: str, degrees: int = 0) -> Image.Image:
    """Geometric figure cards for 4.G.A.1: point / segment / ray / line,
    parallel / perpendicular / intersecting line pairs, and a single angle."""
    w, h = 260, 170
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    a, b = (45, 120), (215, 50)  # default slanted stroke

    if figure == "point":
        _endpoint_dot(d, (w // 2, h // 2), ACCENT)
    elif figure == "segment":
        d.line([a, b], fill=INK, width=3)
        _endpoint_dot(d, a)
        _endpoint_dot(d, b)
    elif figure == "ray":
        d.line([a, b], fill=INK, width=3)
        _endpoint_dot(d, a)
        _arrow_head(d, b, a)
    elif figure == "line":
        d.line([a, b], fill=INK, width=3)
        _arrow_head(d, a, b)
        _arrow_head(d, b, a)
    elif figure == "parallel":
        for dy in (-30, 30):
            p, q = (40, 95 + dy), (220, 45 + dy)
            d.line([p, q], fill=INK, width=3)
            _arrow_head(d, p, q)
            _arrow_head(d, q, p)
    elif figure in ("perpendicular", "intersecting"):
        c = (w // 2, h // 2)
        d.line([(c[0] - 95, c[1]), (c[0] + 95, c[1])], fill=INK, width=3)
        _arrow_head(d, (c[0] - 95, c[1]), c)
        _arrow_head(d, (c[0] + 95, c[1]), c)
        ang = math.radians(90 if figure == "perpendicular" else 50)
        dx, dy = 75 * math.cos(ang), 75 * math.sin(ang)
        p, q = (c[0] - dx, c[1] + dy), (c[0] + dx, c[1] - dy)
        d.line([p, q], fill=INK, width=3)
        _arrow_head(d, p, q)
        _arrow_head(d, q, p)
        if figure == "perpendicular":
            _right_angle_mark(d, c, (c[0] + 95, c[1]), q)
    elif figure == "angle":
        v = (110, 135)  # centered enough that obtuse rays stay on the canvas
        r = 100
        p1 = (v[0] + r, v[1])  # ray along 0 degrees
        rad = math.radians(degrees)
        p2 = (v[0] + r * math.cos(rad), v[1] - r * math.sin(rad))
        d.line([v, p1], fill=INK, width=3)
        d.line([v, p2], fill=INK, width=3)
        _arrow_head(d, p1, v)
        _arrow_head(d, p2, v)
        _endpoint_dot(d, v)
        if degrees == 90:
            _right_angle_mark(d, v, p1, p2)
        else:
            d.arc([v[0] - 28, v[1] - 28, v[0] + 28, v[1] + 28],
                  start=-degrees, end=0, fill=ACCENT, width=3)
    else:
        raise KeyError(f"unknown figure: {figure}")
    return img


def _polygon(points: list, ticks: list | None = None, right_marks: list | None = None) -> Image.Image:
    """Filled polygon for 4.G.A.2, with optional equal-side tick marks (count
    per side) and right-angle marks (vertex indices)."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pad = 22
    w = int(max(xs) - min(xs)) + pad * 2
    h = int(max(ys) - min(ys)) + pad * 2
    pts = [(p[0] - min(xs) + pad, p[1] - min(ys) + pad) for p in points]
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=(238, 232, 250), outline=INK)
    d.line(pts + [pts[0]], fill=INK, width=3)
    n = len(pts)
    for i, count in enumerate(ticks or []):
        if not count:
            continue
        p, q = pts[i], pts[(i + 1) % n]
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        ux, uy = _unit(p, q)
        nx, ny = -uy, ux  # perpendicular to the side
        for k in range(count):
            off = (k - (count - 1) / 2) * 7
            cx, cy = mx + ux * off, my + uy * off
            d.line([(cx - 7 * nx, cy - 7 * ny), (cx + 7 * nx, cy + 7 * ny)],
                   fill=ACCENT, width=3)
    for vi in right_marks or []:
        v = pts[vi]
        _right_angle_mark(d, v, pts[(vi - 1) % n], pts[(vi + 1) % n])
    return img


def _protractor(angle: int) -> Image.Image:
    """A protractor with a single counterclockwise 0-180 scale (0 on the right)
    and an angle to read: one ray along 0, the other at `angle` degrees."""
    w, h = 330, 200
    cx, cy, r = 165, 170, 130
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    # protractor body: half disc + baseline
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=(246, 243, 252), outline=INK, width=2)
    font = _font(14)
    for deg in range(0, 181, 10):
        rad = math.radians(deg)
        major = deg % 30 == 0
        r0 = r - (16 if major else 9)
        d.line(
            [(cx + r0 * math.cos(rad), cy - r0 * math.sin(rad)),
             (cx + r * math.cos(rad), cy - r * math.sin(rad))],
            fill=INK, width=2 if major else 1,
        )
        if major:
            rl = r - 30
            _center_text(d, (cx + rl * math.cos(rad), cy - rl * math.sin(rad)), str(deg), font)
    # the angle: baseline ray at 0, second ray at `angle`
    rad = math.radians(angle)
    d.line([(cx, cy), (cx + (r + 18), cy)], fill=ACCENT, width=4)
    d.line([(cx, cy), (cx + (r + 18) * math.cos(rad), cy - (r + 18) * math.sin(rad))],
           fill=ACCENT, width=4)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=ACCENT)
    return img


_RENDERERS = {
    "clock": lambda s: _clock(s["hour"], s["minute"]),
    "number_line": lambda s: _number_line(s["start"], s["end"], s.get("step", 1), s.get("mark")),
    "fraction_number_line": lambda s: _fraction_number_line(s["denominator"], s["mark"]),
    "array": lambda s: _array(s["rows"], s["cols"]),
    "grid": lambda s: _grid(s["rows"], s["cols"], s.get("shaded", 0)),
    "fraction_bar": lambda s: _fraction_bar(s["numerator"], s["denominator"]),
    "bar_graph": lambda s: _bar_graph(s["categories"], s.get("scale", 1)),
    "figure": lambda s: _figure(s["figure"], s.get("degrees", 0)),
    "polygon": lambda s: _polygon(s["points"], s.get("ticks"), s.get("right_marks")),
    "protractor": lambda s: _protractor(s["angle"]),
}


def render(spec: dict) -> bytes:
    """Render an image spec to PNG bytes. Raises KeyError on an unknown kind."""
    return _png(_RENDERERS[spec["kind"]](spec))


def data_uri(spec: dict) -> str:
    return "data:image/png;base64," + base64.b64encode(render(spec)).decode("ascii")
