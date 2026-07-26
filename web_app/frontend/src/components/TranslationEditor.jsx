import React, { useState, useEffect } from 'react';
import { Languages, Save } from 'lucide-react';
import { saveTranslation } from '../services/api';

export function TranslationEditor({ translations, onSaveSuccess }) {
  const [segments, setSegments] = useState([]);
  const [langMode, setLangMode] = useState('english');

  useEffect(() => {
    if (translations) {
      setSegments(translations.segments || []);
      setLangMode(translations.language_mode || 'english');
    }
  }, [translations]);

  const handleCellChange = (idx, newText) => {
    const updated = [...segments];
    updated[idx].translated_text = newText;
    setSegments(updated);
  };

  const handleSave = async () => {
    try {
      await saveTranslation({
        language_mode: langMode,
        segments: segments,
      });
      alert('✅ ADR translation updates saved!');
      if (onSaveSuccess) onSaveSuccess();
    } catch (e) {
      alert('Failed to save translations: ' + e.message);
    }
  };

  return (
    <div className="glass-card">
      <div className="card-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Languages size={20} style={{ color: 'var(--accent-pink)' }} />
          ADR Script & Translation Editor
        </span>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            className="select-input"
            style={{ width: '140px' }}
            value={langMode}
            onChange={(e) => setLangMode(e.target.value)}
          >
            <option value="english">English ADR</option>
            <option value="tamil">Tamil ADR</option>
            <option value="tanglish">Tanglish ADR</option>
          </select>
          <button className="btn btn-secondary" onClick={handleSave}>
            <Save size={14} /> Save ADR Changes
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Seg</th>
              <th>Speaker</th>
              <th>Duration</th>
              <th>Emotion</th>
              <th>Japanese Source Text</th>
              <th>Dubbed ADR Translation Script</th>
            </tr>
          </thead>
          <tbody>
            {segments.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  No translation data available. Run Step 3 (Translation) or trigger pipeline.
                </td>
              </tr>
            ) : (
              segments.map((seg, idx) => (
                <tr key={seg.segment_id || idx}>
                  <td>{seg.segment_id}</td>
                  <td><strong>{seg.speaker}</strong></td>
                  <td>{seg.duration}s</td>
                  <td>
                    <span style={{ fontSize: '11px', padding: '2px 6px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px' }}>
                      {seg.emotion || 'neutral'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', maxWidth: '200px' }}>
                    {seg.japanese_text || ''}
                  </td>
                  <td>
                    <input
                      type="text"
                      className="text-input"
                      value={seg.translated_text || ''}
                      onChange={(e) => handleCellChange(idx, e.target.value)}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
