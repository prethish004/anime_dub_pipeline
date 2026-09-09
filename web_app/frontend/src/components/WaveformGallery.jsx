import React, { useState, useEffect } from 'react';
import { AudioWaveform, RefreshCw, ImageOff } from 'lucide-react';
import { getWaveformComparisons } from '../services/api';

export function WaveformGallery() {
  const [images, setImages] = useState([]);

  const fetchList = async () => {
    try {
      const data = await getWaveformComparisons();
      setImages(data.files || []);
    } catch (e) {
      console.error('Failed to fetch waveform comparisons', e);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  return (
    <div className="glass-card">
      <div className="card-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AudioWaveform size={20} style={{ color: 'var(--accent-violet)' }} />
          Waveform Comparisons
        </span>
        <button className="btn btn-secondary" onClick={fetchList}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
        Raw synthesized voice vs. the version stretched/trimmed to fit each segment's lip-sync
        duration — generated during Step 4b (Voice Gen &amp; Alignment).
      </p>

      {images.length === 0 ? (
        <div className="media-empty-state">
          <ImageOff size={28} />
          <p>No waveform comparisons yet</p>
          <span>Run Step 4b (Voice Gen &amp; Alignment) to generate them</span>
        </div>
      ) : (
        <div className="waveform-grid">
          {images.map((img) => (
            <a key={img.filename} href={img.url} target="_blank" rel="noopener noreferrer" className="waveform-thumb">
              <img src={img.url} alt={img.filename} loading="lazy" />
              <span>{img.filename}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
