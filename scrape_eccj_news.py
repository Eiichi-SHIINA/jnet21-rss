import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.eccj.or.jp/whatsnewj/"
OUTPUT_FILE = "eccj-news.xml"

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

date_pattern = re.compile(r"\[(\d{2})/(\d{2})\]")
year_pattern = re.compile(r"\((20\d{2})年\)")

items = []
seen = set()
current_year = None

# ページを上から順に走査
for tag in soup.find_all(True):

    text = tag.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    # 「令和８年(2026年)8月新着情報」から西暦年を取得
    year_match = year_pattern.search(text)

    if year_match and "新着情報" in text:
        current_year = int(year_match.group(1))

    # [08/04] のような日付を探す
    date_match = date_pattern.fullmatch(text)

    if not date_match or current_year is None:
        continue

    month = int(date_match.group(1))
    day = int(date_match.group(2))

    # 日付の次にある見出しを取得
    heading = tag.find_next(
        ["h1", "h2", "h3", "h4"]
    )

    if heading is None:
        continue

    title = heading.get_text(
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

    # 見出し内にリンクがあればそれを使用
    a = heading.find(
        "a",
        href=True
    )

    # 見出し自体にリンクがない場合は、
    # その見出しの直後にある最初のリンクを取得
    if a is None:
        a = heading.find_next(
            "a",
            href=True
        )

    if a is None:
        continue

    href = a.get("href", "")

    if not href or href.startswith("#"):
        continue

    url = urljoin(
        SOURCE_URL,
        href
    )

    # 補助リンクを記事として拾わない
    link_title = a.get_text(
        " ",
        strip=True
    )

    if link_title in {
        "ホームページ",
        "こちら",
        "ホームページをご覧ください。",
        "人材公募のページ",
        "新着情報トップ",
    }:
        continue

    date_text = f"{current_year}/{month:02d}/{day:02d}"
    date_key = current_year * 10000 + month * 100 + day

    key = (
        date_text,
        title,
        url,
    )

    if key in seen:
        continue

    seen.add(key)

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
).text = "省エネルギーセンター 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = "一般財団法人省エネルギーセンター 新着情報"

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

    unique_text = f"{date_text}|{title}|{url}"

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = (
        f"urn:eccj-news:{unique_id}"
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
