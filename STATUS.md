# STATUS — what's built, what isn't, and the pathways forward

Living status doc. Pairs with [`DESIGN.md`](DESIGN.md) (the full spec). Last updated 2026-07-18.

Quick health: `uv run pytest` → **1004 passing**, `uv run ruff check` clean. **80 math skills**
across Grades 2–4 (26 / 25 / 29) — the complete catalog. Every skill is structurally verified
by a property test and its math was independently re-solved by an adversarial audit (0 wrong
answers found); the Phase-3 shape cards were additionally verified geometrically (side lengths,
angles, parallelism recomputed from the raw vertices).

---

## Build phases (and where we are)

| Phase | Meaning | State |
|---|---|---|
| **0** | Engine, mastery, spaced-repetition scheduler, daily loop, both dashboards, 3 skills/kid | ✅ done |
| **1** | **Full auto-gradable *text* math** for Grades 2, 3, 4 | ✅ done |
| **2** | **Image-presented but auto-graded** math (clocks, number lines, grids, arrays, graphs, fraction bars) | ✅ done |
| **3** | Fallbacks for open-reasoning / hands-on skills (multiple-choice reframes) | ✅ done (all 7 deferred standards covered as MC/image; no parent-scored queue needed) |
| **4** | **Literacy** (and other subjects) on the same engine | ⛔ not started |
| — | **Web deployment** (Cloudflare Workers + D1 + Access) | ✅ done — live at mathkids.seidmann.workers.dev since 2026-07-18 (see README "Production") |
| later | Richer gamified UI, printables | ⛔ not started |

> Subjects beyond math are **all Phase 4+**. The engine is subject-agnostic — a `Skill` doesn't
> care if it's `2.NBT.B.5` or a spelling skill — so adding literacy is new skill modules, not a rewrite.

---

## ✅ Done — math Grades 2–4 (80 skills, complete catalog)

Skills live in `src/mathkids/engine/grade{2,3,4}/{oa,nbt,nf,md,geometry}.py`. Each ships a
generator, a lesson card, escalating hints, and a per-problem worked example.

- **Grade 2 (26, complete):** OA `2.OA.A.1, B.2, C.3, C.4`; NBT `2.NBT.A.1–A.4, B.5–B.9`;
  MD `2.MD.A.1–A.4, B.5, B.6, C.7, C.8, D.9, D.10`; Geometry `2.G.A.1, A.2, A.3`.
- **Grade 3 (25, complete):** OA `3.OA.A.1–A.4, B.5, B.6, C.7, D.8, D.9`; NBT `3.NBT.A.1–A.3`;
  NF `3.NF.A.1–A.3`; MD `3.MD.A.1, A.2, B.3, B.4, C.5, C.6, C.7, D.8`; Geometry `3.G.A.1, A.2`.
- **Grade 4 (29, complete):** OA `4.OA.A.1, A.2, A.3, A.3.a, B.4, C.5`; NBT `4.NBT.A.1–A.3,
  B.4–B.6`; NF `4.NF.A.1, A.2, B.3, B.4, C.5, C.6, C.7`; MD `4.MD.A.1, A.2, A.3, B.4, C.5, C.6,
  C.7`; Geometry `4.G.A.1, A.2, A.3`.

**Answer types** (`src/mathkids/answers.py`): integer, fraction (reduced/unreduced/mixed),
comparator (`<,=,>`), decimal (`0.7==0.70`), word (with synonyms), ordered sequence, unordered
set, time (`H:MM`), money (`$/¢`, bare whole numbers accepted as dollars), quotient+remainder,
multiple choice (radio buttons; typing the letter or the option text both grade).

**Image skills (Phases 2–3)** render deterministically in `src/mathkids/assets.py` and embed as
inline PNG data-URIs (no asset files, no extra routes). Kinds: `clock`, `number_line`,
`fraction_number_line`, `array`, `grid`, `fraction_bar`, `bar_graph`, plus the Phase-3 kinds
`figure` (points/segments/rays/lines/angle types/line pairs, for 4.G.A.1), `polygon` (marked
triangles & quadrilaterals with side ticks and right-angle squares, for 4.G.A.2), and
`protractor` (single CCW 0–180 scale, for 4.MD.C.6).

