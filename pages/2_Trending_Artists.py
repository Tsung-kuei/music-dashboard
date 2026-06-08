import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="Trending Artists", layout="wide")
st.title("Artist Chart Presence")

if not DB_PATH.exists():
    st.warning("Database not found.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql(
        """SELECT fetch_date, artist,
                  COUNT(*) AS entries,
                  MIN(rank)  AS best_rank
           FROM billboard_charts
           GROUP BY fetch_date, artist
           ORDER BY fetch_date""",
        conn
    )

if df.empty:
    st.info("No Billboard data yet. Run `python pipeline/refresh.py`.")
    st.stop()

top_n = st.sidebar.slider("Top N artists", 5, 20, 10)
top_artists = (
    df.groupby("artist")["entries"].sum()
    .nlargest(top_n).index.tolist()
)
filtered = df[df["artist"].isin(top_artists)]

fig = px.line(
    filtered, x="fetch_date", y="entries",
    color="artist", markers=True,
    labels={"fetch_date": "Date", "entries": "Songs in Hot 100"},
    height=500,
)
fig.update_layout(title_text="")
st.plotly_chart(fig, use_container_width=True)

best = (
    df.groupby("artist")["best_rank"].min()
    .reset_index().sort_values("best_rank")
    .head(top_n)
)
st.subheader("Best peak rank per artist")
fig2 = px.bar(best, x="artist", y="best_rank",
              labels={"best_rank": "Rank (lower = better)"},
              color="best_rank", color_continuous_scale="RdYlGn_r")
fig2.update_layout(coloraxis_showscale=False, title_text="")
st.plotly_chart(fig2, use_container_width=True)
