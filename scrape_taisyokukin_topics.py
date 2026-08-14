import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.taisyokukin.go.jp/topics/"
OUTPUT_FILE = "taisyokukin-topics.xml"

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

date_pattern = re.compile(r"^20\d{2}\.\d{1,2}\.\d{1,2}$")

items = []
seen = set()

for text_node in soup.find_all(string=True):

    date_text = re.sub(
        r"\s+",
        "",
        str(text_node)
    )

    if not date_pattern.match(date_text):
        continue

    date_tag = text_node.parent

    # 日付の次の兄弟要素を、その日の新着ブロックとして扱う
    block = date_tag.find_next_sibling()

    if block is None:
        continue

    block_text = block.get_text(
        " ",
        strip=True
    )

    block_text = re.sub(
        r"\s+",
        " ",
        block_text
    ).strip()

    if not block_text:
        continue

    # 最初に〖 〗で囲まれた見出しがあればタイトルとして使用
    heading_match = re.search(
        r"〖(.+?)〗",
        block_text
    )

    if heading_match:
        title = heading_match.group(1).strip()

    else:
        # リンク付きの通常記事
        a = block.find("a", href=True)

        if a is not None:
            title = a.get_text(
                " ",
                strip=True
            )
            title = re.sub(
                r"\s+",
                " ",
                title
            ).strip()

        else:
            # リンクのないメンテナンス等のお知らせ
            title = block_text

    if not title:
        continue

    # タイトルが部署名だけの場合は、ブロック内のリンク文字を使う
    if title in {
        "資産運用部",
        "財形部",
    }:
        a = block.find("a", href=True)

        if a is not None:
            title = a.get_text(
                " ",
                strip=True
            )
            title = re.sub(
                r"\s+",
                " ",
                title
            ).strip()

    # リンクはブロック内の最初の有効リンク
    a = block.find("a", href=True)

    if a is not None:
        href = a.get("href", "")

        if href and not href.startswith("#"):
            url = urljoin(
                SOURCE_URL,
                href
            )
        else:
            url = SOURCE_URL
    else:
        # リンクなしのお知らせは新着一覧へ
        url = SOURCE_URL

    # 「こちら」などしか取れなかった場合はブロックの見出しを優先
    if title in {
        "こちら",
        "ホームページ",
    }:
        if heading_match:
            title = heading_match.group(1).strip()
        else:
            title = block_text

    # 同一タイトル＋同一URLは1件だけ
    key = (
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

    year, month, day = map(
        int,
        date_text.split(".")
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
).text = "勤労者退職金共済機構 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "勤労者退職金共済機構 新着情報"

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
        f"urn:taisyokukin-topics:{unique_id}"
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
