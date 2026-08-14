import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.tohoku.meti.go.jp/"
OUTPUT_FILE = "tohoku-meti-news.xml"

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

    # 東北経済産業局内の個別情報を基本対象にする
    if "tohoku.meti.go.jp" not in url:
        continue

    # 固定ナビゲーション等を除外
    if title in {
        "ホーム",
        "新着情報",
        "一覧",
        "詳しくはこちら",
        "過去の新着一覧",
        "サイトマップ",
        "お問い合わせ",
    }:
        continue

    # 個別記事らしいURLだけを対象
    if not re.search(
        r"/(?:topics|kobo|press|oshirase|news|koshin)/.*\.(?:html?|htm)$",
        url
    ):
        continue

    key = (
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

    items.append(
        (
            title,
            url,
        )
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
).text = "東北経済産業局 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "東北経済産業局 新着情報"

for title, url in items[:30]:

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

    unique_text = f"{title}|{url}"

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
