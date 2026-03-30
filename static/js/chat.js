const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// 從 HTML data attribute 讀取後端 API 端點，避免硬編碼 URL
const CHAT_API_URL = document.getElementById("chat-container").dataset.chatUrl;

let conversationHistory = [];

function appendMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = "";
  sendBtn.disabled = true;

  conversationHistory.push({ role: "user", content: text });
  appendMessage("user", text);

  const assistantDiv = appendMessage("assistant", "");
  let fullResponse = "";

  const response = await fetch(CHAT_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: conversationHistory }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") break;
      if (data.startsWith("[ERROR]")) {
        assistantDiv.textContent = data.slice(8);
        assistantDiv.style.color = "#e53e3e";
        conversationHistory.pop(); // 移除這次失敗的 user 訊息
        sendBtn.disabled = false;
        inputEl.focus();
        return;
      }
      if (data.startsWith("[SEARCHING]")) {
        assistantDiv.textContent = `🔍 搜尋中：${data.slice(12)}`;
        continue;
      }
      fullResponse += data;
      assistantDiv.textContent = fullResponse;
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  }

  conversationHistory.push({ role: "assistant", content: fullResponse });
  sendBtn.disabled = false;
  inputEl.focus();
}

sendBtn.addEventListener("click", sendMessage);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
