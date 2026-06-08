# Music Charts Dashboard — 講稿

**BDA 2026 Final Bonus Project | Peter (Tsung-kuei)**
**Live URL:** https://tsung-kuei-music-dashboard.streamlit.app/

---

## 開場白

老師好，同學們好。我是 Peter，今天要展示的是我的 Big Data Analytics 期末 Bonus Project——一個叫做「Music Charts Dashboard」的音樂圖表數據儀表板。

這個 Project 我從零開始做，從資料收集、資料庫設計、自動化排程，到最後部署上線，全部都是自己完成的。今天我會帶大家走一遍整個系統的架構，然後做一個 Live Demo。

---

## 動機與問題意識

一開始我在想：音樂排行榜這個東西，其實每週都在變化，但大部分人只看到「現在排第幾名」，沒辦法看到一首歌「怎麼爬上去、又怎麼掉下來」的過程。

所以我的目標是：建一個可以同時看歷史趨勢和即時排行的儀表板。不只是靜態的表格，而是可以互動、可以篩選的視覺化工具。

---

## 資料來源

我用了兩個資料來源，一個是歷史資料，一個是即時資料。

**第一個：Spotify Charts（Kaggle 資料集）**

這是一個在 Kaggle 上公開的資料集，叫做「dhruvildave/spotify-charts」。原始資料有大概 2.6 百萬筆，CSV 檔案大小是 3.3GB，涵蓋 2017 到 2021 年、全球 70 個地區的每日 Top 200 排行榜。

這個資料集很大，所以我做了一個「資料瘦身」的動作：從 70 個地區，只保留串流量最高的 7 個地區——包括 Global、巴西、阿根廷、澳洲、德國、加拿大、智利。最後保留了 730,159 筆資料。這樣在部署的時候，資料庫檔案不會太大，系統才跑得動。

**第二個：Billboard Hot 100（即時抓取）**

這個是美國最有名的音樂排行榜。我用了一個開源的 Python 套件叫做 `billboard.py`，它可以直接去 Billboard 的網站抓取當週最新的 Hot 100 資料——排名、歌名、歌手、已在榜幾週、最高排名，這些都能拿到。

一個是歷史的大資料集，一個是現在進行式的即時資料——兩個加在一起，就可以做到「回顧過去、追蹤現在」。

---

## 資料管線（Data Pipeline / ETL）

ETL 是 Extract、Transform、Load 三個步驟的縮寫。簡單說就是：把資料抓下來、清理整理、然後存進資料庫。

我的 ETL 分成幾個 Python 腳本：

**`pipeline/db.py`**

這是資料庫的「地基」。它定義了三張資料表的結構——`spotify_charts`、`billboard_charts`、還有一個 `pipeline_log`，用來記錄每次執行是否成功。它也提供一個共用的資料庫連線函式，讓其他腳本都能呼叫。

**`pipeline/etl_spotify_csv.py`**

這個腳本處理那 3.3GB 的 Spotify CSV。因為檔案太大，不能一次全部讀進記憶體，所以我用了「分批讀取」的方法——每次讀 50,000 筆，處理完再讀下一批。處理的動作包括：去除重複資料、統一藝人名稱的格式、然後批次寫入資料庫。這個腳本只需要跑一次，是一次性的 ETL。

**`pipeline/refresh.py`**

這個是每天都會自動執行的腳本。它的邏輯是：先檢查今天的 Billboard 資料是不是已經存在了——如果已經有了就跳過，如果沒有就去抓、存進去、然後記錄在 log 裡面。這個設計叫做「idempotent（冪等性）」，意思是不管跑幾次，結果都一樣，不會產生重複資料。

**`pipeline/trim_db.py`**

這是一個工具腳本，用來把完整的資料庫「修剪」成部署用的輕量版本，只保留串流量最高的幾個地區。

---

## 資料庫設計

我用的資料庫是 SQLite。

SQLite 是一個輕量級的 SQL 資料庫，特別的地方是它不需要安裝伺服器——整個資料庫就是一個檔案，叫做 `charts.db`。這對我的 Project 很適合，因為我可以直接把這個檔案放進 GitHub，然後部署的時候直接用。

資料庫有三張表：
- `spotify_charts`：存 Spotify 的歷史排行榜資料
- `billboard_charts`：存每週抓取的 Billboard Hot 100
- `pipeline_log`：記錄每次自動執行的時間、新增了幾筆資料、成功還是失敗

---

## 前端與視覺化

前端我用的是 Streamlit。

Streamlit 是一個 Python 的 Web 框架，特別的地方是：我不需要寫 HTML、CSS、JavaScript，只要寫 Python，就可以做出互動式的網頁。對我來說這個選擇很重要，因為我的強項是 Python，而不是前端開發。

視覺化用的是 Plotly Express——這是一個互動式圖表套件，做出來的圖可以 zoom、hover、點選，不是死的靜態圖片。

儀表板總共有五個頁面：

**第一頁：Overview（總覽）**
顯示當週 Billboard Hot 100。有三個 KPI 卡片：現在排名第一的歌曲、總共有幾首歌在榜、在榜最久的歌。下面有一個橫向長條圖，顯示待榜週數最多的前 10 首歌，最下面是完整的 100 首排行榜表格。

**第二頁：Trending Artists（趨勢藝人）**
用多線折線圖顯示哪些藝人在 Hot 100 出現次數最多。旁邊有一個 slider，可以選「看前幾名的藝人」，從 3 個調到 10 個都可以。

