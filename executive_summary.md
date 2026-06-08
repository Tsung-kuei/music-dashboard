# Music Charts Dashboard
**BDA 2026 Final Bonus | 學生：Tsung-kuei (Peter)**

**Live Demo（公開網址，任何人可直接點開）：**
**[https://tsung-kuei-music-dashboard.streamlit.app/](https://tsung-kuei-music-dashboard.streamlit.app/)**

---

## 專案概述

整合兩個音樂排行榜資料來源，透過自動化 ETL 管線、SQLite 資料庫與 Streamlit 前端，建立一個公開部署的互動式音樂趨勢分析儀表板。資料涵蓋 Spotify 歷史串流紀錄（2017–2021）與每週即時抓取的 Billboard Hot 100。

---

## 資料來源

| 來源 | 說明 | 規模 |
|------|------|------|
| Spotify Charts（Kaggle: dhruvildave/spotify-charts）| 全球 70 地區每日 Top-200，2017–2021 | 原始 2.6M 列；部署版篩選至 7 地區，共 730,159 列 |
| Billboard Hot 100（billboard.py）| 每週自動抓取美國 Hot 100 | 每週 100 筆，持續累積 |

---

## 資料管線

**一次性匯入：** 以 50,000 列為單位分批讀取 3.3GB CSV，清理重複資料後寫入 SQLite。以 `trim_db.py` 依串流量保留前 7 個地區，將資料庫壓縮至 94MB（符合 GitHub 部署限制）。

**每日自動更新：** GitHub Actions 每日 UTC 08:00 觸發 `refresh.py`，抓取最新 Billboard Hot 100 → 寫入 SQLite → 自動 commit → Streamlit Community Cloud 偵測 repo 更新後自動重新部署。全流程零人工介入，具冪等性設計（重複執行不產生重複資料）。

---

## 資料庫

SQLite（`data/charts.db`，隨 GitHub repo 直接部署）

| 資料表 | 欄位摘要 | 用途 |
|--------|----------|------|
| `spotify_charts` | date, region, rank, track_name, artist, streams | Spotify 歷史排行榜 |
| `billboard_charts` | fetch_date, rank, title, artist, weeks_on_chart, peak_rank | Billboard 每週快照 |
| `pipeline_log` | run_time, script, rows_added, status | 執行紀錄 |

---

## 視覺化（首頁 + 3 頁）

| 頁面 | 圖表 | 內容 |
|------|------|------|
| 首頁 | KPI + 橫向長條圖 + 可展開表格 | 本週 Billboard Top 10 與完整 100 名 |
| Trending Artists | 折線圖 + 長條圖 | 藝人出現頻率趨勢與峰值排名 |
| Song Trajectory | 多線折線圖 | 多首歌排名走勢對比（可自由選歌） |
| Historical Spotlight | 散點圖 + 長條圖 | Spotify 歷史聚焦分析（地區 / 年份篩選）|

所有圖表使用 Plotly Express，支援 zoom、hover、互動篩選。

---

## 技術架構

- **前端 & 部署：** Streamlit + Streamlit Community Cloud
- **視覺化：** Plotly Express
- **資料庫：** SQLite
- **ETL 管線：** Python（pandas, billboard.py, sqlite3）
- **自動化排程：** GitHub Actions（每日 cron）
- **版本控制 & 托管：** GitHub
