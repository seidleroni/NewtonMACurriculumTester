-- Add teaching evidence without reinterpreting or deleting historical attempts.
CREATE TABLE learning_state (
    kid_id INTEGER NOT NULL,
    component TEXT NOT NULL,
    band INTEGER NOT NULL,
    stage TEXT NOT NULL DEFAULT 'probe',
    streak INTEGER NOT NULL DEFAULT 0,
    evidence TEXT NOT NULL DEFAULT '[]',
    due_at INTEGER NOT NULL DEFAULT 0,
    revision INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (kid_id, component, band)
);

CREATE TABLE learning_session (
    session_id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    budget INTEGER NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    introduced TEXT,
    revision INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE practice_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    slot INTEGER NOT NULL,
    kid_id INTEGER NOT NULL,
    skill_id TEXT NOT NULL,
    component TEXT NOT NULL,
    band INTEGER NOT NULL,
    mode TEXT NOT NULL,
    snapshot TEXT NOT NULL,
    progress TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 0,
    outcome TEXT,
    attempt_id INTEGER,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    UNIQUE (session_id, slot)
);

CREATE TABLE step_response (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    step_key TEXT NOT NULL,
    component TEXT NOT NULL,
    mode TEXT NOT NULL,
    raw_input TEXT NOT NULL,
    prompt TEXT NOT NULL,
    expected TEXT NOT NULL,
    correct INTEGER NOT NULL,
    response_ms INTEGER NOT NULL,
    day INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (activity_id, revision)
);
CREATE INDEX learning_activity_kid ON practice_activity(kid_id, session_id);
CREATE INDEX learning_response_day ON step_response(day, activity_id);
CREATE INDEX attempt_kid_skill ON attempt(kid_id, skill_id, id);

-- Old double-Start requests left multiple open sessions. Retain the newest;
-- retire only superseded sessions, keeping every plan and answer intact.
UPDATE session SET ended_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
WHERE ended_at IS NULL AND id NOT IN (
    SELECT MAX(id) FROM session WHERE ended_at IS NULL GROUP BY kid_id
);
CREATE UNIQUE INDEX one_active_session ON session(kid_id) WHERE ended_at IS NULL;
