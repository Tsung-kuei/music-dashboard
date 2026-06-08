# Music Charts Dashboard — Executive Summary
**BDA 2026 | Final Bonus Project | Student: Tsung-kuei (Peter)**
**Live URL:** https://tsung-kuei-music-dashboard.streamlit.app/

---

## 專案概述 / Project Overview

本專案建立一個雙來源音樂排行榜儀表板，整合 Spotify 歷史資料（2017–2021）與每週即時抓取的 Billboard Hot 100，透過自動化 ETL 管線、SQLite 資料庫與 Streamlit 視覺化介面，提供互動式音樂趨勢分析工具，並部署於公開 URL 供任何人存取。

A dual-source music charts dashboard combining historical Spotify data (2017–2021) with live-scraped Billboard Hot 100. Built on an automated ETL pipeline and deployed publicly via Streamlit Community Cloud.

---

## 資料來源 / Data Sources

| 來源 | 說明 | 規模 |
|------|------|------|
| Spotify Charts (Kaggle: `dhruvildave/spotify-charts`) | 全球 70 地區每日 Top-200，2017–2021 | 原始 2.6M 列 / 部署版 730,159 列（7 地區） |
| Billboard Hot 100 (`billboard.py` open-source library) | 每週即時抓取美國 Hot 100 | 每週 100 筆，持續累積 |

---

## 資料管線 / Data Pipeline (ETL)

**一次性 ETL（`etl_spotify_csv.py`）：** 以 50,000 列為單位分批讀取 3.3GB CSV，去除重複資料、統一藝人名稱格式，批次寫入 SQLite。並以 `trim_db.py` 按串流量篩選，保留部署用的 7 個最高串流量地區（730,159 列）。

**每日自動更新（`refresh.py`）：** 先確認當日資料是否已存在（冪等性設計），若無則呼叫 `billboard.py` 抓取最新 Hot 100，寫入資料庫並記錄於 `pipeline_log`。

**自動化排程（GitHub Actions）：** 每日 UTC 08:00 自動執行 refresh 腳本 → 將更新後的 `charts.db` 自動 commit 回 GitHub repo → Streamlit Community Cloud 偵測到 repo 更新後自動重新部署，形成完整的「資料更新 → 自動 commit → 自動部署」閉環，無需人工介入。

---

## 資料庫 / Database

**SQLite**（`data/charts.db`，單一檔案格式，隨 GitHub repo 部署）

| 資料表 | 欄位 | 用途 |
|--------|------|------|
| `spotify_charts` | id, date, region, chart, rank, track_name, artist, streams, source | Spotify 歷史排行榜 |
| `billboard_charts` | id, fetch_date, rank, title, artist, weeks_on_chart, peak_rank, source | Billboard 每週快照 |
| `pipeline_log` | id, run_time, script, rows_added, status | 執行稽核紀錄 |

---

## 視覺化 / Visualizations (5 Pages)

| 頁面 | 圖表類型 | 主要功能 |
|------|----------|----------|
| Overview | KPI cards + 橫向長條圖 + 表格 | 當週 Billboard Hot 100 全覽 |
| Trending Artists | 多線折線圖 + 長條圖 + slider | 藝人出現頻率趨勢（可調前 N 名） |
| Song Trajectory | 多線折線圖（Y 軸倒置） | 多首歌同時比較排名走勢 |
| Genre Heatmap | imshow 熱力圖 | 地區 × 月份串流量分佈 |
| Historical Spotlight | 散點圖 + 長條圖 + 地區/年份篩選 | Spotify 歷史聚焦分析 |

所有圖表使用 **Plotly Express**，支援 zoom、hover、互動篩選。

---

## 技術架構 / Tech Stack

- **Front-end & Deployment:** Streamlit + Streamlit Community Cloud
- **Visualization:** Plotly Express
- **Database:** SQLite
- **Pipeline:** Python (pandas, billboard.py, sqlite3)
- **Automation:** GitHub Actions (daily cron schedule)
- **Version Control & Hosting:** GitHub

---

## 核心亮點 / Highlights

1. **多來源 ETL**：大型靜態資料集（730K 列）＋即時抓取，整合於單一 SQLite。
2. **全自動更新閉環**：GitHub Actions → billboard.py → SQLite → auto-commit → Streamlit auto-redeploy，每日更新零人工介入。
3. **冪等性設計**：refresh 腳本可安全重複執行，不產生重複資料。
4. **公開部署**：https://tsung-kuei-music-dashboard.streamlit.app/
