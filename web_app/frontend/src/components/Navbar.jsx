import React from 'react';
import { Play, Square, FolderGit2, Sun, Moon } from 'lucide-react';

export function Navbar({ statusState, sessions, activeSession, onSelectSession, onRunAll, onCancel, theme, onToggleTheme }) {
  const { status, current_step, is_running } = statusState;

  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-title">
          <h1>AI Anime Dubbing Studio</h1>
          <p>Multi-Speaker Voice Cloning & ADR Pipeline (React)</p>
        </div>
      </div>

      <div className="nav-actions">
        {/* Project Session Switcher Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FolderGit2 size={16} style={{ color: 'var(--accent-cyan)' }} />
          <select
            className="select-input"
            style={{ width: '160px', padding: '6px 10px', fontSize: '12px' }}
            value={activeSession || 'default'}
            onChange={(e) => onSelectSession(e.target.value)}
          >
            {sessions.map((s) => (
              <option key={s.name} value={s.name}>
                Project: {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="status-pill">
          <div className={`status-dot ${status}`} />
          <span>
            {status.toUpperCase()}
            {current_step ? ` (${current_step})` : ''}
          </span>
        </div>

        {is_running && (
          <button className="btn btn-danger" onClick={onCancel}>
            <Square size={16} /> Cancel
          </button>
        )}

        <button
          className="btn btn-primary"
          disabled={is_running}
          onClick={onRunAll}
        >
          <Play size={16} /> Run Full Dubbing Pipeline
        </button>

        <button
          className="theme-toggle"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
          title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
