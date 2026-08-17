import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://yorozu-okayama.go.jp/category/news/"
BASE_URL = "https://yorozu-okayama.go.jp/"
OUTPUT_FILE = "yorozu-okayama-news.xml"

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

EXCLUDE_KEYWORDS = [
    "コーディネーター募集",
    "サポーターの公募",
    "採用",
    "業務委託",
]

session = requests.Session()
session.headers.update(HEADERS)

response = session.get(
    SOURCE_URL,
    timeout=60,
    allow_redirects=True,
)

print("status:", response.status_code)
print("final_url:", response.url)

response.raise_for_status()

# 127.0.0.1 等へ飛ばされた場合は明示的に失敗させる
if "127.0.0.1" in response.url or "localhost" in response.url:
    raise RuntimeError(
        f"Unexpected redirect: {response.url}"
    )

response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

items = []
seen = set()

for article in soup.find_all("article"):

    a = article.find("a", href=True)

    if a is None:
        continue

    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    if any(keyword in title for keyword in EXCLUDE_KEYWORDS):
        continue

    href = a.get("href", "").strip()

    if not href:
        continue

    url = urljoin(SOURCE_URL, href)

    if not url.startswith(BASE_URL):
        continue

    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    title = (
        title
        .replace("続きを読む", "")
        .replace("コメントを受け付けていません", "")
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
).text = "岡山県よろず支援拠点 お知らせ"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "岡山県よろず支援拠点のお知らせ・支援情報"
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
    ).text = f"urn:yorozu-okayama-news:{unique_id}"

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(items[:30])
)
