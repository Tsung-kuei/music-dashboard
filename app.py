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
    except Exception:
        last = None
        weeks_tracked = 0
        latest_date = None
        top_song = None
        spotify_count = 0
        top10 = pd.DataFrame()

if last:
    st.sidebar.caption(f"Last updated: {last[0][:19]} UTC")

# KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Weeks tracked", weeks_tracked if weeks_tracked else "—")
col2.metric("Spotify records", f"{spotify_count:,}" if spotify_count else "—")
if top_song and latest_date:
    col3.metric(f"#1 as of {latest_date}", top_song[0], top_song[1])

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

# Page guide
st.subheader("What's in this dashboard")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Overview**")
    st.markdown("Full Billboard Hot 100 ranking for the current week, with a weeks-on-chart comparison chart.")
    st.markdown("**Trending Artists**")
    st.markdown("Which artists appear most often across all tracked weeks, and their best-ever peak rank.")
with c2:
    st.markdown("**Song Trajectory**")
    st.markdown("Select any songs from the chart history and compare how their rank changed week by week.")
    st.markdown("**Genre Heatmap**")
    st.markdown("Monthly streaming volume by region across 2017–2021, visualized as an interactive heatmap.")
with c3:
    st.markdown("**Historical Spotlight**")
    st.markdown("Explore any region and year from the Spotify dataset — rank vs. streams scatter plot and top 15 songs by total streams.")
