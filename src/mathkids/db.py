"""SQLite storage: schema + small explicit query helpers (no ORM).

Dates are stored two ways: human ISO strings (`*_at`) for display, and integer day
ordinals (`due_at`, `day`) for cheap comparison in the scheduler. Callers pass the
current day/timestamp in, which keeps the logic testable.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

DEFAULT_DB = "mathkids.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kid (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT UNIQUE NOT NULL,
    grade      INTEGER NOT NULL,
    emoji      TEXT NOT NULL DEFAULT '🙂',
    daily_goal INTEGER NOT NULL DEFAULT 12
);

CREATE TABLE IF NOT EXISTS skill_state (
    kid_id        INTEGER NOT NULL,
    skill_id      TEXT NOT NULL,
    score         REAL NOT NULL DEFAULT 0,
    level         INTEGER NOT NULL DEFAULT 1,
    box           INTEGER NOT NULL DEFAULT 1,
    consec_correct INTEGER NOT NULL DEFAULT 0,
    recent        TEXT NOT NULL DEFAULT '',
    attempts      INTEGER NOT NULL DEFAULT 0,
    correct       INTEGER NOT NULL DEFAULT 0,
    due_at        INTEGER NOT NULL DEFAULT 0,
    lesson_seen   INTEGER NOT NULL DEFAULT 0,
    introduced_at TEXT,
    mastered_at   TEXT,
    last_seen_at  TEXT,
    PRIMARY KEY (kid_id, skill_id)
);

CREATE TABLE IF NOT EXISTS attempt (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kid_id      INTEGER NOT NULL,
    skill_id    TEXT NOT NULL,
    session_id  INTEGER,
    level       INTEGER NOT NULL,
    prompt      TEXT NOT NULL,
    expected    TEXT NOT NULL,
    given       TEXT NOT NULL,
    correct     INTEGER NOT NULL,
    response_ms INTEGER NOT NULL DEFAULT 0,
    day         INTEGER NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kid_id      INTEGER NOT NULL,
    plan        TEXT NOT NULL DEFAULT '[]',
    answered    INTEGER NOT NULL DEFAULT 0,
    num_correct INTEGER NOT NULL DEFAULT 0,
    day         INTEGER NOT NULL,
    started_at  TEXT NOT NULL,
    ended_at    TEXT
);
"""


def db_path() -> str:
    return os.environ.get("MATHKIDS_DB", DEFAULT_DB)


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def backup_db(conn: sqlite3.Connection) -> str | None:
    """Copy the live DB to backups/<name>-YYYY-MM-DD.db beside it, at most once
    per day. Cheap insurance: all of the kids' history lives in one local file."""
    src = Path(db_path()).resolve()
    out_dir = src.parent / "backups"
    dest = out_dir / f"{src.stem}-{date.today().isoformat()}.db"
    if dest.exists():
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    target = sqlite3.connect(dest)
    try:
        with target:
            conn.backup(target)
    finally:
        target.close()
    return str(dest)


def today_ordinal() -> int:
    return date.today().toordinal()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --- kids -----------------------------------------------------------------

def create_kid(conn, name: str, grade: int, emoji: str, daily_goal: int = 12) -> int:
    cur = conn.execute(
        "INSERT INTO kid (name, grade, emoji, daily_goal) VALUES (?, ?, ?, ?)",
        (name, grade, emoji, daily_goal),
    )
    conn.commit()
    return cur.lastrowid


def get_kids(conn) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM kid ORDER BY id").fetchall()


def get_kid(conn, kid_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM kid WHERE id = ?", (kid_id,)).fetchone()


# --- skill state ----------------------------------------------------------

def get_skill_states(conn, kid_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute("SELECT * FROM skill_state WHERE kid_id = ?", (kid_id,)).fetchall()
    return {r["skill_id"]: r for r in rows}


def get_skill_state(conn, kid_id: int, skill_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM skill_state WHERE kid_id = ? AND skill_id = ?",
        (kid_id, skill_id),
    ).fetchone()


def introduce_skill(conn, kid_id: int, skill_id: str, today: int, now: str) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO skill_state
           (kid_id, skill_id, due_at, introduced_at) VALUES (?, ?, ?, ?)""",
        (kid_id, skill_id, today, now),
    )
    conn.commit()


def save_skill_state(conn, kid_id: int, skill_id: str, **fields) -> None:
    cols = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [kid_id, skill_id]
    conn.execute(
        f"UPDATE skill_state SET {cols} WHERE kid_id = ? AND skill_id = ?", params
    )
    conn.commit()


# --- attempts -------------------------------------------------------------

def record_attempt(
    conn,
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
    conn.execute(
        """INSERT INTO attempt
           (kid_id, skill_id, session_id, level, prompt, expected, given, correct,
            response_ms, day, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (kid_id, skill_id, session_id, level, prompt, expected, given, int(correct),
         response_ms, today, now),
    )
    conn.commit()


def recent_correctness(conn, kid_id: int, skill_id: str, limit: int = 10) -> list[int]:
    rows = conn.execute(
        "SELECT correct FROM attempt WHERE kid_id = ? AND skill_id = ? "
        "ORDER BY id DESC LIMIT ?",
        (kid_id, skill_id, limit),
    ).fetchall()
    return [r["correct"] for r in reversed(rows)]


def total_attempts(conn, kid_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM attempt WHERE kid_id = ?", (kid_id,)
    ).fetchone()
    return row["n"]


def week_stats(conn, kid_id: int, today: int) -> dict:
    since = today - 6
    row = conn.execute(
        """SELECT COUNT(*) AS problems,
                  COALESCE(SUM(correct), 0) AS correct,
                  COUNT(DISTINCT day) AS days
           FROM attempt WHERE kid_id = ? AND day >= ?""",
        (kid_id, since),
    ).fetchone()
    return {"problems": row["problems"], "correct": row["correct"], "days": row["days"]}


# --- sessions -------------------------------------------------------------

def create_session(conn, kid_id: int, plan_json: str, today: int, now: str) -> int:
    cur = conn.execute(
        "INSERT INTO session (kid_id, plan, day, started_at) VALUES (?, ?, ?, ?)",
        (kid_id, plan_json, today, now),
    )
    conn.commit()
    return cur.lastrowid


def update_session_plan(conn, session_id: int, plan_json: str) -> None:
    conn.execute("UPDATE session SET plan = ? WHERE id = ?", (plan_json, session_id))
    conn.commit()


def get_active_session(conn, kid_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM session WHERE kid_id = ? AND ended_at IS NULL "
        "ORDER BY id DESC LIMIT 1",
        (kid_id,),
    ).fetchone()


def get_latest_session(conn, kid_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM session WHERE kid_id = ? ORDER BY id DESC LIMIT 1", (kid_id,)
    ).fetchone()


def advance_session(conn, session_id: int, answered: int, num_correct: int) -> None:
    conn.execute(
        "UPDATE session SET answered = ?, num_correct = ? WHERE id = ?",
        (answered, num_correct, session_id),
    )
    conn.commit()


def end_session(conn, session_id: int, now: str) -> None:
    conn.execute("UPDATE session SET ended_at = ? WHERE id = ?", (now, session_id))
    conn.commit()
