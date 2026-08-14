import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://yorozu-okayama.go.jp/category/news/"
OUTPUT_FILE = "yorozu-okayama-news.xml"

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

    # 同サイト内の個別記事だけを対象
    if "yorozu-okayama.go.jp" not in url:
        continue

    # 一覧ページ自身やページネーションを除外
    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    if re.search(
        r"/news/page/\d+/?$",
        url
    ):
        continue

    if title in {
        "ホーム",
        "お知らせ",
        "一覧を見る",
        "次へ",
        "前へ",
    }:
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
).text = "岡山県よろず支援拠点 お知らせ"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "岡山県よろず支援拠点 お知らせ"

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
        f"urn:yorozu-okayama-news:{unique_id}"
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
