import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.siip.city.sendai.jp/news/news.html"
OUTPUT_FILE = "sendai-news.xml"

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

SubElement(channel, "title").text = "仙台市産業振興事業団 お知らせ・プレスリリース"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "仙台市産業振興事業団 お知らせ・プレスリリース"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    # 一覧の記事はタイトル内に日付が含まれている
    if not title.startswith("20"):
        continue

    url = urljoin(SOURCE_URL, a["href"])
    parsed = urlparse(url)

    if parsed.netloc != "www.siip.city.sendai.jp":
        continue

    if url in seen:
        continue

    seen.add(url)

    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

    count += 1

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
