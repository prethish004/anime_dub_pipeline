import React, { useRef, useEffect } from 'react';
import { Terminal, Trash2 } from 'lucide-react';
import { useSSELogs } from '../hooks/useSSELogs';

export function TerminalConsole() {
  const { logs, clearLogs } = useSSELogs();
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="terminal-card">
      <div className="terminal-header">
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Terminal size={14} style={{ color: 'var(--accent-cyan)' }} />
          Live Execution Logs
        </span>
        <button
          className="btn btn-secondary"
          style={{ padding: '4px 8px', fontSize: '11px' }}
          onClick={clearLogs}
        >
          <Trash2 size={12} /> Clear Logs
        </button>
      </div>

      <div ref={bodyRef} className="terminal-body">
        {logs.length === 0 ? (
          '[00:00:00] AI Anime Dubbing Studio initialized...\n'
        ) : (
          logs.map((log, idx) => <div key={idx}>{log}</div>)
        )}
      </div>
    </div>
  );
}
