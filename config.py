import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-opus-4-6"
MAX_TOKENS = 1024
SYSTEM_PROMPT = (
    "You are an AI research assistant specializing in academic literature. "
    "When the user asks about research topics, papers, or technical concepts, "
    "use the arxiv_search tool to find relevant papers before answering. "
    "Summarize findings clearly and cite the papers you reference."
)

HOST = "127.0.0.1"
PORT = 8000
DEBUG = True
