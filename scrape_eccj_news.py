import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.eccj.or.jp/whatsnewj/"
OUTPUT_FILE = "eccj-news.xml"

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
    r"20\d{2}[./年]\d{1,2}[./月]\d{1,2}日?"
)

items = []
seen = set()

for text_node in soup.find_all(string=date_pattern):

    match = date_pattern.search(
        str(text_node)
    )

    if not match:
        continue

    date_text = match.group()

    # 日付の直後にある最初のリンクを取得
    a = text_node.find_next(
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

    # 明らかな補助リンク・ナビゲーションを除外
    if title in {
        "ECCJ Home",
        "省エネ人材育成Top",
        "講座案内",
        "ホームページ",
        "こちら",
        "ホームページをご覧ください。",
        "人材公募のページ",
        "新着情報トップ",
        "過去の新着情報",
    }:
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

    # 日付を並び替え用に数値化
    normalized = (
        date_text
        .replace("年", "/")
        .replace("月", "/")
        .replace("日", "")
        .replace(".", "/")
    )

    parts = normalized.split("/")

    if len(parts) != 3:
        continue

    year, month, day = map(
        int,
        parts
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
).text = "省エネルギーセンター 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "一般財団法人省エネルギーセンター 新着情報"

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
        f"urn:eccj-news:{unique_id}"
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