**Phase 3 (MC reframes)** covers the 7 standards that can't be typed-answer graded:
`2.NBT.B.9` (pick the *reason* a strategy works), `2.MD.A.1` (pick the measuring tool),
`2.MD.A.2` (relate two-unit measurements), `2.MD.A.3` (most reasonable estimate),
`4.G.A.1` / `4.G.A.2` (classify drawn figures), and `4.MD.C.6` (read a rendered protractor,
typed degrees). Hands-on halves (actually using a tool, sketching angles) stay family
activities by design — no parent-scored task queue was needed.

**App / loop / data:** `app.py` (FastAPI daily loop + dashboards), `mastery.py`,
`scheduler.py`, `db.py` (SQLite). New kids are seeded with their first 2 grade skills; the rest
unlock as they progress. A **placement probe** (ace the first 2 attempts on a new skill → start
at level 2) keeps already-known skills from being a grind, **within-session adaptivity**
rewrites the rest of today's plan when a level changes mid-session, an unfinished same-day
session is **resumed** (not discarded) by the Start button, and completing a session writes a
once-daily **DB backup** to `backups/`. Finishing the day's set lands on a **celebration
screen**: confetti, an accuracy-tiered headline (always positive — finishing is the win), a
counting-up score, a 🏅 banner for any skill mastered today, and a 🏆 banner when the kid's
all-time solved count crosses a century — only-up signals, per the no-streaks rule.

---

## ⛔ Not done yet (and why)

### Partial coverage within implemented skills
Several standards have a **"draw / construct / physically measure" half** that we don't grade —
we assess the readable/typed/choosable half instead:
- Drawing a shape (2.G.A.1), partitioning by hand (2.G.A.3, 3.G.A.2), constructing a graph or
  line plot (2.MD.D.9/D.10, 3.MD.B.3/B.4), placing a point on a number line by hand
  (3.NF.A.2), measuring real objects (2.MD.A.1/A.2/A.4 hands-on, 3.MD.B.4), sketching angles
  with a real protractor (4.MD.C.6), drawing lines/angles (4.G.A.1), counting lines of symmetry
  by drawing them (4.G.A.3). Freehand/physical production is a family activity by design.

### Engine / product features not built yet
- **Re-opening a lesson from the dashboard**: not built (the lesson card shows once, on
  introduction).
- **Other grades**: only Grades 2–4 math. Grade 1 / Grade 5+ are not authored (engine supports them).
- **Subjects beyond math** (literacy, etc.): not started — Phase 4.

---

## Pathways — how to extend (for future me / contributors)

- **Add a skill:** create a `Skill` subclass in the right `engine/grade{N}/{domain}.py`, implement
  `generate / lesson / hints / worked_example`, `register()` it, and add its id to
  `SEQUENCES[grade]` in `engine/base.py`. The property test (`tests/test_generators.py`) then
  verifies it automatically; run `uv run pytest`.
- **Add an answer type:** add a class to `answers.py` (implement `grade` + `canonical`), register
  it in `ANSWER_TYPES`, and add cases to `tests/test_answers.py`.
- **Add an image kind:** add a renderer to `assets.py` `_RENDERERS`, then reference it from a
  skill's `payload["image"]`. Add a case to `tests/test_assets.py`.
- **Add a subject (e.g. literacy):** the engine, mastery, scheduler, dashboards, and DB are
  subject-agnostic. Author new skill modules with new ids and a new `SEQUENCES` grade/track; the
  daily loop and progress views work unchanged.
- **Verification habit:** structural correctness is guarded by the property test; for new math,
  also run an adversarial re-solve (see the `audit-math-skills` workflow used for Grades 2–4) to
  catch wrong-but-self-consistent formulas, which the property test cannot.
