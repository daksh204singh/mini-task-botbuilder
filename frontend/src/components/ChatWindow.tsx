import React, { useRef, useEffect, useState } from 'react';
import MessageBubble, { Message } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [typingStartTime, setTypingStartTime] = useState<number | null>(null);
  const [currentTypingTime, setCurrentTypingTime] = useState<number>(0);
  const [isScrolling,setIsScrolling]=useState(false);
  const scrollTimeout = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // Always scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isLoading) {
      setTypingStartTime(Date.now());
      setCurrentTypingTime(0);
      // Scroll to bottom when loading starts
      scrollToBottom();
    } else {
      setTypingStartTime(null);
      setCurrentTypingTime(0);
      // Scroll to bottom when loading ends
      scrollToBottom();
    }
  }, [isLoading]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (typingStartTime) {
      interval = setInterval(() => {
        setCurrentTypingTime(Date.now() - typingStartTime);
      }, 100);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [typingStartTime]);

  useEffect(()=>{
    const el=containerRef.current;
    if(!el) return;
    const onScroll=()=>{
      if(scrollTimeout.current) clearTimeout(scrollTimeout.current);
      setIsScrolling(true);
      scrollTimeout.current=setTimeout(()=>setIsScrolling(false),1000);
    };
    el.addEventListener('scroll',onScroll);
    return ()=>{el.removeEventListener('scroll',onScroll); if(scrollTimeout.current) clearTimeout(scrollTimeout.current);} ;
  },[]);

  const formatTypingTime = (time: number) => {
    if (time < 1000) {
      return `${time}ms`;
    } else {
      return `${(time / 1000).toFixed(1)}s`;
    }
  };

  return (
    <div ref={containerRef} className={`chat-window ${isScrolling ? 'scrolling' : ''}`}>
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🤖</div>
            <h3>Welcome to TutorBot</h3>
            <p>Start a conversation with your AI tutor. Ask questions, get explanations, or explore any topic you'd like to learn about.</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="message-bubble bot-message">
                <div className="bot-avatar">
                  <img 
                    src="/assets/colorizeAnimationTest3.gif" 
                    alt="Bot Avatar" 
                    className="robot-icon-small"
                  />
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                    {currentTypingTime > 0 && (
                      <span className="typing-time">
                        {formatTypingTime(currentTypingTime)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
