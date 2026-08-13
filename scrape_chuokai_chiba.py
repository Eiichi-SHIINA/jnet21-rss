import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-chiba.or.jp/chuokai/?post_type=chuokai_info"
OUTPUT_FILE = "chuokai-chiba-info.xml"

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

SubElement(channel, "title").text = "千葉県中小企業団体中央会 お知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "千葉県中小企業団体中央会 トップページのお知らせ"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    url = urljoin(SOURCE_URL, a["href"])
    parsed = urlparse(url)

    if parsed.netloc != "www.chuokai-chiba.or.jp":
        continue

    # お知らせ個別ページだけを対象
    if "chuokai_info=" not in parsed.query:
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
