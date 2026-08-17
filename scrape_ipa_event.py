import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.ipa.go.jp/event/events-hold.html"
OUTPUT_FILE = "ipa-event.xml"

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
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

EXCLUDE_PATHS = [
    "/event/events-hold.html",
    "/event/index.html",
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
    href = a.get("href", "").strip()

    if not href:
        continue

    if href.startswith("#"):
        continue

    if href.startswith("javascript:"):
        continue

    url = urljoin(SOURCE_URL, href)
    parsed = urlparse(url)

    # IPAサイト内のHTMLページだけ
    if parsed.netloc != "www.ipa.go.jp":
        continue

    if not parsed.path.endswith(".html"):
        continue

    if parsed.path in EXCLUDE_PATHS:
        continue

    # リンクを含むイベントカード全体の文字列を取得
    card = a

    for _ in range(4):
        parent = card.parent

        if parent is None:
            break

        text = parent.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        # イベントカードらしい要素
        if (
            ("申込受付中" in text or "申込終了" in text)
            and (
                "セミナー" in text
                or "イベント" in text
                or "説明会" in text
                or "演習" in text
                or "講座" in text
            )
        ):
            card = parent
            break

        card = parent

    title = card.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    # イベントカードでないリンクは除外
    if not (
        "申込受付中" in title
        or "申込終了" in title
    ):
        continue

    # 申込状況だけ除去
    title = title.replace("申込受付中", "")
    title = title.replace("申込終了", "")
    title = re.sub(r"\s+", " ", title).strip()

    if len(title) < 8:
        continue

    key = url

    if key in seen:
        continue

    seen.add(key)
    items.append((title, url))

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(
    channel,
    "title"
).text = "IPA イベント・セミナー"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "IPA 情報処理推進機構の開催予定・開催中のイベント・セミナー情報"
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
    ).text = f"urn:ipa-event:{unique_id}"

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(items[:30])
)
