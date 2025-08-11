import React, { useState, useRef, useEffect } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import './App.css';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate bot response with educational responses
    setTimeout(() => {
      const botResponses = [
        "Great question! Let me explain that in a simple way...",
        "That's an interesting topic! Here's what you should know...",
        "Excellent curiosity! Let me break this down for you...",
        "I love this question! Here's the answer...",
        "That's a smart question! Let me help you understand...",
        "Perfect! Here's what I can tell you about that...",
        "That's a wonderful question! Let me explain...",
        "I'm excited to help you with this! Here's what I know..."
      ];
      
      const randomResponse = botResponses[Math.floor(Math.random() * botResponses.length)];
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `${randomResponse} ${messageText} is a fascinating topic to explore. I'm here to make learning fun and engaging for you!`,
        isUser: false,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, 1200);
  };

  return (
    <div className="App">
      <Header />
      <ChatWindow messages={messages} isLoading={isLoading} />
      <InputBar onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}

export default App;
