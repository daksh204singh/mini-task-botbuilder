import React from 'react';

interface MessageBubbleProps {
  message: string;
  isUser: boolean;
  timestamp: Date;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser, timestamp }) => {
  return (
    <div className={`message-bubble ${isUser ? 'user-message' : 'bot-message'}`}>
      {!isUser && (
        <div className="bot-avatar">
          <svg className="robot-icon-small" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
            <circle cx="9" cy="9" r="1" fill="currentColor"/>
            <circle cx="15" cy="9" r="1" fill="currentColor"/>
            <path d="M9 15C9 13.8954 9.89543 13 11 13H13C14.1046 13 15 13.8954 15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
      )}
      <div className="message-content">
        <div className="message-text">{message}</div>
        <div className="message-timestamp">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
