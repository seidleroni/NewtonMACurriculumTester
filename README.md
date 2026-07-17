# Newton Math — daily practice for Jacob & Samuel

A daily math practice web app, grounded in the Newton, MA elementary curriculum
(Investigations 3 → 2017 Massachusetts Math Framework). See [`DESIGN.md`](DESIGN.md) for the
full specification. Runs two ways from the same code: locally (uvicorn + sqlite) and on
**Cloudflare Workers + D1** behind Cloudflare Access (see *Deploy to Cloudflare* below).

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
src/worker.py    # Cloudflare Workers entry point (bridges workerd -> the FastAPI app)
src/mathkids/
  engine/        # Skill base + registry + SEQUENCES; per-grade packages:
    grade2/      #   oa.py nbt.py md.py geometry.py
    grade3/      #   oa.py nbt.py nf.py md.py geometry.py
    grade4/      #   oa.py nbt.py nf.py md.py geometry.py
  answers.py     # typed answers: normalization + deterministic grading
  mastery.py     # 0..1 proficiency score, level-ups, "mastered" — ceiling-by-difficulty
  scheduler.py   # Leitner spacing + daily session composition
  db.py          # async query helpers over two backends: local sqlite / Cloudflare D1
  app.py         # FastAPI routes + server-rendered HTML (forms; keyboard-first)
  templates/     # Jinja2 (baked into a generated module for the Workers bundle)
public/static/   # CSS + JS, incl. images.js (SVG figures: clocks, number lines, ...)
migrations/      # D1 schema (also the sqlite schema source of truth)
tools/           # embed_templates.py (build hook) + export_d1.py (data migration)
tests/           # property + unit + endpoint tests
```

> UI note: Phase 0 uses classic server-rendered form posts (sturdy, zero-dependency, fully
> testable without a browser) plus a tiny progressive-enhancement script. HTMX-style partial
> swaps can be layered on later without changing the endpoints.
>
> Problem figures are drawn client-side by `public/static/images.js` from a JSON spec the
> generator puts in `payload["image"]` — same geometry the old Pillow renderer produced.

## Deploy to Cloudflare (free tier)

The deployed app is the same FastAPI code running as a **Python Worker** with **D1** (serverless
SQLite) for storage and **Cloudflare Access** as the family login. One-time setup:

```bash
# 1. Log in (opens a browser; free Cloudflare account is fine)
npx wrangler login

# 2. Create the D1 database, then paste the printed database_id into wrangler.jsonc
npx wrangler d1 create mathkids

# 3. Create the schema in the real (remote) database
npx wrangler d1 migrations apply mathkids --remote

# 4. Copy the kids' local history into D1 (re-run both steps any time before cutover)
uv run python tools/export_d1.py
npx wrangler d1 execute mathkids --remote --file tools/d1_seed.sql

# 5. Ship it
uv run pywrangler deploy        # -> https://mathkids.<your-subdomain>.workers.dev
```

Then lock it down (Cloudflare dashboard, one time):

1. **Workers & Pages → mathkids → Settings → Domains & Routes** → on the `workers.dev` route,
   enable **Cloudflare Access**. (If the toggle isn't offered, attach a custom domain and create
   a self-hosted Access application for it in Zero Trust instead.)
2. **Zero Trust → Access → Applications** → the auto-created app → add one **Allow** policy:
   *Include → Emails* → the family's email addresses (free for up to 50 users).
3. Authentication: **One-time PIN** (emailed code, no identity provider needed).
   Set the session duration to the maximum (1 month) so the kids rarely re-login.

Day-to-day:

```bash
uv run pywrangler dev           # local Workers runtime + local D1 at http://localhost:8787
uv run pywrangler deploy        # redeploy after changes
```

Notes:
- "Today" for scheduling is computed in **America/New_York** regardless of where the Worker
  runs, so Leitner due-dates roll over at midnight Eastern.
- Backups: D1 keeps ~30 days of point-in-time history (Time Travel). For a belt-and-braces
  copy, occasionally run:
  `npx wrangler d1 export mathkids --remote --output backups/mathkids-remote.sql`
- The old local mode still works (`uv run mathkids` against `mathkids.db`) and is the dev loop;
  after cutover, D1 is the system of record — don't practice in both.
