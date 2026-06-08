import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="歌曲走勢", layout="wide")
st.title("歌曲排名走勢")

if not DB_PATH.exists():
    st.warning("找不到資料庫。")
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
    st.info("尚無 Billboard 資料。")
    st.stop()

song_labels = (all_songs["title"] + " — " + all_songs["artist"]).tolist()
selected = st.multiselect(
    "選擇要比較的歌曲",
    options=song_labels,
    default=song_labels[:3] if len(song_labels) >= 3 else song_labels,
)

if not selected:
    st.info("請從上方選擇至少一首歌。")
    st.stop()

selected_titles = [s.split(" — ")[0] for s in selected]
filtered = df_all[df_all["title"].isin(selected_titles)].copy()
filtered["label"] = filtered["title"] + " — " + filtered["artist"]

fig = px.line(
    filtered, x="fetch_date", y="rank",
    color="label", markers=True,
    labels={"fetch_date": "日期", "rank": "排名", "label": "歌曲"},
    height=500,
)
fig.update_yaxes(range=[101, 0])
fig.update_layout(legend_title_text="歌曲", title_text="")
st.plotly_chart(fig, use_container_width=True)

st.caption("名次 1 = 排行榜冠軍。空白處表示該週歌曲未在榜上。")
