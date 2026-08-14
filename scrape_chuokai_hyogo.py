import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai.com/info/"
OUTPUT_FILE = "chuokai-hyogo-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(
    SOURCE_URL,
    headers=HEADERS,
    timeout=60,
)
response.raise_for_status()

response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "兵庫県中小企業団体中央会 お知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "兵庫県中小企業団体中央会 お知らせ"

items = []
seen = set()

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    # 一覧の「続きを読む」などは除外
    if title in {
        "続きを読む",
        "詳しく見る",
        "MORE",
        "more",
    }:
        continue

    href = a.get("href", "")
    if not href or href.startswith("#"):
        continue

    url = urljoin(SOURCE_URL, href)

    # 兵庫県中央会サイト内の記事だけを対象
    if not url.startswith("https://www.chuokai.com/"):
        continue

    # 一覧・カテゴリ・固定ページ等を除外
    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    if any(
        part in url
        for part in [
            "/category/",
            "/tag/",
            "/author/",
            "/page/",
            "/wp-content/",
        ]
    ):
        continue

    # 明らかなナビゲーションを除外
    if title in {
        "ホーム",
        "お知らせ",
        "お問い合わせ",
        "中央会概要",
    }:
        continue

    key = (title, url)

    if key in seen:
        continue

    seen.add(key)

    items.append(
        (
            title,
            url,
        )
    )

for title, url in items[:30]:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url

    unique_text = f"{title}|{url}"
    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(item, "guid").text = (
        f"urn:chuokai-hyogo:{unique_id}"
    )

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(items[:30])
)
