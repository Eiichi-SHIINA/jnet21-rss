import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.nipc.or.jp/news/index.php"
OUTPUT_FILE = "nipc-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "名古屋産業振興公社 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "名古屋産業振興公社 新着情報"

seen = set()
count = 0

for page in range(1, 4):
    if page == 1:
        page_url = SOURCE_URL
    else:
        page_url = f"{SOURCE_URL}?page={page}"

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)

        if not title:
            continue

        # 新着情報の記事タイトルは日付から始まる
        if not re.match(r"^\d{4}/\d{2}/\d{2}", title):
            continue

        url = urljoin(page_url, a["href"])
        parsed = urlparse(url)

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
