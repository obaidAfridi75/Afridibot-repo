async function sendMessage() {
  const input = document.getElementById("user-input");
  const msg = input.value.trim();
  if (!msg) return;

  const chatBox = document.getElementById("chat-box");

  // User message
  const userMsg = document.createElement("div");
  userMsg.className = "message user";
  userMsg.textContent = msg;
  chatBox.appendChild(userMsg);
  input.value = "";

  // Auto-scroll to bottom
  chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });

  // Typing indicator
  const typing = document.createElement("div");
  typing.className = "message bot typing";
  typing.textContent = "GoldBot is Thinking...";
  chatBox.appendChild(typing);
  chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });

    const data = await response.json();
    chatBox.removeChild(typing);

    const botMsg = document.createElement("div");
    botMsg.className = "message bot";

    //  Render Markdown if available
    if (window.marked && data.reply) {
      botMsg.innerHTML = marked.parse(data.reply);
    } else {
      botMsg.textContent = data.reply || "⚠️ No response received.";
    }

    chatBox.appendChild(botMsg);
    // Auto-scroll again
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });

  } catch (err) {
    chatBox.removeChild(typing);
    const errMsg = document.createElement("div");
    errMsg.className = "message bot";
    errMsg.textContent = "⚠️ Connection error. Please try again.";
    chatBox.appendChild(errMsg);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
  }
}

// Handle Enter key press
document.getElementById("user-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

// Optional: handle Send button click if exists
const sendBtn = document.getElementById("send-btn");
if (sendBtn) sendBtn.addEventListener("click", sendMessage);

