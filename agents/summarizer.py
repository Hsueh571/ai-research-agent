import anthropic

SUMMARIZER_SYSTEM = """You are a research report writer. Given a research topic and a list of academic papers from arXiv, produce a structured report.

Format your response in this structure:
## Overview
Brief summary of the research landscape for this topic.

## Key Papers
For each paper, write 2-3 sentences covering: what problem it solves, its approach, and key findings.

## Common Themes
Patterns and connections you notice across the papers.

## Conclusion
What the current state of research means, and suggested directions for further reading.

Respond in the same language the user used to ask their question."""


def run(
    client: anthropic.Anthropic,
    topic: str,
    research_text: str,
    model: str,
    max_tokens: int,
):
    """
    接收研究主題和論文清單，stream 一份結構化報告。

    Args:
        topic: 使用者的原始問題
        research_text: arxiv_search 回傳的論文清單文字
    """
    messages = [
        {
            "role": "user",
            "content": f"Research topic: {topic}\n\nFound papers:\n\n{research_text}",
        }
    ]

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=SUMMARIZER_SYSTEM,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text