let chatId = null;
let chats = JSON.parse(localStorage.getItem("chats") || "{}");
let chatTitles = JSON.parse(localStorage.getItem("chatTitles") || "{}");
let chatHistory = [];

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

    // Add references if available
    if (msg.references && msg.references.length > 0) {
      const refDiv = document.createElement("div");
      refDiv.className = "references";
      msg.references.forEach(ref => {
        const link = document.createElement("a");
        link.href = ref.url;
        link.target = "_blank";
        link.textContent = `[${ref.id}]`;
        link.style.marginRight = "5px";
        refDiv.appendChild(link);
      });
      bubble.appendChild(refDiv);
    }

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

async function handleNewChatClick(previousChatId) {
  const lastChat = chats[previousChatId];
  if (!lastChat || lastChat.length < 2 || lastChat.feedbackGiven) return;

  const feedbackPayload = {
    messages: lastChat,
    strategy: "cot",
    prompt_version: "v1",
    model_name: "gpt-4o-mini-voc2",
    feedback: "thumbs_up"
  };

  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedbackPayload)
    });

    if (res.ok) {
      const result = await res.json();
      chatTitles[previousChatId] = result.title || `Chat ${new Date(Number(previousChatId)).toLocaleTimeString()}`;
      chats[previousChatId].feedbackGiven = true;
      localStorage.setItem("chats", JSON.stringify(chats));
      localStorage.setItem("chatTitles", JSON.stringify(chatTitles));
      updateHistory();
    } else {
      console.error("❌ Feedback request failed:", await res.text());
    }
  } catch (err) {
    console.error("❌ Feedback logging error:", err);
  }
}

async function sendMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  const chat = chats[chatId] || [];
  chat.push({ role: "user", content: text });
  chatHistory.push({ role: "user", content: text });
  chats[chatId] = chat;
  localStorage.setItem("chats", JSON.stringify(chats));
  renderChat(chat);
  input.value = "";
  input.focus();

  showLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: chatHistory })
    });

    if (!response.ok) throw new Error("Failed to fetch response from server");

    const data = await response.json();
    const assistantReply = data.reply || "Sorry, I didn't understand that.";
    const references = data.references || [];

    const assistantMessage = {
      role: "assistant",
      content: assistantReply,
      references: references
    };

    chat.push(assistantMessage);
    chatHistory.push(assistantMessage);
    chats[chatId] = chat;
    localStorage.setItem("chats", JSON.stringify(chats));
    renderChat(chat);
  } catch (error) {
    alert("Error: " + error.message);
  } finally {
    showLoading(false);
  }
}

function sendFeedback(type) {
  fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: chats[chatId],
      strategy: "cot",
      prompt_version: "v1",
      model_name: "gpt-4o-mini-voc2",
      feedback: type
    })
  })
    .then(res => res.json())
    .then(result => {
      chatTitles[chatId] = result.title || `Chat ${new Date(Number(chatId)).toLocaleTimeString()}`;
      chats[chatId].feedbackGiven = true;
      localStorage.setItem("chats", JSON.stringify(chats));
      localStorage.setItem("chatTitles", JSON.stringify(chatTitles));
      updateHistory();
    });

  if (!chats[chatId]) return;
}

async function newChat() {
  const previousChatId = chatId;
  await handleNewChatClick(previousChatId);

  chatId = Date.now().toString();
  chatHistory = [{ role: "assistant", content: "Hello! How can I help you today?" }];
  chats[chatId] = [...chatHistory];
  localStorage.setItem("chats", JSON.stringify(chats));
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
      chatHistory = [...chats[id]];
      renderChat(chats[chatId]);
    };

    const feedbackStatus = document.createElement("span");
    feedbackStatus.style.marginLeft = "8px";
    feedbackStatus.textContent = chats[id].feedbackGiven ? "✅" : "🟡";
    feedbackStatus.title = chats[id].feedbackGiven ? "Feedback logged" : "Feedback pending";

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
        if (chatId) {
          chatHistory = [...chats[chatId]];
          renderChat(chats[chatId]);
        } else {
          chatHistory = [];
          document.getElementById("chatWindow").innerHTML = "";
        }
      }
    };

    entry.appendChild(title);
    entry.appendChild(feedbackStatus);
    entry.appendChild(renameBtn);
    entry.appendChild(delBtn);
    historyDiv.appendChild(entry);
  });
}

function showLoading(show) {
  document.getElementById("loadingIndicator").style.display = show ? "block" : "none";
}

function getReadableChat(chat) {
  return chat.map(m => `${m.role.toUpperCase()}: ${m.content}`).join("\n");
}

document.getElementById("userInput").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

const existingIds = Object.keys(chats);
if (existingIds.length > 0) {
  chatId = existingIds[existingIds.length - 1];
  chatHistory = [...chats[chatId]];
  renderChat(chats[chatId]);
} else {
  newChat();
}
updateHistory();