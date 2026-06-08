"""
One-time ETL: load Spotify Charts CSV into SQLite.

Usage:
    python pipeline/etl_spotify_csv.py --csv path/to/charts.csv

The CSV is the Kaggle dataset "dhruvildave/spotify-charts":
  Columns: title, rank, date, artist, url, region, chart, trend, streams
Download via:
    kaggle datasets download -d dhruvildave/spotify-charts
"""
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from db import get_conn, init_db

CHUNK_SIZE = 50_000


def normalize_artist(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip()


def load_csv(csv_path: Path) -> int:
    init_db()
    total_rows = 0

    with get_conn() as conn:
        # Check already-loaded dates to allow re-run idempotently
        existing = set(pd.read_sql("SELECT DISTINCT date FROM spotify_charts", conn)["date"])

    for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, low_memory=False):
        chunk = chunk.rename(columns={"title": "track_name"})

        # Keep only needed columns, fill missing
        needed = ["date", "region", "chart", "rank", "track_name", "artist", "streams"]
        for col in needed:
            if col not in chunk.columns:
                chunk[col] = None

        chunk = chunk[needed].copy()
        chunk["artist"] = chunk["artist"].apply(normalize_artist)
        chunk["streams"] = pd.to_numeric(chunk["streams"], errors="coerce").astype("Int64")
        chunk["rank"] = pd.to_numeric(chunk["rank"], errors="coerce").astype("Int64")

        # Skip dates already in DB
        new_rows = chunk[~chunk["date"].isin(existing)]
        if new_rows.empty:
            continue

        with get_conn() as conn:
            new_rows.to_sql("spotify_charts", conn, if_exists="append", index=False,
                            method="multi", chunksize=1000)
            existing |= set(new_rows["date"].unique())
            total_rows += len(new_rows)
            print(f"  Loaded {total_rows:,} rows so far...", end="\r")

    # Log the run
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pipeline_log (run_time, script, rows_added, status) VALUES (?,?,?,?)",
            (datetime.utcnow().isoformat(), "etl_spotify_csv", total_rows, "success")
        )

    print(f"\nDone. Total rows inserted: {total_rows:,}")
    return total_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to Spotify Charts CSV file")
    args = parser.parse_args()
    load_csv(Path(args.csv))
