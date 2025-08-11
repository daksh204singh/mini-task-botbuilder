import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import Sidebar, { Chat } from './components/Sidebar';
import BotCreationModal, { BotConfig } from './components/BotCreationModal';
import { Message } from './components/MessageBubble';
import LogsPanel, { LogEntry } from './components/LogsPanel';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showBotModal, setShowBotModal] = useState(false);
  const [currentBotConfig, setCurrentBotConfig] = useState<BotConfig | undefined>(undefined);
  const [isInitialized, setIsInitialized] = useState(false);
  const [showLogsPanel, setShowLogsPanel] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Load data from localStorage on component mount
  useEffect(() => {
    try {
      console.log('Loading data from localStorage...');
      const savedChats = localStorage.getItem('mini-task-chats');
      const savedActiveChatId = localStorage.getItem('mini-task-activeChatId');
      const savedCurrentBotConfig = localStorage.getItem('mini-task-currentBotConfig');
      const savedSidebarOpen = localStorage.getItem('mini-task-sidebarOpen');
      const savedLogs = localStorage.getItem('mini-task-logs');

      console.log('Saved chats:', savedChats);
      console.log('Saved active chat ID:', savedActiveChatId);

      if (savedChats) {
        const parsedChats = JSON.parse(savedChats);
        console.log('Parsed chats:', parsedChats);
        if (Array.isArray(parsedChats) && parsedChats.length > 0) {
          setChats(parsedChats);
        }
      }
      
      if (savedActiveChatId) {
        setActiveChatId(savedActiveChatId);
      }
      
      if (savedCurrentBotConfig) {
        setCurrentBotConfig(JSON.parse(savedCurrentBotConfig));
      }
      
      if (savedSidebarOpen !== null) {
        setSidebarOpen(JSON.parse(savedSidebarOpen));
      }
      
      if (savedLogs) {
        const parsedLogs = JSON.parse(savedLogs);
        if (Array.isArray(parsedLogs)) {
          setLogs(parsedLogs);
        }
      }
      
      setIsInitialized(true);
    } catch (error) {
      console.error('Error loading from localStorage:', error);
      setIsInitialized(true);
    }
  }, []);

  // Save chats to localStorage whenever chats change (but only after initialization)
  useEffect(() => {
    if (!isInitialized) return;
    
    try {
      console.log('Saving chats to localStorage:', chats);
      localStorage.setItem('mini-task-chats', JSON.stringify(chats));
    } catch (error) {
      console.error('Error saving chats to localStorage:', error);
    }
  }, [chats, isInitialized]);

  // Save activeChatId to localStorage whenever it changes
  useEffect(() => {
    if (!isInitialized) return;
    
    try {
      if (activeChatId) {
        localStorage.setItem('mini-task-activeChatId', activeChatId);
      } else {
        localStorage.removeItem('mini-task-activeChatId');
      }
    } catch (error) {
      console.error('Error saving activeChatId to localStorage:', error);
    }
  }, [activeChatId, isInitialized]);

  // Save currentBotConfig to localStorage whenever it changes
  useEffect(() => {
    if (!isInitialized) return;
    
    try {
      if (currentBotConfig) {
        localStorage.setItem('mini-task-currentBotConfig', JSON.stringify(currentBotConfig));
      } else {
        localStorage.removeItem('mini-task-currentBotConfig');
      }
    } catch (error) {
      console.error('Error saving currentBotConfig to localStorage:', error);
    }
  }, [currentBotConfig, isInitialized]);

  // Save sidebarOpen to localStorage whenever it changes
  useEffect(() => {
    if (!isInitialized) return;
    
    try {
      localStorage.setItem('mini-task-sidebarOpen', JSON.stringify(sidebarOpen));
    } catch (error) {
      console.error('Error saving sidebarOpen to localStorage:', error);
    }
  }, [sidebarOpen, isInitialized]);

  // Save logs to localStorage whenever they change
  useEffect(() => {
    if (!isInitialized) return;
    
    try {
      localStorage.setItem('mini-task-logs', JSON.stringify(logs));
    } catch (error) {
      console.error('Error saving logs to localStorage:', error);
    }
  }, [logs, isInitialized]);

  // Calculate storage usage
  const getStorageUsage = () => {
    try {
      let totalSize = 0;
      const keys = ['mini-task-chats', 'mini-task-activeChatId', 'mini-task-currentBotConfig', 'mini-task-sidebarOpen', 'mini-task-logs'];
      
      keys.forEach(key => {
        const item = localStorage.getItem(key);
        if (item) {
          totalSize += item.length;
        }
      });
      
      // Convert to MB (1 character = 2 bytes in UTF-16)
      const sizeInMB = (totalSize * 2) / (1024 * 1024);
      const maxSizeInMB = 5; // Conservative estimate of 5MB limit
      const percentage = (sizeInMB / maxSizeInMB) * 100;
      
      return {
        used: sizeInMB,
        max: maxSizeInMB,
        percentage: Math.min(percentage, 100),
        totalSize
      };
    } catch (error) {
      console.error('Error calculating storage usage:', error);
      return { used: 0, max: 5, percentage: 0, totalSize: 0 };
    }
  };

  // Get current active chat's messages
  const activeChat = chats.find(chat => chat.id === activeChatId);
  const messages = activeChat?.messages || [];

  const handleSendMessage = async (messageText: string) => {
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

    // Prepare messages for API call
    const messagesForAPI = [
      ...messages.map(msg => ({
        role: msg.isUser ? 'user' : 'assistant',
        content: msg.text,
        timestamp: msg.timestamp
      })),
      {
        role: 'user',
        content: messageText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];

    // Call backend API
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messagesForAPI,
          persona: {
            bot_name: currentBotConfig?.name || 'Assistant',
            persona: currentBotConfig?.persona || 'a helpful assistant',
            model: currentBotConfig?.model || 'gemini-2.0-flash-exp'
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        responseTime: Math.round(data.response_time * 1000)
      };

      // Create log entry for this interaction
      const logEntry: LogEntry = {
        id: Date.now().toString(),
        date: new Date().toLocaleDateString(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: data.model,
        prompt: messageText,
        response: data.response
      };

      // Add log entry and keep only last 5
      setLogs(prev => {
        const newLogs = [logEntry, ...prev.slice(0, 4)];
        console.log('Updated logs:', newLogs);
        return newLogs;
      });

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
      
    } catch (error) {
      console.error('Error calling backend API:', error);
      
      // Fallback error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        responseTime: 0
      };

      setChats(prev => prev.map(chat => {
        if (chat.id === activeChatId) {
          return {
            ...chat,
            messages: [...chat.messages, errorMessage]
          };
        }
        return chat;
      }));
    } finally {
      setIsLoading(false);
    }
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

  const handleLogsToggle = () => {
    setShowLogsPanel(!showLogsPanel);
  };

  const handleMainContentClick = () => {
    if (window.innerWidth <= 768 && sidebarOpen) {
      setSidebarOpen(false);
    }
  };

  const handleBotCreation = async (botConfig: BotConfig) => {
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
    
    // Show loading state
    setIsLoading(true);
    
    try {
      // Call backend API for welcome message
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
                  body: JSON.stringify({
            messages: [{
              role: 'user',
              content: 'Please introduce yourself as a new tutor and welcome the user to start a conversation.',
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }],
          persona: {
            bot_name: botConfig.name,
            persona: botConfig.persona,
            model: botConfig.model
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Create welcome message from API response
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        text: data.response,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        responseTime: Math.round(data.response_time * 1000)
      };
      
      // Create log entry for the welcome message
      const welcomeLogEntry: LogEntry = {
        id: Date.now().toString(),
        date: new Date().toLocaleDateString(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: data.model,
        prompt: "New chat started",
        response: data.response
      };

      // Add welcome log entry
      setLogs(prev => {
        const newLogs = [welcomeLogEntry, ...prev.slice(0, 4)];
        console.log('Added welcome log entry:', newLogs);
        return newLogs;
      });

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
      
    } catch (error) {
      console.error('Error generating welcome message:', error);
      
      // Fallback welcome message
      const fallbackMessage: Message = {
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

      // Create fallback log entry
      const fallbackLogEntry: LogEntry = {
        id: Date.now().toString(),
        date: new Date().toLocaleDateString(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: botConfig.model,
        prompt: "New chat started",
        response: fallbackMessage.text
      };

      // Add fallback log entry
      setLogs(prev => {
        const newLogs = [fallbackLogEntry, ...prev.slice(0, 4)];
        console.log('Added fallback welcome log entry:', newLogs);
        return newLogs;
      });

      // Update the new chat with the fallback welcome message
      setChats(prev => prev.map(chat => {
        if (chat.id === newChat.id) {
          return {
            ...chat,
            messages: [fallbackMessage]
          };
        }
        return chat;
      }));
    } finally {
      setIsLoading(false);
    }
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

  const clearAllData = () => {
    try {
      // Clear localStorage
      localStorage.removeItem('mini-task-chats');
      localStorage.removeItem('mini-task-activeChatId');
      localStorage.removeItem('mini-task-currentBotConfig');
      localStorage.removeItem('mini-task-sidebarOpen');
      localStorage.removeItem('mini-task-logs');
      
      // Reset state
      setChats([]);
      setActiveChatId(null);
      setCurrentBotConfig(undefined);
      setSidebarOpen(true);
      setShowBotModal(false);
      setLogs([]);
    } catch (error) {
      console.error('Error clearing data:', error);
    }
  };

  // Check if we should show the welcome screen (no chats at all)
  const shouldShowWelcomeScreen = chats.length === 0;
  
  // Check if we should show the no-active-chat message (has chats but none selected)
  // const shouldShowNoActiveChat = chats.length > 0 && !activeChatId;

  return (
    <div className="App">
      {chats.length > 0 && (
        <Sidebar 
          chats={chats}
          activeChatId={activeChatId}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          onClearAllData={clearAllData}
          storageUsage={getStorageUsage()}
          isOpen={sidebarOpen}
        />
      )}
      
      <div className="main-content" onClick={handleMainContentClick}>
        <Header onMenuToggle={handleMenuToggle} onLogsToggle={handleLogsToggle} />
        
        {activeChatId ? (
          <>
            <ChatWindow messages={messages} isLoading={isLoading} />
            <InputBar onSendMessage={handleSendMessage} botConfig={currentBotConfig} />
          </>
        ) : (
          <div className="no-active-chat-container">
            <div className="no-active-chat-content">
              <div className="no-active-chat-icon">💬</div>
              <h3>No Active Chat</h3>
              <p>Select a chat from the sidebar or create a new one to start messaging.</p>
              <div className="no-active-chat-actions">
                <button className="new-chat-button-secondary" onClick={handleNewChat}>
                  New Chat
                </button>
              </div>
            </div>
          </div>
        )}
        
        {shouldShowWelcomeScreen && (
          <div className="welcome-overlay">
            <div className="welcome-content">
              <h1>Welcome to TutorBot</h1>
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

      {showLogsPanel && (
        <LogsPanel
          onClose={() => setShowLogsPanel(false)}
          logs={logs}
        />
      )}
    </div>
  );
}

export default App;
