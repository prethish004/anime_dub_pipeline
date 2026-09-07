import React, { useState, useEffect } from 'react';
import { Film, Download, RefreshCw, FileVideo } from 'lucide-react';
import { getOutputs } from '../services/api';

export function MediaCenter() {
  const [outputs, setOutputs] = useState([]);

  const fetchOutputList = async () => {
    try {
      const data = await getOutputs();
      setOutputs(data.files || []);
    } catch (e) {
      console.error('Failed to fetch outputs', e);
    }
  };

  useEffect(() => {
    fetchOutputList();
  }, []);

  const videoOutput = outputs.find((f) => f.filename.toLowerCase().endsWith('.mp4'));

  return (
    <div className="glass-card">
      <div className="card-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Film size={20} style={{ color: 'var(--accent-green)' }} />
          Dubbed Video Output
        </span>
        <button className="btn btn-secondary" onClick={fetchOutputList}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {videoOutput ? (
        <div className="media-preview-container">
          <video controls src={videoOutput.url}>
            Your browser does not support video playback.
          </video>
        </div>
      ) : (
        <div className="media-empty-state">
          <FileVideo size={28} />
          <p>No dubbed video yet</p>
          <span>Run Step 5 (Assembly &amp; Muxing) to generate one</span>
        </div>
      )}

      <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {outputs.length === 0 ? (
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            No generated outputs found. Run Step 5 (Assembly & Muxing) first.
          </p>
        ) : (
          outputs.map((f) => (
            <div
              key={f.filename}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            >
              <span>📄 <strong>{f.filename}</strong> ({f.size_mb} MB)</span>
              <a
                href={f.url}
                download
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '11px' }}
              >
                <Download size={12} /> Download
              </a>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
