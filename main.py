import anthropic
from flask import Flask, request, render_template, Response, stream_with_context
import config

app = Flask(__name__)
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    def generate():
        try:
            with client.messages.stream(
                model=config.MODEL,
                max_tokens=config.MAX_TOKENS,
                system=config.SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {text}\n\n"
        except anthropic.BadRequestError as e:
            yield f"data: [ERROR] {e.message}\n\n"
        except anthropic.AuthenticationError:
            yield "data: [ERROR] API Key 無效，請確認 .env 設定\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
