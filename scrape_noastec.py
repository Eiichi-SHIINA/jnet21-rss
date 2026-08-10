import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

FEEDS = [
    {
        "name": "NOASTEC セミナー・イベント",
        "url": "https://www.noastec.jp/news/seminar-event",
        "output": "noastec-seminar.xml",
    },
    {
        "name": "NOASTEC プレスリリース",
        "url": "https://www.noastec.jp/news/pressrelease",
        "output": "noastec-pressrelease.xml",
    },
    {
        "name": "NOASTEC 補助・助成",
        "url": "https://www.noastec.jp/news/subsidy",
        "output": "noastec-subsidy.xml",
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

        if "/news/" not in href or "/post_" not in href:
            continue

        url = urljoin(config["url"], href)

        if url in seen:
            continue

        seen.add(url)

        title = link.get_text(" ", strip=True)

        if not title:
            continue

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