**第三頁：Song Trajectory（歌曲軌跡）**
可以選多首歌，然後看它們在 Hot 100 的排名隨時間的變化。Y 軸是反向的——排名第 1 在最上面，視覺上更直覺。

**第四頁：Genre Heatmap（熱力圖）**
如果有 Spotify 資料，這個頁面會顯示每個地區、每個月的串流量熱力圖——哪個地區哪個月最熱門，一眼就看出來。如果只有 Billboard 資料，它會 fallback 到顯示藝人對月份的最高排名熱力圖。

**第五頁：Historical Spotlight（歷史聚焦）**
這頁是給 Spotify 歷史資料用的。可以選地區和年份，然後看散點圖（rank vs. streams），還有那個地區那一年串流量最高的前 15 首歌。

---

## 自動更新機制

這是我覺得這個 Project 最有趣的部分。

我用的工具叫做 **GitHub Actions**。它是 GitHub 內建的 CI/CD 工具，可以設定「在特定時間自動執行某個腳本」。

我設定的邏輯是這樣的：

1. 每天早上 UTC+0 八點（台灣時間下午四點），GitHub Actions 自動啟動
2. 它安裝好所有需要的套件，然後跑 `python pipeline/refresh.py`
3. `refresh.py` 去 Billboard 網站抓最新資料，存進 `charts.db`
4. GitHub Actions 自動把更新後的 `charts.db` commit 回 GitHub repo
5. Streamlit Community Cloud 偵測到 GitHub repo 有更新，自動重新部署

所以整個流程是一個完整的循環：資料更新 → 自動 commit → 自動部署 → 使用者看到最新資料。不需要我手動做任何事情。

---

## Live Demo

現在來看一下實際的網站。

Live URL 是：**https://tsung-kuei-music-dashboard.streamlit.app/**

（帶老師和同學看每個頁面，邊說邊指）

- 這是 Overview 頁面，可以看到當週排名第一的是...，在榜最久的是...
- 這是 Trending Artists，我可以調這個 slider，選看前五名的藝人，折線圖會即時更新
- 這是 Song Trajectory，我選幾首歌來比較，可以看到它們的排名起伏
- 這是 Historical Spotlight，我選 Global、2020 年，可以看到疫情那年哪些歌最流行

---

## 結論

整個 Project 涵蓋了完整的資料工程週期：從原始資料的清理與匯入、資料庫的設計、到視覺化介面的建立，最後透過自動化排程讓資料保持更新。

我學到最多的是：真實世界的資料不會很乾淨，需要花很多時間在 ETL 上。還有就是「自動化」的概念——當一個系統可以自己跑，不需要人手動介入，這才是真正的 Data Pipeline 的意義。

謝謝老師和同學，我的報告到這裡，有任何問題歡迎提問。

---

## Q&A 備考筆記（自己看，不要念出來）

**Q：為什麼選 SQLite 不選 PostgreSQL 或 MongoDB？**
A：因為這個 Project 的資料是靜態居多（Spotify 不會再更新）、加上需要把資料庫檔案放進 GitHub repo，SQLite 的「單一檔案」特性最適合。如果資料量更大、或者有多個使用者同時寫入，才需要 PostgreSQL 這類的伺服器型資料庫。

**Q：billboard.py 是什麼？你自己寫的嗎？**
A：不是，這是一個開源套件，作者是 guoguo12，在 GitHub 上公開。它本質上是一個 web scraper，自動去 Billboard 網站抓資料、解析成結構化格式。我的工作是把它整合進我的 pipeline，並且加上 idempotent 檢查和 log 記錄。

**Q：3.3GB 的 CSV 怎麼處理？**
A：我用 pandas 的 `chunksize` 參數，每次讀 50,000 筆，處理完再讀下一批，這樣就不會撐爆記憶體。這個方法叫做「chunked reading」或「streaming ETL」。

**Q：GitHub Actions 會不會失敗？失敗了怎麼辦？**
A：有可能失敗，例如 Billboard 網站暫時下線、或 rate limiting。所以我在 `pipeline_log` 裡面記錄了每次執行的 status。如果失敗，下次執行還是會再試，因為 refresh.py 的 idempotent 設計不怕重複跑。

**Q：Streamlit 適合做生產環境嗎？**
A：Streamlit 比較適合快速原型和內部工具，不太適合高流量的生產環境。如果要擴大規模，可以考慮換成 Flask/FastAPI 後端 + React 前端。但對這個 Project 的規模，Streamlit Cloud 完全夠用。

**Q：資料有沒有清理過？**
A：有。Spotify 的原始資料有藝人名稱格式不一致的問題（比如大小寫、多餘空格），我在 ETL 腳本裡做了 normalize。另外也做了 deduplication，確保同一天同一首歌不會重複出現。

**Q：為什麼只選 7 個地區？**
A：原始資料有 70 個地區、260 萬筆。部署到 Streamlit Cloud 有 GitHub 100MB 單檔上限，所以我用串流量當指標，取前 7 名的地區（保留了 73 萬筆），這樣保留了最有代表性的資料，同時讓 app 可以在免費方案上跑。

---

## 參考來源 / Sources

- Kaggle Spotify Charts dataset: https://www.kaggle.com/datasets/dhruvildave/spotify-charts
- billboard.py library: https://github.com/guoguo12/billboard-charts
- Streamlit Community Cloud: https://streamlit.io/cloud
- GitHub Actions docs: https://docs.github.com/en/actions
- Plotly Express docs: https://plotly.com/python/plotly-express/
