import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.tokyo-kosha.or.jp/topics/index.html"
OUTPUT_FILE = "tokyo-kosha.xml"

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
print("=== TOKYO KOSHA LINKS ===")

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    href = a.get("href", "")

    if title and (
        "/topics/" in href
        or "/support/" in href
    ):
        print(href, "|", title)

print("=== END TOKYO KOSHA LINKS ===")

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "東京都中小企業振興公社 公社からのお知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "東京都中小企業振興公社 公社からのお知らせ"

seen = set()
count = 0

main = soup.find("main")

if main is None:
    main = soup

for a in main.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    url = urljoin(SOURCE_URL, a["href"])
    parsed = urlparse(url)

    if parsed.netloc != "www.tokyo-kosha.or.jp":
        continue

    # ページ内リンクやメニュー類を除外
    if url == SOURCE_URL:
        continue

    if title in [
        "トップ",
        "お知らせ",
        "メインコンテンツへスキップ",
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

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, count)
