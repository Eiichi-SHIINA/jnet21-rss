import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.tec-lab.pref.gunma.jp/"
BASE_URL = "https://www.tec-lab.pref.gunma.jp/"
OUTPUT_FILE = "gunma-tec-news.xml"

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

KEYWORDS = [
    "公募",
    "募集",
    "参加企業",
    "支援",
    "受付開始",
    "申込受付",
    "補助金",
    "補助事業",
]

EXCLUDE_KEYWORDS = [
    "入札",
    "採用",
    "職員",
    "インターンシップ",
    "利用受付停止",
    "予約停止",
    "復旧",
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

    # 公募・募集・支援等だけ残す
    if not any(keyword in title for keyword in KEYWORDS):
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

    # セミナーは別RSSで監視するため除外
    if "/seminar/" in url:
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

    # 表示上の余計な文言を削除
    title = title.replace(
        "open_in_new",
        ""
    ).strip()

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
).text = "群馬県立産業技術センター 公募・募集・支援情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "群馬県立産業技術センターの公募・募集・支援等の情報"
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
        f"urn:gunma-tec-news:{unique_id}"
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
