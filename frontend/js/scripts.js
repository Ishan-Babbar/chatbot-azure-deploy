let chatId = null;
let chats = JSON.parse(localStorage.getItem("chats") || "{}");
let chatTitles = JSON.parse(localStorage.getItem("chatTitles") || "{}");

function renderChat(chat) {
  const chatWindow = document.getElementById("chatWindow");
  chatWindow.innerHTML = "";
  chat.forEach(msg => {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${msg.role}`;

    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src = msg.role === "user" ? "assets/user-avatar.png" : "assets/assistant-avatar.png";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = marked.parse(msg.content);

    const timestamp = document.createElement("div");
    timestamp.className = "timestamp";
    timestamp.textContent = new Date().toLocaleTimeString();

    bubble.appendChild(timestamp);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatWindow.appendChild(messageDiv);
  });
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  const chat = chats[chatId] || [];
  chat.push({ role: "user", content: text });
  chats[chatId] = chat;
  localStorage.setItem("chats", JSON.stringify(chats));
  renderChat(chat);
  input.value = "";
  input.focus();

  showLoading(true);

  try {
    const response = await fetch("http://127.0.0.1:5000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ messages: chat })
    });

    if (!response.ok) throw new Error("Failed to fetch response from server");

    const data = await response.json();
    const assistantReply = data.reply || "Sorry, I didn't understand that.";

    chat.push({ role: "assistant", content: assistantReply });
    chats[chatId] = chat;
    localStorage.setItem("chats", JSON.stringify(chats));
    renderChat(chat);
  } catch (error) {
    alert("Error: " + error.message);
  } finally {
    showLoading(false);
  }
}

function newChat() {
  chatId = Date.now().toString();
  chats[chatId] = [{ role: "assistant", content: "Hello! How can I help you today?" }];
  chatTitles[chatId] = `Chat ${new Date(Number(chatId)).toLocaleTimeString()}`;
  localStorage.setItem("chats", JSON.stringify(chats));
  localStorage.setItem("chatTitles", JSON.stringify(chatTitles));
  updateHistory();
  renderChat(chats[chatId]);
}

function updateHistory() {
  const historyDiv = document.getElementById("chatHistory");
  historyDiv.innerHTML = "";
  Object.keys(chats).forEach(id => {
    const entry = document.createElement("div");
    entry.className = "chat-entry";

    const title = document.createElement("span");
    title.textContent = chatTitles[id] || `Chat ${new Date(Number(id)).toLocaleString()}`;
    title.onclick = () => {
      chatId = id;
      renderChat(chats[id]);
    };

    const renameBtn = document.createElement("button");
    renameBtn.textContent = "✏️";
    renameBtn.onclick = (e) => {
      e.stopPropagation();
      const newTitle = prompt("Rename this chat:", chatTitles[id]);
      if (newTitle && newTitle.trim()) {
        chatTitles[id] = newTitle.trim();
        localStorage.setItem("chatTitles", JSON.stringify(chatTitles));
        updateHistory();
      }
    };

    const delBtn = document.createElement("button");
    delBtn.textContent = "🗑️";
    delBtn.onclick = (e) => {
      e.stopPropagation();
      delete chats[id];
      delete chatTitles[id];
      localStorage.setItem("chats", JSON.stringify(chats));
      localStorage.setItem("chatTitles", JSON.stringify(chatTitles));
      updateHistory();
      if (chatId === id) {
        const remainingIds = Object.keys(chats);
        chatId = remainingIds.length ? remainingIds[0] : null;
        if (chatId) renderChat(chats[chatId]);
        else document.getElementById("chatWindow").innerHTML = "";
      }
    };

    entry.appendChild(title);
    entry.appendChild(renameBtn);
    entry.appendChild(delBtn);
    historyDiv.appendChild(entry);
  });
}

// function toggleSidebar() {
//   document.getElementById("sidebar").classList.toggle("collapsed");
// }

function showLoading(show) {
  document.getElementById("loadingIndicator").style.display = show ? "block" : "none";
}

document.getElementById("userInput").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Initialize
const existingIds = Object.keys(chats);
if (existingIds.length > 0) {
  chatId = existingIds[existingIds.length - 1];
  renderChat(chats[chatId]);
} else {
  newChat(); // creates first chat and updates history
}
updateHistory();