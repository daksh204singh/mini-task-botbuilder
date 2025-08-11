import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import Sidebar, { Chat } from './components/Sidebar';
import { Message } from './components/MessageBubble';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSendMessage = (messageText: string) => {
    if (!messageText.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    // If this is the first message in a new chat, update the chat title
    if (messages.length === 0 && activeChatId) {
      const chatTitle = messageText.length > 30 ? messageText.substring(0, 30) + '...' : messageText;
      setChats(prev => prev.map(chat => 
        chat.id === activeChatId 
          ? { ...chat, title: chatTitle }
          : chat
      ));
    }

    setMessages(prev => [...prev, newMessage]);
    setIsLoading(true);

    // Track response start time
    const responseStartTime = Date.now();

    // Simulate bot response with markdown
    setTimeout(() => {
      const botResponses = [
        {
          text: `# Welcome to the Classroom! 👋

I'm your AI tutor, ready to help you learn. Here are some things I can help you with:

## 📚 Subjects I can teach:
- **Mathematics**: Algebra, Calculus, Geometry
- **Science**: Physics, Chemistry, Biology
- **Programming**: Python, JavaScript, React
- **Languages**: English, Spanish, French
- **History**: World History, Art History

## 💡 How to get started:
1. Ask me any question
2. Request explanations of concepts
3. Get help with homework problems
4. Practice with interactive examples

*What would you like to learn today?*`,
          delay: 1200
        },
        {
          text: `## Great question! 🤔

Let me break this down for you:

### Key Points:
- **Point 1**: This is important to understand
- **Point 2**: Another crucial concept
- **Point 3**: Don't forget this detail

### Example:
\`\`\`python
def example_function():
    return "This is how it works"
\`\`\`

> **Pro tip**: Always remember to practice what you learn!

Would you like me to explain anything specific about this topic?`,
          delay: 1800
        },
        {
          text: `### Here's what you need to know:

**Step 1**: Start with the basics
**Step 2**: Build on your foundation  
**Step 3**: Practice regularly

| Concept | Description | Difficulty |
|---------|-------------|------------|
| Basic | Foundation concepts | Easy |
| Intermediate | Building blocks | Medium |
| Advanced | Complex applications | Hard |

\`\`\`javascript
// Example code
function learn() {
    console.log("Learning is fun!");
}
\`\`\`

*Keep practicing and you'll master this in no time!*`,
          delay: 2200
        },
        {
          text: `# Let's explore this together! 🚀

## What we'll cover:
1. **Introduction** - Getting started
2. **Core Concepts** - Understanding the basics
3. **Practical Examples** - Real-world applications
4. **Practice Problems** - Test your knowledge

### Quick Start:
\`\`\`html
<div class="learning">
    <h1>Learning is Awesome!</h1>
    <p>Every expert was once a beginner.</p>
</div>
\`\`\`

> *"The only way to learn a new programming language is by writing programs in it."* - Dennis Ritchie

Ready to dive deeper into this topic?`,
          delay: 1600
        }
      ];

      const randomResponse = botResponses[Math.floor(Math.random() * botResponses.length)];
      
      // Calculate response time
      const responseTime = Date.now() - responseStartTime;
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: randomResponse.text,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        responseTime: responseTime
      };

      setMessages(prev => {
        const newMessages = [...prev, botMessage];
        
        // Update chat metrics
        if (activeChatId) {
          const botMessages = newMessages.filter(msg => !msg.isUser);
          const totalResponseTime = botMessages.reduce((sum, msg) => sum + (msg.responseTime || 0), 0);
          const averageResponseTime = botMessages.length > 0 ? totalResponseTime / botMessages.length : 0;
          
          setChats(prevChats => prevChats.map(chat => 
            chat.id === activeChatId 
              ? { 
                  ...chat, 
                  averageResponseTime: Math.round(averageResponseTime),
                  messageCount: newMessages.length
                }
              : chat
          ));
        }
        
        return newMessages;
      });
      
      setIsLoading(false);
    }, 1500);
  };

  const handleNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: `Chat ${chats.length + 1}`,
      date: new Date().toLocaleDateString(),
      isActive: true
    };

    // Deactivate current chat
    setChats(prev => prev.map(chat => ({ ...chat, isActive: false })));
    
    // Add new chat
    setChats(prev => [...prev, newChat]);
    setActiveChatId(newChat.id);
    setMessages([]);
  };

  const handleSelectChat = (chatId: string) => {
    setChats(prev => prev.map(chat => ({ 
      ...chat, 
      isActive: chat.id === chatId 
    })));
    setActiveChatId(chatId);
    // In a real app, you'd load the messages for this chat
    setMessages([]);
  };

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleMainContentClick = () => {
    if (window.innerWidth <= 768 && sidebarOpen) {
      setSidebarOpen(false);
    }
  };

  return (
    <div className="App">
      <Sidebar 
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        isOpen={sidebarOpen}
      />
      
      <div className="main-content" onClick={handleMainContentClick}>
        <Header onMenuToggle={handleMenuToggle} />
        <ChatWindow messages={messages} isLoading={isLoading} />
        <InputBar onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
}

export default App;
