# --- 設定區 ---

# 共同設定參數
# 檔案與資料庫路徑
COOKIES_FILE = "cookies.js"
DB_NAME = "Threads_crawler_database.db"

# 瀏覽器設定
HEADLESS = True                # 是否以無頭模式運行瀏覽器

# main_phase1.py 中會用到的設定參數
# 搜尋設定
SEARCH_KEYWORD = "筆電推薦"
TARGET_URL = "https://www.threads.com/search?q=%E7%AD%86%E9%9B%BB%E6%8E%A8%E8%96%A6&serp_type=default&hl=zh-tw"

# 爬蟲行為設定
TARGET_Total_COUNT = 1000      # 貼文連結目標數量
BATCH_SIZE = 100            # 每多少筆存一個檔案
SCROLL_PAUSE_TIME = 5.0      # 每次滾動後的等待時間 (秒)
STABILITY_THRESHOLD = 10      # 如果連續N次滾動後連結數沒增加，就判斷為已到底部

#main_phase2.py 中會用到的設定參數
# 爬蟲行為設定
MAX_RETRIES = 3                   # 最大重試次數，超過則標記為失敗 (-1)
PAUSE_MIN = 3                     # 隨機休息時間下限 (秒)
PAUSE_MAX = 8                     # 隨機休息時間上限 (秒)
# 父層選擇器
CONTENT_SELECTOR = "div.x1n2onr6.x1f9n5g.x17dsfyh.xzzag5r.x1losyl9.xsag5q8.x1iorvi4.x1sqbtui"
# 內文子層部分 class 字串
PARTIAL_CONTENT_CLASS = "x1lliihq x1plvlek xryxfnj x1n2onr6 xyejjpt x15dsfln xi7mnp6 x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xjohtrz xo1l8bm xp07o12 x1yc453h xat24cr"