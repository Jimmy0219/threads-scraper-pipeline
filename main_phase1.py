#匯入模組
import time
from playwright.sync_api import sync_playwright
#匯入自製函式
from actions import wait_for_main_content, get_browser_context
from database import ThreadsDB
from config import (
    DB_NAME,
    COOKIES_FILE,
    SEARCH_KEYWORD,
    TARGET_URL,
    TARGET_Total_COUNT,
    BATCH_SIZE,
    SCROLL_PAUSE_TIME,
    STABILITY_THRESHOLD,
)

# --- 主函式 ---
def main():
    # 1. 初始化 DB 物件
    db = ThreadsDB(DB_NAME)
    db.initialize()

    # 2. 檢查目前進度
    current_count = db.get_keyword_count(SEARCH_KEYWORD)
    print("--- 專案啟動 ---")
    print(f"資料庫目前已有: {current_count} 筆")

    if current_count >= TARGET_Total_COUNT:
        print("目前數量已達標，無需執行爬蟲。")
        return
    
    # 3. 啟動 Playwright
    with sync_playwright() as p:
        try:
            context = get_browser_context(p, COOKIES_FILE) 
            page = context.new_page()

            # 前往目標頁面並等待核心內容載入
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            wait_for_main_content(page, timeout=15)

            # 暫存區 
            links_buffer = [] # 用於暫存當前批次
            stability_counter = 0 # 用於偵測是否已滾到底部

            seen_links_cache = set() # 用於記憶已見過的連結，避免重複處理

            # 進入主要爬取迴圈
            while current_count < TARGET_Total_COUNT:
                # A. 滾動與等待
                page.mouse.wheel(0, 1500)
                time.sleep(SCROLL_PAUSE_TIME)

                # B. 使用 JavaScript 直接提取連結
                new_links_from_page = page.evaluate("""() => {
                    const links = [];
                    // 選取所有帶有 href 的 a 標籤
                    document.querySelectorAll('a[href*="/post/"]').forEach(a => {
                        // 排除包含 /media 的連結 (避免抓到圖片的連結)
                        if (!a.href.includes('/media')) {
                            links.push(a.href);
                        }
                    });
                    return links;
                }""")
                
                # C. Python 端記憶體去重 
                # 只保留「這一次執行還沒看過」的連結
                unique_new_links = []
                for link in new_links_from_page:
                    if link not in seen_links_cache:
                        seen_links_cache.add(link)
                        unique_new_links.append(link)

                # 如果有新連結，加入暫存區
                if unique_new_links:
                    links_buffer.extend(unique_new_links)
                    print(f"   -> 掃描到 {len(new_links_from_page)} 個連結，其中 {len(unique_new_links)} 個是新的。")

                # D. 寫入資料庫
                if len(links_buffer) >= BATCH_SIZE:
                    print("   -> 正在寫入批次資料...")
                    
                    # 假設你已經換成了 database.py 模組
                    new_added_count = db.add_links(links_buffer, SEARCH_KEYWORD)
                    current_count = db.get_keyword_count(SEARCH_KEYWORD)

                    print(f"      實際入庫: {new_added_count} 筆 | 總數: {current_count}")
                    
                    # E. 穩定性檢測 (判斷是否到底)
                    if new_added_count == 0:
                        stability_counter += 1
                        print(f"      (警告: 連續 {stability_counter} 次批次寫入無新資料)")
                    else:
                        stability_counter = 0 # 只要有抓到新資料，計數器歸零
                    
                    if stability_counter >= STABILITY_THRESHOLD:
                        print("警告: 連續多次未發現新連結，判斷已達底部或是 Threads 停止載入。")
                        break

            # 收尾寫入
            if links_buffer:
                db.add_links(links_buffer, SEARCH_KEYWORD)

        except Exception as e:
            print(f"發生錯誤: {e}")
        finally:
            print("關閉瀏覽器。")
            context.close()


if __name__ == "__main__":
    main()