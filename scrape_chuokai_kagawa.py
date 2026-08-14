import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-kagawa.or.jp/chuokai/"
OUTPUT_FILE = "chuokai-kagawa-news.xml"

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
    r"20\d{2}/\d{1,2}/\d{1,2}"
)

items = []
seen = set()

# TOPICS を起点にする
start_text = soup.find(
    string=lambda s: s and "TOPICS" in s
)

if start_text is None:
    raise RuntimeError(
        "TOPICSが見つかりませんでした"
    )

for a in start_text.find_all_next("a", href=True):

    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    # リンク周辺から掲載日を探す
    parent = a.parent

    if parent is None:
        continue

    parent_text = parent.get_text(" ", strip=True)
    match = date_pattern.search(parent_text)

    if not match:
        continue

    date_text = match.group()

    href = a.get("href", "")

    if not href or href.startswith("#"):
        continue

    url = urljoin(
        SOURCE_URL,
        href
    )

    # NEW等がタイトル末尾に入った場合は除去
    title = re.sub(
        r"\s*NEW\s*$",
        "",
        title,
        flags=re.IGNORECASE
    ).strip()

    if not title:
        continue

    key = (
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

    year, month, day = map(
        int,
        date_text.split("/")
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
).text = "香川県中小企業団体中央会 TOPICS"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "香川県中小企業団体中央会 TOPICS"

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

    unique_text = f"{date_text}|{title}|{url}"

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = (
        f"urn:chuokai-kagawa:{unique_id}"
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
