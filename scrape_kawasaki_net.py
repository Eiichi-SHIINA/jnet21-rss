import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.kawasaki-net.ne.jp/news/"
BASE_URL = "https://www.kawasaki-net.ne.jp/"
OUTPUT_FILE = "kawasaki-net-news.xml"

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
    "採用情報",
    "職員募集",
    "入札",
    "開催結果",
    "結果発表",
    "開催報告",
    "システムメンテナンス",
    "休館",
    "PODCAST",
]

EXCLUDE_PATHS = [
    "/about/",
    "/business/",
    "/access/",
    "/contact/",
    "/news/",
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

    if href.startswith("#"):
        continue

    if href.startswith("javascript:"):
        continue

    url = urljoin(SOURCE_URL, href)
    parsed = urlparse(url)

    # 川崎市産業振興財団ドメイン内だけ
    if parsed.netloc != "www.kawasaki-net.ne.jp":
        continue

    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    # ナビゲーション・固定ページを除外
    if any(parsed.path.startswith(path) for path in EXCLUDE_PATHS):
        continue

    # お知らせ詳細記事だけを対象
    if not re.match(
        r"^/info\d{8}(?:-\d+)?/?$",
        parsed.path
    ):
        continue

    if url.lower().endswith((
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    )):
        continue

    if len(title) < 8:
        continue

    title = (
        title
        .replace("詳細はこちら", "")
        .replace("open_in_new", "")
        .strip()
    )

    # 先頭のカテゴリ・日付を削除
    title = re.sub(
        r"^(お知らせ|セミナー・イベント)\s+\d{4}\.\d{2}\.\d{2}\s+",
        "",
        title
    )

    # 更新案内以降の本文を削除
    title = re.split(
        r"\s+(?:"
        r"イベントページを更新しました。"
        r"|イベントの開催情報を掲載しました"
        r"|令和8年熊本地震の発生に伴い"
        r"|クレジットカード売上の早期決済代行サービス"
        r"|「九都県市合同商談会in幕張メッセ2027」"
        r"|昨年度に好評だった"
        r")",
        title,
        maxsplit=1,
    )[0]

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
).text = "川崎市産業振興財団 お知らせ"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "川崎市産業振興財団のセミナー・イベント・募集・支援等の情報"
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
        f"urn:kawasaki-net:{unique_id}"
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
