import React, { useState, useRef, useEffect } from 'react';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // C 1. Create a persistent thread_id (Change to load from localStorage so it persists across refreshes)
  const [threadId] = useState(() => {
    const savedThread = localStorage.getItem('chat_thread_id');
    if (savedThread) return savedThread;
    const newThread = 'thread_' + Math.random().toString(36).substring(2, 11);
    localStorage.setItem('chat_thread_id', newThread);
    return newThread;
  });
  const chatEndRef = useRef(null);

  // Automatically scroll to the bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 2. Fetch history from FastAPI on initial application mount
  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await fetch(`http://localhost:8000/chat/history/${threadId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.history) {
            setMessages(data.history);
          }
        }
      } catch (error) {
        console.error("Error loading chat context history:", error);
      }
    };

    fetchChatHistory();
  }, [threadId]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userPrompt = input;
    setInput('');
    setLoading(true);

    // Append the user's message to the chat container
    setMessages((prev) => [...prev, { role: 'user', content: userPrompt }]);

    // Append a placeholder entry for the incoming AI stream
    const assistantMessageId = 'ai_' + Date.now();
    setMessages((prev) => [...prev, { id: assistantMessageId, role: 'assistant', content: '' }]);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userPrompt, thread_id: threadId }),
      });

      if (!response.ok) throw new Error('Failed to connect to backend server.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedResponse = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Handle server-sent events delimiter
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6));
              accumulatedResponse += parsed.token;

              // Inject tokens in real-time into the correct placeholder
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: accumulatedResponse }
                    : msg
                )
              );
            } catch (err) {
              console.error('Error parsing line chunk:', err);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming connection error:', error);
      // Fallback message styling on connection drops
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: '⚠️ Error: Failed to generate response from local LLM.' }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h2>Local AI Chat Assistant</h2>
        <span style={styles.badge}>Thread: {threadId}</span>
      </header>

      <div style={styles.chatBox}>
        {messages.map((msg, index) => (
          <div
            key={msg.id || index}
            style={{
              ...styles.messageWrapper,
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                ...styles.messageBubble,
                backgroundColor: msg.role === 'user' ? '#007bff' : '#e9ecef',
                color: msg.role === 'user' ? '#fff' : '#333',
              }}
            >
              <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong>
              <div style={styles.textContent}>{msg.content || (loading && 'Thinking...')}</div>
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={sendMessage} style={styles.inputForm}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Ollama something..."
          disabled={loading}
          style={styles.inputField}
        />
        <button type="submit" disabled={loading || !input.trim()} style={styles.sendButton}>
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

// Inline styling dictionary for zero-dependency plug-and-play installation
const styles = {
  container: { maxWidth: '700px', margin: '40px auto', display: 'flex', flexDirection: 'column', height: '80vh', border: '1px solid #ddd', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', fontFamily: 'system-ui, sans-serif' },
  header: { backgroundColor: '#f8f9fa', padding: '15px 20px', borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  badge: { fontSize: '12px', color: '#6c757d', background: '#e2e3e5', padding: '4px 8px', borderRadius: '4px' },
  chatBox: { flex: 1, padding: '20px', overflowY: 'auto', backgroundColor: '#fff', display: 'flex', flexDirection: 'column', gap: '15px' },
  messageWrapper: { display: 'flex', width: '100%' },
  messageBubble: { maxWidth: '75%', padding: '12px 16px', borderRadius: '16px', lineHeight: '1.5', fontSize: '15px' },
  textContent: { marginTop: '5px', whiteSpace: 'pre-wrap' },
  inputForm: { display: 'flex', padding: '15px', borderTop: '1px solid #ddd', backgroundColor: '#f8f9fa', gap: '10px' },
  inputField: { flex: 1, padding: '12px', border: '1px solid #ccc', borderRadius: '8px', fontSize: '15px', outline: 'none' },
  sendButton: { padding: '12px 24px', backgroundColor: '#007bff', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }
};

export default App;