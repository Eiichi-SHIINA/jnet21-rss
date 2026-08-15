import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

BASE_URL = "https://www.tohoku.meti.go.jp/"
OUTPUT_FILE = "tohoku-meti-event.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.meti.go.jp/",
}

# イベント情報が掲載される主な部署ページ
SOURCE_URLS = [
    "https://www.tohoku.meti.go.jp/s_joho/index_joho.html",
    "https://www.tohoku.meti.go.jp/s_cyusyo/index_cyusyo.html",
    "https://www.tohoku.meti.go.jp/s_shinki/index_shinki.html",
    "https://www.tohoku.meti.go.jp/s_kokusai/index_kokusai.html",
    "https://www.tohoku.meti.go.jp/chiiki_supporter/index.html",
    "https://www.tohoku.meti.go.jp/kikaku/chihososei/index.html",
    "https://www.tohoku.meti.go.jp/s_shigen_ene/syo_energy/index.html",
]

KEYWORDS = [
    "セミナー",
    "説明会",
    "相談会",
    "フォーラム",
    "イベント",
    "講座",
    "研修",
    "シンポジウム",
    "交流会",
    "勉強会",
    "ワークショップ",
    "Meetup",
    "ミートアップ",
]

items = []
seen = set()

for source_url in SOURCE_URLS:
    try:
        response = requests.get(
            source_url,
            headers=HEADERS,
            timeout=60,
        )
        response.raise_for_status()

    except requests.RequestException as e:
        print(
            "取得失敗:",
            source_url,
            e,
        )
        continue

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for a in soup.find_all("a", href=True):
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

        if not any(
            keyword.lower() in title.lower()
            for keyword in KEYWORDS
        ):
            continue

        href = a.get(
            "href",
            ""
        ).strip()

        if not href:
            continue

        if href.startswith("#"):
            continue

        if href.startswith("javascript:"):
            continue

        url = urljoin(
            source_url,
            href
        )

        if not url.startswith(BASE_URL):
            continue

        # PDFそのものは除外
        if url.lower().endswith(".pdf"):
            continue

        # 固定メニュー等を除外
        if title in {
            "セミナー",
            "イベント",
            "研修",
            "説明会",
        }:
            continue

        key = (
            title,
            url,
        )

        if key in seen:
            continue

        seen.add(key)

        items.append(
            (
                title,
                url,
            )
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
).text = "東北経済産業局 イベント・セミナー情報"

SubElement(
    channel,
    "link"
).text = BASE_URL

SubElement(
    channel,
    "description"
).text = (
    "東北経済産業局のセミナー・説明会・相談会・"
    "イベント等の情報"
)

for title, url in items[:30]:
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
        f"{title}|{url}"
    )

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = (
        f"urn:tohoku-meti-event:{unique_id}"
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
