import { useState, useEffect, useRef, type KeyboardEvent } from 'react'
import './index.css'

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'process' | 'question';
  text: string;
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [agentStatus, setAgentStatus] = useState<string>('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socket = new WebSocket('ws://127.0.0.1:8080/ws');
    
    socket.onopen = () => {
      console.log('Connected to Orchestrator');
      setAgentStatus('Connected');
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.state) {
          const s = data.state;
          if (s === 'waiting for user input ..') {
            setAgentStatus(s);
          } else if (s === 'EXECUTION') {
            setAgentStatus('executor agent is running...');
          } else if (s === 'STARTED') {
            setAgentStatus('orchestrator started');
          } else if (s === 'COMPLETED') {
            setAgentStatus('completed');
          } else if (s === 'FAILED') {
            setAgentStatus('failed');
          } else {
            setAgentStatus(`${s.toLowerCase()} agent is thinking...`);
          }
        }
        // Only append messages that have an explicit type (from ws_print) to avoid duplicate state echoes
        if (data.message && data.type) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            sender: data.type, // 'agent', 'process', 'question'
            text: data.message
          }]);
        }
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };
    
    socket.onclose = () => {
      console.log('Disconnected');
      setAgentStatus('Disconnected');
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  const handleSend = () => {
    if (!inputValue.trim() || !ws) return;
    
    const msg = inputValue.trim();
    setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'user', text: msg }]);
    ws.send(msg);
    setInputValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const isThinking = agentStatus && !['Connected', 'Disconnected', 'completed', 'failed', 'orchestrator started'].includes(agentStatus);

  // Formatter to colorize [Agent Name] tags and format code blocks
  const renderMessageText = (text: string) => {
    // Check if the text contains a markdown code block
    if (text.includes('```python') || text.includes('```')) {
      const parts = text.split(/```(?:python)?\n?/);
      return parts.map((part, index) => {
        // Even indices are normal text, odd indices are code blocks
        if (index % 2 === 1) {
          return (
            <pre key={index} className="code-snippet">
              <code>{part.trim()}</code>
            </pre>
          );
        }
        return <span key={index}>{renderPrefix(part)}</span>;
      });
    }
    return renderPrefix(text);
  };

  const renderPrefix = (text: string) => {
    const regex = /^(\[.*?\])(.*)/s;
    const match = text.match(regex);
    if (match) {
      return (
        <>
          <span className="agent-name">{match[1]}</span>
          {match[2]}
        </>
      );
    }
    return text;
  };

  return (
    <>
      <div className="chat-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-message ${msg.sender}`}>
            {renderMessageText(msg.text)}
          </div>
        ))}
        {isThinking && (
          <div className="agent-status">
            {agentStatus}
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="input-container">
        <span className={`status-dot ${agentStatus === 'Connected' ? 'online' : 'offline'}`} title={`Status: ${agentStatus}`}></span>
        <input 
          type="text" 
          className="chat-input" 
          placeholder="Type your CAD instructions here..." 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button 
          className="send-button" 
          onClick={handleSend}
          disabled={!inputValue.trim() || !ws}
        >
          ↑
        </button>
      </div>
    </>
  )
}

export default App
