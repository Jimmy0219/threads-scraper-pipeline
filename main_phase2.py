# 匯入模組
import time
import random
from playwright.sync_api import sync_playwright
#匯入自製函式
from actions import get_browser_context
from parsers import parse_post_details
from database import ThreadsDB
from config import (
    DB_NAME,
    COOKIES_FILE,
    MAX_RETRIES,
    PAUSE_MIN,
    PAUSE_MAX,
    CONTENT_SELECTOR,
)

# --- 主函式 ---

def main():
    # 1. 初始化 DB
    db = ThreadsDB(DB_NAME)
    db.initialize()
    
    # 2. 啟動瀏覽器
    with sync_playwright() as p:
        try:
            context = get_browser_context(p, COOKIES_FILE)
            print("瀏覽器初始化成功，Cookie 已載入。")
        except Exception as e:
            print(f"無法初始化瀏覽器: {e}")
            return
        
        page = context.new_page()

        # 3. 進入任務迴圈 (Infinite Loop until no tasks)
        while True:
            # A. 領取任務
            link = db.get_pending_task()
            
            # 如果沒有任務了，就結束
            if not link:
                print("\n所有任務已完成！沒有待處理的連結了。")
                break
            
            # 顯示目前進度
            stats = db.get_stats() # 取代 get_progress_stats()
            print(f"\n處理中... (待辦: {stats.get(0,0)} | 成功: {stats.get(1,0)} | 失敗: {stats.get(-1,0)})")
            print(f"Target: {link}")

            try:
                # B. 執行爬取
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                
                # 等待關鍵元素出現 (防呆)
                try:
                    page.wait_for_selector(CONTENT_SELECTOR, timeout=10000)
                except Exception as e:
                    print(f"   (等待元素超時或發生錯誤: {e})")

                # 解析
                post_details = parse_post_details(page.content())
                content_text = post_details.get("content")

                # 檢查內容是否有效
                if content_text and content_text != "N/A - Not Found":
                    # C1. 成功路徑
                    print(f"  成功抓取: {content_text[:30]}...")
                    db.mark_success(link, content_text) 
                else:
                    raise ValueError("解析結果為空或 Not Found")

            except Exception as e:
                # C2. 失敗路徑
                error_msg = str(e).split('\n')[0] # 只取第一行錯誤訊息
                print(f"  發生錯誤: {error_msg}")
                db.mark_fail(link, error_msg, MAX_RETRIES)

            # D. 隨機休息 (避免被偵測)
            time.sleep(random.uniform(PAUSE_MIN, PAUSE_MAX))

        context.close()

if __name__ == "__main__":
    main()

