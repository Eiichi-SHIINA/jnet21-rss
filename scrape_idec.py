import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.idec.or.jp/event/index.html"
OUTPUT_FILE = "idec-event.xml"

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

SubElement(channel, "title").text = "横浜企業経営支援財団 セミナー・イベント"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "横浜企業経営支援財団 セミナー・イベント"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    url = urljoin(SOURCE_URL, a["href"])
    parsed = urlparse(url)

    if parsed.netloc != "www.idec.or.jp":
        continue

    # 個別イベントページだけ取得
    if parsed.path != "/event/seminar_info.html":
        continue

    if "id=" not in parsed.query:
        continue

    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{parsed.query}"

    if clean_url in seen:
        continue

    seen.add(clean_url)

    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = clean_url
    SubElement(item, "guid").text = clean_url

    count += 1

    if count >= 30:
        break

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
