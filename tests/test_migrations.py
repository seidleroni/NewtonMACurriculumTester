import asyncio
from pathlib import Path

from mathkids import db


def test_upgrade_preserves_history_and_only_retires_superseded_sessions(tmp_path):
    d = db.SqliteDB(str(tmp_path / "old.db"))
    schema = Path(__file__).resolve().parents[1] / "migrations" / "0001_init.sql"
    d._conn.executescript(schema.read_text(encoding="utf-8"))
    d._conn.executescript("""
        INSERT INTO kid VALUES (1,'Example',2,'X',12);
        INSERT INTO skill_state (kid_id,skill_id,score,attempts,correct,mastered_at)
        VALUES (1,'2.NBT.B.7',0.97,20,19,'2026-06-01');
        INSERT INTO session (kid_id,day,plan,answered,num_correct,started_at)
        VALUES (1,123,'[]',1,1,'2026-06-01');
        INSERT INTO session (kid_id,day,plan,started_at) VALUES (1,124,'[]','2026-06-02');
        INSERT INTO attempt (kid_id,skill_id,session_id,level,prompt,expected,given,correct,day,created_at)
        VALUES (1,'2.NBT.B.7',1,2,'1 + 2','3','3',1,123,'2026-06-01');
    """)
    old_attempts = d._conn.execute("SELECT * FROM attempt").fetchall()
    old_states = d._conn.execute("SELECT * FROM skill_state").fetchall()
    asyncio.run(db.init_db(d))
    assert d._conn.execute("SELECT * FROM attempt").fetchall() == old_attempts
    assert d._conn.execute("SELECT * FROM skill_state").fetchall() == old_states
    assert d._conn.execute("SELECT COUNT(*) FROM learning_state").fetchone()[0] == 0
    assert d._conn.execute("SELECT id FROM session WHERE ended_at IS NULL").fetchone()[0] == 2
    first = list(d._conn.iterdump())
    asyncio.run(db.init_db(d))
    assert list(d._conn.iterdump()) == first
    assert d._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    d.close()
