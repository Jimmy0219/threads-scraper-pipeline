# Threads Crawler Pipeline (Threads 貼文自動化採集系統)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-green)](https://playwright.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey)](https://www.sqlite.org/)

這是一個針對 Meta Threads 平台設計的**高穩健性**資料爬蟲專案。與一般的單一腳本爬蟲不同，本專案採用**生產者-消費者 (Producer-Consumer)** 架構，將「連結採集」與「內容解析」解耦，並結合 SQLite 實作**斷點續傳**與**任務隊列**機制，專為大規模、長時間的資料採集任務而設計。

##  專案亮點 

這不僅僅是一個腳本，而是一個具備容錯能力的資料工程 (Data Engineering) 原型：

* *** 高效能瀏覽器端解析 ***
    * 在 Phase 1 採集連結時，捨棄傳統 Python 端 (`BeautifulSoup`) 解析整頁 HTML 的高耗能做法。
    * 改用 Playwright 的 `page.evaluate` 直接在瀏覽器 V8 引擎中執行 JavaScript 提取 DOM 節點，大幅降低 CPU 負載並提升爬取速度。
* *** 模組化與分層架構 ***
    * 實作 **DAO (Data Access Object)** 模式 (`database.py`)，將業務邏輯與資料存取層完全分離，提高程式碼的可維護性與擴充性。
* *** 狀態管理與斷點續傳 ***
    * 使用 SQLite 建立任務狀態機（Status: 待處理 / 成功 / 失敗）。
    * 具備自動重試機制 (`MAX_RETRIES`)，若程式中斷或崩潰，重啟後可直接從上次進度繼續執行，無需由頭開始。
* *** 抗偵測與自動化 ***
    * 整合 Cookies 管理與 User-Agent 模擬。
    * 實作隨機延遲 (Random Delays) 與類比人類行為，降低被反爬蟲機制封鎖的風險。

##  技術整合

| 類別 | 技術 / 套件 | 說明 |
| :--- | :--- | :--- |
| **核心語言** | Python 3.13 | 專案開發語言 |
| **瀏覽器自動化** | Playwright (Chromium) | 處理動態渲染與模擬使用者操作 |
| **資料庫** | SQLite3 | 輕量級關聯式資料庫，儲存任務隊列與爬取結果 |
| **HTML 解析** | BeautifulSoup4 | 用於 Phase 2 的靜態內文精細解析 |
| **配置管理** | JSON, Python Config | 管理 Cookies 與全域參數 |

##  專案結構
```text
.
├── main_phase1.py          # [生產者] 負責搜尋關鍵字，大量滾動並採集貼文連結 (入庫)
├── main_phase2.py          # [消費者] 從資料庫領取任務，進入內頁解析詳細內文
├── database.py             # [DAO層] 封裝所有 SQL 操作 (Create, Insert, Update)
├── parsers.py              # [解析層] 定義 HTML 解析邏輯與 CSS Selectors
├── actions.py              # [行為層] 定義瀏覽器行為 (如載入 Cookies、等待元素)
├── config.py               # [配置層] 統一管理全域參數 (重試次數、延遲時間、Selectors)
├── save_threads_cookies.py # [工具] 用於手動登入並提取有效 Cookies
└── cookies.js              # (自動生成) 存放登入憑證
```

##  快速開始
* ### 1.安裝依賴 
    * 確保已安裝 Python 3.13，並安裝所需套件：
    ```text
    Bash
    ```
    ```text
    pip install playwright beautifulsoup4
    playwright install chromium
    ```

* ### 2. 準備 Cookies (繞過登入驗證)
    * 由於 Threads 內容瀏覽受限，需先進行一次性登入：
    ```text
    Bash
    ```
    ```text
    python3 save_threads_cookies.py
    ```
    * 程式會開啟瀏覽器，請手動輸入帳號密碼登入 Threads。
    * 登入成功後，程式會自動擷取 Cookies 並存為 cookies.js。

* ### 3. 執行 Phase 1：採集連結 (Producer) 
    * 設定 config.py 中的 SEARCH_KEYWORD (例如："筆電推薦")，然後執行：
    ```text
    Bash
    ```
    ```text
    python main_phase1.py
    ```
    * 此階段會自動滾動頁面，收集貼文連結並存入 SQLite 資料庫 (狀態為 0: 待處理)。
    * 具備去重機制，不會重複採集已存在的連結。

* ### 4. 執行 Phase 2：解析內文 (Consumer) 
    ```text
    Bash
    ```
    ```text
    python main_phase2.py
    ```
    * 程式會從資料庫讀取 status=0 的連結。
    * 進入內頁抓取內文，成功後標記 status=1，失敗則標記 status=0 (重試) 或 status=-1 (超過重試次數)。

## 資料庫結構
資料表 search_results 設計如下：

| 欄位名稱 | 類型 | 說明 |
| :--- | :--- | :--- |
| **link** | TEXT (PK) | 貼文網址 (Unique) |
| **status** | INTEGER	| 0:待辦, 1:成功, -1:失敗 |
| **keyword** | TEXT | 搜尋關鍵字 |
| **content** | TEXT | 貼文內文 (Phase 2 填入) |
| **retry_count** | INTEGER | 失敗重試次數 |
| **error_log** | TEXT | 錯誤訊息紀錄 |
| **created_at** | TIMESTAMP | 建立時間 |
| **updated_at** | TIMESTAMP | 最後更新時間 |

## 未來展望
身為資料科學背景的開發者，本專案的下一步計畫包括：
* 資料視覺化 (Dashboard): 使用 Streamlit 建立儀表板，即時監控爬蟲進度與資料分佈。
* NLP 分析: 對抓取到的內容進行斷詞 (jieba) 與情感分析 (Sentiment Analysis)，產出輿情報告。
* 容器化: 撰寫 Dockerfile，實現更便捷的部署。

## 免責聲明
本專案僅供學術研究與技術交流使用。請遵守目標網站的 robots.txt 規範與服務條款 (ToS)。請勿將本工具用於任何商業用途或惡意攻擊。