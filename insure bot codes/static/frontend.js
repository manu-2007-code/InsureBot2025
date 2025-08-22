// ✅ FINAL frontend.js

function showInterface(id) {
  document.querySelectorAll('.interface').forEach(div => div.classList.remove('active'));
  document.getElementById(id).classList.add('active');

  if (id === "historyInterface") {
    loadHistoryInterface();
  }
}

function scrollToBottom() {
  const chatMessages = document.getElementById("chatMessages");
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Live Chat
function sendMessage() {
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;

  const chatMessages = document.getElementById("chatMessages");
  const userDiv = document.createElement("div");
  userDiv.className = "message-box user";
  userDiv.textContent = "You: " + message;
  chatMessages.appendChild(userDiv);
  scrollToBottom();
  input.value = "";

  fetch("http://127.0.0.1:5000/api/send_message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  })
    .then(response => response.json())
    .then(data => {
      const reply = data.response || "Sorry, I couldn't understand.";
      const botDiv = document.createElement("div");
      botDiv.className = "message-box bot";
      botDiv.textContent = "Bot: " + reply;
      chatMessages.appendChild(botDiv);
      scrollToBottom();
    })
    .catch(error => {
      console.error("Fetch error:", error);
    });
}

// 🎤 Voice Chat
function startVoice() {
  const resultDiv = document.getElementById("voiceResult");
  resultDiv.textContent = "🎙 Listening...";

  fetch("http://127.0.0.1:5000/api/listen_and_reply", {
    method: "POST"
  })
     .then(res => {
      if (!res.ok || !res.headers.get("content-type")?.includes("application/json")) {
        throw new Error("❌ Server error or invalid JSON");
      }
      return res.json();
    })
    .then(data => {
      const spoken = data.spoken || "";
      const botReply = data.response || "";
      if (spoken) {
        resultDiv.innerHTML = `<div class="message-box user">You: ${spoken}</div>`;
      }

      const replyDiv = document.createElement("div");
      replyDiv.className = "message-box bot";
      replyDiv.textContent = "Bot: " + botReply;
      resultDiv.appendChild(replyDiv);
    })
    .catch(err => {
      resultDiv.textContent = "❌ Error: " + err.message;
    });
}

// Chat History
function loadHistoryInterface() {
  fetch("http://127.0.0.1:5000/api/get_history")
    .then(res => res.json())
    .then(data => {
      const historyDiv = document.getElementById("historyMessages");
      historyDiv.innerHTML = "";
      data.reverse().forEach(msg => {
        const userDiv = document.createElement("div");
        userDiv.className = "message-box user";
        userDiv.textContent = "You: " + msg.user;
        historyDiv.appendChild(userDiv);

        const botDiv = document.createElement("div");
        botDiv.className = "message-box bot";
        botDiv.textContent = "Bot: " + msg.bot;
        historyDiv.appendChild(botDiv);
      });
    })
    .catch(err => console.error("Error loading history:", err));
}
