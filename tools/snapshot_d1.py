"""Copy the production D1 database into a local SQLite file, read-only on the remote.

Usage:
    uv run python tools/snapshot_d1.py                  # -> backups/d1-snapshot-<date>.db
    uv run python tools/snapshot_d1.py --out some.db

The copy has the real schema (it is built by applying migrations/*.sql, exactly like a
local dev database), so the app, tests and tools/simulate_teaching.py can run on it.
Never upload it back: remote D1 stays the system of record.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

from mathkids import db

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["kid", "skill_state", "session", "attempt", "learning_state", "learning_session",
          "practice_activity", "step_response"]


def fetch(table: str) -> list[dict]:
    npx = shutil.which("npx") or "npx"
    out = subprocess.run(
        [npx, "wrangler", "d1", "execute", "mathkids", "--remote", "--json",
         "--command", f"SELECT * FROM {table}"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, check=True,
    )
    return json.loads(out.stdout)[0]["results"]


def write(path: Path, data: dict[str, list[dict]]) -> None:
    if path.exists():
        path.unlink()
    dbx = db.SqliteDB(str(path))
    asyncio.run(db.init_db(dbx))
    with dbx._conn:
        for table in TABLES:
            for row in data[table]:
                cols = list(row)
                dbx._conn.execute(
                    f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [row[c] for c in cols],
                )
    dbx.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path,
                        default=ROOT / "backups" / f"d1-snapshot-{date.today():%Y%m%d}.db")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = {t: fetch(t) for t in TABLES}
    write(args.out, data)
    print(args.out, {t: len(rows) for t, rows in data.items()})


if __name__ == "__main__":
    main()
