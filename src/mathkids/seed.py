"""Create the database and the two kid profiles (idempotent)."""

from __future__ import annotations

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


def main() -> None:
    conn = db.connect()
    db.init_db(conn)
    today, now = db.today_ordinal(), db.now_iso()
    existing = {k["name"] for k in db.get_kids(conn)}
    for name, grade, emoji, goal in KIDS:
        if name not in existing:
            kid_id = db.create_kid(conn, name, grade, emoji, goal)
            for skill_id in SEQUENCES.get(grade, [])[:INITIAL_SKILLS]:
                db.introduce_skill(conn, kid_id, skill_id, today, now)
    names = [k["name"] for k in db.get_kids(conn)]
    conn.close()
    print(f"Seeded {db.db_path()} — kids: {', '.join(names)}")


if __name__ == "__main__":
    main()
