"""Create the database and the two kid profiles (idempotent)."""

from __future__ import annotations

import asyncio

from mathkids import db
from mathkids.engine import SEQUENCES

KIDS = [
    # name, grade, emoji, daily_goal
    ("Jacob", 2, "🦖", 12),
    ("Samuel", 4, "🚀", 12),
]

# How many skills a brand-new kid starts with (so every kid begins populated and
# symmetric — the rest unlock as they progress). Matches the app's lazy-intro logic.
INITIAL_SKILLS = 2


async def seed(dbx) -> list[str]:
    """Insert any missing kids (works on either backend); returns kid names."""
    today, now = db.today_ordinal(), db.now_iso()
    existing = {k["name"] for k in await db.get_kids(dbx)}
    for name, grade, emoji, goal in KIDS:
        if name not in existing:
            kid_id = await db.create_kid(dbx, name, grade, emoji, goal)
            for skill_id in SEQUENCES.get(grade, [])[:INITIAL_SKILLS]:
                await db.introduce_skill(dbx, kid_id, skill_id, today, now)
    return [k["name"] for k in await db.get_kids(dbx)]


async def _main() -> None:
    dbx = db.SqliteDB()
    await db.init_db(dbx)
    names = await seed(dbx)
    dbx.close()
    print(f"Seeded {db.db_path()} — kids: {', '.join(names)}")


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
