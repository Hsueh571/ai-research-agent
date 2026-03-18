import anthropic
from tools import arxiv_search

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

MAX_TOOL_ROUNDS = 5


def _execute_tool(block) -> tuple[str, str]:
    """執行單一 tool_use block，回傳 (search_query, result_text)。"""
    query = block.input.get("query", "")
    max_results = min(block.input.get("max_results", 5), 10)
    sort_by = block.input.get("sort_by", "relevance")
    papers = arxiv_search.search(query=query, max_results=max_results, sort_by=sort_by)
    return query, arxiv_search.format_results(papers)


def run(client: anthropic.Anthropic, messages: list, system: str, model: str, max_tokens: int):
    """
    Researcher agentic loop，支援多輪工具呼叫。

    流程：
      - 用 non-streaming + tools 呼叫 Claude（可重複至 MAX_TOOL_ROUNDS 次）
      - 每次 stop_reason == "tool_use"：執行工具，把結果餵回，繼續迴圈
      - stop_reason == "end_turn"：yield 最終文字，結束
      - 超過最大輪數：用 streaming（不帶 tools）強制取得最終回答
    """
    current_messages = list(messages)

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=[ARXIV_TOOL],
            messages=current_messages,
        )

        # Claude 決定直接回答，逐字 yield（模擬 streaming）
        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    for char in block.text:
                        yield char
            return

        # Claude 要使用工具，執行並收集結果
        tool_results = []
        for block in response.content:
            if block.type != "tool_use" or block.name != "arxiv_search":
                continue
            query, result_text = _execute_tool(block)
            yield f"[SEARCHING] {query}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        # 更新對話記錄，進入下一輪
        current_messages = current_messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results},
        ]

    # 超過最大輪數，不再帶 tools，強制 Claude 給最終回答
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=current_messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
