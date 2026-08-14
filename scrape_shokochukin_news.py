import re
import hashlib
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

BASE_URL = "https://www.shokochukin.co.jp/news/"
CURRENT_YEAR = datetime.now().year
SOURCE_URL = f"{BASE_URL}{CURRENT_YEAR}/"
OUTPUT_FILE = "shokochukin-news.xml"

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

date_pattern = re.compile(
    r"20\d{2}年\d{1,2}月\d{1,2}日"
)

items = []
seen = set()

for a in soup.find_all("a", href=True):
    text = a.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    match = date_pattern.search(text)

    if not match:
        continue

    date_text = match.group()

    title = text.replace(date_text, "", 1).strip()

    # PDF容量などの表記はそのままでもよいが、
    # 先頭の余分な空白だけ整理
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    href = a.get("href", "")

    if not href or href.startswith("#"):
        continue

    url = urljoin(
        SOURCE_URL,
        href
    )

    key = (
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

    m = re.match(
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        date_text
    )

    if not m:
        continue

    year, month, day = map(
        int,
        m.groups()
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

rss = Element(
    "rss",
    version="2.0"
)

channel = SubElement(
    rss,
    "channel"
)

SubElement(
    channel,
    "title"
).text = "商工中金 お知らせ"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "商工中金 お知らせ"

for date_key, date_text, title, url in items[:30]:

    item = SubElement(
        channel,
        "item"
    )

    SubElement(
        item,
        "title"
    ).text = title

    SubElement(
        item,
        "link"
    ).text = url

    unique_text = (
        f"{date_text}|{title}|{url}"
    )

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = (
        f"urn:shokochukin-news:{unique_id}"
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
