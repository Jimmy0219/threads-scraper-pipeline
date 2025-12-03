# threads_scraper/save_cookies.py
# -*- coding: utf-8 -*-
"""
save_cookies.py
- 使用 Playwright 啟動瀏覽器，導向 Threads 登入頁。
- 使用者手動完成登入後，腳本會自動偵測。
- 成功後，過濾出 Threads 相關的 cookies，並儲存為 Playwright 可直接使用的 `cookies.js` 格式。
"""
import json
import time
from playwright.sync_api import sync_playwright

# ===================== 固定參數 =====================
LOGIN_URL = "https://www.threads.net/login"
OUTPUT_PATH = "cookies.js"  # 輸出符合專案需求的 cookies.js
CHECK_INTERVAL = 3  # 每隔 3 秒檢查一次登入狀態
# ===================================================

def is_logged_in(context) -> bool:
    """以 'sessionid' cookie 判斷是否已登入"""
    for cookie in context.cookies():
        if cookie.get("name") == "sessionid" and cookie.get("value"):
            return True
    return False

def save_threads_cookies(context, path: str):
    """過濾並儲存 Threads 的 Cookies 為 Playwright 適用的 JS 格式"""
    all_cookies = context.cookies()
    
    # Playwright 的 cookies() 回傳的 domain key 會包含前面的 "."，所以過濾時要留意
    threads_cookies = [
        c for c in all_cookies
        if '.threads.net' in c.get('domain', '') or '.threads.com' in c.get('domain', '')
    ]

    # 寫入 Playwright context_state 需要的 JS 格式 (module.exports)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(threads_cookies, f, indent=2, ensure_ascii=False)

    print(f"✅ 成功儲存 {len(threads_cookies)} 筆 Threads cookies 到：{path}")

def main():
    with sync_playwright() as p:
        print(f"💾 目標檔案：{OUTPUT_PATH}")
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("➡️  開啟 Threads 登入頁...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            print("📝 請在開啟的瀏覽器視窗中手動登入 Threads。")
            print("   登入成功後，腳本會自動偵測並儲存 cookies。")

            while not is_logged_in(context):
                print("   ...等待登入中...")
                time.sleep(CHECK_INTERVAL)

            print("\n✅ 偵測到登入成功！")
            save_threads_cookies(context, OUTPUT_PATH)

        except KeyboardInterrupt:
            print("\n⏹️  流程被手動中斷（Ctrl+C），未儲存 cookies。")
        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
        finally:
            print("🚪 關閉瀏覽器。")
            browser.close()

if __name__ == "__main__":
    main()
