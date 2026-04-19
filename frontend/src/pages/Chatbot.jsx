import { useState } from "react";

export default function Chatbot() {
  // Give model instructions; set default messages state
  const [messages, setMessages] = useState([
    { role: "system", content: "You are a helpful assistant." },
    { role: "assistant", content: "Hi! Ask me anything." },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    // Prevent empty inputs or response is loading
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input };

    // Create new array containing previous messages + user message
    // Example:
    // const messages = [
    //   { role: "system", content: "You are a helpful assistant." },
    //   { role: "assistant", content: "Hi! Ask me anything." },
    //   { role: "user", content: "What is React?" }
    // ];
    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages)  // Update message UI immediately while waiting for backend
    setInput("")           // Clear text box after sending
    setLoading(true)

    // Start request
    try {
      // Send request to python backend
      const response = await fetch("http://127.0.0.1:5000/api/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: updatedMessages,
        }),
      });

      // { reply: "Hello!" }
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }

      // Update messages with assisstant reply
      setMessages([
        // Make sure to include previous messages
        ...updatedMessages,
        // Add chatbot reply to messages
        { role: "assistant", content: data.reply },
      ])
    }

    catch (error) {
      setMessages([
        ...updatedMessages,
        {
          role: "assistant", content: `Error: ${error.message}`,
        },
      ]);
    }

    finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2>Chatbot</h2>

      <div className="chat-box">
        {messages
          // Filter out messages whose role == "system"; "system" messages are for LLM, not message history
          .filter((msg) => msg.role !== "system")
          // Iterate over each message and return html element
          .map((msg, index) => (
            // Create CSS class for user/bot
            <div key={index} className={`chat-message ${msg.role}`}>
              <strong>{msg.role === "user" ? "You" : "Bot"}:</strong>{" "} {msg.content}
            </div>
          ))
        }
      </div>

      <form onSubmit={handleSubmit} className="form">
        <label>
          Message
          <textarea
            rows="3"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Thinking..." : "Send"}
        </button>
      </form>
    </section>
  )
}
