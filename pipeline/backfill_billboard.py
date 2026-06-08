"""
Backfill historical Billboard Hot 100 charts so time-series visualizations
have enough data to actually show trends (a single week = no lines).

Walks backwards week by week using billboard.py's previousDate field.
Idempotent: skips dates already in DB.

Usage:
    python pipeline/backfill_billboard.py --weeks 52
"""
import argparse
import sys
import time
from datetime import datetime, timedelta, date

import billboard

from db import get_conn, init_db


def fetch_one(target_date_str: str) -> list:
    """Fetch Hot 100 for a given date. Returns rows or empty list on failure."""
    try:
        chart = billboard.ChartData("hot-100", date=target_date_str)
    except Exception as exc:
        print(f"  ERROR fetching {target_date_str}: {exc}", file=sys.stderr)
        return []

    actual_date = chart.date or target_date_str
    return [
        {
            "fetch_date": actual_date,
            "rank": entry.rank,
            "title": entry.title,
            "artist": entry.artist,
            "weeks_on_chart": entry.weeks,
            "peak_rank": entry.peakPos,
        }
        for entry in chart
    ]


def backfill(weeks: int) -> int:
    init_db()
    total_inserted = 0

    # Billboard charts are published weekly on Saturdays.
    # Walk back from this week's Saturday in 7-day increments.
    today = date.today()
    days_since_saturday = (today.weekday() - 5) % 7  # weekday(): Mon=0 ... Sat=5
    latest_saturday = today - timedelta(days=days_since_saturday)

    for i in range(weeks):
        target = latest_saturday - timedelta(weeks=i)
        target_str = target.isoformat()

        with get_conn() as conn:
            existing = conn.execute(
                "SELECT COUNT(*) FROM billboard_charts WHERE fetch_date = ?",
                (target_str,),
            ).fetchone()[0]

        if existing > 0:
            print(f"[{i+1:>3}/{weeks}] {target_str}: already in DB, skipping")
            continue

        rows = fetch_one(target_str)
        if not rows:
            print(f"[{i+1:>3}/{weeks}] {target_str}: empty response, skipping")
            time.sleep(0.5)
            continue

        with get_conn() as conn:
            conn.executemany(
                """INSERT INTO billboard_charts
                   (fetch_date, rank, title, artist, weeks_on_chart, peak_rank)
                   VALUES (:fetch_date, :rank, :title, :artist, :weeks_on_chart, :peak_rank)""",
                rows,
            )
        total_inserted += len(rows)
        actual_dt = rows[0]["fetch_date"]
        print(f"[{i+1:>3}/{weeks}] requested {target_str} → got {actual_dt}: inserted {len(rows)} rows")

        time.sleep(0.4)  # be polite to Billboard's servers

    # Log
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pipeline_log (run_time, script, rows_added, status) VALUES (?,?,?,?)",
            (datetime.utcnow().isoformat(), "backfill_billboard", total_inserted, "success"),
        )

    print(f"\nBackfill complete. Total rows inserted: {total_inserted:,}")
    return total_inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=52, help="How many weeks back to fetch")
    args = parser.parse_args()
    backfill(args.weeks)
