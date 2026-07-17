"""Storage layer: async query helpers over two interchangeable backends.

- ``SqliteDB``  — local sqlite3 file (dev server, seed script, pytest).
- ``D1DB``      — Cloudflare D1 binding (the deployed Worker); same SQL dialect,
                  reached through the async JS bridge (``env.DB``).

Every helper takes an adapter as its first argument and is async so route code
is identical on both backends. Rows are plain dicts either way.

The schema lives in ``migrations/0001_init.sql`` (applied to D1 with
``wrangler d1 migrations apply``); ``init_db`` executes the same file for the
sqlite backend so the two can never drift.

Dates are stored two ways: human ISO strings (`*_at`) for display, and integer
day ordinals (`due_at`, `day`) for cheap comparison in the scheduler. "Today"
is computed in the family's timezone (America/New_York) — the Worker runs in
UTC, and a UTC "today" would flip the Leitner due-dates at 8pm Eastern.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_DB = "mathkids.db"
TZ = ZoneInfo("America/New_York")

_SCHEMA_FILE = Path(__file__).resolve().parents[2] / "migrations" / "0001_init.sql"


def db_path() -> str:
    return os.environ.get("MATHKIDS_DB", DEFAULT_DB)


def today_ordinal() -> int:
    return datetime.now(TZ).date().toordinal()


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


# --- backends ---------------------------------------------------------------

class SqliteDB:
    """Local sqlite3 file behind the async interface."""

    def __init__(self, path: str | None = None):
        self._conn = sqlite3.connect(path or db_path(), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    async def all(self, sql: str, *params) -> list[dict]:
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    async def first(self, sql: str, *params) -> dict | None:
        row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None

    async def run(self, sql: str, *params) -> int | None:
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur.lastrowid

    def close(self) -> None:
        self._conn.close()


class D1DB:
    """Cloudflare D1 binding (env.DB) behind the same interface."""

    def __init__(self, binding):
        self._db = binding

    async def all(self, sql: str, *params) -> list[dict]:
        res = await self._db.prepare(sql).bind(*params).all()
        return [_to_dict(r) for r in res.results]

    async def first(self, sql: str, *params) -> dict | None:
        row = await self._db.prepare(sql).bind(*params).first()
        return _to_dict(row) if row is not None else None

    async def run(self, sql: str, *params) -> int | None:
        res = await self._db.prepare(sql).bind(*params).run()
        meta = res.meta
        last_id = getattr(meta, "last_row_id", None)
        return int(last_id) if last_id is not None else None

    def close(self) -> None:  # the binding is owned by the runtime
        pass


def _to_dict(row) -> dict:
    d = row.to_py() if hasattr(row, "to_py") else dict(row)
    # D1 values cross the JS bridge as doubles; the scheduler and seed
    # arithmetic (level, day, session ids) must see real ints.
    return {
        k: (int(v) if isinstance(v, float) and v.is_integer() else v)
        for k, v in d.items()
    }


async def init_db(dbx: SqliteDB) -> None:
    """Create tables on the sqlite backend (D1 uses wrangler migrations)."""
    dbx._conn.executescript(_SCHEMA_FILE.read_text(encoding="utf-8"))
    dbx._conn.commit()


# --- kids -----------------------------------------------------------------

async def create_kid(dbx, name: str, grade: int, emoji: str, daily_goal: int = 12) -> int:
    return await dbx.run(
        "INSERT INTO kid (name, grade, emoji, daily_goal) VALUES (?, ?, ?, ?)",
        name, grade, emoji, daily_goal,
    )


async def get_kids(dbx) -> list[dict]:
    return await dbx.all("SELECT * FROM kid ORDER BY id")


async def get_kid(dbx, kid_id: int) -> dict | None:
    return await dbx.first("SELECT * FROM kid WHERE id = ?", kid_id)


# --- skill state ----------------------------------------------------------

async def get_skill_states(dbx, kid_id: int) -> dict[str, dict]:
    rows = await dbx.all("SELECT * FROM skill_state WHERE kid_id = ?", kid_id)
    return {r["skill_id"]: r for r in rows}


async def get_skill_state(dbx, kid_id: int, skill_id: str) -> dict | None:
    return await dbx.first(
        "SELECT * FROM skill_state WHERE kid_id = ? AND skill_id = ?",
        kid_id, skill_id,
    )


async def introduce_skill(dbx, kid_id: int, skill_id: str, today: int, now: str) -> None:
    await dbx.run(
        """INSERT OR IGNORE INTO skill_state
           (kid_id, skill_id, due_at, introduced_at) VALUES (?, ?, ?, ?)""",
        kid_id, skill_id, today, now,
    )


async def save_skill_state(dbx, kid_id: int, skill_id: str, **fields) -> None:
    cols = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [kid_id, skill_id]
    await dbx.run(
        f"UPDATE skill_state SET {cols} WHERE kid_id = ? AND skill_id = ?", *params
    )


# --- attempts -------------------------------------------------------------

async def record_attempt(
    dbx,
    kid_id: int,
    skill_id: str,
    session_id: int,
    level: int,
    prompt: str,
    expected: str,
    given: str,
    correct: bool,
    response_ms: int,
    today: int,
    now: str,
) -> None:
    await dbx.run(
        """INSERT INTO attempt
           (kid_id, skill_id, session_id, level, prompt, expected, given, correct,
            response_ms, day, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        kid_id, skill_id, session_id, level, prompt, expected, given, int(correct),
        response_ms, today, now,
    )


