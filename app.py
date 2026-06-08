import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "charts.db"

st.set_page_config(
    page_title="Music Charts",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Music Charts Dashboard")
st.caption("Billboard Hot 100 (live, weekly) + Spotify Global Charts (historical 2017–2021)")

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
        top10 = pd.read_sql(
            """SELECT rank, title, artist, weeks_on_chart
               FROM billboard_charts WHERE fetch_date = ? ORDER BY rank LIMIT 10""",
            conn, params=(latest_date,)
        )
        full_chart = pd.read_sql(
            """SELECT rank, title, artist, weeks_on_chart, peak_rank
               FROM billboard_charts WHERE fetch_date = ? ORDER BY rank""",
            conn, params=(latest_date,)
        )
    except Exception:
        last = None
        weeks_tracked = 0
        latest_date = None
        top_song = None
        spotify_count = 0
        top10 = pd.DataFrame()
        full_chart = pd.DataFrame()

if last:
    st.sidebar.caption(f"Last updated: {last[0][:19]} UTC")

# KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Weeks tracked", weeks_tracked if weeks_tracked else "—")
col2.metric("Spotify records", f"{spotify_count:,}" if spotify_count else "—")
if top_song and latest_date:
    col3.metric(f"#1 as of {latest_date}", top_song[0], top_song[1])

# Page guide — visible without scrolling
st.subheader("Pages")
c1, c2, c3, c4 = st.columns(4)
c1.markdown("**Trending Artists**\nArtist chart presence over time and peak rank comparison.")
c2.markdown("**Song Trajectory**\nCompare how songs' ranks change week by week.")
c3.markdown("**Genre Heatmap**\nMonthly Spotify streams by region (2017–2021).")
c4.markdown("**Historical Spotlight**\nExplore any region × year in the Spotify dataset.")

# Current Top 10 bar chart
if not top10.empty:
    st.subheader(f"Current Top 10 — Billboard Hot 100 ({latest_date})")
    fig = px.bar(
        top10[::-1], x="weeks_on_chart", y="title",
        orientation="h", color="artist",
        labels={"weeks_on_chart": "Weeks on Chart", "title": "Song", "artist": "Artist"},
        height=380,
    )
    fig.update_layout(showlegend=False, yaxis_title="", title_text="")
    st.plotly_chart(fig, use_container_width=True)

# Full chart in expander
if not full_chart.empty:
    with st.expander(f"Full Billboard Hot 100 — {latest_date} ({len(full_chart)} songs)"):
        st.dataframe(
            full_chart,
            column_config={
                "rank": "Rank",
                "title": "Song",
                "artist": "Artist",
                "weeks_on_chart": "Weeks on Chart",
                "peak_rank": "Peak Rank",
            },
            use_container_width=True, hide_index=True
        )
