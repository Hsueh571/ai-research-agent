import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-opus-4-6"
MAX_TOKENS = 1024
SYSTEM_PROMPT = "You are a helpful AI assistant."

HOST = "127.0.0.1"
PORT = 8000
DEBUG = True
