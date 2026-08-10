import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from xml.etree.ElementTree import Element, SubElement, ElementTree

FEEDS = [
    {
        "name": "栃木県産業振興センター お知らせ",
        "url": "https://www.tochigi-iin.or.jp/home/10/",
        "article_pattern": re.compile(r"^/home/10/home/10/\d+\.html$"),
        "output": "tochigi-news.xml",
    },
    {
        "name": "栃木県産業振興センター 助成金",
        "url": "https://www.tochigi-iin.or.jp/home/11/",
        "article_pattern": re.compile(r"^/home/11/\d+\.html$"),
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
        timeout=60,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = config["name"]
    SubElement(channel, "link").text = config["url"]
    SubElement(channel, "description").text = config["name"]

    seen = set()
    count = 0

    for link in soup.find_all("a", href=True):
        title = link.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin(config["url"], link["href"])
        parsed = urlparse(url)

        if parsed.netloc != "www.tochigi-iin.or.jp":
            continue

        if not config["article_pattern"].match(parsed.path):
            continue

        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if url in seen:
            continue

        seen.add(url)

        item = SubElement(channel, "item")
        SubElement(item, "title").text = title
        SubElement(item, "link").text = url
        SubElement(item, "guid").text = url

        count += 1

    ElementTree(rss).write(
        config["output"],
        encoding="utf-8",
        xml_declaration=True,
    )

    print(config["output"], count)

for feed in FEEDS:
    create_feed(feed)
