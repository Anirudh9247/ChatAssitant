// ✅ Selecting DOM Elements
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

// ✅ Create typing indicator element
const typingIndicator = document.createElement("div");
typingIndicator.classList.add("message", "evo-ai", "typing");
typingIndicator.innerHTML = `<em>EVO-AI is typing...</em>`;

// ✅ Append messages with fade-in animation
function appendMessage(sender, message) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", sender.toLowerCase());
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    messageElement.style.opacity = 0;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    // Fade in
    let opacity = 0;
    const fadeIn = setInterval(() => {
        opacity += 0.05;
        messageElement.style.opacity = opacity;
        if (opacity >= 1) clearInterval(fadeIn);
    }, 15);
}

// ✅ Show typing indicator
function showTyping() {
    chatBox.appendChild(typingIndicator);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ✅ Remove typing indicator
function removeTyping() {
    if (chatBox.contains(typingIndicator)) {
        chatBox.removeChild(typingIndicator);
    }
}

// ✅ Handle sending message
function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    appendMessage("You", message);
    userInput.value = "";
    userInput.disabled = true;
    sendButton.disabled = true;

    showTyping();

    fetch("/get_response", {
        method: "POST",
        body: JSON.stringify({ message }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        removeTyping();
        appendMessage("EVO-AI", data.response || "⚠️ No response received.");
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    })
    .catch(error => {
        removeTyping();
        console.error("Error:", error);
        appendMessage("EVO-AI", "❌ Something went wrong.");
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    });
}

// ✅ Event listeners
sendButton.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") sendMessage();
});

// ✅ Auto-focus input on page load
window.onload = () => {
    userInput.focus();
};
