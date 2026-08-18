import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://yorozu-miyazaki.go.jp/consultation"
OUTPUT_FILE = "yorozu-miyazaki-consultation.xml"
MAX_ITEMS = 30

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
seen_urls = set()

for a in soup.find_all("a", href=True):
    href = a.get("href", "").strip()

    if not href:
        continue

    url = urljoin(SOURCE_URL, href)
    parsed = urlparse(url)

    # 宮崎県よろず支援拠点サイト内だけ
    if parsed.netloc != "yorozu-miyazaki.go.jp":
        continue

    # 相談会の詳細ページだけ
    if not re.match(r"^/consultation/\d+\.html$", parsed.path):
        continue

    if url in seen_urls:
        continue

    # 「詳細を見る」リンクを含む掲載ブロックから相談会名を取得
    title = ""

    parent = a

    for _ in range(6):
        parent = parent.parent

        if parent is None:
            break

        heading = parent.find(["h2", "h3", "h4", "h5"])

        if heading:
            candidate = heading.get_text(" ", strip=True)
            candidate = re.sub(r"\s+", " ", candidate).strip()

            if candidate and candidate != "CONSULTATION 相談会":
                title = candidate
                break

    if not title:
        continue

    seen_urls.add(url)
    items.append((title, url))

if not items:
    raise RuntimeError("RSS対象を1件も取得できませんでした")

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(
    channel,
    "title"
).text = "宮崎県よろず支援拠点 定期相談会"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "宮崎県よろず支援拠点の定期相談会情報"

for title, url in items[:MAX_ITEMS]:
    item = SubElement(channel, "item")

    SubElement(
        item,
        "title"
    ).text = title

    SubElement(
        item,
        "link"
    ).text = url

    unique_id = hashlib.sha256(
        f"{title}|{url}".encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = f"urn:yorozu-miyazaki-consultation:{unique_id}"

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(items[:MAX_ITEMS])
)
