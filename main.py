import json
import anthropic
from flask import Flask, request, render_template, Response, stream_with_context
import config
from agents import researcher

app = Flask(__name__)
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def sse(msg: str) -> str:
    return f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    def generate():
        try:
            for chunk in researcher.run(
                client=client,
                messages=messages,
                system=config.SYSTEM_PROMPT,
                model=config.MODEL,
                max_tokens=config.MAX_TOKENS,
            ):
                yield sse(chunk)
        except anthropic.AuthenticationError:
            yield sse("[ERROR] API Key 無效，請確認 .env 設定")
        except anthropic.RateLimitError:
            yield sse("[ERROR] 請求太頻繁，請稍後幾秒再試（429 Rate Limit）")
        except anthropic.APIStatusError as e:
            if e.status_code == 429:
                yield sse("[ERROR] 請求太頻繁，請稍後幾秒再試（429 Rate Limit）")
            else:
                yield sse(f"[ERROR] API 錯誤（{e.status_code}）：{e.message}")
        except anthropic.BadRequestError as e:
            yield sse(f"[ERROR] {e.message}")
        except Exception as e:
            msg = str(e)
            if "429" in msg:
                yield sse("[ERROR] arXiv 請求太頻繁，請稍後再試")
            else:
                yield sse(f"[ERROR] {msg}")
        yield sse("[DONE]")

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
