import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

SOURCE_URL = "https://direct.jfc.go.jp/w110_SeminarList"
OUTPUT_FILE = "jfc-seminar.xml"
MAX_ITEMS = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def clean_parts(strings):
    """連続して重複する表示用テキストを除去する"""
    result = []

    for text in strings:
        text = " ".join(text.split())

        if not text:
            continue

        if result and result[-1] == text:
            continue

        result.append(text)

    return result


def fetch_items():
    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    items = []
    seen_urls = set()

    for anchor in soup.find_all(
        "a",
        href=lambda href: href and "w112_SeminarApply?id=" in href
    ):
        title = " ".join(anchor.get_text(" ", strip=True).split())

        if not title:
            continue

        link = urljoin(SOURCE_URL, anchor["href"])

        # 同じオンラインセミナー等が複数地域に掲載されるため
        # 詳細URL単位で重複排除
        if link in seen_urls:
            continue

        seen_urls.add(link)

        parent = anchor.find_parent("li")

        description = ""

        if parent:
            parts = clean_parts(parent.stripped_strings)

            # タイトル自体はdescriptionから除外
            info_parts = [
                part for part in parts
                if part != title
            ]

            description = " / ".join(info_parts)

        items.append({
            "title": title,
            "link": link,
            "description": description,
        })

        if len(items) >= MAX_ITEMS:
            break

    return items


def build_rss(items):
    rss = ET.Element(
        "rss",
        version="2.0"
    )

    channel = ET.SubElement(rss, "channel")

    ET.SubElement(
        channel,
        "title"
    ).text = "日本政策金融公庫｜セミナー情報"

    ET.SubElement(
        channel,
        "link"
    ).text = SOURCE_URL

    ET.SubElement(
        channel,
        "description"
    ).text = "日本政策金融公庫のセミナー情報一覧"

    for item_data in items:
        item = ET.SubElement(channel, "item")

        ET.SubElement(
            item,
            "title"
        ).text = item_data["title"]

        ET.SubElement(
            item,
            "link"
        ).text = item_data["link"]

        ET.SubElement(
            item,
            "guid",
            isPermaLink="true"
        ).text = item_data["link"]

        if item_data["description"]:
            ET.SubElement(
                item,
                "description"
            ).text = item_data["description"]

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")

    tree.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True
    )


def main():
    items = fetch_items()

    if not items:
        raise RuntimeError("セミナー情報を取得できませんでした")

    build_rss(items)

    print(f"{len(items)}件を取得しました")
    print(f"{OUTPUT_FILE} を生成しました")


if __name__ == "__main__":
    main()
