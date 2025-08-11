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
  const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash-exp');

  // Character limits
  const BOT_NAME_LIMIT = 15;
  const PERSONA_LIMIT = 60;

  const models = [
    { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash', description: 'Latest fast and efficient model for general tasks' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', description: 'Previous generation fast model' }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (botName.trim() && persona.trim() && selectedModel) {
      onSave({
        name: botName.trim(),
        persona: persona.trim(),
        model: selectedModel
      });
      // Reset form
      setBotName('');
      setPersona('');
      setSelectedModel('gemini-2.0-flash-exp');
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
              required
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
