import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

OUTPUT_FILE = "tokyo-chuokai-news.xml"

PAGES = [
    "https://www.tokyochuokai.or.jp/flashpast/flash-2026.html",
    "https://www.tokyochuokai.or.jp/hotnews/hot-2026.html",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "東京都中小企業団体中央会 新着情報"
SubElement(channel, "link").text = "https://www.tokyochuokai.or.jp/"
SubElement(channel, "description").text = "東京都中小企業団体中央会 中央会Flash・Hot News"

items = []
seen = set()

for page_url in PAGES:
    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)

        if not title:
            continue

        # 記事周辺に日付があるものだけ取得
        parent = a
        found_date = None

        for _ in range(4):
            parent = parent.parent

            if parent is None:
                break

            text = parent.get_text(" ", strip=True)

            match = re.search(
                r"20\d{2}年\d{2}月\d{2}日",
                text
            )

            if match:
                found_date = match.group()
                break

        if not found_date:
            continue

        href = a.get("href", "")

        if href.startswith("#"):
            continue

        url = urljoin(page_url, href)

        # 一覧ページ自身などを除外
        if url in PAGES:
            continue

        if url in seen:
            continue

        seen.add(url)

        date_key = found_date.replace("年", "").replace("月", "").replace("日", "")

        items.append(
            (date_key, title, url)
        )

# FlashとHot Newsを日付順にまとめる
items.sort(
    key=lambda x: x[0],
    reverse=True
)

for date_key, title, url in items[:30]:
    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, len(items[:30]))
