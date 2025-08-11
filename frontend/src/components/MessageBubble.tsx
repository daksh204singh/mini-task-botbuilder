import React from 'react';
import ReactMarkdown from 'react-markdown';

export interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
  responseTime?: number; // Time in milliseconds
}

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const formatResponseTime = (time: number) => {
    if (time < 1000) {
      return `${time}ms`;
    } else {
      return `${(time / 1000).toFixed(1)}s`;
    }
  };

  return (
    <div className={`message-bubble ${message.isUser ? 'user-message' : 'bot-message'}`}>
      {!message.isUser && (
        <div className="bot-avatar">
          <img 
            src="/assets/colorizeAnimationTest3.gif" 
            alt="Bot Avatar" 
            className="robot-icon-small"
          />
        </div>
      )}
      
      <div className="message-content">
        <div className="message-text">
          {message.isUser ? (
            message.text
          ) : (
            <div className="markdown-content">
              <ReactMarkdown>{message.text}</ReactMarkdown>
            </div>
          )}
        </div>
        <div className="message-timestamp">
          {message.timestamp}
          {!message.isUser && message.responseTime && (
            <span className="response-time">
              • {formatResponseTime(message.responseTime)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
