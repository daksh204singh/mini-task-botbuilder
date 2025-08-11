import React from 'react';

export interface Chat {
  id: string;
  title: string;
  date: string;
  isActive: boolean;
  averageResponseTime?: number;
  messageCount?: number;
}

interface SidebarProps {
  chats: Chat[];
  activeChatId: string | null;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  isOpen?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  chats, 
  activeChatId, 
  onNewChat, 
  onSelectChat,
  isOpen = true 
}) => {
  const formatResponseTime = (time: number) => {
    if (time < 1000) {
      return `${time}ms`;
    } else {
      return `${(time / 1000).toFixed(1)}s`;
    }
  };

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-button" onClick={onNewChat}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          New Chat
        </button>
      </div>
      
      <div className="chat-list">
        {chats.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '20px', 
            color: '#718096',
            fontSize: '13px'
          }}>
            No chats yet
          </div>
        ) : (
          chats.map((chat) => (
            <div
              key={chat.id}
              className={`chat-item ${chat.isActive ? 'active' : ''}`}
              onClick={() => onSelectChat(chat.id)}
            >
              <svg className="chat-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <div className="chat-item-content">
                <div className="chat-item-title">{chat.title}</div>
                <div className="chat-item-meta">
                  <span className="chat-item-date">{chat.date}</span>
                  {chat.averageResponseTime && (
                    <span className="chat-item-response-time">
                      • Avg: {formatResponseTime(chat.averageResponseTime)}
                    </span>
                  )}
                  {chat.messageCount && (
                    <span className="chat-item-message-count">
                      • {chat.messageCount} messages
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Sidebar;
