import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.b-nest.jp/topics/"
OUTPUT_FILE = "bnest-topics.xml"

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

SubElement(channel, "title").text = "B-nest セミナー＆イベント情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "B-nest セミナー・イベント・公募・補助金情報"

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

    # メニュー・カテゴリリンク等を除外
    if url == SOURCE_URL:
        continue

    if title in [
        "トップ",
        "セミナー＆イベント情報",
        "ブログ一覧",
        "登録専門家検索",
        "目的で探す",
        "窓口相談スケジュール",
    ]:
        continue

    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    if parsed.query:
        clean_url += f"?{parsed.query}"

    if parsed.fragment:
        clean_url += f"#{parsed.fragment}"

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
