import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.joho-kochi.or.jp/center/bkno_2026.php"
OUTPUT_FILE = "joho-kochi-news.xml"

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

SubElement(channel, "title").text = "高知県産業振興センター 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "高知県産業振興センター 2026年度新着情報"

seen = set()
count = 0
started = False

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    # 過年度バックナンバーを除外
    if re.match(r"^R\d+年度$", title):
        break

    # 本文の更新情報エリア開始位置
    if title == "補助金・融資など":
        started = True
        continue

    if not started:
        continue

    # ページ内のカテゴリ移動リンクは除外
    if title in [
        "セミナー・イベント",
        "その他お知らせ",
    ]:
        continue

    href = a.get("href", "")

    # ページ内アンカーやナビゲーションを除外
    if href.startswith("#"):
        continue

    url = urljoin(SOURCE_URL, href)

    if url == SOURCE_URL:
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
