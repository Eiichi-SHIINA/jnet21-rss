import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

BASE_URL = "https://www.ksrp.or.jp/blog/"
OUTPUT_FILE = "ksrp-blog.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

PAGES = [
    BASE_URL,
    urljoin(BASE_URL, "index_2.html"),
]

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "北九州学術研究都市 新着情報"
SubElement(channel, "link").text = BASE_URL
SubElement(channel, "description").text = "北九州学術研究都市 新着情報"

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

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        href = a.get("href", "")

        if not title:
            continue

        url = urljoin(page_url, href)

        # 個別記事だけ取得
        if not re.search(
            r"^https://www\.ksrp\.or\.jp/blog/archives/\d+\.html$",
            url
        ):
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
