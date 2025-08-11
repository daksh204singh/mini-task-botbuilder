import React, { useState, useRef, useEffect } from 'react';
import { BotConfig } from './BotCreationModal';

interface InputBarProps {
  onSendMessage: (messageText: string) => void;
  botConfig?: BotConfig;
}

const InputBar: React.FC<InputBarProps> = ({ onSendMessage, botConfig }) => {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 100; // max-height from CSS
      const newHeight = Math.min(scrollHeight, maxHeight);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    adjustTextareaHeight();
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue]);

  return (
    <div className="input-bar">
      <div className="input-container">
        <textarea
          ref={textareaRef}
          className="message-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Ask your tutor..."
          rows={1}
        />
        
        <div className="bot-info">
          <div className="bot-details">
            {botConfig ? (
              <>
                <div className="bot-detail">
                  <span className="bot-detail-label">Bot:</span>
                  <span className="bot-detail-value">{botConfig.name}</span>
                </div>
                <div className="bot-detail">
                  <span className="bot-detail-label">Model:</span>
                  <span className="bot-detail-value">{botConfig.model}</span>
                </div>
                <div className="bot-detail">
                  <span className="bot-detail-label">Persona:</span>
                  <span className="bot-detail-value">{botConfig.persona}</span>
                </div>
              </>
            ) : (
              <>
                <div className="bot-detail">
                  <span className="bot-detail-label">Model:</span>
                  <span className="bot-detail-value">GPT-4</span>
                </div>
                <div className="bot-detail">
                  <span className="bot-detail-label">Persona:</span>
                  <span className="bot-detail-value">Tutor</span>
                </div>
              </>
            )}
          </div>
          
          <button 
            className="send-button" 
            onClick={handleSendMessage}
            disabled={!inputValue.trim()}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputBar;
