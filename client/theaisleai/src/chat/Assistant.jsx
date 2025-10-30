import React, { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";
import { CHAT } from "../urls"; 


const HR_CHAT_URL = CHAT.MULTI_AGENT_CHAT;
const FRONTEND_TOKEN = "lYrCN/UOC8c+e7CveLp1awTcoUJG8wGDYw5IaK5wf+w="; 

const Assistant = () => {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I'm your Finance Assistant, here to support you every step of the way. How can I help you today?",
    },
  ]);
  const [newMessage, setNewMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [chatSessionId, setChatSessionId] = useState(null); 
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = useCallback(async (e) => {
    if (e && e.preventDefault) {
        e.preventDefault();
    }
    
    const userQuestion = newMessage.trim();
    if (userQuestion === "" || isTyping) return;

    // 1. Add user message to history and clear input
    setMessages((prev) => [...prev, { sender: "user", text: userQuestion }]);
    setNewMessage(""); 
    setIsTyping(true); 

    try {
      // 2. Ensure session ID exists
      let currentChatId = chatSessionId;
      if (!currentChatId) {
        currentChatId = uuidv4();
        setChatSessionId(currentChatId);
      }
      
      // 3. Send query to backend using the successfully working URL
      const response = await axios.post(
        HR_CHAT_URL, 
        {
          query: userQuestion,
          chat_id: currentChatId,
          
        },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${FRONTEND_TOKEN}`,
          },
          
        }
      );

      
      const botAnswer = response.data.answer || response.data.response || "No answer from multi-agent backend";

      
      if (response.data.chat_id && !chatSessionId) {
        setChatSessionId(response.data.chat_id);
      }

      // 4. Update chat history with bot's response
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: botAnswer.normalize("NFC") },
      ]);
      
    } catch (error) {
      console.error("HR Assistant chat error:", error);
      
      
      let errorMessage = "Connection failed. Please check your network or contact IT.";
      if (error.code === 'ERR_NETWORK' || error.message.includes('CONNECTION_RESET')) {
          errorMessage = "Request succeeded on the server but the response was blocked. The conversation history may be updated.";
      } else if (error.response?.data?.detail) {
          errorMessage = `API Error: ${error.response.data.detail}`;
      } else if (error.message) {
          errorMessage = `Error: ${error.message}`;
      }

      // Display the error message in the chat
      setMessages((prev) => [
        ...prev,
        { 
          sender: "bot", 
          text: `🚨 ${errorMessage}` 
        },
      ]);
    } finally {
      setIsTyping(false); 
    }
  }, [newMessage, chatSessionId, isTyping]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && newMessage.trim() && !isTyping) {
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'linear-gradient(to bottom right, #f8fafc, #dbeafe, #ccfbf1)' }}>
      {/* Navbar */}
      <nav style={{ background: '#0d9488', padding: '16px 24px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', position: 'sticky', top: 0, zIndex: 1000 }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 'bold', color: 'white', letterSpacing: '0.5px', margin: 0 }}>
              HR Assistant
            </h1>
          </div>
        </div>
      </nav>

      {/* Chat Area */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', justifyContent: 'center', padding: '24px 16px' }}>
        <div style={{ width: '100%', maxWidth: '1000px', background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(10px)', borderRadius: '16px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', border: '1px solid rgba(255,255,255,0.6)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
            {messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  gap: '12px',
                  justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
                  marginBottom: '16px',
                  animation: 'fadeIn 0.3s ease-out'
                }}
              >
                {/* Bot Avatar */}
                {msg.sender === "bot" && (
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(to bottom right, #14b8a6, #06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                    </svg>
                  </div>
                )}
                {/* Message Bubble */}
                <div
                  style={{
                    maxWidth: '75%',
                    padding: '12px 20px',
                    borderRadius: '16px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    background: msg.sender === "user" ? 'linear-gradient(to right, #3b82f6, #6366f1)' : 'white',
                    color: msg.sender === "user" ? 'white' : '#1f2937',
                    border: msg.sender === "bot" ? '1px solid #e5e7eb' : 'none',
                    borderTopLeftRadius: msg.sender === "bot" ? '4px' : '16px',
                    borderTopRightRadius: msg.sender === "user" ? '4px' : '16px'
                  }}
                >
                  <p style={{ fontSize: '14px', lineHeight: '1.6', margin: 0 }}>{msg.text}</p>
                </div>
                {/* User Avatar */}
                {msg.sender === "user" && (
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(to bottom right, #3b82f6, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                  </div>
                )}
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', animation: 'fadeIn 0.3s ease-out' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(to bottom right, #14b8a6, #06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                  </svg>
                </div>
                <div style={{ maxWidth: '75%', padding: '12px 20px', borderRadius: '16px', borderTopLeftRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', background: 'white', border: '1px solid #e5e7eb' }}>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <div style={{ width: '8px', height: '8px', background: '#9ca3af', borderRadius: '50%', animation: 'bounce 1s infinite' }}></div>
                    <div style={{ width: '8px', height: '8px', background: '#9ca3af', borderRadius: '50%', animation: 'bounce 1s infinite 0.15s' }}></div>
                    <div style={{ width: '8px', height: '8px', background: '#9ca3af', borderRadius: '50%', animation: 'bounce 1s infinite 0.3s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} style={{ width: '100%', padding: '16px', borderTop: '1px solid rgba(229,231,235,0.5)', background:'#42baacff' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', background: 'white', borderRadius: '9999px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', border: '1px solid rgba(229,231,235,0.5)', padding: '12px 20px', transition: 'all 0.2s' }}>
              <input
                type="text"
                placeholder="Type your message..."
                style={{ flex: 1, outline: 'none', background: 'transparent', color: '#1f2937', fontSize: '14px', border: 'none', placeholder: { color: "#9ca3af" } }}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyDown} 
                disabled={isTyping} 
              />
              <button
                type="submit" 
                disabled={!newMessage.trim() || isTyping} 
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: (newMessage.trim() && !isTyping) ? 'linear-gradient(to right, #14b8a6, #06b6d4)' : '#a1a1ae', 
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: 'none',
                  cursor: (newMessage.trim() && !isTyping) ? 'pointer' : 'not-allowed',
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                  transition: 'all 0.2s',
                  opacity: (newMessage.trim() && !isTyping) ? 1 : 0.5
                }}
                onMouseEnter={(e) => {
                  if (newMessage.trim() && !isTyping) {
                    e.currentTarget.style.background = 'linear-gradient(to right, #0f766e, #0e7490)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (newMessage.trim() && !isTyping) {
                    e.currentTarget.style.background = 'linear-gradient(to right, #14b8a6, #06b6d4)';
                  }
                }}
                onMouseDown={(e) => {
                  if (newMessage.trim() && !isTyping) {
                    e.currentTarget.style.transform = 'scale(0.95)';
                  }
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>

      <style>{`
        input::placeholder {
        color: #9ca3af;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes bounce {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-5px);
          }
        }
      `}</style>
    </div>
  );
};

export default Assistant;