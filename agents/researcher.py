import time
import anthropic
from tools import arxiv_search, web_search
from agents import summarizer

ARXIV_TOOL = {
    "name": "arxiv_search",
    "description": (
        "搜尋 arXiv 學術論文資料庫。當使用者詢問研究主題、論文、技術方法或學術概念時使用。\n\n"
        "Query 語法指引：\n"
        "- ti:\"keyword\" 只搜標題（最精確）\n"
        "- abs:\"keyword\" 搜摘要\n"
        "- 組合範例：ti:\"retrieval augmented generation\" AND cat:cs.IR\n"
        "- 預設使用 sort_by=relevance\n"
        "- 使用者明確要求最新論文時才用 sort_by=lastUpdatedDate，"
        "且必須搭配 ti: 或 abs: 語法確保結果在主題內，"
        "禁止單用關鍵字搭配 lastUpdatedDate"
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

WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "使用 DuckDuckGo 搜尋一般網頁。適用於以下情境：\n"
        "- 非學術性內容（新聞、教學、部落格、官方文件）\n"
        "- arXiv 上找不到的主題（業界實作、工具比較、最新動態）\n"
        "- 使用者明確要求搜尋網路資料\n\n"
        "學術論文請優先使用 arxiv_search；一般知識或實作問題才使用 web_search。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜尋關鍵字，使用自然語言即可，例如 'how to implement RAG with LangChain'",
            },
            "max_results": {
                "type": "integer",
                "description": "回傳結果數量，預設 5，最多 10",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

TOOLS = [ARXIV_TOOL, WEB_SEARCH_TOOL]
MAX_RETRIES = 3


def _call_claude(client, **kwargs):
    """Generator：yield 狀態訊息，return Claude response。"""
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
    """Generator：yield 狀態訊息，return (query, result_text)。"""
    query = block.input.get("query", "")
    max_results = min(block.input.get("max_results", 5), 10)
    sort_by = block.input.get("sort_by", "relevance")

    yield f"[SEARCHING] arXiv｜{query}"
    for attempt in range(MAX_RETRIES):
        try:
            yield "[STATUS] 正在讀取 arXiv..."
            papers = arxiv_search.search(query=query, max_results=max_results, sort_by=sort_by)
            return query, arxiv_search.format_results(papers)
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 5 * (attempt + 1)
            yield f"[STATUS] arXiv 重試中（{attempt + 1}/{MAX_RETRIES}），等待 {wait}s..."
            time.sleep(wait)


def _fetch_web(block):
    """Generator：yield 狀態訊息，return (query, result_text)。"""
    query = block.input.get("query", "")
    max_results = min(block.input.get("max_results", 5), 10)

    yield f"[SEARCHING] Web｜{query}"
    for attempt in range(MAX_RETRIES):
        try:
            yield "[STATUS] 正在搜尋網頁..."
            results = web_search.search(query=query, max_results=max_results)
            return query, web_search.format_results(results)
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 5 * (attempt + 1)
            yield f"[STATUS] 網頁搜尋重試中（{attempt + 1}/{MAX_RETRIES}），等待 {wait}s..."
            time.sleep(wait)


def _extract_user_question(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
    return ""


def _drain(gen):
    """消耗 generator，yield 所有狀態字串，最後回傳 return value。"""
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
      Call 1：Claude 決定使用哪個工具（arxiv_search / web_search / 皆不用）
        - 有 tool_use → 執行對應搜尋 → Call 2（summarizer, streaming）
        - 無 tool_use → 直接回答
    """
    user_question = _extract_user_question(messages)

    # Call 1
    response = yield from _drain(_call_claude(
        client,
        model=model,
        max_tokens=max_tokens,
        system=system,
        tools=TOOLS,
        messages=messages,
    ))

    # 沒有使用工具：直接回答
    if response.stop_reason != "tool_use":
        for block in response.content:
            if hasattr(block, "text"):
                for char in block.text:
                    yield char
        return

    # 執行工具（可能同時呼叫 arxiv_search 和 web_search）
    all_results_text = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        if block.name == "arxiv_search":
            _, result_text = yield from _drain(_fetch_arxiv(block))
            all_results_text.append(result_text)
        elif block.name == "web_search":
            _, result_text = yield from _drain(_fetch_web(block))
            all_results_text.append(result_text)

    # Call 2：summarizer
    time.sleep(1)
    yield "[SUMMARIZING]"
    combined = "\n\n---\n\n".join(all_results_text)
    yield from summarizer.run(client, user_question, combined, model, max_tokens)
