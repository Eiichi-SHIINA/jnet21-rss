import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.tohoku.meti.go.jp/koho/koshin/archive.html"
OUTPUT_FILE = "tohoku-meti-news.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.tohoku.meti.go.jp/",
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
    r"20\d{2}年\d{2}月\d{2}日"
)

items = []
seen = set()
current_date = None

for tag in soup.find_all(["p", "li", "dt", "dd", "a", "span", "div"]):

    text = tag.get_text(
        " ",
        strip=True
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    date_match = date_pattern.fullmatch(text)

    if date_match:
        current_date = date_match.group()
        continue

    if current_date is None:
        continue

    if tag.name != "a":
        continue

    href = tag.get("href", "")

    if not href or href.startswith("#"):
        continue

    title = tag.get_text(
        " ",
        strip=True
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    ).strip()

    if not title:
        continue

    if title in {
        "ホーム",
        "トピックス一覧",
        "2026年度",
        "2025年度",
        "2024年度",
        "2023年度",
    }:
        continue

    url = urljoin(
        SOURCE_URL,
        href
    )

    if url.startswith("javascript:"):
        continue

    key = (
        current_date,
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

    m = re.match(
        r"(\d{4})年(\d{2})月(\d{2})日",
        current_date
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
            current_date,
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
).text = "東北経済産業局 トピックス"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "東北経済産業局 トピックス一覧"

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
        f"urn:tohoku-meti:{unique_id}"
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
