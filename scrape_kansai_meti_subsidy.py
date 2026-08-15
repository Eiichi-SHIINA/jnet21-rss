import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.kansai.meti.go.jp/koubo.html"
BASE_URL = "https://www.kansai.meti.go.jp/"
OUTPUT_FILE = "kansai-meti-subsidy.xml"

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

EXCLUDE_TITLES = {
    "本文へ",
    "局のご案内",
    "電話番号案内",
    "相談窓口",
    "トップページ",
    "申請・届出",
    "公募情報",
    "施策のご案内",
    "イベント",
    "入札・調達",
    "統計・経済動向",
    "ウェブサイト利用規約",
    "法的事項",
    "サイトマップ",
    "プライバシーポリシー",
    "ウェブアクセシビリティ方針",
    "メンテナンス情報",
    "ページ上部へ戻る",
    "過去の公募情報",

    "PDFファイルをご覧いただくためにはAdobe Readerが必要です。",
    "お問い合せ、ご意見はこちら",
    "10月9日 更新しました",
}

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        continue

    if title in EXCLUDE_TITLES:
        continue

    href = a.get("href", "").strip()

    if not href:
        continue

    if href.startswith("#"):
        continue

    if href.startswith("javascript:"):
        continue

    url = urljoin(SOURCE_URL, href)

    # 添付ファイルは除外
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

    # ページ自身は除外
    if url.rstrip("/") == SOURCE_URL.rstrip("/"):
        continue

    # 過去公募一覧へのリンクは除外
    if "koubo20" in url.lower():
        continue

    # 短いナビゲーション文言は除外
    if len(title) < 8:
        continue

    key = (title, url)

    if key in seen:
        continue

    seen.add(key)
    items.append((title, url))

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "近畿経済産業局 公募情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = (
    "近畿経済産業局の公募予告及び公募中の情報"
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
        f"urn:kansai-meti-subsidy:{unique_id}"
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
