import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.tokyochuokai.or.jp/"
OUTPUT_FILE = "tokyo-chuokai-news.xml"

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

SubElement(channel, "title").text = "東京都中小企業団体中央会 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "東京都中小企業団体中央会 中央会Flash・Hot News"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    # リンク周辺に YYYY.MM.DD 形式の日付があるものだけ取得
    parent = a.parent
    if parent is None:
        continue

    text = parent.get_text(" ", strip=True)

    if not re.search(
        r"20\d{2}\.\d{2}\.\d{2}",
        text
    ):
        continue

    href = a.get("href", "")

    if href.startswith("#"):
        continue

    url = urljoin(SOURCE_URL, href)

    # 一覧へのリンクなどを除外
    if "flashpast" in url:
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
