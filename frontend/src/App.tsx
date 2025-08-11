import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import Sidebar, { Chat } from './components/Sidebar';
import BotCreationModal, { BotConfig } from './components/BotCreationModal';
import { Message } from './components/MessageBubble';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showBotModal, setShowBotModal] = useState(false);
  const [currentBotConfig, setCurrentBotConfig] = useState<BotConfig | undefined>(undefined);

  // Get current active chat's messages
  const activeChat = chats.find(chat => chat.id === activeChatId);
  const messages = activeChat?.messages || [];

  const handleSendMessage = (messageText: string) => {
    if (!messageText.trim()) return;

    // If no active chat exists, create a temporary one
    if (!activeChatId) {
      const tempChat: Chat = {
        id: 'temp-' + Date.now(),
        title: 'New Chat',
        date: new Date().toLocaleDateString(),
        isActive: true,
        messages: []
      };
      setChats([tempChat]);
      setActiveChatId(tempChat.id);
    }

    const newMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    // Update the active chat with the new message
    setChats(prev => prev.map(chat => {
      if (chat.id === activeChatId) {
        const updatedMessages = [...chat.messages, newMessage];
        
        // Update chat title if this is the first message
        const newTitle = chat.messages.length === 0 
          ? (messageText.length > 30 ? messageText.substring(0, 30) + '...' : messageText)
          : chat.title;
        
        return {
          ...chat,
          title: newTitle,
          messages: updatedMessages
        };
      }
      return chat;
    }));

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

      // Update the active chat with the bot response
      setChats(prev => prev.map(chat => {
        if (chat.id === activeChatId) {
          const updatedMessages = [...chat.messages, botMessage];
          
          // Calculate metrics
          const botMessages = updatedMessages.filter(msg => !msg.isUser);
          const totalResponseTime = botMessages.reduce((sum, msg) => sum + (msg.responseTime || 0), 0);
          const averageResponseTime = botMessages.length > 0 ? totalResponseTime / botMessages.length : 0;
          
          return {
            ...chat,
            messages: updatedMessages,
            averageResponseTime: Math.round(averageResponseTime),
            messageCount: updatedMessages.length
          };
        }
        return chat;
      }));
      
      setIsLoading(false);
    }, 1500);
  };

  const handleNewChat = () => {
    setShowBotModal(true);
  };

  const handleSelectChat = (chatId: string) => {
    // Deactivate all chats and activate the selected one
    setChats(prev => prev.map(chat => ({
      ...chat,
      isActive: chat.id === chatId
    })));
    
    setActiveChatId(chatId);
    
    // Get the selected chat's bot config
    const selectedChat = chats.find(chat => chat.id === chatId);
    setCurrentBotConfig(selectedChat?.botConfig);
    // Messages are now automatically loaded from the activeChat computed value
  };

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleMainContentClick = () => {
    if (window.innerWidth <= 768 && sidebarOpen) {
      setSidebarOpen(false);
    }
  };

  const handleBotCreation = (botConfig: BotConfig) => {
    setCurrentBotConfig(botConfig);
    setShowBotModal(false);
    
    // Create new chat with bot config
    const newChat: Chat = {
      id: Date.now().toString(),
      title: botConfig.name,
      date: new Date().toLocaleDateString(),
      isActive: true,
      botConfig: botConfig,
      messages: [] // Initialize messages for new chat
    };

    // Deactivate current chat
    setChats(prev => prev.map(chat => ({ ...chat, isActive: false })));
    
    // Add new chat
    setChats(prev => [...prev, newChat]);
    setActiveChatId(newChat.id);
    
    // Add welcome message
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      text: `# Welcome! I'm ${botConfig.name} 🤖

${botConfig.persona}

I'm here to help you learn and grow. Feel free to ask me anything!

**Model**: ${botConfig.model}

*What would you like to explore today?*`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      responseTime: 0
    };
    
    // Update the new chat with the welcome message
    setChats(prev => prev.map(chat => {
      if (chat.id === newChat.id) {
        return {
          ...chat,
          messages: [welcomeMessage]
        };
      }
      return chat;
    }));
  };

  const handleBeginClick = () => {
    setShowBotModal(true);
  };

  const handleDeleteChat = (chatId: string) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    
    // If we're deleting the active chat, clear the active state
    if (activeChatId === chatId) {
      setActiveChatId(null);
      setCurrentBotConfig(undefined);
    }
  };

  return (
    <div className="App">
      {chats.length > 0 && (
        <Sidebar 
          chats={chats}
          activeChatId={activeChatId}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          isOpen={sidebarOpen}
        />
      )}
      
      <div className="main-content" onClick={handleMainContentClick}>
        <Header onMenuToggle={handleMenuToggle} />
        
        <ChatWindow messages={messages} isLoading={isLoading} />
        <InputBar onSendMessage={handleSendMessage} botConfig={currentBotConfig} />
        
        {chats.length === 0 && (
          <div className="welcome-overlay">
            <div className="welcome-content">
              <h1>Welcome to Minimal Futuristic Classroom</h1>
              <p>Create your first AI tutor to start learning</p>
              <button className="begin-button" onClick={handleBeginClick}>
                Begin
              </button>
            </div>
          </div>
        )}
      </div>

      <BotCreationModal
        isOpen={showBotModal}
        onClose={() => setShowBotModal(false)}
        onSave={handleBotCreation}
      />
    </div>
  );
}

export default App;
