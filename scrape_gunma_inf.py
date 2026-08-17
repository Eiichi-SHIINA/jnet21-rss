import re
import ssl
import hashlib
import requests
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from xml.etree.ElementTree import Element, SubElement, ElementTree

SOURCE_URL = "https://www.g-inf.or.jp/"
OUTPUT_FILE = "gunma-inf.xml"

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
}

EXCLUDE_KEYWORDS = [
    "交付決定事業者",
    "交付決定者",
    "採択結果",
    "公募型プロポーザル",
    "業務委託",
    "支援マネージャーの募集",
    "事例紹介を更新",
    "フィッシングメール",
]

LINK_EXCLUDE_KEYWORDS = [
    "申込",
    "お申込",
    "申し込み",
    "募集要領",
    "公募要領",
    "交付要領",
    "仕様書",
    "様式",
    "こちら",
    "PDF",
]

DATE_PATTERN = re.compile(r"^20\d{2}/\d{2}/\d{2}$")


class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


session = requests.Session()
session.mount("https://", LegacySSLAdapter())

response = session.get(
    SOURCE_URL,
    headers=HEADERS,
    timeout=60,
)
response.raise_for_status()

response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

# 新着情報の見出しを探す
news_heading = soup.find(
    lambda tag: (
        tag.name in ["h1", "h2", "h3", "h4", "div", "p"]
        and tag.get_text(" ", strip=True) == "新着情報"
    )
)

if news_heading is None:
    raise RuntimeError("新着情報欄が見つかりません")

items = []
current_date = None
current_title = None
current_url = None

started = False

for node in news_heading.find_all_next():

    if isinstance(node, NavigableString):
        continue

    text = node.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        continue

    # 新着情報の次のセクションで終了
    if text == "メールマガジン配信登録":
        break

    # 日付を検出
    if DATE_PATTERN.fullmatch(text):

        # 前の記事を保存
        if current_date and current_title:
            if not any(
                keyword in current_title
                for keyword in EXCLUDE_KEYWORDS
            ):
                items.append((
                    current_date,
                    current_title,
                    current_url or SOURCE_URL
                ))

        current_date = text
        current_title = None
        current_url = None
        started = True
        continue

    if not started or current_date is None:
        continue

    # 日付直後の最初の適切な文字列をタイトルにする
    if current_title is None:

        # 説明文やボタン類をタイトルにしない
        if any(
            text.startswith(prefix)
            for prefix in [
                "日時",
                "会場",
                "対象",
                "定員",
                "受講料",
                "参加費",
                "締切",
                "申込",
                "お問合わせ",
                "募集期間",
                "設置期間",
                "相談窓口",
                "貸出",
            ]
        ):
            continue

        if len(text) < 8:
            continue

        # 長い説明文はタイトルではない
        if len(text) > 180:
            continue

        current_title = text

        # タイトル自体がリンクならそのURLを使う
        if node.name == "a" and node.get("href"):
            href = node.get("href", "").strip()

            if href and not href.lower().endswith((
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
            )):
                current_url = urljoin(SOURCE_URL, href)

        continue

    # タイトルにリンクがない記事は関連リンクを探す
    if current_url is None and node.name == "a":
        href = node.get("href", "").strip()
        link_text = text

        if not href:
            continue

        if any(
            keyword in link_text
            for keyword in LINK_EXCLUDE_KEYWORDS
        ):
            continue

        url = urljoin(SOURCE_URL, href)

        if url.lower().endswith((
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
        )):
            continue

        current_url = url


# 最後の記事を保存
if current_date and current_title:
    if not any(
        keyword in current_title
        for keyword in EXCLUDE_KEYWORDS
    ):
        items.append((
            current_date,
            current_title,
            current_url or SOURCE_URL
        ))


# 重複除去
clean_items = []
seen = set()

for date, title, url in items:

    title = (
        title
        .replace("別ウィンドウで開きます", "")
        .replace("PDFファイルが別ウィンドウで開きます", "")
        .strip()
    )

    title = re.sub(r"\s+", " ", title).strip()

    key = (date, title)

    if key in seen:
        continue

    seen.add(key)
    clean_items.append((date, title, url))


rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(
    channel,
    "title"
).text = "群馬県産業支援機構 新着情報"

SubElement(
    channel,
    "link"
).text = SOURCE_URL

SubElement(
    channel,
    "description"
).text = (
    "群馬県産業支援機構のセミナー・募集・補助金・支援等の新着情報"
)

for date, title, url in clean_items[:30]:

    item = SubElement(channel, "item")

    SubElement(
        item,
        "title"
    ).text = title

    SubElement(
        item,
        "link"
    ).text = url

    unique_text = f"{date}|{title}"

    unique_id = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()

    SubElement(
        item,
        "guid"
    ).text = f"urn:gunma-inf:{unique_id}"


ElementTree(rss).write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    OUTPUT_FILE,
    len(clean_items[:30])
)
