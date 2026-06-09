# Newton Math — daily practice for Jacob & Samuel

A local-first daily math practice web app, grounded in the Newton, MA elementary curriculum
(Investigations 3 → 2017 Massachusetts Math Framework). See [`DESIGN.md`](DESIGN.md) for the
full specification.

**Phases 0–3 are done** (see [`STATUS.md`](STATUS.md) for the full done / not-done breakdown):
the skill engine, mastery + spaced-repetition scheduler (with a placement probe and
within-session adaptivity), the full daily loop, kid and parent dashboards, and the **complete
80-skill Grade 2–4 catalog** — including image-based skills (clocks, number lines, arrays,
grids, bar graphs, fraction bars, marked shapes, a protractor) and multiple-choice reframes of
the open-reasoning standards. Jacob starts on Grade 2, Samuel on Grade 4; Grade 3 is included
as a cross-grade safety net.

Everything runs offline with no AI at runtime. Problems are generated and graded by pure,
deterministic Python; lessons and hints are authored ahead of time. Every skill is verified by a
property test, and the math was independently re-solved by an adversarial audit.

## Quick start

```bash
uv sync                 # create the venv and install deps
uv run mathkids-seed    # create mathkids.db and the two kid profiles
uv run mathkids         # serve at http://127.0.0.1:8000
```

Open http://127.0.0.1:8000, pick a face, and start the day's set.

## Develop & test

```bash
uv run pytest           # full test suite (generators verified with property-based tests)
uv run ruff check       # lint
```

## How it's organized

```
src/mathkids/
  engine/        # Skill base + registry + SEQUENCES; per-grade packages:
    grade2/      #   oa.py nbt.py md.py geometry.py
    grade3/      #   oa.py nbt.py nf.py md.py geometry.py
    grade4/      #   oa.py nbt.py nf.py md.py geometry.py
  answers.py     # typed answers: normalization + deterministic grading
  assets.py      # deterministic Pillow image rendering (Phase-2 image skills)
  mastery.py     # 0..1 proficiency score, level-ups, "mastered" — ceiling-by-difficulty
  scheduler.py   # Leitner spacing + daily session composition
  db.py          # SQLite schema + helpers
  app.py         # FastAPI routes + server-rendered HTML (forms; keyboard-first)
  templates/     # Jinja2
  static/        # CSS + ~50 lines of JS (autofocus, Enter-to-continue, a-d picks a choice)
tests/           # property + unit + endpoint tests (551 passing)
```

> UI note: Phase 0 uses classic server-rendered form posts (sturdy, zero-dependency, fully
> testable without a browser) plus a tiny progressive-enhancement script. HTMX-style partial
> swaps can be layered on later without changing the endpoints.
