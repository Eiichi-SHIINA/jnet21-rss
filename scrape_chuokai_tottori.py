import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.chuokai-tottori.or.jp/?post_type=news"
OUTPUT_FILE = "chuokai-tottori-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

date_pattern = re.compile(
    r"20\d{2}/\d{1,2}/\d{1,2}"
)

items = []
seen = set()

for page in range(1, 4):

    if page == 1:
        page_url = SOURCE_URL
    else:
        page_url = (
            f"https://www.chuokai-tottori.or.jp/"
            f"page/{page}/?post_type=news"
        )

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for text_node in soup.find_all(string=date_pattern):

        match = date_pattern.search(
            str(text_node)
        )

        if not match:
            continue

        date_text = match.group()

        # 日付の直後にある記事タイトルリンク
        a = text_node.find_next(
            "a",
            href=True
        )

        if a is None:
            continue

        title = a.get_text(
            " ",
            strip=True
        )

        title = re.sub(
            r"\s+",
            " ",
            title
        ).strip()

        if not title:
            continue

        href = a.get("href", "")

        if not href or href.startswith("#"):
            continue

        url = urljoin(
            page_url,
            href
        )

        # 記事URLだけを対象
        if "?news=" not in url:
            continue

        key = (
            date_text,
            title,
            url,
        )

        if key in seen:
            continue

        seen.add(key)

        year, month, day = map(
            int,
            date_text.split("/")
        )

        date_key = (
            year * 10000
            + month * 100
            + day
        )

        items.append(
            (
                date_key,
                date_text,
                title,
                url,
            )
        )

items.sort(
    key=lambda x: x[0],
    reverse=True
)

rss = Element(
    "rss",
    version="2.0"
)

channel = SubElement(
    rss,
    "channel"
)

SubElement(
    channel,
    "title"
).text = "鳥取県中小企業団体中央会 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "鳥取県中小企業団体中央会 新着情報"

for date_key, date_text, title, url in items[:30]:

    item = SubElement(
        channel,
        "item"
    )

    SubElement(
        item,
        "title"
    ).text = title

    SubElement(
        item,
        "link"
    ).text = url

    unique_text = (
        f"{date_text}|{title}|{url}"
    )

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = (
        f"urn:chuokai-tottori:{unique_id}"
    )

ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(items[:30])
)
