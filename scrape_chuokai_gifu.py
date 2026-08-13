import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-gifu.or.jp/chuokai/news/news_new.html"
OUTPUT_FILE = "chuokai-gifu-news.xml"

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

SubElement(channel, "title").text = "岐阜県中小企業団体中央会 新着情報"
SubElement(channel, "link").text = SOURCE_URL
SubElement(channel, "description").text = "岐阜県中小企業団体中央会 掲載情報"

seen = set()
items = []

for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)

    if not title:
        continue

    # 年度切替・ページ上部・フッターなどを除外
    if re.fullmatch(r"20\d{2}", title):
        continue

    if title in [
        "▲ページ上へもどる",
        "個人情報の保護に関する基本方針",
        "個人情報の利用目的",
    ]:
        continue

    # 記事タイトルには一覧上で日付が付いている
    if not re.search(
        r"\(20\d{2}\.\d{1,2}\.\d{1,2}\)",
        title
    ):
        continue

    url = urljoin(SOURCE_URL, a["href"])

    if url in seen:
        continue

    seen.add(url)

    # タイトル末尾の日付だけ除去
    clean_title = re.sub(
        r"\s*[（(]20\d{2}\.\d{1,2}\.\d{1,2}[）)]\s*$",
        "",
        title
    ).strip()

    items.append((title, clean_title, url))

for original_title, clean_title, url in items[:30]:
    item = SubElement(channel, "item")
    SubElement(item, "title").text = clean_title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(OUTPUT_FILE, len(items[:30]))
