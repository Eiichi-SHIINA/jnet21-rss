import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://nb-fun.jp/category/news"
OUTPUT_FILE = "nbfun-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "名古屋市小規模事業金融公社 お知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "名古屋市小規模事業金融公社 お知らせ"

seen = set()
count = 0

for page in range(1, 4):
    if page == 1:
        page_url = SOURCE_URL
    else:
        page_url = f"{SOURCE_URL}/page/{page}"

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

        parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""

        if not re.search(r"\d{4}\.\d{2}\.\d{2}", parent_text):
            continue

        if title in ["次のページ »", "前のページ «"]:
            continue

        url = urljoin(page_url, a["href"])

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
