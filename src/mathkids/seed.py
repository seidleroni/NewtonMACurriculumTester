"""Create the database and the two kid profiles (idempotent)."""

from __future__ import annotations

from mathkids import db

KIDS = [
    # name, grade, emoji, daily_goal
    ("Jacob", 2, "🦖", 12),
    ("Samuel", 4, "🚀", 12),
]


def main() -> None:
    conn = db.connect()
    db.init_db(conn)
    existing = {k["name"] for k in db.get_kids(conn)}
    for name, grade, emoji, goal in KIDS:
        if name not in existing:
            db.create_kid(conn, name, grade, emoji, goal)
    names = [k["name"] for k in db.get_kids(conn)]
    conn.close()
    print(f"Seeded {db.db_path()} — kids: {', '.join(names)}")


if __name__ == "__main__":
    main()
