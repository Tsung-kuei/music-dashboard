# Music Charts Dashboard — Executive Summary

**Student:** Peter | **Course:** BDA 2026 | **Due:** Jun 8, 2026

---

## Motivation

Music consumption has shifted from album sales to streaming metrics and chart rankings. This dashboard aggregates two major public chart sources — **Billboard Hot 100** (weekly US rankings) and **Spotify Global Charts** (daily streaming data) — to reveal how songs rise, plateau, and fall across global markets. The goal is to turn raw chart data into actionable visual insight: which artists dominate over time, which regions drive streams, and how rank correlates with streaming volume.

---

## Data Sources & Pipeline

| Source | Data Type | Volume | Method |
|--------|-----------|--------|--------|
| Spotify Charts (Kaggle) | Historical daily CSV | ~5 M rows, 2017–2023 | One-time ETL via `etl_spotify_csv.py` |
| Billboard Hot 100 | Weekly live scrape | 100 rows/week | Daily via `billboard.py` library |

**ETL steps:**
1. Download Spotify CSV → deduplicate → normalize artist names → bulk-insert into SQLite (`spotify_charts` table)
2. `refresh.py` fetches the latest Billboard Hot 100 chart and appends it to `billboard_charts`, skipping duplicate dates (idempotent)
3. Both scripts write to a `pipeline_log` table with timestamps and row counts

---

## Data Refresh Mechanism

A **GitHub Actions** workflow (`daily_refresh.yml`) runs at 08:00 UTC every day:
- Installs dependencies
- Executes `pipeline/refresh.py`
- Auto-commits the updated `data/charts.db` to the repository
- **Streamlit Community Cloud** detects the push and automatically redeploys the app

The dashboard sidebar displays the last pipeline run timestamp so viewers can verify data freshness.

---

## Dashboard — 5 Pages

| Page | Key Visualization | Insight |
|------|------------------|---------|
| **Overview** | KPI cards + horizontal bar chart | Current Hot 100 top 10 at a glance |
| **Trending Artists** | Multi-line chart over time | Which artists have the most persistent chart presence |
| **Song Trajectory** | Inverted rank line chart (multi-select) | How individual songs climb and fall week by week |
| **Genre Heatmap** | Plotly imshow heatmap | Region × month streaming intensity; artist × month best rank |
| **Historical Spotlight** | Scatter + bar with year slider | Streams vs rank correlation across years and regions |

---

## Technology Stack

- **Frontend:** Streamlit + Plotly Express
- **Database:** SQLite (committed to GitHub repository)
- **Pipeline:** Python (`pandas`, `billboard.py`)
- **Automation:** GitHub Actions (cron schedule)
- **Deployment:** Streamlit Community Cloud (public URL, free tier)

---

## Deployment URL

> _To be filled in after Streamlit Cloud deployment_

---

## Limitations

- Spotify API access is heavily restricted as of Feb 2026; historical CSV data ends at 2023
- Billboard scraping depends on the `billboard.py` community library; changes to Billboard's site structure could break the refresh
- SQLite committed to the repository is not suitable for high-concurrency production use; adequate for a course demo
