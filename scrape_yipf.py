import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://yipf.or.jp/"
OUTPUT_FILE = "yipf-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

ALLOWED_PREFIXES = (
    "/topics/",
    "/event/",
    "/subsidy/",
    "/proposal/",
    "/bid/",
)

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

SubElement(channel, "title").text = "やまぐち産業振興財団 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "やまぐち産業振興財団 新着情報"

seen = set()
count = 0

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    url = urljoin(SOURCE_URL, a["href"])
    parsed = urlparse(url)

    if parsed.netloc not in ["yipf.or.jp", "www.yipf.or.jp"]:
        continue

    if not parsed.path.startswith(ALLOWED_PREFIXES):
        continue

    # 一覧ページ自体は除外
    if parsed.path in [
        "/topics/",
        "/event/",
        "/subsidy/",
        "/proposal/",
        "/bid/",
    ]:
        continue

    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    if parsed.query:
        clean_url += f"?{parsed.query}"

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
