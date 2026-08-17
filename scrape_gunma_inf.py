import re
import ssl
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.g-inf.or.jp/"
BASE_URL = "https://www.g-inf.or.jp/"
OUTPUT_FILE = "gunma-inf.xml"

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
    "交付決定",
    "採択結果",
    "公募型プロポーザル",
    "業務委託",
    "支援マネージャーの募集",
    "採用",
    "職員募集",
]

class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()

        # 古いTLS設定のサーバーとの互換性を確保
        context.set_ciphers("DEFAULT@SECLEVEL=1")

        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


session = requests.Session()
session.mount("https://", LegacySSLAdapter())

response = session.get(
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

    if not url.startswith(BASE_URL):
        continue

    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
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
        .replace("詳細を見る", "")
        .replace("別ウィンドウで開きます", "")
        .strip()
    )

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
).text = "群馬県産業支援機構 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "群馬県産業支援機構のセミナー・募集・補助金・支援等の新着情報"
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
        f"urn:gunma-inf:{unique_id}"
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
