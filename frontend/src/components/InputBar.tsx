import React, { useState } from 'react';

interface InputBarProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const InputBar: React.FC<InputBarProps> = ({ onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSendMessage = () => {
    if (!inputValue.trim() || isLoading) return;
    onSendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="input-bar">
      <div className="input-container">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask your tutor anything..."
          disabled={isLoading}
          aria-label="Message input"
          className="message-input"
          rows={1}
        />
        
        <div className="bot-info">
          <div className="bot-details">
            <div className="bot-detail">
              <span className="bot-detail-label">Model:</span>
              <span className="bot-detail-value">GPT-4</span>
            </div>
            <div className="bot-detail">
              <span className="bot-detail-label">Persona:</span>
              <span className="bot-detail-value">Friendly Tutor</span>
            </div>
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
            aria-label="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputBar;
