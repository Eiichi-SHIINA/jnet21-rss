import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

FEEDS = [
    {
        "name": "栃木県産業振興センター お知らせ",
        "url": "https://www.tochigi-iin.or.jp/home/10/",
        "output": "tochigi-news.xml",
        # お知らせの記事URL
        "article_pattern": r"^/home/10/home/10/\d+\.html$",
    },
    {
        "name": "栃木県産業振興センター 助成金",
        "url": "https://www.tochigi-iin.or.jp/home/11/",
        "output": "tochigi-subsidy.xml",
        # 助成金の記事URL
        "article_pattern": r"^/home/11/home/10/\d+\.html$",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def create_feed(config):
    response = requests.get(
        config["url"],
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = config["name"]
    SubElement(channel, "link").text = config["url"]
    SubElement(channel, "description").text = config["name"]

    seen = set()
    article_pattern = re.compile(config["article_pattern"])

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        title = link.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin(config["url"], href)
        parsed = urlparse(url)

        # 栃木県産業振興センター内のみ
        if parsed.netloc != "www.tochigi-iin.or.jp":
            continue

        # 記事URLのパターンに一致するものだけ取得
        if not article_pattern.match(parsed.path):
            continue

        # 同じ記事の重複を除外
        if url in seen:
            continue

        seen.add(url)

        item = SubElement(channel, "item")
        SubElement(item, "title").text = title
        SubElement(item, "link").text = url
        SubElement(item, "guid").text = url

    ElementTree(rss).write(
        config["output"],
        encoding="utf-8",
        xml_declaration=True,
    )

    print(config["output"], len(seen))


for feed in FEEDS:
    create_feed(feed)
