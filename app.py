import streamlit as st
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "charts.db"

st.set_page_config(
    page_title="Music Charts",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Music Charts Dashboard")

if not DB_PATH.exists():
    st.warning("No database found. Run `python pipeline/refresh.py` first.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    try:
        last = conn.execute(
            "SELECT run_time FROM pipeline_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        weeks_tracked = conn.execute(
            "SELECT COUNT(DISTINCT fetch_date) FROM billboard_charts"
        ).fetchone()[0]
        latest_date = conn.execute(
            "SELECT MAX(fetch_date) FROM billboard_charts"
        ).fetchone()[0]
        top_song = conn.execute(
            "SELECT title, artist FROM billboard_charts WHERE fetch_date = ? AND rank = 1",
            (latest_date,),
        ).fetchone()
        spotify_count = conn.execute("SELECT COUNT(*) FROM spotify_charts").fetchone()[0]
    except Exception:
        last = None
        weeks_tracked = 0
        latest_date = None
        top_song = None
        spotify_count = 0

if last:
    st.sidebar.caption(f"Last updated: {last[0][:19]} UTC")

col1, col2, col3 = st.columns(3)
col1.metric("Weeks tracked", weeks_tracked if weeks_tracked else "—")
col2.metric("Spotify records", f"{spotify_count:,}" if spotify_count else "—")
if top_song and latest_date:
    col3.metric(f"#1 as of {latest_date}", top_song[0], top_song[1])
