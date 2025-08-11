import React from 'react';

interface HeaderProps {
  onMenuToggle?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
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
              src="/assets/colorizeAnimationTest3.gif" 
              alt="Bot Avatar" 
              className="robot-icon"
            />
          </div>
        </div>
        
        <div className="header-center">
          <h1 className="app-title">Minimal Futuristic Classroom</h1>
        </div>
      </div>
    </div>
  );
};

export default Header;
