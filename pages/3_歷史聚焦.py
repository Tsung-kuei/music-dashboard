import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="歷史聚焦", layout="wide")
st.title("Spotify 歷史資料")

if not DB_PATH.exists():
    st.warning("找不到資料庫。")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    count = conn.execute("SELECT COUNT(*) FROM spotify_charts").fetchone()[0]

if count == 0:
    st.info(
        "尚未載入 Spotify 資料。"
        "請執行 `python pipeline/etl_spotify_csv.py --csv path/to/charts.csv`。"
    )
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    regions = pd.read_sql("SELECT DISTINCT region FROM spotify_charts ORDER BY region", conn)["region"].tolist()

region = st.sidebar.selectbox("地區", ["Global"] + [r for r in regions if r != "Global"])

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql(
        """SELECT date, rank, track_name, artist, streams
           FROM spotify_charts
           WHERE region = ? AND streams IS NOT NULL
           ORDER BY date""",
        conn, params=(region,)
    )

df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year

years = sorted(df["year"].unique())
selected_year = st.sidebar.select_slider("年份", options=years, value=years[-1])

year_df = df[df["year"] == selected_year].copy()

st.subheader(f"串流數 vs. 排名 — {region} {selected_year}")
sample = year_df.sample(min(2000, len(year_df)), random_state=42) if len(year_df) > 2000 else year_df
fig = px.scatter(
    sample, x="rank", y="streams",
    color="artist", hover_data=["track_name", "date"],
    labels={"rank": "排名", "streams": "串流數"},
    opacity=0.6, height=500,
)
fig.update_layout(showlegend=False, title_text="")
st.plotly_chart(fig, use_container_width=True)

st.subheader(f"串流量前 15 名歌曲 — {region} {selected_year}")
top_songs = (
    year_df.groupby(["track_name", "artist"])["streams"]
    .sum().reset_index()
    .sort_values("streams", ascending=False)
    .head(15)
)
fig2 = px.bar(
    top_songs[::-1], x="streams", y="track_name",
    orientation="h", color="artist",
    labels={"streams": "總串流數", "track_name": "歌曲"},
    height=480,
)
fig2.update_layout(showlegend=False, yaxis_title="", title_text="")
st.plotly_chart(fig2, use_container_width=True)
