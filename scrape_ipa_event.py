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

# 「開催予定・開催中のイベント・セミナー」の見出しを探す
heading = soup.find(
    lambda tag: (
        tag.name in ["h1", "h2", "h3"]
        and "開催予定・開催中のイベント・セミナー"
        in tag.get_text(" ", strip=True)
    )
)

if heading is None:
    raise RuntimeError("イベント一覧の見出しが見つかりません")

# 見出し以降のリンクを順に取得
for a in heading.find_all_next("a", href=True):
    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    # 一覧の終端
    if "イベント・セミナー一覧" in title:
        break

    href = a.get("href", "").strip()

    if not href:
        continue

    url = urljoin(SOURCE_URL, href)
    parsed = urlparse(url)

    # IPA内のHTMLページだけ
    if parsed.netloc != "www.ipa.go.jp":
        continue

    if not parsed.path.endswith(".html"):
        continue

    # 申込状況・カテゴリ・日付などを含む長い表示から
    # 余分な先頭ラベルだけ軽く除去
    title = re.sub(
        r"^(申込受付中|申込終了)\s+",
        "",
        title
    )

    title = re.sub(r"\s+", " ", title).strip()

    if len(title) < 8:
        continue

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
