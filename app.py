import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "charts.db"

st.set_page_config(
    page_title="音樂排行榜",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("音樂排行榜儀表板")
st.caption("Billboard Hot 100（每週即時抓取）＋ Spotify 全球榜（2017–2021 歷史資料）")

if not DB_PATH.exists():
    st.warning("找不到資料庫。請先執行 `python pipeline/refresh.py`。")
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
    st.sidebar.caption(f"最後更新：{last[0][:19]} UTC")

col1, col2, col3 = st.columns(3)
col1.metric("已追蹤週數", weeks_tracked if weeks_tracked else "—")
col2.metric("Spotify 資料筆數", f"{spotify_count:,}" if spotify_count else "—")
if top_song and latest_date:
    col3.metric(f"本週冠軍（{latest_date}）", top_song[0], top_song[1])

st.subheader("分頁導覽")
c1, c2, c3 = st.columns(3)
c1.markdown("**藝人趨勢**\n各藝人在榜頻率變化與峰值排名比較。")
c2.markdown("**歌曲走勢**\n比較多首歌的排名逐週變化。")
c3.markdown("**歷史聚焦**\nSpotify 2017–2021 任意地區與年份的資料探索。")

if not top10.empty:
    st.subheader(f"本週 Billboard Hot 100 前十名（{latest_date}）")
    fig = px.bar(
        top10[::-1], x="weeks_on_chart", y="title",
        orientation="h", color="artist",
        labels={"weeks_on_chart": "在榜週數", "title": "歌曲", "artist": "藝人"},
        height=380,
    )
    fig.update_layout(showlegend=False, yaxis_title="", title_text="")
    st.plotly_chart(fig, use_container_width=True)

if not full_chart.empty:
    with st.expander(f"完整 Billboard Hot 100 — {latest_date}（共 {len(full_chart)} 首）"):
        st.dataframe(
            full_chart,
            column_config={
                "rank": "名次",
                "title": "歌曲",
                "artist": "藝人",
                "weeks_on_chart": "在榜週數",
                "peak_rank": "最高名次",
            },
            use_container_width=True, hide_index=True
        )
