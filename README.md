# My First LLM Project

A simple chat application that lets you have a conversation with OpenAI's language model from your terminal.

---

## Prerequisites

Make sure you have the following installed before getting started:

- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # On macOS/Linux
venv\Scripts\activate           # On Windows
```

### 3. Install dependencies

```bash
pip install openai
```

### 4. Add your OpenAI API key

Create a file named `.env` in the project root:

```bash
touch .env
```

Open `.env` and add your API key:

```
OPENAI_API_KEY=your-api-key-here
```

> **Note:** Never share your `.env` file or commit it to GitHub. The `.gitignore` should already exclude it.

### 5. Run the app

```bash
python main.py
```

You should see a prompt in your terminal. Start chatting!

---

## Usage

```
You: Hello, who are you?
AI: I'm an AI assistant powered by OpenAI. How can I help you today?

You: quit
```

Type `quit` or `exit` to end the conversation.

---

## Project Structure

```
.
├── main.py          # Entry point — starts the chat loop
├── agents/
│   ├── planner.py   # Planning agent
│   ├── researcher.py
│   └── summarizer.py
├── rag/
│   ├── embedding.py
│   └── vector_store.py
├── tools/
│   ├── arxiv_search.py
│   └── web_search.py
├── .env             # Your API key (not committed to git)
└── README.md
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'openai'`**
Run `pip install openai` and make sure your virtual environment is activated.

**`AuthenticationError`**
Double-check that your API key in `.env` is correct and has not expired.

**`python` command not found**
Try using `python3` instead of `python`.
