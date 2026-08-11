import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.optic.or.jp/"
OUTPUT_FILE = "optic-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

DATE_PATTERN = re.compile(r"^\d{4}/\d{2}/\d{2}")

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

SubElement(channel, "title").text = "岡山県産業振興財団 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "岡山県産業振興財団 新着情報"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    # リンク周辺に日付があるものだけを記事候補にする
    parent = a.parent
    found_article = False

    for _ in range(5):
        if parent is None:
            break

        text = parent.get_text(" ", strip=True)

        if re.search(r"\d{4}/\d{2}/\d{2}", text):
            found_article = True
            break

        parent = parent.parent

    if not found_article:
        continue

    url = urljoin(SOURCE_URL, a["href"])

    if url == SOURCE_URL:
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

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
