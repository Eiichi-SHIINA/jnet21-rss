import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.aibsc.jp/news/"
OUTPUT_FILE = "aibsc-news.xml"

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
}

EXCLUDE_KEYWORDS = [
    "マネージャーを募集",
    "職員募集",
    "採用",
    "入札",
    "採択企業",
    "採択結果",
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

# 日付が表示されている新着欄のリンクだけを取得
for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    if any(keyword in title for keyword in EXCLUDE_KEYWORDS):
        continue

    href = a.get("href", "").strip()
    url = urljoin(SOURCE_URL, href)

    # 新着記事は support 配下
    if not re.match(
        r"^https://www\.aibsc\.jp/support/\d+/?$",
        url
    ):
        continue

    # 親要素付近に掲載日があるものだけ＝新着欄
    parent_text = ""
    parent = a.parent

    for _ in range(4):
        if parent is None:
            break

        parent_text = parent.get_text(" ", strip=True)

        if re.search(r"20\d{2}-\d{2}-\d{2}", parent_text):
            break

        parent = parent.parent

    if not re.search(r"20\d{2}-\d{2}-\d{2}", parent_text):
        continue

    title = (
        title
        .replace("続きを読む", "")
        .replace("詳細はこちら", "")
        .replace("NEW", "")
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
).text = "あいち産業振興機構 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "あいち産業振興機構の募集・商談会・セミナー・補助金・支援等の新着情報"
)

for title, url in items[:30]:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url

    unique_text = f"{title}|{url}"

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(item, "guid").text = (
        f"urn:aibsc-news:{unique_id}"
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
