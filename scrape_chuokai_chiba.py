import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-chiba.or.jp/chuokai/?post_type=chuokai_info"
OUTPUT_FILE = "chuokai-chiba-info.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "千葉県中小企業団体中央会 お知らせ"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "千葉県中小企業団体中央会 トップページのお知らせ"

seen = set()
count = 0

# 最新30件まで取得するため3ページ確認
pages = [
    SOURCE_URL,
    "https://www.chuokai-chiba.or.jp/chuokai/?post_type=chuokai_info&paged=2",
    "https://www.chuokai-chiba.or.jp/chuokai/?post_type=chuokai_info&paged=3",
]

for page_url in pages:
    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")

    # WordPressの記事枠ごとに取得
    for article in soup.find_all("article"):
        heading = article.find(["h1", "h2", "h3"])

        if heading is None:
            continue

        a = heading.find("a", href=True)

        if a is None:
            continue

        title = a.get_text(" ", strip=True)

        if not title:
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
