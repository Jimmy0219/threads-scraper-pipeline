import sqlite3
from datetime import datetime
from config import (
    DB_NAME
)

class ThreadsDB:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    def _connect(self):
        """內部使用的連線 helper"""
        return sqlite3.connect(self.db_name)

    def initialize(self):
        """
        初始化資料庫：
        1. 建立基礎資料表 (如果不存在)
        2. 確保所有 Phase 2 需要的欄位都存在 (Migration)
        """
        conn = self._connect()
        cursor = conn.cursor()

        # 1. 建立基礎表結構 (包含所有欄位，一步到位)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                link TEXT PRIMARY KEY,
                status INTEGER DEFAULT 0,
                keyword TEXT,
                created_at TIMESTAMP,
                content TEXT,
                retry_count INTEGER DEFAULT 0,
                error_log TEXT,
                updated_at TIMESTAMP
            )
        ''')

        # 2. 檢查並補齊欄位 (為了相容舊有的 DB 檔案)
        # 這裡保留你原本的防呆邏輯
        cursor.execute("PRAGMA table_info(search_results)")
        current_columns = [info[1].lower() for info in cursor.fetchall()]
        
        columns_to_ensure = [
            ("content", "TEXT"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("error_log", "TEXT"),
            ("updated_at", "TIMESTAMP")
        ]

        for col_name, col_type in columns_to_ensure:
            if col_name.lower() not in current_columns:
                try:
                    cursor.execute(f"ALTER TABLE search_results ADD COLUMN {col_name} {col_type}")
                    print(f"[DB] 自動補上欄位: {col_name}")
                except sqlite3.OperationalError:
                    pass

        conn.commit()
        conn.close()

    # --- Phase 1 相關方法 ---

    def get_keyword_count(self, keyword):
        """取得特定關鍵字的目前抓取總數"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE keyword = ?", (keyword,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def add_links(self, links, keyword):
        """
        批次寫入連結
        回傳: 實際新增的筆數 (用於判斷是否到底)
        """
        if not links:
            return 0
        
        conn = self._connect()
        cursor = conn.cursor()
        
        # 記錄寫入前的數量
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE keyword = ?", (keyword,))
        count_before = cursor.fetchone()[0]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 準備資料: link, status=0, keyword, created_at
        data_to_insert = [(link, 0, keyword, now) for link in links]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO search_results (link, status, keyword, created_at)
            VALUES (?, ?, ?, ?)
        ''', data_to_insert)
        
        conn.commit()
        
        # 計算實際新增數量
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE keyword = ?", (keyword,))
        count_after = cursor.fetchone()[0]
        conn.close()
        
        return count_after - count_before

    # --- Phase 2 相關方法 ---

    def get_pending_task(self):
        """領取一筆待處理 (status=0) 的任務"""
        conn = self._connect()
        cursor = conn.cursor()
        # 這裡可以考慮加上 ORDER BY RANDOM() 或是 created_at DESC
        cursor.execute("SELECT link FROM search_results WHERE status = 0 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def mark_success(self, link, content):
        """標記任務成功"""
        conn = self._connect()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE search_results 
            SET status = 1, content = ?, updated_at = ? 
            WHERE link = ?
        ''', (content, now, link))
        conn.commit()
        conn.close()

    def mark_fail(self, link, error_msg, max_retries=3):
        """
        標記任務失敗
        自動處理 retry_count 邏輯：
        - 如果重試次數未達上限 -> status 保持 0 (重試)
        - 如果超過上限 -> status 設為 -1 (永久失敗)
        """
        conn = self._connect()
        cursor = conn.cursor()
        
        # 查詢目前重試次數
        cursor.execute("SELECT retry_count FROM search_results WHERE link = ?", (link,))
        result = cursor.fetchone()
        current_retry = result[0] if result else 0
        new_retry = current_retry + 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if new_retry >= max_retries:
            # 永久失敗
            status_code = -1
            print(f"   -> [DB] 此連結已失敗 {new_retry} 次，標記為永久失敗 (-1)。")
        else:
            # 稍後重試
            status_code = 0
            print(f"   -> [DB] 失敗紀錄 (第 {new_retry} 次)，保留重試。")

        cursor.execute('''
            UPDATE search_results 
            SET status = ?, retry_count = ?, error_log = ?, updated_at = ?
            WHERE link = ?
        ''', (status_code, new_retry, error_msg, now, link))
        
        conn.commit()
        conn.close()

    def get_stats(self):
        """取得進度統計"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM search_results GROUP BY status")
        stats = dict(cursor.fetchall()) 
        conn.close()
        return stats