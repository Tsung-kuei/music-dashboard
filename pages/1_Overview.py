import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="Overview", layout="wide")

if not DB_PATH.exists():
    st.warning("Database not found. Run `python pipeline/refresh.py` first.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    latest_date = pd.read_sql(
        "SELECT MAX(fetch_date) AS d FROM billboard_charts", conn
    )["d"][0]

    if not latest_date:
        st.warning("No Billboard data yet. Run `python pipeline/refresh.py`.")
        st.stop()

    df = pd.read_sql(
        "SELECT rank, title, artist, weeks_on_chart, peak_rank FROM billboard_charts WHERE fetch_date = ? ORDER BY rank",
        conn, params=(latest_date,)
    )

st.title(f"Billboard Hot 100 — {latest_date}")

col1, col2, col3 = st.columns(3)
col1.metric("#1 Song", df.iloc[0]["title"] if len(df) else "N/A", df.iloc[0]["artist"] if len(df) else "")
col2.metric("Total entries", len(df))
longest = df.loc[df["weeks_on_chart"].idxmax()] if len(df) else None
col3.metric("Longest on chart", longest["title"] if longest is not None else "N/A",
            f"{int(longest['weeks_on_chart'])} weeks" if longest is not None else "")

top10 = df.head(10).copy()
fig = px.bar(
    top10[::-1], x="weeks_on_chart", y="title",
    orientation="h", color="artist",
    labels={"weeks_on_chart": "Weeks on Chart", "title": "Song"},
    height=420,
)
fig.update_layout(showlegend=False, yaxis_title="", title_text="")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Full Chart")
st.dataframe(
    df[["rank", "title", "artist", "weeks_on_chart", "peak_rank"]],
    column_config={
        "rank": "Rank",
        "title": "Song",
        "artist": "Artist",
        "weeks_on_chart": "Weeks on Chart",
        "peak_rank": "Peak Rank",
    },
    use_container_width=True, hide_index=True
)
