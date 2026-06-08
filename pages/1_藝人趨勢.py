import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="藝人趨勢", layout="wide")
st.title("藝人在榜表現")

if not DB_PATH.exists():
    st.warning("找不到資料庫。")
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
    st.info("尚無 Billboard 資料，請先執行 `python pipeline/refresh.py`。")
    st.stop()

top_n = st.sidebar.slider("顯示前 N 名藝人", 5, 20, 10)
top_artists = (
    df.groupby("artist")["entries"].sum()
    .nlargest(top_n).index.tolist()
)
filtered = df[df["artist"].isin(top_artists)]

fig = px.line(
    filtered, x="fetch_date", y="entries",
    color="artist", markers=True,
    labels={"fetch_date": "日期", "entries": "在榜歌曲數", "artist": "藝人"},
    height=500,
)
fig.update_layout(title_text="", legend_title_text="藝人")
st.plotly_chart(fig, use_container_width=True)

best = (
    df.groupby("artist")["best_rank"].min()
    .reset_index().sort_values("best_rank")
    .head(top_n)
)
st.subheader("各藝人最佳名次")
fig2 = px.bar(best, x="artist", y="best_rank",
              labels={"best_rank": "最佳名次（數字越小越好）", "artist": "藝人"},
              color="best_rank", color_continuous_scale="RdYlGn_r")
fig2.update_layout(coloraxis_showscale=False, title_text="")
st.plotly_chart(fig2, use_container_width=True)
