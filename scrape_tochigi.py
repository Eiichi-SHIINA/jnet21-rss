import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

FEEDS = [
    {
        "name": "栃木県産業振興センター お知らせ",
        "url": "https://www.tochigi-iin.or.jp/home/10/",
        "output": "tochigi-news.xml",
    },
    {
        "name": "栃木県産業振興センター 助成金",
        "url": "https://www.tochigi-iin.or.jp/home/11/",
        "output": "tochigi-subsidy.xml",
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

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        title = link.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin(config["url"], href)

        # 同一ページ自身や明らかなナビゲーションを除外
        if url == config["url"]:
            continue

        if url in seen:
            continue

        # 栃木県産業振興センター内の記事リンクだけを対象
        if "tochigi-iin.or.jp" not in url:
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
