import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS spotify_charts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT NOT NULL,
                region    TEXT NOT NULL,
                chart     TEXT NOT NULL,
                rank      INTEGER NOT NULL,
                track_name TEXT NOT NULL,
                artist    TEXT NOT NULL,
                streams   INTEGER,
                source    TEXT DEFAULT 'spotify'
            );

            CREATE TABLE IF NOT EXISTS billboard_charts (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                fetch_date     TEXT NOT NULL,
                rank           INTEGER NOT NULL,
                title          TEXT NOT NULL,
                artist         TEXT NOT NULL,
                weeks_on_chart INTEGER,
                peak_rank      INTEGER,
                source         TEXT DEFAULT 'billboard'
            );

            CREATE TABLE IF NOT EXISTS pipeline_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time   TEXT NOT NULL,
                script     TEXT NOT NULL,
                rows_added INTEGER DEFAULT 0,
                status     TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_spotify_date   ON spotify_charts(date);
            CREATE INDEX IF NOT EXISTS idx_spotify_artist ON spotify_charts(artist);
            CREATE INDEX IF NOT EXISTS idx_bb_date        ON billboard_charts(fetch_date);
        """)
