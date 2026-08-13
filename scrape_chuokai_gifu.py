import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-gifu.or.jp/chuokai/news/news_new.html"
OUTPUT_FILE = "chuokai-gifu-news.xml"

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

SubElement(channel, "title").text = "岐阜県中小企業団体中央会 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "岐阜県中小企業団体中央会 掲載情報"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title or title == "）":
        parent = a.parent

        if parent is not None:
            title = parent.get_text(" ", strip=True)

    if not title:
        continue

    title = re.sub(r"\s+", " ", title).strip()

    href = a.get("href", "")
    url = urljoin(SOURCE_URL, href)

    # 2026年の個別記事・PDF等を対象
    if "/chuokai/news/2026/" not in url:
        continue

    # 年度一覧ページなどは除外
    if url.endswith("news_new.html"):
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
