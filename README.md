# Newton Math — daily practice for Jacob & Samuel

A local-first daily math practice web app, grounded in the Newton, MA elementary curriculum
(Investigations 3 → 2017 Massachusetts Math Framework). See [`DESIGN.md`](DESIGN.md) for the
full specification.

This is **Phase 0** — the runnable first slice: the skill engine, mastery + spaced-repetition
logic, the full daily loop, both dashboards, and three skills per kid:

- **Jacob (Grade 2):** add/subtract facts within 20, three-digit place value, add/subtract within 100.
- **Samuel (Grade 4):** ×/÷ facts to 12×12, multi-digit multiplication, add/subtract fractions.

Everything runs offline with no AI at runtime. Problems are generated and graded by pure,
deterministic Python; lessons and hints are authored ahead of time.

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
  engine/      # Skill base + per-grade skill modules (generate / lesson / hints / worked_example)
  answers.py   # typed answers: normalization + deterministic grading
  mastery.py   # 0..1 proficiency score, level-ups, "mastered" — ceiling-by-difficulty
  scheduler.py # Leitner spacing + daily session composition
  db.py        # SQLite schema + helpers
  app.py       # FastAPI routes + server-rendered HTML (forms; keyboard-first)
  templates/   # Jinja2
  static/      # CSS + ~40 lines of JS (autofocus + Enter-to-continue)
tests/         # property + unit + endpoint tests
```

> UI note: Phase 0 uses classic server-rendered form posts (sturdy, zero-dependency, fully
> testable without a browser) plus a tiny progressive-enhancement script. HTMX-style partial
> swaps can be layered on later without changing the endpoints.
