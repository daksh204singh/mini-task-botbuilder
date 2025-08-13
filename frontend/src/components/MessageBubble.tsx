import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import 'katex/dist/katex.min.css';
import 'highlight.js/styles/github.css';

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
            src="/assets/AIRobot.jpg" 
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
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex, rehypeHighlight]}
                components={{
                  // Custom styling for tables
                  table: ({node, ...props}) => (
                    <div className="table-container">
                      <table {...props} />
                    </div>
                  ),
                  // Custom styling for code blocks
                  code: ({node, className, children, ...props}: any) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !className || !match;
                    return !isInline ? (
                      <pre className={className}>
                        <code className={className} {...props}>
                          {children}
                        </code>
                      </pre>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {message.text}
              </ReactMarkdown>
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
