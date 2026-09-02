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
    // Use 38080 if running on Vite dev server (5173), otherwise use the dynamic host URL
    const isDev = window.location.port === '5173';
    const wsUrl = isDev 
      ? 'ws://127.0.0.1:38080/ws' 
      : `ws://${window.location.host}/ws`;
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      console.log('Connected to FreeGen Orchestrator');
      setAgentStatus('Connected');
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.state) {
          const s = data.state;
          if (s === 'waiting for user input ..') {
            setAgentStatus('Waiting for your input...');
          } else if (s === 'EXECUTION') {
            setAgentStatus('Executing in FreeCAD...');
          } else if (s === 'STARTED') {
            setAgentStatus('Orchestrator started...');
          } else if (s === 'COMPLETED') {
            setAgentStatus('Completed');
          } else if (s === 'FAILED') {
            setAgentStatus('Failed');
          } else {
            setAgentStatus(`${s.toLowerCase()} agent thinking...`);
          }
        }
        
        if (data.message) {
          const senderType = data.type || 'agent';
          setMessages(prev => [...prev, {
            id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
            sender: senderType,
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
    setMessages(prev => [...prev, { 
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`, 
      sender: 'user', 
      text: msg 
    }]);
    ws.send(msg);
    setInputValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const isThinking = agentStatus && !['Connected', 'Disconnected', 'Completed', 'Failed'].includes(agentStatus);

  // Formatter to colorize [Agent Name] tags and format code blocks
  const renderMessageText = (text: string) => {
    if (text.includes('```python') || text.includes('```')) {
      const parts = text.split(/```(?:python)?\n?/);
      return parts.map((part, index) => {
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
      <header className="header titlebar">
        <div className="header-left">
          <img src="/freegen.ico" alt="FreeGen Logo" className="header-logo" />
          <span className="header-title">FreeGen</span>
        </div>
        <div className="header-right">
          <span className={`status-dot ${agentStatus !== 'Disconnected' ? 'online' : 'offline'}`} title={`Status: ${agentStatus}`}></span>
        </div>
      </header>

      <div className="chat-container">
        {messages.length === 0 && (
          <div className="chat-message process">
            Welcome to FreeGen! Type any 3D CAD instruction to begin (e.g., "Create a 20mm cube" or "Build a cylinder of radius 15mm and height 40mm").
          </div>
        )}
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

