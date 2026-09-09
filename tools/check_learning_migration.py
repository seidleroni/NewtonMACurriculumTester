"""Rehearse local migrations on a COPY; never change the supplied source database.

uv run python tools/check_learning_migration.py SOURCE.db backups/migration-check.db
"""
import argparse
import asyncio
import sqlite3
from pathlib import Path

from mathkids import db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_file() or output.exists() or source == output:
        parser.error("Source must exist and output must be a new file.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as original:
        with sqlite3.connect(output) as copy:
            original.backup(copy)
    adapter = db.SqliteDB(str(output))
    try:
        preserved = {table: adapter._conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                     for table in ("kid", "attempt", "skill_state")}
        sessions = adapter._conn.execute("SELECT * FROM session ORDER BY id").fetchall()
        asyncio.run(db.init_db(adapter))
        for table, rows in preserved.items():
            assert adapter._conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall() == rows
            print(f"Preserved {len(rows)} {table} rows, including IDs and values")
        after = adapter._conn.execute("SELECT * FROM session ORDER BY id").fetchall()
        assert len(after) == len(sessions)
        retired = 0
        for old, new in zip(sessions, after):
            assert {k: old[k] for k in old.keys() if k != "ended_at"} == {
                k: new[k] for k in new.keys() if k != "ended_at"
            }
            if old["ended_at"] != new["ended_at"]:
                assert old["ended_at"] is None and new["ended_at"] is not None
                retired += 1
        dump = list(adapter._conn.iterdump())
        asyncio.run(db.init_db(adapter))
        assert list(adapter._conn.iterdump()) == dump
        assert adapter._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        print(f"Retired {retired} superseded open sessions; reapplication is a no-op; integrity OK")
        print(f"Migrated copy: {output}")
    finally:
        adapter.close()


if __name__ == "__main__":
    main()
