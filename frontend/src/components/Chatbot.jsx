import { useState } from 'react'

export default function Chatbot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! Ask me about predictions, player context, or how the model made a decision.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSend(event) {
    event.preventDefault()

    const trimmed = input.trim()
    if (!trimmed) return

    const userMessage = { role: 'user', content: trimmed }
    const nextMessages = [...messages, userMessage]

    setMessages(nextMessages)
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: nextMessages,
        }),
      })

      const data = await response.json()
      console.log('Chatbot API response:', data)

      const botText =
        data.response ||
        data.answer ||
        data.reply ||
        data.message ||
        data.error ||
        'I could not generate a response.'

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: botText,
        },
      ])
    } catch (err) {
      console.error(err)

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I had trouble reaching the chatbot service.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chatbot-widget">
      {open && (
        <div className="chatbot-panel">
          <div className="chatbot-header">
            <div>
              <h3>NBA Assistant</h3>
              <p>Ask about predictions, players, and model context</p>
            </div>

            <button
              type="button"
              className="chatbot-close"
              onClick={() => setOpen(false)}
              aria-label="Close chatbot"
            >
              ×
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`chat-message ${
                  message.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'
                }`}
              >
                {message.content}
              </div>
            ))}

            {loading && (
              <div className="chat-message chat-message-assistant chatbot-typing">
                Thinking...
              </div>
            )}
          </div>

          <form className="chatbot-input-row" onSubmit={handleSend}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about this prediction..."
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        className="chatbot-toggle"
        onClick={() => setOpen((prev) => !prev)}
        aria-label="Open chatbot"
      >
        {open ? '×' : 'AI'}
      </button>
    </div>
  )
}