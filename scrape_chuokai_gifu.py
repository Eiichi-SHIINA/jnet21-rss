import re
import hashlib
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

items = []
seen = set()

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    title = re.sub(r"\s+", " ", title).strip()

    match = re.search(
        r"20\d{2}\.\d{1,2}\.\d{1,2}",
        title
    )

    if not match:
        continue

    # 「日付だけ」「）」だけ等の補助リンクを除外
    title_without_date = re.sub(
        r"[（(]?\s*20\d{2}\.\d{1,2}\.\d{1,2}\s*[）)]?",
        "",
        title
    ).strip(" 　（）()、,")

    if len(title_without_date) < 5:
        continue

    href = a.get("href", "")

    if not href or href.startswith("#"):
        continue

    url = urljoin(SOURCE_URL, href)

    # 完全に同じ項目だけ重複除外
    key = (title, url)

    if key in seen:
        continue

    seen.add(key)

    year, month, day = map(
        int,
        match.group().split(".")
    )

    date_key = year * 10000 + month * 100 + day

    items.append(
        (date_key, title, url)
    )

items.sort(
    key=lambda x: x[0],
    reverse=True
)

for date_key, title, url in items[:30]:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url

    unique_text = f"{url}|{title}"
    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(item, "guid").text = (
        f"urn:chuokai-gifu:{unique_id}"
    )

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, len(items[:30]))
