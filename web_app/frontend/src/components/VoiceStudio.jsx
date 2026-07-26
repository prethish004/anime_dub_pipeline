import React, { useState, useEffect } from 'react';
import { Mic, Save, Volume2 } from 'lucide-react';
import { getVoices, saveSpeakerConfig, getSpeakerConfig } from '../services/api';

export function VoiceStudio({ profiles }) {
  const [voices, setVoices] = useState({ female: [], male: [], tamil: [], all: [] });
  const [speakerConfigs, setSpeakerConfigs] = useState({});

  useEffect(() => {
    async function loadData() {
      try {
        const vData = await getVoices();
        setVoices(vData);

        const cData = await getSpeakerConfig();
        if (cData.speaker_configs) {
          setSpeakerConfigs(cData.speaker_configs);
        }
      } catch (e) {
        console.error('Failed to load voice studio data', e);
      }
    }
    loadData();
  }, []);

  const handleConfigChange = (speaker, field, value) => {
    setSpeakerConfigs((prev) => ({
      ...prev,
      [speaker]: {
        ...prev[speaker],
        [field]: value,
      },
    }));
  };

  const handleSave = async () => {
    const payload = {
      speaker_configs: speakerConfigs,
      global_toggles: { emotion_dsp: true, age_transform: true },
    };
    try {
      await saveSpeakerConfig(payload);
      alert('✅ Speaker configuration saved successfully!');
    } catch (e) {
      alert('Failed to save configuration: ' + e.message);
    }
  };

  const speakers = profiles ? Object.keys(profiles) : [];

  return (
    <div className="glass-card">
      <div className="card-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Mic size={20} style={{ color: 'var(--accent-violet)' }} />
          Voice Casting Studio
        </span>
        <button className="btn btn-secondary" onClick={handleSave}>
          <Save size={14} /> Save Speaker Config
        </button>
      </div>

      <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
        Assign cloned reference voice samples, age categories, and vocal tones to detected character speakers.
      </p>

      <div className="speakers-grid">
        {speakers.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            No speaker profiles loaded yet. Run Step 2 (Diarization & ASR) first.
          </p>
        ) : (
          speakers.map((spk) => {
            const prof = profiles[spk];
            const gender = prof.gender || 'unknown';
            const cfg = speakerConfigs[spk] || {};
            const selectedVoice = cfg.voice_file || (voices.all[0] ? voices.all[0].path : '');

            return (
              <div key={spk} className="speaker-card">
                <div className="speaker-header">
                  <strong style={{ fontSize: '15px' }}>{spk}</strong>
                  <span className={`speaker-badge ${gender}`}>{gender}</span>
                </div>

                {/* Original Speaker Segment Audio */}
                {prof.audio_file && (
                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      Detected Audio Segment:
                    </label>
                    <audio
                      controls
                      src={`/${prof.audio_file}`}
                      style={{ width: '100%', height: '32px', marginTop: '2px' }}
                    />
                  </div>
                )}

                {/* Voice Clone Sample Selector */}
                <div className="form-group">
                  <label>Selected Voice Clone Sample:</label>
                  <select
                    className="select-input"
                    value={selectedVoice}
                    onChange={(e) => handleConfigChange(spk, 'voice_file', e.target.value)}
                  >
                    {voices.female.length > 0 && (
                      <optgroup label="Female Voice Samples">
                        {voices.female.map((v) => (
                          <option key={v.path} value={v.path}>
                            {v.name} (Female)
                          </option>
                        ))}
                      </optgroup>
                    )}
                    {voices.male.length > 0 && (
                      <optgroup label="Male Voice Samples">
                        {voices.male.map((v) => (
                          <option key={v.path} value={v.path}>
                            {v.name} (Male)
                          </option>
                        ))}
                      </optgroup>
                    )}
                    {voices.tamil.length > 0 && (
                      <optgroup label="Tamil Voice Samples">
                        {voices.tamil.map((v) => (
                          <option key={v.path} value={v.path}>
                            {v.name} (Tamil)
                          </option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                </div>

                {/* Play Selected Reference Voice Sample */}
                {selectedVoice && (
                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Volume2 size={12} /> Reference Voice Clip Preview:
                    </label>
                    <audio
                      controls
                      src={`/${selectedVoice}`}
                      style={{ width: '100%', height: '32px', marginTop: '2px' }}
                    />
                  </div>
                )}

                {/* Age & Tone Selectors */}
                <div className="form-group" style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <label>Age Preset:</label>
                    <select
                      className="select-input"
                      value={cfg.age_category || 'adult'}
                      onChange={(e) => handleConfigChange(spk, 'age_category', e.target.value)}
                    >
                      <option value="adult">Adult</option>
                      <option value="child_young">Young Child</option>
                      <option value="child_teen">Teenager</option>
                      <option value="old_60s">Elderly (60s)</option>
                      <option value="old_80s">Elderly (80s)</option>
                      <option value="robot">Robot LPC</option>
                    </select>
                  </div>

                  <div style={{ flex: 1 }}>
                    <label>Vocal Tone:</label>
                    <select
                      className="select-input"
                      value={cfg.tone_category || 'neutral'}
                      onChange={(e) => handleConfigChange(spk, 'tone_category', e.target.value)}
                    >
                      <option value="neutral">Neutral</option>
                      <option value="ecchi">Ecchi / Soft</option>
                      <option value="sexy">Sexy / Whisper</option>
                      <option value="calm">Calm / Cool</option>
                      <option value="hard">Hard / Shouting</option>
                      <option value="kid">Kid Voice</option>
                    </select>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
