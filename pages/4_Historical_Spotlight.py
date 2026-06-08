import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="Historical Spotlight", layout="wide")
st.title("Spotify Historical Data")

if not DB_PATH.exists():
    st.warning("Database not found.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    count = conn.execute("SELECT COUNT(*) FROM spotify_charts").fetchone()[0]

if count == 0:
    st.info(
        "Spotify data not loaded yet. "
        "Run `python pipeline/etl_spotify_csv.py --csv path/to/charts.csv` "
        "after downloading from Kaggle (`dhruvildave/spotify-charts`)."
    )
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    regions = pd.read_sql("SELECT DISTINCT region FROM spotify_charts ORDER BY region", conn)["region"].tolist()

region = st.sidebar.selectbox("Region", ["Global"] + [r for r in regions if r != "Global"])

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
selected_year = st.sidebar.select_slider("Year", options=years, value=years[-1])

year_df = df[df["year"] == selected_year].copy()

st.subheader(f"Streams vs Rank — {region} {selected_year}")
sample = year_df.sample(min(2000, len(year_df)), random_state=42) if len(year_df) > 2000 else year_df
fig = px.scatter(
    sample, x="rank", y="streams",
    color="artist", hover_data=["track_name", "date"],
    labels={"rank": "Chart Rank", "streams": "Streams"},
    opacity=0.6, height=500,
)
fig.update_layout(showlegend=False, title_text="")
st.plotly_chart(fig, use_container_width=True)

st.subheader(f"Top 15 songs by total streams — {region} {selected_year}")
top_songs = (
    year_df.groupby(["track_name", "artist"])["streams"]
    .sum().reset_index()
    .sort_values("streams", ascending=False)
    .head(15)
)
fig2 = px.bar(
    top_songs[::-1], x="streams", y="track_name",
    orientation="h", color="artist",
    labels={"streams": "Total Streams", "track_name": "Song"},
    height=480,
)
fig2.update_layout(showlegend=False, yaxis_title="", title_text="")
st.plotly_chart(fig2, use_container_width=True)
