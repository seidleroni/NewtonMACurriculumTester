# STATUS — what's built, what isn't, and the pathways forward

Living status doc. Pairs with [`DESIGN.md`](DESIGN.md) (the full spec). Last updated 2026-06-05.

Quick health: `uv run pytest` → **484 passing**, `uv run ruff check` clean. **73 math skills**
across Grades 2–4 (22 / 25 / 26). Every skill is structurally verified by a property test and
its math was independently re-solved by an adversarial audit (0 wrong answers found).

---

## Build phases (and where we are)

| Phase | Meaning | State |
|---|---|---|
| **0** | Engine, mastery, spaced-repetition scheduler, daily loop, both dashboards, 3 skills/kid | ✅ done |
| **1** | **Full auto-gradable *text* math** for Grades 2, 3, 4 | ✅ done |
| **2** | **Image-presented but auto-graded** math (clocks, number lines, grids, arrays, graphs, fraction bars) | ✅ done |
| **3** | Fallbacks for open-reasoning / hands-on skills (multiple-choice reframes, parent-scored tasks) | ⛔ not started |
| **4** | **Literacy** (and other subjects) on the same engine | ⛔ not started |
| later | Web deployment, richer gamified UI, printables | ⛔ not started |

> Subjects beyond math are **all Phase 4+**. The engine is subject-agnostic — a `Skill` doesn't
> care if it's `2.NBT.B.5` or a spelling skill — so adding literacy is new skill modules, not a rewrite.

---

## ✅ Done — math Grades 2–4 (73 skills)

Skills live in `src/mathkids/engine/grade{2,3,4}/{oa,nbt,nf,md,geometry}.py`. Each ships a
generator, a lesson card, escalating hints, and a per-problem worked example.

- **Grade 2 (22):** OA `2.OA.A.1, B.2, C.3, C.4`; NBT `2.NBT.A.1–A.4, B.5–B.8`; MD `2.MD.A.4,
  B.5, B.6, C.7, C.8, D.9, D.10`; Geometry `2.G.A.1, A.2, A.3`.
- **Grade 3 (25, complete):** OA `3.OA.A.1–A.4, B.5, B.6, C.7, D.8, D.9`; NBT `3.NBT.A.1–A.3`;
  NF `3.NF.A.1–A.3`; MD `3.MD.A.1, A.2, B.3, B.4, C.5, C.6, C.7, D.8`; Geometry `3.G.A.1, A.2`.
- **Grade 4 (26):** OA `4.OA.A.1, A.2, A.3, A.3.a, B.4, C.5`; NBT `4.NBT.A.1–A.3, B.4–B.6`;
  NF `4.NF.A.1, A.2, B.3, B.4, C.5, C.6, C.7`; MD `4.MD.A.1, A.2, A.3, B.4, C.5, C.7`;
  Geometry `4.G.A.3`.

**Answer types** (`src/mathkids/answers.py`): integer, fraction (reduced/unreduced/mixed),
comparator (`<,=,>`), decimal (`0.7==0.70`), word (with synonyms), ordered sequence, unordered
set, time (`H:MM`), money (`$/¢`), quotient+remainder.

**Image skills (Phase 2)** render deterministically in `src/mathkids/assets.py` and embed as
inline PNG data-URIs (no asset files, no extra routes). Kinds: `clock`, `number_line`,
`fraction_number_line`, `array`, `grid`, `fraction_bar`, `bar_graph`. Used by e.g. 2.MD.C.7
(clock), 2.OA.C.4 (array), 2.G.A.2 / 3.MD.C.5 / 3.MD.C.6 (grid), 3.NF.A.1 / 3.G.A.2 (fraction
bar), 3.NF.A.2 (fraction number line), 2.MD.B.6 (number line), 2.MD.D.9/D.10 / 3.MD.B.3/B.4 (bar
graph).

**App / loop / data:** unchanged from Phase 0 in shape — `app.py` (FastAPI daily loop +
dashboards), `mastery.py`, `scheduler.py`, `db.py` (SQLite). New kids are seeded with their
first 2 grade skills; the rest unlock as they progress.

---

## ⛔ Not done yet (and why)

### Skills intentionally deferred to Phase 3 (7 of the 80 catalog standards)
These can't be auto-generated *and* auto-graded as typed answers; they need a multiple-choice
reframe, an interactive widget, or a parent check. Listed in `DESIGN.md` §9–10 as P3/P4.

| Standard | Skill | Why deferred | Future approach |
|---|---|---|---|
| `2.NBT.B.9` | Explain why add/subtract strategies work | open-ended reasoning | multiple-choice "best reason" |
| `2.MD.A.1` | Choose & use a measuring tool | needs a physical tool | MC tool-choice / parent task |
| `2.MD.A.2` | Measure with two different units | hands-on | MC concept + parent task |
| `2.MD.A.3` | Estimate lengths | no single right answer | MC "most reasonable estimate" |
| `4.MD.C.6` | Measure/sketch angles with a protractor | reading/drawing a protractor | rendered-angle image + typed degrees |
| `4.G.A.1` | Identify/draw lines & angles in figures | classify from a drawn figure | tagged shape-image library + MC |
| `4.G.A.2` | Classify 2-D figures | classify from a drawn figure | tagged shape-image library + MC |

### Partial coverage within implemented skills
Several standards have a **"draw / construct / physically measure" half** that we don't grade —
we assess the typed/answer half instead:
- Drawing a shape (2.G.A.1), partitioning by hand (2.G.A.3, 3.G.A.2), constructing a graph or
  line plot (2.MD.D.9/D.10, 3.MD.B.3/B.4), placing a point on a number line by hand
  (3.NF.A.2), measuring real objects (2.MD.A.4 hands-on, 3.MD.B.4), counting lines of symmetry
  by drawing them (4.G.A.3). The app asks the *readable/typed* version; freehand production is
  Phase 3 (interactive widgets) or a parent task.

### Engine / product features not built yet
- **Phase-3 fallbacks**: multiple-choice answer type + UI, parent-scored "real-world" task queue.
- **Within-session adaptivity**: a problem's difficulty level is fixed when the session plan is
  built (captured per item). Mid-session level bumps (described in `DESIGN.md` §7.3) are not yet
  implemented — level changes take effect on the *next* session. Cross-session adaptivity works.
- **Placement probe** (`DESIGN.md` §7.4) and **re-opening a lesson from the dashboard**: not built.
- **Other grades**: only Grades 2–4 math. Grade 1 / Grade 5+ are not authored (engine supports them).
- **Subjects beyond math** (literacy, etc.): not started — Phase 4.
- **Web deployment**: app is local-only (`uv run mathkids`), by design for now. No auth/hosting.
- **Cosmetic polish**: a few generated prompts have minor grammar slips (e.g. "5 of those parts
  *is* shaded", "*a* isosceles triangle"). Harmless; not yet swept.

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
