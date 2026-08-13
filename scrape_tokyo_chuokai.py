import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.tokyochuokai.or.jp/"
OUTPUT_FILE = "tokyo-chuokai-news.xml"

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

SubElement(channel, "title").text = "東京都中小企業団体中央会 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "東京都中小企業団体中央会 中央会Flash・Hot News"

seen = set()
items = []


def collect_section(heading_text):
    heading = None

    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)

        if heading_text.lower() in text.lower():
            heading = tag
            break

    if heading is None:
        print("Section not found:", heading_text)
        return

    for element in heading.find_all_next(["a", "h2", "h3", "h4"]):
        # 次の見出しに来たら、この区画は終了
        if element.name in ["h2", "h3", "h4"]:
            if element is not heading:
                break
            continue

        title = element.get_text(" ", strip=True)

        if not title:
            continue

        # 過去記事一覧へのリンクは除外
        if title in [
            "過去の中央会Flash",
            "過去のHot News",
        ]:
            continue

        href = element.get("href", "")

        if not href:
            continue

        if href.startswith("#"):
            continue

        url = urljoin(SOURCE_URL, href)

        if url in seen:
            continue

        seen.add(url)
        items.append((title, url))


collect_section("中央会 Flash")
collect_section("Hot News")

for title, url in items[:30]:
    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, len(items[:30]))
