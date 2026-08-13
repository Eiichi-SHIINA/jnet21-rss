import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.aiweb.or.jp/topics/index.html"
OUTPUT_FILE = "aiweb-topics.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

PAGES = [
    SOURCE_URL,
    "https://www.aiweb.or.jp/topics/index.html?p=2",
    "https://www.aiweb.or.jp/topics/index.html?p=3",
    "https://www.aiweb.or.jp/topics/index.html?p=4",
    "https://www.aiweb.or.jp/topics/index.html?p=5",
]

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "愛知県中小企業団体中央会 お知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "愛知県中小企業団体中央会 お知らせ一覧"

seen = set()
count = 0

for page_url in PAGES:
    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")

    for heading in soup.find_all(["h2", "h3"]):
        a = heading.find("a", href=True)

        if a is None:
            continue

        title = a.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin(page_url, a["href"])

        # 一覧・カテゴリページ等は除外
        if url.rstrip("/") in [
            "https://www.aiweb.or.jp",
            "https://www.aiweb.or.jp/topics",
        ]:
            continue

        if "/topics/index.html" in url:
            continue

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

    if count >= 30:
        break

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
