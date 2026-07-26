import React, { useRef } from 'react';
import { Upload, Video } from 'lucide-react';
import { uploadVideo } from '../services/api';

export function VideoWorkspace({ onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);

  const handleFileChange = async (e) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    try {
      await uploadVideo(file);
      if (videoRef.current) {
        videoRef.current.src = '/input/anime.mp4?t=' + Date.now();
      }
      if (onUploadSuccess) onUploadSuccess(file.name);
    } catch (err) {
      alert('Upload failed: ' + err.message);
    }
  };

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

      <div className="media-preview-container">
        <video ref={videoRef} controls src="/input/anime.mp4">
          Your browser does not support video playback.
        </video>
      </div>
    </div>
  );
}
