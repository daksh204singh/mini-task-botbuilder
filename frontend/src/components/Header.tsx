import React from 'react';

interface HeaderProps {
  onMenuToggle?: () => void;
  onLogsToggle?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle, onLogsToggle }) => {
  return (
    <div className="app-header">
      <div className="header-content">
        <div className="header-left">
          <button 
            className="mobile-menu-button"
            onClick={onMenuToggle}
            aria-label="Toggle menu"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18"/>
            </svg>
          </button>
          <div className="robot-avatar">
            <img 
              src={`${process.env.PUBLIC_URL}/assets/AIRobot.jpg`} 
              alt="Bot Avatar" 
              className="robot-icon"
            />
          </div>
        </div>
        
        <div className="header-center">
          <h1 className="app-title">TutorBot</h1>
        </div>
        
        <div className="header-right">
          <button 
            className="logs-button"
            onClick={onLogsToggle}
            aria-label="View chat logs"
            title="View chat logs"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Header;
