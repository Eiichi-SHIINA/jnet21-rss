import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.jcci.or.jp/news/"
OUTPUT_FILE = "jcci-news.xml"

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

SubElement(channel, "title").text = "日本商工会議所 ニュース"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "日本商工会議所 ニュース"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    href = a.get("href", "")
    url = urljoin(SOURCE_URL, href)

    # 個別ニュース記事らしいURLだけ取得
    if "/news/" not in url:
        continue

    # 一覧・カテゴリページを除外
    if url.endswith("/index.html"):
        continue

    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    # タイトル周辺に日付がある記事だけ対象
    parent = a.parent
    if parent is None:
        continue

    text = parent.get_text(" ", strip=True)

    if not re.search(
        r"20\d{2}年\d{1,2}月\d{1,2}日",
        text
    ):
        continue

    if url in seen:
        continue

    seen.add(url)

    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

    count += 1

    if count >= 30:
        break

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
