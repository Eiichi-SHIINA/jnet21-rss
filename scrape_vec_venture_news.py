import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.vec.or.jp/venture_news"
OUTPUT_FILE = "vec-venture-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

items = []
seen = set()

for page in range(1, 6):

    if page == 1:
        page_url = SOURCE_URL
    else:
        page_url = f"{SOURCE_URL}?page={page}"

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):

        href = a.get("href", "")
        url = urljoin(
            SOURCE_URL,
            href
        )

        # 個別のベンチャーニュース記事だけを対象
        if not re.search(
            r"/venture_news/\d+$",
            url
        ):
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

        # 「続きを読む」リンク等は除外
        if "続きを読む" in title or "詳細を見る" in title:
            continue

        key = (
            title,
            url,
        )

        if key in seen:
            continue

        seen.add(key)

        # URL末尾に YYYYMMDDHH が入っているため並び替えに利用
        match = re.search(
            r"/venture_news/(\d{8,12})$",
            url
        )

        if match:
            date_key = int(match.group(1))
        else:
            date_key = 0

        items.append(
            (
                date_key,
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
).text = "ベンチャーエンタープライズセンター ベンチャーニュース"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "一般財団法人ベンチャーエンタープライズセンター ベンチャーニュース"

for date_key, title, url in items[:30]:

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

    unique_text = f"{title}|{url}"

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = (
        f"urn:vec-venture-news:{unique_id}"
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
