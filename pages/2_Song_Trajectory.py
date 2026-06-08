import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="Song Trajectory", layout="wide")
st.title("Song Trajectory")

if not DB_PATH.exists():
    st.warning("Database not found.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    all_songs = pd.read_sql(
        "SELECT DISTINCT title, artist FROM billboard_charts ORDER BY title", conn
    )
    df_all = pd.read_sql(
        "SELECT fetch_date, rank, title, artist FROM billboard_charts ORDER BY fetch_date",
        conn
    )

if df_all.empty:
    st.info("No Billboard data yet.")
    st.stop()

song_labels = (all_songs["title"] + " — " + all_songs["artist"]).tolist()
selected = st.multiselect(
    "Select songs to compare",
    options=song_labels,
    default=song_labels[:3] if len(song_labels) >= 3 else song_labels,
)

if not selected:
    st.info("Select at least one song above.")
    st.stop()

selected_titles = [s.split(" — ")[0] for s in selected]
filtered = df_all[df_all["title"].isin(selected_titles)].copy()
filtered["label"] = filtered["title"] + " — " + filtered["artist"]

fig = px.line(
    filtered, x="fetch_date", y="rank",
    color="label", markers=True,
    labels={"fetch_date": "Date", "rank": "Chart Rank", "label": "Song"},
    height=500,
)
fig.update_yaxes(range=[101, 0])
fig.update_layout(legend_title_text="Song", title_text="")
st.plotly_chart(fig, use_container_width=True)

st.caption("Rank 1 = top of chart. Gaps indicate weeks the song dropped off.")
