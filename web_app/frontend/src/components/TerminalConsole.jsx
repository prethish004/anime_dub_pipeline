import React, { useRef, useEffect, useMemo, useState } from 'react';
import { Terminal, Trash2, Copy, Check } from 'lucide-react';
import { useSSELogs } from '../hooks/useSSELogs';
import { groupLogs, classifyGroup } from '../utils/logGrouping';

function writeClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try {
    document.execCommand('copy');
  } finally {
    document.body.removeChild(ta);
  }
  return Promise.resolve();
}

function CopyButton({ getText, label = 'Copy' }) {
  const [copied, setCopied] = useState(false);

  const handleClick = () => {
    writeClipboard(getText()).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleClick}>
      {copied ? <Check size={11} /> : <Copy size={11} />}
      {copied ? 'Copied' : label}
    </button>
  );
}

export function TerminalConsole() {
  const { logs, clearLogs } = useSSELogs();
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [logs]);

  const groups = useMemo(() => groupLogs(logs), [logs]);

  return (
    <div className="terminal-card">
      <div className="terminal-header">
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Terminal size={13} style={{ color: 'var(--accent-cyan)' }} />
          Live Execution Logs
        </span>
        <div className="terminal-header-actions">
          {logs.length > 0 && (
            <CopyButton label="Copy all" getText={() => logs.join('\n')} />
          )}
          <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '11px' }} onClick={clearLogs}>
            <Trash2 size={12} /> Clear
          </button>
        </div>
      </div>

      <div ref={bodyRef} className="terminal-body">
        {groups.length === 0 ? (
          <div className="log-empty">[00:00:00] AI Anime Dubbing Studio initialized...</div>
        ) : (
          groups.map((group, idx) => {
            const isLast = idx === groups.length - 1;
            const state = classifyGroup(group.lines, isLast);
            return (
              <div className="log-group" key={group.key}>
                <div className="log-group-head">
                  <span className={`log-group-dot ${state}`} />
                  <span className="log-group-title">{group.title}</span>
                  <CopyButton getText={() => group.lines.join('\n')} />
                </div>
                <div className="log-group-body">{group.lines.join('\n')}</div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