async def recent_correctness(dbx, kid_id: int, skill_id: str, limit: int = 10) -> list[int]:
    rows = await dbx.all(
        "SELECT correct FROM attempt WHERE kid_id = ? AND skill_id = ? "
        "ORDER BY id DESC LIMIT ?",
        kid_id, skill_id, limit,
    )
    return [r["correct"] for r in reversed(rows)]


async def total_attempts(dbx, kid_id: int) -> int:
    row = await dbx.first(
        "SELECT COUNT(*) AS n FROM attempt WHERE kid_id = ?", kid_id
    )
    return row["n"]


async def week_stats(dbx, kid_id: int, today: int) -> dict:
    since = today - 6
    row = await dbx.first(
        """SELECT COUNT(*) AS problems,
                  COALESCE(SUM(correct), 0) AS correct,
                  COUNT(DISTINCT day) AS days
           FROM attempt WHERE kid_id = ? AND day >= ?""",
        kid_id, since,
    )
    return {"problems": row["problems"], "correct": row["correct"], "days": row["days"]}


# --- sessions -------------------------------------------------------------

async def create_session(dbx, kid_id: int, plan_json: str, today: int, now: str) -> int:
    return await dbx.run(
        "INSERT INTO session (kid_id, plan, day, started_at) VALUES (?, ?, ?, ?)",
        kid_id, plan_json, today, now,
    )


async def update_session_plan(dbx, session_id: int, plan_json: str) -> None:
    await dbx.run("UPDATE session SET plan = ? WHERE id = ?", plan_json, session_id)


async def get_active_session(dbx, kid_id: int) -> dict | None:
    return await dbx.first(
        "SELECT * FROM session WHERE kid_id = ? AND ended_at IS NULL "
        "ORDER BY id DESC LIMIT 1",
        kid_id,
    )


async def get_latest_session(dbx, kid_id: int) -> dict | None:
    return await dbx.first(
        "SELECT * FROM session WHERE kid_id = ? ORDER BY id DESC LIMIT 1", kid_id
    )


async def advance_session(dbx, session_id: int, answered: int, num_correct: int) -> None:
    await dbx.run(
        "UPDATE session SET answered = ?, num_correct = ? WHERE id = ?",
        answered, num_correct, session_id,
    )


async def end_session(dbx, session_id: int, now: str) -> None:
    await dbx.run("UPDATE session SET ended_at = ? WHERE id = ?", now, session_id)
