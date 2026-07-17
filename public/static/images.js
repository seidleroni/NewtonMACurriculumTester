// Client-side SVG rendering of problem figures.
//
// The server puts the problem's image spec (JSON) in a
// <div class="figure" data-image-spec='{"kind": "clock", ...}'> hook; this file
// draws it. Each renderer mirrors the geometry of the original Pillow renderer
// (src/mathkids/assets.py) so figures look the same as they always did. The
// image is presentation only — grading never depends on it.

(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var INK = "#2b2440";
  var ACCENT = "#6a4ea8";
  var SHADE = "#b49ee0";
  var DOT = "#8a6fd0";
  var POLY_FILL = "#eee8fa";
  var PROTRACTOR_FILL = "#f6f3fc";
  var FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif";

  function el(name, attrs) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  function svgCanvas(w, h) {
    return el("svg", {
      viewBox: "0 0 " + w + " " + h,
      width: w,
      height: h,
      role: "presentation",
    });
  }

  function line(svg, x1, y1, x2, y2, color, width) {
    svg.appendChild(el("line", {
      x1: x1, y1: y1, x2: x2, y2: y2,
      stroke: color, "stroke-width": width, "stroke-linecap": "round",
    }));
  }

  function rect(svg, x, y, w, h, fill, stroke, width) {
    svg.appendChild(el("rect", {
      x: x, y: y, width: w, height: h,
      fill: fill, stroke: stroke, "stroke-width": width,
    }));
  }

  function circle(svg, cx, cy, r, fill) {
    svg.appendChild(el("circle", { cx: cx, cy: cy, r: r, fill: fill }));
  }

  function text(svg, x, y, s, size, color) {
    var t = el("text", {
      x: x, y: y,
      "text-anchor": "middle", "dominant-baseline": "central",
      "font-family": FONT, "font-size": size, fill: color || INK,
    });
    t.textContent = String(s);
    svg.appendChild(t);
  }

  function unit(from, to) {
    var dx = to[0] - from[0], dy = to[1] - from[1];
    var n = Math.hypot(dx, dy) || 1;
    return [dx / n, dy / n];
  }

  // Small open arrow head at `tip`, pointing away from `awayFrom`.
  function arrowHead(svg, tip, awayFrom, color, width) {
    var ang = Math.atan2(tip[1] - awayFrom[1], tip[0] - awayFrom[0]);
    [150, -150].forEach(function (daDeg) {
      var a = ang + (daDeg * Math.PI) / 180;
      line(svg, tip[0], tip[1],
        tip[0] + 13 * Math.cos(a), tip[1] + 13 * Math.sin(a),
        color || INK, width || 3);
    });
  }

  function endpointDot(svg, p, color) {
    circle(svg, p[0], p[1], 6, color || INK);
  }

  // Small square at `vertex` between the directions of p1 and p2.
  function rightAngleMark(svg, vertex, p1, p2, size) {
    size = size || 14;
    var u1 = unit(vertex, p1);
    var u2 = unit(vertex, p2);
    var a = [vertex[0] + size * u1[0], vertex[1] + size * u1[1]];
    var b = [a[0] + size * u2[0], a[1] + size * u2[1]];
    var c = [vertex[0] + size * u2[0], vertex[1] + size * u2[1]];
    svg.appendChild(el("polyline", {
      points: a.join(",") + " " + b.join(",") + " " + c.join(","),
      fill: "none", stroke: ACCENT, "stroke-width": 2,
    }));
  }

  // --- renderers, one per spec kind ---------------------------------------

  function clock(spec) {
    var size = 240, cx = 120, cy = 120, r = 100;
    var svg = svgCanvas(size, size);
    svg.appendChild(el("circle", {
      cx: cx, cy: cy, r: r, fill: "white", stroke: INK, "stroke-width": 4,
    }));
    for (var n = 1; n <= 12; n++) {
      var ang = (n * 30 * Math.PI) / 180;
      text(svg, cx + (r - 18) * Math.sin(ang), cy - (r - 18) * Math.cos(ang), n, 18);
    }
    var ha = (((spec.hour % 12) * 30 + spec.minute * 0.5) * Math.PI) / 180;
    line(svg, cx, cy, cx + 52 * Math.sin(ha), cy - 52 * Math.cos(ha), INK, 6);
    var ma = ((spec.minute * 6) * Math.PI) / 180;
    line(svg, cx, cy, cx + 82 * Math.sin(ma), cy - 82 * Math.cos(ma), ACCENT, 4);
    circle(svg, cx, cy, 6, INK);
    return svg;
  }

  function numberLine(spec) {
    var step = spec.step || 1;
    var vals = [];
    for (var v = spec.start; v <= spec.end; v += step) vals.push(v);
    var pad = 40, gap = 70, h = 120;
    var w = pad * 2 + gap * (vals.length - 1);
    var svg = svgCanvas(w, h);
    var y = 60;
    line(svg, pad, y, w - pad, y, INK, 3);
    var markX = null;
    vals.forEach(function (val, i) {
      var x = pad + i * gap;
      if (spec.mark !== undefined && spec.mark !== null && val === spec.mark) markX = x;
      line(svg, x, y - 7, x, y + 7, INK, 2);
      text(svg, x, y + 22, val, 16);
    });
    if (markX !== null) {
      svg.appendChild(el("polygon", {
        points: markX + "," + (y - 10) + " " + (markX - 7) + "," + (y - 26) +
          " " + (markX + 7) + "," + (y - 26),
        fill: ACCENT,
      }));
    }
    return svg;
  }

  function fractionNumberLine(spec) {
    var pad = 40, gap = 70, h = 110;
    var w = pad * 2 + gap * spec.denominator;
    var svg = svgCanvas(w, h);
    var y = 55;
    line(svg, pad, y, w - pad, y, INK, 3);
    for (var i = 0; i <= spec.denominator; i++) {
      var x = pad + i * gap;
      line(svg, x, y - 7, x, y + 7, INK, 2);
      if (i === 0) text(svg, x, y + 22, "0", 16);
      else if (i === spec.denominator) text(svg, x, y + 22, "1", 16);
    }
    var mx = pad + spec.mark * gap;
    svg.appendChild(el("polygon", {
      points: mx + "," + (y - 10) + " " + (mx - 7) + "," + (y - 28) +
        " " + (mx + 7) + "," + (y - 28),
      fill: ACCENT,
    }));
    return svg;
  }

  function dotArray(spec) {
    var pad = 26, gap = 34, rad = 9;
    var w = pad * 2 + gap * (spec.cols - 1);
    var h = pad * 2 + gap * (spec.rows - 1);
    var svg = svgCanvas(w, h);
    for (var r = 0; r < spec.rows; r++)
      for (var c = 0; c < spec.cols; c++)
        circle(svg, pad + c * gap, pad + r * gap, rad, DOT);
    return svg;
  }

  function grid(spec) {
    var cell = 30, pad = 12, shaded = spec.shaded || 0;
    var w = pad * 2 + spec.cols * cell;
    var h = pad * 2 + spec.rows * cell;
    var svg = svgCanvas(w, h);
    var k = 0;
    for (var r = 0; r < spec.rows; r++)
      for (var c = 0; c < spec.cols; c++) {
        rect(svg, pad + c * cell, pad + r * cell, cell, cell,
          k < shaded ? SHADE : "white", INK, 2);
        k++;
      }
    return svg;
  }

  function fractionBar(spec) {
    var cell = 44, h = 56, pad = 12;
    var w = pad * 2 + spec.denominator * cell;
    var svg = svgCanvas(w, h + pad * 2);
    for (var i = 0; i < spec.denominator; i++)
      rect(svg, pad + i * cell, pad, cell, h,
        i < spec.numerator ? SHADE : "white", INK, 2);
    return svg;
  }

  function barGraph(spec) {
    // spec.categories: list of [label, value]
    var bw = 48, gap = 26, baseY = 200, topPad = 24, leftPad = 44;
    var cats = spec.categories;
    var w = leftPad + cats.length * (bw + gap) + 20;
    var h = baseY + 40;
    var svg = svgCanvas(w, h);
    var maxV = 1;
    cats.forEach(function (c) { if (c[1] > maxV) maxV = c[1]; });
    var u = 160 / Math.max(maxV, 1);
    line(svg, leftPad - 6, topPad, leftPad - 6, baseY, INK, 2);
    line(svg, leftPad - 6, baseY, w - 10, baseY, INK, 2);
    var tick = Math.max(spec.scale || 1, 1);
    for (var v = 0; v <= maxV; v += tick) {
      var y = baseY - v * u;
      line(svg, leftPad - 10, y, leftPad - 6, y, INK, 2);
      text(svg, leftPad - 20, y, v, 15);
    }
    cats.forEach(function (c, i) {
      var x0 = leftPad + i * (bw + gap);
      rect(svg, x0, baseY - c[1] * u, bw, c[1] * u, ACCENT, INK, 2);
      text(svg, x0 + bw / 2, baseY + 16, c[0], 15);
    });
    return svg;
  }

  // Geometric figure cards for 4.G.A.1: point / segment / ray / line,
  // parallel / perpendicular / intersecting line pairs, and a single angle.
  function figure(spec) {
    var w = 260, h = 170;
    var svg = svgCanvas(w, h);
    var a = [45, 120], b = [215, 50]; // default slanted stroke
    var f = spec.figure;

    if (f === "point") {
      endpointDot(svg, [w / 2, h / 2], ACCENT);
    } else if (f === "segment") {
      line(svg, a[0], a[1], b[0], b[1], INK, 3);
      endpointDot(svg, a);
      endpointDot(svg, b);
    } else if (f === "ray") {
      line(svg, a[0], a[1], b[0], b[1], INK, 3);
      endpointDot(svg, a);
      arrowHead(svg, b, a);
    } else if (f === "line") {
      line(svg, a[0], a[1], b[0], b[1], INK, 3);
      arrowHead(svg, a, b);
      arrowHead(svg, b, a);
    } else if (f === "parallel") {
      [-30, 30].forEach(function (dy) {
        var p = [40, 95 + dy], q = [220, 45 + dy];
        line(svg, p[0], p[1], q[0], q[1], INK, 3);
        arrowHead(svg, p, q);
        arrowHead(svg, q, p);
      });
    } else if (f === "perpendicular" || f === "intersecting") {
      var c = [w / 2, h / 2];
      line(svg, c[0] - 95, c[1], c[0] + 95, c[1], INK, 3);
      arrowHead(svg, [c[0] - 95, c[1]], c);
      arrowHead(svg, [c[0] + 95, c[1]], c);
      var ang = ((f === "perpendicular" ? 90 : 50) * Math.PI) / 180;
      var dx = 75 * Math.cos(ang), dy = 75 * Math.sin(ang);
      var p = [c[0] - dx, c[1] + dy], q = [c[0] + dx, c[1] - dy];
      line(svg, p[0], p[1], q[0], q[1], INK, 3);
      arrowHead(svg, p, q);
      arrowHead(svg, q, p);
      if (f === "perpendicular") rightAngleMark(svg, c, [c[0] + 95, c[1]], q);
    } else if (f === "angle") {
      var deg = spec.degrees || 0;
      var vtx = [110, 135], r = 100; // centered enough that obtuse rays fit
      var p1 = [vtx[0] + r, vtx[1]]; // ray along 0 degrees
      var rad = (deg * Math.PI) / 180;
      var p2 = [vtx[0] + r * Math.cos(rad), vtx[1] - r * Math.sin(rad)];
      line(svg, vtx[0], vtx[1], p1[0], p1[1], INK, 3);
      line(svg, vtx[0], vtx[1], p2[0], p2[1], INK, 3);
      arrowHead(svg, p1, vtx);
      arrowHead(svg, p2, vtx);
      endpointDot(svg, vtx);
      if (deg === 90) {
        rightAngleMark(svg, vtx, p1, p2);
      } else {
        // arc from the tilted ray down to the baseline, radius 28
        var sx = vtx[0] + 28 * Math.cos(rad), sy = vtx[1] - 28 * Math.sin(rad);
        svg.appendChild(el("path", {
          d: "M " + sx + " " + sy + " A 28 28 0 " + (deg > 180 ? 1 : 0) +
            " 1 " + (vtx[0] + 28) + " " + vtx[1],
          fill: "none", stroke: ACCENT, "stroke-width": 3,
        }));
      }
    }
    return svg;
  }

  // Filled polygon for 4.G.A.2, with optional equal-side tick marks (count
  // per side) and right-angle marks (vertex indices).
  function polygon(spec) {
    var xs = spec.points.map(function (p) { return p[0]; });
    var ys = spec.points.map(function (p) { return p[1]; });
    var minX = Math.min.apply(null, xs), minY = Math.min.apply(null, ys);
    var pad = 22;
    var w = Math.max.apply(null, xs) - minX + pad * 2;
    var h = Math.max.apply(null, ys) - minY + pad * 2;
    var pts = spec.points.map(function (p) {
      return [p[0] - minX + pad, p[1] - minY + pad];
    });
    var svg = svgCanvas(w, h);
    svg.appendChild(el("polygon", {
      points: pts.map(function (p) { return p.join(","); }).join(" "),
      fill: POLY_FILL, stroke: INK, "stroke-width": 3, "stroke-linejoin": "round",
    }));
    var n = pts.length;
    (spec.ticks || []).forEach(function (count, i) {
      if (!count) return;
      var p = pts[i], q = pts[(i + 1) % n];
      var mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2;
      var u = unit(p, q);
      var nx = -u[1], ny = u[0]; // perpendicular to the side
      for (var k = 0; k < count; k++) {
        var off = (k - (count - 1) / 2) * 7;
        var cx = mx + u[0] * off, cy = my + u[1] * off;
        line(svg, cx - 7 * nx, cy - 7 * ny, cx + 7 * nx, cy + 7 * ny, ACCENT, 3);
      }
    });
    (spec.right_marks || []).forEach(function (vi) {
      rightAngleMark(svg, pts[vi], pts[(vi - 1 + n) % n], pts[(vi + 1) % n]);
    });
    return svg;
  }

  // A protractor with a single counterclockwise 0-180 scale (0 on the right)
  // and an angle to read: one ray along 0, the other at spec.angle degrees.
  function protractor(spec) {
    var w = 330, h = 200, cx = 165, cy = 170, r = 130;
    var svg = svgCanvas(w, h);
    // body: half disc (flat side down) + the two radii of the pie slice
    svg.appendChild(el("path", {
      d: "M " + (cx - r) + " " + cy + " A " + r + " " + r + " 0 0 1 " +
        (cx + r) + " " + cy + " Z",
      fill: PROTRACTOR_FILL, stroke: INK, "stroke-width": 2,
    }));
    for (var deg = 0; deg <= 180; deg += 10) {
      var rad = (deg * Math.PI) / 180;
      var major = deg % 30 === 0;
      var r0 = r - (major ? 16 : 9);
      line(svg,
        cx + r0 * Math.cos(rad), cy - r0 * Math.sin(rad),
        cx + r * Math.cos(rad), cy - r * Math.sin(rad),
        INK, major ? 2 : 1);
      if (major) {
        var rl = r - 30;
        text(svg, cx + rl * Math.cos(rad), cy - rl * Math.sin(rad), deg, 14);
      }
    }
    var arad = (spec.angle * Math.PI) / 180;
    line(svg, cx, cy, cx + r + 18, cy, ACCENT, 4);
    line(svg, cx, cy,
      cx + (r + 18) * Math.cos(arad), cy - (r + 18) * Math.sin(arad), ACCENT, 4);
    circle(svg, cx, cy, 5, ACCENT);
    return svg;
  }

  var RENDERERS = {
    clock: clock,
    number_line: numberLine,
    fraction_number_line: fractionNumberLine,
    array: dotArray,
    grid: grid,
    fraction_bar: fractionBar,
    bar_graph: barGraph,
    figure: figure,
    polygon: polygon,
    protractor: protractor,
  };

  document.addEventListener("DOMContentLoaded", function () {
    var hooks = document.querySelectorAll("[data-image-spec]");
    Array.prototype.forEach.call(hooks, function (div) {
      var spec;
      try {
        spec = JSON.parse(div.getAttribute("data-image-spec"));
      } catch (e) {
        return;
      }
      var render = RENDERERS[spec.kind];
      if (render) div.appendChild(render(spec));
    });
  });
})();
