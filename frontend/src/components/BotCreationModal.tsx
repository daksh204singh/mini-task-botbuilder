import React, { useState } from 'react';

export interface BotConfig {
  name: string;
  persona: string;
  model: string;
}

interface BotCreationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (botConfig: BotConfig) => void;
}

const BotCreationModal: React.FC<BotCreationModalProps> = ({ isOpen, onClose, onSave }) => {
  const [botName, setBotName] = useState('');
  const [persona, setPersona] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4');

  // Character limits
  const BOT_NAME_LIMIT = 15;
  const PERSONA_LIMIT = 60;

  const models = [
    { id: 'gpt-4', name: 'GPT-4', description: 'Most capable model for complex tasks' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and efficient for most tasks' },
    { id: 'claude-3', name: 'Claude 3', description: 'Excellent for analysis and writing' },
    { id: 'gemini-pro', name: 'Gemini Pro', description: 'Great for creative and technical tasks' }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (botName.trim() && persona.trim()) {
      onSave({
        name: botName.trim(),
        persona: persona.trim(),
        model: selectedModel
      });
      // Reset form
      setBotName('');
      setPersona('');
      setSelectedModel('gpt-4');
    }
  };

  const handleBotNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= BOT_NAME_LIMIT) {
      setBotName(value);
    }
  };

  const handlePersonaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= PERSONA_LIMIT) {
      setPersona(value);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Create Your AI Tutor</h2>
          <button className="modal-close" onClick={onClose}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="botName">Bot Name</label>
            <input
              id="botName"
              type="text"
              value={botName}
              onChange={handleBotNameChange}
              placeholder="e.g., Math Tutor, Science Helper"
              maxLength={BOT_NAME_LIMIT}
              required
            />
            <div className="character-count">
              {botName.length}/{BOT_NAME_LIMIT}
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="persona">Persona</label>
            <input
              id="persona"
              type="text"
              value={persona}
              onChange={handlePersonaChange}
              placeholder="e.g., Friendly math tutor who explains concepts clearly"
              maxLength={PERSONA_LIMIT}
              required
            />
            <div className="character-count">
              {persona.length}/{PERSONA_LIMIT}
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="model">AI Model</label>
            <select
              id="model"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              {models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name} - {model.description}
                </option>
              ))}
            </select>
          </div>
          
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Create Bot & Start Chat
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BotCreationModal;
