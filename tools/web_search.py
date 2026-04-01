from dataclasses import dataclass
from ddgs import DDGS


@dataclass
class Result:
    title: str
    url: str
    snippet: str

    def to_text(self) -> str:
        return (
            f"**{self.title}**\n"
            f"來源：{self.url}\n"
            f"摘要：{self.snippet}"
        )


def search(query: str, max_results: int = 5) -> list[Result]:
    """
    使用 DuckDuckGo 搜尋網頁。不需要 API key。

    Args:
        query: 搜尋關鍵字
        max_results: 最多回傳幾筆結果（預設 5，上限 10）

    Returns:
        Result 物件的清單
    """
    max_results = min(max_results, 10)
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(Result(
                title=r.get("title", ""),
                url=r.get("href", ""),
                snippet=r.get("body", ""),
            ))

    return results


def format_results(results: list[Result]) -> str:
    """將搜尋結果格式化成可讀文字。"""
    if not results:
        return "找不到相關網頁結果。"
    lines = [f"找到 {len(results)} 筆網頁結果：\n"]
    for i, result in enumerate(results, 1):
        lines.append(f"[{i}] {result.to_text()}\n")
    return "\n".join(lines)
