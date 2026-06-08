"""
Create a trimmed deployment DB from the full charts.db.
Keeps all Billboard data; keeps Spotify data for top N regions by stream count.
Output overwrites data/charts.db in-place (original is backed up as charts_full.db).

Run from repo root:
    python pipeline/trim_db.py --regions 10
"""
import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"
BACKUP_PATH = Path(__file__).parent.parent / "data" / "charts_full.db"


def trim(n_regions: int) -> None:
    if not DB_PATH.exists():
        sys.exit(f"ERROR: {DB_PATH} not found")

    print(f"Source DB: {DB_PATH} ({DB_PATH.stat().st_size / 1e6:.1f} MB)")

    with sqlite3.connect(DB_PATH) as src:
        top_regions = [
            row[0]
            for row in src.execute(
                """SELECT region
                   FROM spotify_charts
                   WHERE streams IS NOT NULL
                   GROUP BY region
                   ORDER BY SUM(streams) DESC
                   LIMIT ?""",
                (n_regions,),
            ).fetchall()
        ]

    print(f"Top {n_regions} regions by streams: {top_regions}")

    # Count rows to be kept
    placeholders = ",".join("?" * len(top_regions))
    with sqlite3.connect(DB_PATH) as src:
        spotify_kept = src.execute(
            f"SELECT COUNT(*) FROM spotify_charts WHERE region IN ({placeholders})",
            top_regions,
        ).fetchone()[0]
        billboard_total = src.execute("SELECT COUNT(*) FROM billboard_charts").fetchone()[0]

    print(f"Spotify rows to keep: {spotify_kept:,} | Billboard rows: {billboard_total}")

    # Backup full DB before overwriting
    if not BACKUP_PATH.exists():
        print(f"Backing up full DB → {BACKUP_PATH.name} ...")
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print("Backup done.")
    else:
        print("Backup already exists, skipping.")

    # Build trimmed DB into a temp file then replace
    tmp_path = DB_PATH.with_suffix(".tmp")
    tmp_path.unlink(missing_ok=True)

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(tmp_path)
    try:
        # Copy schema
        dst.executescript("""
            CREATE TABLE IF NOT EXISTS spotify_charts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT NOT NULL,
                region     TEXT NOT NULL,
                chart      TEXT NOT NULL,
                rank       INTEGER NOT NULL,
                track_name TEXT NOT NULL,
                artist     TEXT NOT NULL,
                streams    INTEGER,
                source     TEXT DEFAULT 'spotify'
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

        # Copy all billboard rows
        rows = src.execute("SELECT fetch_date, rank, title, artist, weeks_on_chart, peak_rank FROM billboard_charts").fetchall()
        dst.executemany(
            "INSERT INTO billboard_charts (fetch_date, rank, title, artist, weeks_on_chart, peak_rank) VALUES (?,?,?,?,?,?)",
            rows,
        )
        dst.commit()
        print(f"Copied {len(rows)} Billboard rows.")

        # Copy subset of Spotify rows in batches
        total = 0
        cursor = src.execute(
            f"""SELECT date, region, chart, rank, track_name, artist, streams, source
                FROM spotify_charts WHERE region IN ({placeholders})""",
            top_regions,
        )
        batch_size = 50_000
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
            dst.executemany(
                "INSERT INTO spotify_charts (date, region, chart, rank, track_name, artist, streams, source) VALUES (?,?,?,?,?,?,?,?)",
                batch,
            )
            dst.commit()
            total += len(batch)
            print(f"  Spotify rows inserted: {total:,}", end="\r")

        print(f"\nCopied {total:,} Spotify rows.")

        # Copy pipeline log
        logs = src.execute("SELECT run_time, script, rows_added, status FROM pipeline_log").fetchall()
        dst.executemany(
            "INSERT INTO pipeline_log (run_time, script, rows_added, status) VALUES (?,?,?,?)",
            logs,
        )
        dst.commit()
    finally:
        src.close()
        dst.close()

    # VACUUM: open with isolation_level=None (autocommit) so it can run outside any transaction
    vac = sqlite3.connect(tmp_path, isolation_level=None)
    try:
        print("Running VACUUM...")
        vac.execute("VACUUM")
    finally:
        vac.close()

    # All connections to DB_PATH are now closed — safe to replace
    import shutil
    shutil.move(str(tmp_path), str(DB_PATH))
    DB_PATH.stat()
    print(f"\nTrimmed DB written: {DB_PATH} ({DB_PATH.stat().st_size / 1e6:.1f} MB)")
    print("Full DB preserved at:", BACKUP_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--regions", type=int, default=10, help="Number of top regions to keep")
    args = parser.parse_args()
    trim(args.regions)
