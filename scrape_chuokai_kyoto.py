import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-kyoto.or.jp/news/information/"
OUTPUT_FILE = "chuokai-kyoto-news.xml"

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

SubElement(channel, "title").text = "京都府中小企業団体中央会 中央会からのお知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "京都府中小企業団体中央会 中央会からのお知らせ"

date_pattern = re.compile(
    r"20\d{2}年\d{1,2}月\d{1,2}日"
)

items = []
seen = set()

for text_node in soup.find_all(string=date_pattern):
    match = date_pattern.search(str(text_node))

    if not match:
        continue

    date_text = match.group()

    # 日付の後にある最初の記事リンク
    a = text_node.find_next("a", href=True)

    if a is None:
        continue

    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    href = a.get("href", "")

    if not href or href.startswith("#"):
        continue

    url = urljoin(SOURCE_URL, href)

    # 個別記事・PDFなどはそのまま許可
    # 月別アーカイブや一覧ページ自身は除外
    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    if re.search(r"/news/information/\d{4}/\d{2}/?$", url):
        continue

    key = (
        date_text,
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

    date_match = re.match(
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        date_text
    )

    if not date_match:
        continue

    year, month, day = map(
        int,
        date_match.groups()
    )

    date_key = (
        year * 10000
        + month * 100
        + day
    )

    items.append(
        (
            date_key,
            date_text,
            title,
            url,
        )
    )

items.sort(
    key=lambda x: x[0],
    reverse=True
)

for date_key, date_text, title, url in items[:30]:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url

    unique_text = f"{date_text}|{title}|{url}"
    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(item, "guid").text = (
        f"urn:chuokai-kyoto:{unique_id}"
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
