-- Schema source of truth (mirrored by db.init_db for the local sqlite backend).
-- Applied to D1 via: npx wrangler d1 migrations apply mathkids [--local|--remote]

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
