import ssl
import certifi
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_NS = "http://www.w3.org/2005/Atom"


@dataclass
class Paper:
    title: str
    authors: list[str]
    summary: str
    url: str
    published: str
    categories: list[str]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "summary": self.summary,
            "url": self.url,
            "published": self.published,
            "categories": self.categories,
        }

    def to_text(self) -> str:
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += f" 等 {len(self.authors)} 人"
        return (
            f"**{self.title}**\n"
            f"作者：{authors_str}\n"
            f"發表：{self.published[:10]}\n"
            f"類別：{', '.join(self.categories)}\n"
            f"連結：{self.url}\n"
            f"摘要：{self.summary[:300]}{'...' if len(self.summary) > 300 else ''}"
        )


def search(query: str, max_results: int = 5, sort_by: str = "relevance") -> list[Paper]:
    """
    搜尋 arXiv 論文。

    Args:
        query: 搜尋關鍵字，支援 arXiv 查詢語法（如 "ti:transformer AND cat:cs.LG"）
        max_results: 最多回傳幾篇論文（預設 5，上限 50）
        sort_by: 排序方式，"relevance"（相關性）或 "lastUpdatedDate"（最新）

    Returns:
        Paper 物件的清單
    """
    max_results = min(max_results, 50)

    params = urllib.parse.urlencode({
        "search_query": query,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    })

    url = f"{ARXIV_API_URL}?{params}"

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=30, context=ssl_ctx) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    papers = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        title = entry.findtext(f"{{{ARXIV_NS}}}title", "").strip().replace("\n", " ")
        summary = entry.findtext(f"{{{ARXIV_NS}}}summary", "").strip().replace("\n", " ")
        published = entry.findtext(f"{{{ARXIV_NS}}}published", "")
        link_el = entry.find(f"{{{ARXIV_NS}}}link[@type='text/html']")
        url = link_el.get("href", "") if link_el is not None else ""

        authors = [
            author.findtext(f"{{{ARXIV_NS}}}name", "")
            for author in entry.findall(f"{{{ARXIV_NS}}}author")
        ]

        categories = [
            tag.get("term", "")
            for tag in entry.findall("{http://arxiv.org/schemas/atom}primary_category")
            + entry.findall("{http://www.w3.org/2005/Atom}category")
        ]
        categories = list(dict.fromkeys(categories))  # 去重，保留順序

        papers.append(Paper(
            title=title,
            authors=authors,
            summary=summary,
            url=url,
            published=published,
            categories=categories,
        ))

    return papers


def format_results(papers: list[Paper]) -> str:
    """將搜尋結果格式化成可讀文字。"""
    if not papers:
        return "找不到相關論文。"
    lines = [f"找到 {len(papers)} 篇論文：\n"]
    for i, paper in enumerate(papers, 1):
        lines.append(f"[{i}] {paper.to_text()}\n")
    return "\n".join(lines)
