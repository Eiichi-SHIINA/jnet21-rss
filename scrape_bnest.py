import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.b-nest.jp/topics/"
OUTPUT_FILE = "bnest-topics.xml"

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

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "B-nest セミナー＆イベント情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "B-nest セミナー・イベント・公募・補助金情報"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    href = a.get("href", "")

    if not title:
        continue

    if title in [
        "ホーム",
        "施設予約",
        "施設利用",
        "B-nestとは",
        "お問い合わせ",
        "閉じる",
        "トップ",
    ]:
        continue

    if href.startswith("javascript:"):
        continue

    if href.startswith("/search"):
        continue

    if href in [
        "/",
        "/topics/",
        "/blog/",
        "/profile/",
        "/shisetsu/",
        "/shien/",
        "/kigyo-shien/",
        "/soudan/",
    ]:
        continue

    parent = a.parent
    found_article = False

    for _ in range(5):
        if parent is None:
            break

        text = parent.get_text(" ", strip=True)

        if (
            "2026年" in text
            and (
                "講座・セミナー" in text
                or "イベント" in text
                or "各種公募・補助金情報" in text
            )
        ):
            found_article = True
            break

        parent = parent.parent

    if not found_article:
        continue

    url = urljoin(SOURCE_URL, href)

    if url in seen:
        continue

    seen.add(url)

    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

    count += 1

    if count >= 30:
        break

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
