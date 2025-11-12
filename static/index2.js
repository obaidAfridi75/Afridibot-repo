// Chat Memory
let chatHistory = [];

function saveMessage(role, content) {
    chatHistory.push({ role, content });
}

// Clear chat on page load (keep default message)
window.addEventListener("load", () => {
    const chatBox = document.getElementById("chat-box");
    if (chatBox) {
        const messages = chatBox.querySelectorAll('.message');
        // Keep only first message (default), remove others
        for (let i = messages.length - 1; i >= 1; i--) {
            messages[i].remove();
        }
    }
    chatHistory = []; // Reset memory
});

async function sendMessage() {
  const input = document.getElementById("user-input");
  const msg = input.value.trim();
  if (!msg) return;

  const chatBox = document.getElementById("chat-box");
    input.value = "";

 // Check for recap before sending to backend
if (msg.toLowerCase().includes("what we discussed") || 
    msg.toLowerCase().includes("recap") ||
    msg.toLowerCase().includes("summary") ||
    msg.toLowerCase().includes("history") ||
    msg.toLowerCase().includes("previous chat") ||
    msg.toLowerCase().includes("conversation so far") ||
    msg.toLowerCase().includes("what did we talk") ||
    msg.toLowerCase().includes("show me our chat") ||
    msg.toLowerCase().includes("remember what we") ||
    msg.toLowerCase().includes("our discussion")) {
    
    const recapMsg = document.createElement("div");
    recapMsg.className = "message bot";
    
    if (chatHistory.length === 0) {
        recapMsg.textContent = "We haven't discussed anything yet! Ask me about gold prices. ";
    } else {
        let summary = "**Here's a summary of our conversation:**\n\n";
        
        // Filter out recap messages to avoid loops
        const filteredHistory = chatHistory.filter(m => 
            !m.content.toLowerCase().includes("what we discussed") &&
            !m.content.toLowerCase().includes("recap") &&
            !m.content.toLowerCase().includes("summary") &&
            !m.content.toLowerCase().includes("history") &&
            !m.content.toLowerCase().includes("previous chat") &&
            !m.content.toLowerCase().includes("conversation so far") &&
            !m.content.toLowerCase().includes("what did we talk") &&
            !m.content.toLowerCase().includes("show me our chat") &&
            !m.content.toLowerCase().includes("remember what we") &&
            !m.content.toLowerCase().includes("our discussion")
        );
        
        const userMessages = filteredHistory.filter(m => m.role === "user");
        const botMessages = filteredHistory.filter(m => m.role === "bot");

        // Numbered list format
        for (let i = 0; i < userMessages.length; i++) {
            const userMsg = userMessages[i]?.content || "";
            const botMsg = botMessages[i]?.content || "";
            
            // Clean the bot response for summary
            const cleanBotMsg = botMsg
                .replace(/\*\*/g, "")
                .replace(/\*/g, "")
                .replace(/Today's Gold Rates in .*?\(approx\):/gi, "Current gold rates:")
                .replace(/ Note:.*/gi, "")
                .replace(/\n/g, " ")
                .substring(0, 120) + (botMsg.length > 120 ? "..." : "");

            summary += `**${i + 1}. You asked:** "${userMsg}"\n`;
            summary += `   **I replied:** ${cleanBotMsg}\n\n`;
        }

        summary += `**Total topics discussed:** ${userMessages.length}`;

        // Render with markdown formatting
        if (window.marked) {
            recapMsg.innerHTML = marked.parse(summary);
        } else {
            recapMsg.textContent = summary;
        }
    }
    
    chatBox.appendChild(recapMsg);
    saveMessage("bot", recapMsg.textContent);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
    return; // Stop here - don't send to backend
}
  // User message
  const userMsg = document.createElement("div");
  userMsg.className = "message user";
  userMsg.textContent = msg;
  chatBox.appendChild(userMsg);

  // Save user message to memory
  saveMessage("user", msg);

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

    // Save bot response to memory
    saveMessage("bot", data.reply || "⚠️ No response received.");

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
