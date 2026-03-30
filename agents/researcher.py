import time
import anthropic
from tools import arxiv_search
from agents import summarizer

ARXIV_TOOL = {
    "name": "arxiv_search",
    "description": (
        "搜尋 arXiv 學術論文資料庫。"
        "當使用者詢問研究主題、論文、技術方法或學術概念時使用。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "搜尋關鍵字，支援 arXiv 查詢語法，"
                    "例如 'transformer attention' 或 'ti:BERT cat:cs.CL'"
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "回傳論文數量，預設 5，最多 10",
                "default": 5,
            },
            "sort_by": {
                "type": "string",
                "enum": ["relevance", "lastUpdatedDate"],
                "description": "relevance（相關性）或 lastUpdatedDate（最新更新）",
                "default": "relevance",
            },
        },
        "required": ["query"],
    },
}

MAX_RETRIES = 3


def _call_claude(client, **kwargs):
    """
    Generator：yield 狀態訊息，return Claude response。

    用法：
        gen = _call_claude(client, model=..., ...)
        try:
            while True:
                yield next(gen)   # 轉發狀態
        except StopIteration as e:
            response = e.value    # 取得結果
    """
    yield "[STATUS] 正在呼叫 Claude..."
    for attempt in range(MAX_RETRIES):
        try:
            result = client.messages.create(**kwargs)
            return result
        except anthropic.RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            yield f"[STATUS] Claude 重試中（{attempt + 1}/{MAX_RETRIES}）..."
            time.sleep(5 * (attempt + 1))


def _fetch_arxiv(block):
    """
    Generator：yield 狀態訊息，return (query, result_text)。
    """
    query = block.input.get("query", "")
    max_results = min(block.input.get("max_results", 5), 10)
    sort_by = block.input.get("sort_by", "relevance")

    yield f"[SEARCHING] {query}"
    for attempt in range(MAX_RETRIES):
        try:
            yield "[STATUS] 正在讀取 arXiv..."
            papers = arxiv_search.search(query=query, max_results=max_results, sort_by=sort_by)
            return query, arxiv_search.format_results(papers)
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 5 * (attempt + 1)  # 5s, 10s
            yield f"[STATUS] arXiv 重試中（{attempt + 1}/{MAX_RETRIES}），等待 {wait}s..."
            time.sleep(wait)


def _extract_user_question(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
    return ""


def _drain(gen):
    """
    消耗 generator，yield 所有狀態字串，最後回傳 return value。

    用法：
        result = yield from _drain(some_generator())
    """
    result = None
    try:
        while True:
            yield next(gen)
    except StopIteration as e:
        result = e.value
    return result


def run(client: anthropic.Anthropic, messages: list, system: str, model: str, max_tokens: int):
    """
    流程（固定 2 次 Claude API call）：
      Call 1：Claude 決定是否搜尋
        - 有 tool_use → 執行 arXiv 搜尋 → Call 2（summarizer, streaming）
        - 無 tool_use → 直接回答
    """
    user_question = _extract_user_question(messages)

    # Call 1
    response = yield from _drain(_call_claude(
        client,
        model=model,
        max_tokens=max_tokens,
        system=system,
        tools=[ARXIV_TOOL],
        messages=messages,
    ))

    # 沒有使用工具：直接回答
    if response.stop_reason != "tool_use":
        for block in response.content:
            if hasattr(block, "text"):
                for char in block.text:
                    yield char
        return

    # 執行 arXiv 搜尋
    all_papers_text = []
    for block in response.content:
        if block.type != "tool_use" or block.name != "arxiv_search":
            continue
        _, result_text = yield from _drain(_fetch_arxiv(block))
        all_papers_text.append(result_text)

    # Call 2：summarizer
    time.sleep(1)
    yield "[SUMMARIZING]"
    combined = "\n\n---\n\n".join(all_papers_text)
    yield from summarizer.run(client, user_question, combined, model, max_tokens)
