// ChatWidget.jsx
import React, { useState, useEffect, useRef } from "react";

const ChatWidget = ({ socket }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Listen for chat messages
  const handleWebSocketMessage = (message) => {
    if (message.type === "chat_message") {
      setMessages((prev) => [...prev, message.data]);
      setIsLoading(false);
    } else if (message.type === "error") {
      console.error("Chat error:", message.message);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    socket.onMessage = handleWebSocketMessage;
  }, [socket]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setIsLoading(true);
    socket.send({
      type: "chat_message",
      message: input,
    });

    setInput("");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "400px" }}>
      <div style={{ flex: 1, overflowY: "auto", borderBottom: "1px solid #ddd" }}>
        {messages.map((msg) => (
          <div key={msg.message_id} style={{ padding: "8px", borderBottom: "1px solid #f0f0f0" }}>
            <strong>{msg.username}</strong>
            <span style={{ fontSize: "12px", color: "#999", marginLeft: "8px" }}>
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
            <p style={{ margin: "4px 0" }}>{msg.message}</p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} style={{ padding: "8px", display: "flex", gap: "8px" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={isLoading}
          style={{ flex: 1, padding: "8px", borderRadius: "4px", border: "1px solid #ddd" }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            padding: "8px 16px",
            backgroundColor: "#007bff",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: isLoading ? "not-allowed" : "pointer",
            opacity: isLoading ? 0.6 : 1,
          }}
        >
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
};

export default ChatWidget;
