"""
Daily refresh: fetch Billboard Hot 100 and append to SQLite.
Idempotent — skips if today's data already exists.

Run manually:   python pipeline/refresh.py
Run via Actions: triggered by daily_refresh.yml
"""
import sys
from datetime import date, datetime

import billboard

from db import get_conn, init_db


def fetch_billboard() -> int:
    today = date.today().isoformat()
    init_db()

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM billboard_charts WHERE fetch_date = ?", (today,)
        ).fetchone()[0]

    if existing > 0:
        print(f"Billboard data for {today} already in DB. Skipping.")
        return 0

    print(f"Fetching Billboard Hot 100 for {today}...")
    try:
        chart = billboard.ChartData("hot-100")
    except Exception as exc:
        print(f"ERROR fetching Billboard: {exc}", file=sys.stderr)
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO pipeline_log (run_time, script, rows_added, status) VALUES (?,?,?,?)",
                (datetime.utcnow().isoformat(), "refresh_billboard", 0, f"error: {exc}")
            )
        return 0

    rows = [
        {
            "fetch_date": today,
            "rank": entry.rank,
            "title": entry.title,
            "artist": entry.artist,
            "weeks_on_chart": entry.weeks,
            "peak_rank": entry.peakPos,
        }
        for entry in chart
    ]

    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO billboard_charts
               (fetch_date, rank, title, artist, weeks_on_chart, peak_rank)
               VALUES (:fetch_date, :rank, :title, :artist, :weeks_on_chart, :peak_rank)""",
            rows,
        )
        conn.execute(
            "INSERT INTO pipeline_log (run_time, script, rows_added, status) VALUES (?,?,?,?)",
            (datetime.utcnow().isoformat(), "refresh_billboard", len(rows), "success")
        )

    print(f"Inserted {len(rows)} entries for {today}.")
    return len(rows)


if __name__ == "__main__":
    fetch_billboard()
