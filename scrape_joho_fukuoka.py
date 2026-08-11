import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.joho-fukuoka.or.jp/info.html"
OUTPUT_FILE = "joho-fukuoka-info.xml"

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

SubElement(channel, "title").text = "福岡県中小企業振興センター お知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "福岡県中小企業振興センター センターからのお知らせ"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    parent = a.parent
    if parent is None:
        continue

    text = parent.get_text(" ", strip=True)

    # 記事の周辺に YYYY.M.D / YYYY.MM.DD 形式の日付があるものだけ対象
    if not re.search(r"\b20\d{2}\.\d{1,2}\.\d{1,2}\b", text):
        continue

    # 「詳細はこちら」など本文中の補助リンクは除外
    if title.startswith("詳細"):
        continue

    if title in [
        "ホーム",
        "センターからのお知らせ",
        "トップへ戻る",
    ]:
        continue

    url = urljoin(SOURCE_URL, a["href"])

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
