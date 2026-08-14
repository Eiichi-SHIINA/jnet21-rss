import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.nta.go.jp/information/news/index.htm"
OUTPUT_FILE = "nta-topics.xml"

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
    r"令和\s*([0-9０-９]+)年\s*([0-9０-９]+)月\s*([0-9０-９]+)日"
)

items = []
seen = set()

def to_ascii_number(text):
    return int(
        text.translate(
            str.maketrans("０１２３４５６７８９", "0123456789")
        )
    )

for text_node in soup.find_all(string=True):

    text = re.sub(
        r"\s+",
        " ",
        str(text_node)
    ).strip()

    match = date_pattern.search(text)

    if not match:
        continue

    era_year = to_ascii_number(match.group(1))
    month = to_ascii_number(match.group(2))
    day = to_ascii_number(match.group(3))

    year = era_year + 2018
    date_text = match.group()

    # 日付の次にある記事リンクを取得
    a = text_node.parent.find_next(
        "a",
        href=True
    )

    if a is None:
        continue

    title = a.get_text(
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

    href = a.get("href", "")

    if not href or href.startswith("#"):
        continue

    url = urljoin(
        SOURCE_URL,
        href
    )

    if url.startswith("javascript:"):
        continue

    # 一覧やナビゲーションを除外
    if title in {
        "トピックス一覧",
        "トップページ",
        "詳細はこちら",
    }:
        continue

    key = (
        date_text,
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

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
).text = "国税庁 トピックス"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "国税庁 トピックス一覧"

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
        f"urn:nta-topics:{unique_id}"
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
