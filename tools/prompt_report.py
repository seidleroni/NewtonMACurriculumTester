"""Which question wordings trip the kids up? A report over a database snapshot.

Usage:
    uv run python -m tools.prompt_report backups/d1-snapshot-20261023.db

Every stored question (whole problems and teaching steps) is reduced to a template by
replacing numbers with #. Templates seen at least MIN_SEEN times on at least two days
are listed with their error rate and median answer time; unusually error-prone or
slow ones are flagged (see WRONG_FLOOR and SLOW). A flagged wording is a
candidate for rewording ("Put # with the tens" was 40% wrong at 25 s).
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from statistics import median

MIN_SEEN = 5
WRONG_FLOOR = 0.15  # flag a wording missed at least this often (and at least twice)...
SLOW = 2.5          # ...or answered this many times slower than the median wording
NUMBER = re.compile(r"\d[\d,]*")


def template(prompt: str) -> str:
    return NUMBER.sub("#", prompt).strip()


def report(path: str) -> list[dict]:
    con = sqlite3.connect(path)
    rows = con.execute(
        """SELECT prompt, correct, response_ms, day FROM attempt
           WHERE TRIM(COALESCE(given,'')) <> ''
           UNION ALL
           SELECT prompt, correct, response_ms, day FROM step_response
           WHERE TRIM(raw_input) <> ''""").fetchall()
    con.close()
    groups: dict[str, list] = {}
    for prompt, correct, ms, day in rows:
        groups.setdefault(template(prompt), []).append((correct, ms, day))
    stats = [dict(template=t, seen=len(v), misses=sum(1 for c, _, _ in v if not c),
                  wrong=sum(1 for c, _, _ in v if not c) / len(v),
                  ms=median(ms for _, ms, _ in v))
             for t, v in groups.items()
             if len(v) >= MIN_SEEN and len({d for _, _, d in v}) >= 2]
    if not stats:
        return []
    # Most wordings are answered perfectly, so the bar has a floor.
    bar = max(2 * median(s["wrong"] for s in stats), WRONG_FLOOR)
    base_ms = median(s["ms"] for s in stats)
    for s in stats:
        s["flag"] = (s["wrong"] >= bar and s["misses"] >= 2) or s["ms"] >= SLOW * base_ms
    return sorted(stats, key=lambda s: (-s["flag"], -s["wrong"], -s["ms"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("snapshot")
    args = parser.parse_args()
    for s in report(args.snapshot):
        print(f"{'FLAG' if s['flag'] else '    '} {s['wrong']:4.0%} wrong  "
              f"{s['ms'] / 1000:5.1f} s  n={s['seen']:3}  {s['template'][:90]}")


if __name__ == "__main__":
    main()
