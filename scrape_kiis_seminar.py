import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.kiis.or.jp/seminar/"
OUTPUT_FILE = "kiis-seminar.xml"

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
    title = a.get_text(" ", strip=True)
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

    # 一覧ページ自身やナビゲーションを除外
    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    if title in {
        "ホーム",
        "トップページ",
        "セミナー・イベント情報",
        "お問い合わせ",
        "アクセス",
        "プライバシーポリシー",
    }:
        continue

    # KIISのセミナー詳細・申込に関係するリンクを優先
    if not (
        "/form/" in url
        or "secure.kiis.or.jp" in url
        or "/seminar/" in url
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
).text = "関西情報センター KIIS セミナー・イベント情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "一般財団法人関西情報センター セミナー・イベント情報"

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
        f"urn:kiis-seminar:{unique_id}"
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
