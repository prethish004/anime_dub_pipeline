import React, { useRef, useState } from 'react';
import { Upload, Video, FileVideo } from 'lucide-react';
import { uploadVideo } from '../services/api';

export function VideoWorkspace({ videoUrl, onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const [optimisticUrl, setOptimisticUrl] = useState(null);

  const handleFileChange = async (e) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    try {
      const result = await uploadVideo(file);
      if (result && result.file) {
        setOptimisticUrl('/' + result.file + '?t=' + Date.now());
      }
      if (onUploadSuccess) onUploadSuccess(file.name);
    } catch (err) {
      alert('Upload failed: ' + err.message);
    }
  };

  const src = optimisticUrl || videoUrl;

  return (
    <div className="glass-card">
      <div className="card-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Video size={20} style={{ color: 'var(--accent-cyan)' }} />
          Target Input Video
        </span>
        <input
          type="file"
          ref={fileInputRef}
          accept="video/mp4,video/*"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button
          className="btn btn-secondary"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={14} /> Upload New Video
        </button>
      </div>

      {src ? (
        <div className="media-preview-container">
          <video controls src={src}>
            Your browser does not support video playback.
          </video>
        </div>
      ) : (
        <div className="media-empty-state">
          <FileVideo size={28} />
          <p>No video uploaded for this session yet</p>
          <span>Click "Upload New Video" to get started</span>
        </div>
      )}
    </div>
  );
}
