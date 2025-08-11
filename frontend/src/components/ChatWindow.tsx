import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🎓</div>
            <h3>Welcome to Your Classroom!</h3>
            <p>Ask your tutor anything and start learning in a fun, interactive way.</p>
          </div>
        )}
        
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message.text}
            isUser={message.isUser}
            timestamp={message.timestamp}
          />
        ))}
        
        {isLoading && (
          <div className="message-bubble bot-message">
            <div className="bot-avatar">
              <svg className="robot-icon-small" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
                <circle cx="9" cy="9" r="1" fill="currentColor"/>
                <circle cx="15" cy="9" r="1" fill="currentColor"/>
                <path d="M9 15C9 13.8954 9.89543 13 11 13H13C14.1046 13 15 13.8954 15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
