#匯入模組
from bs4 import BeautifulSoup
from config import (
    CONTENT_SELECTOR,
    PARTIAL_CONTENT_CLASS
)

# 錨定內文所在並解析的函式
def parse_post_details(html_content: str) -> dict:
    soup = BeautifulSoup(html_content, "lxml")
    post_data = {
        "content": "N/A - Not Found" 
    }

    # 1. 錨定父層 div
    # 使用 CSS Selector 語法可以同時指定多個 class
    parent_selector = CONTENT_SELECTOR
    parent_div = soup.select_one(parent_selector)

    if not parent_div:
        print("(警告: 找不到指定的父層 Div，無法繼續解析內文。)")
        return post_data

    # 2. 在父層中尋找子層 span
    # 同樣使用 CSS Selector，注意 class 名稱中的空格要換成點 '.'
    partial_class_string = PARTIAL_CONTENT_CLASS
    child_selector = f'span[class*="{partial_class_string}"]'
    content_spans = parent_div.select(child_selector)

    if content_spans:
        # 使用列表推導式 (List Comprehension) 提取所有 span 的文字
        all_texts = [span.get_text(strip=True) for span in content_spans]
        post_data["content"] = "\n".join(all_texts)
    else:
        print("(警告: 在父層 Div 中找不到指定的內文 Span。)")

    return post_data