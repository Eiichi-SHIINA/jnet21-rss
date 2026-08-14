import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
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

    # ページネーション除外
    if re.search(
        r"/seminar/\?pages=\d+",
        url
    ):
        continue

    # まず申込フォームは対象
    is_form = bool(
        re.search(
            r"https://www\.kiis\.or\.jp/form/\?id=\d+",
            url
        )
    )

    # secure.kiis.or.jp は、一覧の記事らしい文章だけ対象
    is_secure_event = (
        urlparse(url).netloc == "secure.kiis.or.jp"
        and (
            "開催します" in title
            or "研修" in title
            or "セミナー" in title
        )
    )

    if not (
        is_form
        or is_secure_event
    ):
        continue

    # 共通サービス・ナビゲーション除外
    if title in {
        "関西CIOカンファレンス",
        "ITシンポジウム インフォテック",
        "e-Kansaiレポート",
        "ビジネス・イノベーション・セミナー",
        "サイバーセキュリティ研究会",
        "プライバシーマーク審査員研修",
        "未来創造サロン",
        "先端技術・ビジネス動向研究会（ABIT-Forum）",
        "施設予約",
        "セキュアサポートサービス",
        "Pマーク審査",
        "Pマーク 取得申請",
        "Pマーク取得申請",
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
