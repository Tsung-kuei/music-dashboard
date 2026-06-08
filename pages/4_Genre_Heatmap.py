import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "charts.db"

st.set_page_config(page_title="Chart Heatmap", layout="wide")

if not DB_PATH.exists():
    st.warning("Database not found.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    spotify_count = conn.execute("SELECT COUNT(*) FROM spotify_charts").fetchone()[0]

if spotify_count == 0:
    st.title("Artist Frequency Heatmap")

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(
            "SELECT fetch_date, artist, rank FROM billboard_charts", conn
        )

    if df.empty:
        st.warning("No data available. Run the pipeline first.")
        st.stop()

    df["month"] = pd.to_datetime(df["fetch_date"]).dt.to_period("M").astype(str)
    pivot = (
        df.groupby(["artist", "month"])["rank"]
        .min().reset_index()
        .pivot(index="artist", columns="month", values="rank")
    )
    top_artists = df["artist"].value_counts().head(15).index
    pivot = pivot.loc[pivot.index.isin(top_artists)]

    fig = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn_r",
        labels={"color": "Best Rank", "x": "Month", "y": "Artist"},
        aspect="auto",
        height=550,
    )
    fig.update_layout(title_text="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Best rank per month per artist. Lower value = higher chart position.")

else:
    st.title("Streams by Region")

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(
            """SELECT date, region, SUM(streams) AS total_streams
               FROM spotify_charts
               WHERE streams IS NOT NULL
               GROUP BY date, region
               ORDER BY date""",
            conn
        )

    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    pivot = (
        df.groupby(["region", "month"])["total_streams"]
        .sum().reset_index()
        .pivot(index="region", columns="month", values="total_streams")
    )

    top_regions = df.groupby("region")["total_streams"].sum().nlargest(20).index
    pivot = pivot.loc[pivot.index.isin(top_regions)]

    fig = px.imshow(
        pivot / 1e6,
        color_continuous_scale="Viridis",
        labels={"color": "Streams (M)", "x": "Month", "y": "Region"},
        aspect="auto",
        height=600,
    )
    fig.update_layout(title_text="")
    st.plotly_chart(fig, use_container_width=True)
