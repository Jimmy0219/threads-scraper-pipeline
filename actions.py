import json
from playwright.sync_api import sync_playwright, BrowserContext, Page

# 載入cookies的函式
def get_browser_context(p: sync_playwright, cookies_file: str) -> BrowserContext:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)

    try:
        with open(cookies_file, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print("Cookies 載入成功")
    except Exception as e:
        print(f"Cookies 載入失敗: {e}")
        raise e 

    return context

# 等待頁面主要內容載入的函式
def wait_for_main_content(page: Page, timeout: int) -> bool:
    try:
        main_content_area = page.get_by_label("直欄內文")
        main_content_area.wait_for(timeout=timeout * 1000)
        print("內容區塊已成功載入")
        return True
    except Exception:
        print(f"等待超時 ({timeout}秒)，找不到指定的內容區塊。")
        return False