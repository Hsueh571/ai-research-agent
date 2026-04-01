# AI Research Agent

A web-based research assistant powered by Claude. Ask research questions and get structured reports — the agent automatically searches arXiv for academic papers or the web for general information, then summarizes findings with citations.

---

## Features

- **Dual search tools** — arXiv for academic papers, DuckDuckGo for general web results
- **Agentic loop** — Claude decides which tool to use based on your question
- **Structured reports** — Overview, Key Papers, Common Themes, Conclusion
- **Streaming UI** — real-time status updates and markdown rendering
- **Retry logic** — handles rate limits from both Anthropic and arXiv APIs

---

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Hsueh571/ai-research-agent.git
cd ai-research-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Anthropic API key

```bash
touch .env
```

Open `.env` and add:

```
ANTHROPIC_API_KEY=your-api-key-here
```

> Never commit `.env` to git — it's already in `.gitignore`.

### 5. Run the app

```bash
python main.py
```

Open your browser at `http://127.0.0.1:8000`.

---

## Usage

Type any research question in the chat box:

- **Academic questions** → agent searches arXiv and returns a structured paper summary
- **General questions** → agent searches the web and summarizes results
- **Non-research questions** → agent answers directly without searching

---

## Project Structure

```
.
├── main.py               # Flask server, SSE streaming endpoint
├── config.py             # API key, model, and prompt configuration
├── agents/
│   ├── researcher.py     # Orchestration agent — decides which tools to use
│   └── summarizer.py     # Generates structured reports from search results
├── tools/
│   ├── arxiv_search.py   # arXiv API client
│   └── web_search.py     # DuckDuckGo web search
├── rag/                  # Planned: embeddings and vector store
├── templates/
│   └── index.html        # Chat UI
├── static/
│   ├── css/style.css
│   └── js/chat.js
├── requirements.txt
└── .env                  # API key (not committed)
```

---

## Troubleshooting

**`ModuleNotFoundError`**
Make sure your virtual environment is activated and run `pip install -r requirements.txt`.

**`429 Rate Limit`**
The agent has built-in retry logic, but new Anthropic accounts start at Tier 1 (50 RPM). Wait a few seconds and try again, or upgrade your tier at [console.anthropic.com](https://console.anthropic.com/).

**`SSL certificate verify failed`**
Run `pip install certifi` and ensure your Python installation is up to date.

**`python` command not found**
Try `python3` instead of `python`.
