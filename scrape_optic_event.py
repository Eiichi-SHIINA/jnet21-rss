import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.optic.or.jp/event/event_search/index.html"
BASE_URL = "https://www.optic.or.jp/"
OUTPUT_FILE = "optic-event.xml"

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
}

EXCLUDE_KEYWORDS = [
    "募集終了",
    "受付終了",
    "開催終了",
    "開催報告",
]

response = requests.get(
    SOURCE_URL,
    headers=HEADERS,
    timeout=60,
)
response.raise_for_status()

response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

items = []
seen = set()

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    if any(keyword in title for keyword in EXCLUDE_KEYWORDS):
        continue

    href = a.get("href", "").strip()

    if not href:
        continue

    url = urljoin(SOURCE_URL, href)

    # イベント詳細だけ
    if not re.match(
        r"^https://www\.optic\.or\.jp/event/event_detail/index/\d+\.html$",
        url
    ):
        continue

    title = (
        title
        .replace("NEW", "")
        .replace("詳細", "")
        .strip()
    )

    title = re.sub(r"\s+", " ", title).strip()

    key = (title, url)

    if key in seen:
        continue

    seen.add(key)
    items.append((title, url))

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(
    channel,
    "title"
).text = "岡山県産業振興財団 イベント情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "岡山県産業振興財団のセミナー・商談会・研修・募集等のイベント情報"
)

for title, url in items[:30]:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url

    unique_id = hashlib.sha256(
        f"{title}|{url}".encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = f"urn:optic-event:{unique_id}"

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(items[:30])
)
