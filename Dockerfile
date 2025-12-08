# 使用微軟官方提供的 Playwright Python 映像檔 (這已包含 Python 和 瀏覽器環境)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

ENV PYTHONUNBUFFERED=1

# 設定工作目錄
WORKDIR /app

# 將當前目錄的所有檔案複製到容器內的 /app
COPY . /app

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 需要的瀏覽器 (Chromium)
RUN playwright install chromium

# 設定容器啟動時執行的指令
# 這裡假設我們要跑 main_phase1.py，你可以根據需求改成你的主程式
# 注意：在雲端執行時，記得要用 Headless 模式 (你的程式碼預設應該要是 True)
CMD ["python", "main_phase1.py"]