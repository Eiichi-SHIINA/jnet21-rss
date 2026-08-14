import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.jemai.or.jp/"
OUTPUT_FILE = "jemai-news.xml"

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

exclude_words = [
    "環境省からのお知らせ",
    "関係団体からのお知らせ",
    "会員企業からのお知らせ",
]

items = []
seen = set()

for a in soup.find_all("a", href=True):

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

    # JEMAI自身のページだけを基本対象にする
    parsed = urlparse(url)

    if parsed.netloc not in {
        "www.jemai.or.jp",
        "jemai.or.jp",
        "www.e-jemai.jp",
        "e-jemai.jp",
    }:
        continue

    # リンク周辺のブロックを取得
    block = a

    for _ in range(4):
        if block.parent is None:
            break

        block = block.parent

        block_text = block.get_text(
            " ",
            strip=True
        )

        block_text = re.sub(
            r"\s+",
            " ",
            block_text
        ).strip()

        date_match = date_pattern.search(
            block_text
        )

        if date_match:
            break

    if not date_match:
        continue

    # 他団体由来の案内を除外
    if any(
        word in block_text
        for word in exclude_words
    ):
        continue

    date_text = date_match.group()

    # ナビゲーションや固定メニューを除外
    if title in {
        "過去の情報",
        "過去の情報>>",
        "詳細はこちら",
        "こちら",
        "トップページ",
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
).text = "産業環境管理協会 JEMAI 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "産業環境管理協会による募集・セミナー・事業等の新着情報"

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
        f"urn:jemai-news:{unique_id}"
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
