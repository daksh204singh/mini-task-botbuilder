import React from 'react';
import './LogsPanel.css';

export interface LogEntry {
  id: string;
  date: string;
  timestamp: string;
  model: string;
  prompt: string;
  response: string;
}

interface LogsPanelProps {
  onClose: () => void;
  logs: LogEntry[];
}

const LogsPanel: React.FC<LogsPanelProps> = ({ onClose, logs }) => {
  const truncateText = (text: string, maxLength: number = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="logs-panel-overlay" onClick={onClose}>
      <div className="logs-panel" onClick={(e) => e.stopPropagation()}>
        <div className="logs-panel-header">
          <h3>Chat Logs</h3>
          <button className="logs-panel-close" onClick={onClose}>
            ×
          </button>
        </div>
        
        <div className="logs-panel-content">
          {logs.length === 0 ? (
            <div className="no-logs">
              <p>No chat interactions yet.</p>
              <p>Start chatting to see logs here.</p>
            </div>
          ) : (
            <div className="logs-list">
              {logs.map((log) => (
                <div key={log.id} className="log-entry">
                  <div className="log-line">
                    <span className="log-datetime">{log.date} {log.timestamp}</span>
                    <span className="log-separator"> | </span>
                    <span className="log-model">{log.model}</span>
                    <span className="log-separator"> | </span>
                    <span className="log-prompt">"{truncateText(log.prompt)}"</span>
                    <span className="log-separator"> | </span>
                    <span className="log-response">"{truncateText(log.response)}"</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsPanel;
