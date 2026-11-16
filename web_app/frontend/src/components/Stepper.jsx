import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Info, X, Check } from 'lucide-react';
import { useSSELogs } from '../hooks/useSSELogs';
import { deriveStepStates } from '../utils/logGrouping';

const STEPS = [
  {
    id: 'step1_extract_audio',
    label: '1. Extraction & Demucs',
    circle: '1',
    verify: false,
    mode: 'offline',
    modeLabel: '⚡ Local',
    modeTooltip: '100% Offline processing using local FFmpeg and PyTorch Demucs.',
    note: 'Fully automated — just run it. Nothing to review before moving on.',
  },
  {
    id: 'step2_transcribe_diarization',
    label: '2. Diarization & ASR',
    circle: '2',
    verify: true,
    mode: 'hybrid',
    modeLabel: '🔄 HF Sync',
    modeTooltip: 'HuggingFace Auth check on startup, then runs 100% offline.',
    note: 'Skim the detected speaker count and transcript for obvious mix-ups — everything downstream (translation, voices) builds on this.',
  },
  {
    id: 'step2b_gender_confirm',
    label: '2b. Gender Check',
    circle: '2b',
    verify: false,
    mode: 'offline',
    modeLabel: '⚡ Local',
    modeTooltip: '100% Offline frame extraction using OpenCV.',
    note: 'Currently non-functional (known issue: the blur filter rejects every frame, so it never saves screenshots) — nothing to verify here yet.',
  },
  {
    id: 'step3_translation',
    label: '3. Emotion & ADR',
    circle: '3',
    verify: true,
    mode: 'online',
    modeLabel: '🌐 Cloud API',
    modeTooltip: 'Requires OpenAI API access. Runs offline if manually edited.',
    note: 'Read through the translated lines in the ADR editor and fix anything awkward — much cheaper to fix text now than to re-generate voice audio later.',
  },
  {
    id: 'step4_setup',
    label: '4a. Voice Casting',
    circle: '4a',
    verify: true,
    mode: 'offline',
    modeLabel: '⚡ Local',
    modeTooltip: '100% Offline voice sample catalogue scanning.',
    note: 'Check the auto-assigned voice sample actually fits each character (age/gender/personality) in Voice Casting Studio before running the slow voice-gen step.',
  },
  {
    id: 'step4_genvoice_complete',
    label: '4b. Voice Gen & Alignment',
    circle: '4b',
    verify: false,
    mode: 'offline',
    modeLabel: '⚡ Local',
    modeTooltip: '100% Offline TTS voice synthesis & DSP alignment on GPU/CPU.',
    note: 'Fully automated once casting is approved — just run it. Worth a quick listen to the final output afterward, but no setup needed mid-run.',
  },
  {
    id: 'step5_assembly',
    label: '5. Timeline & Muxing',
    circle: '5',
    verify: false,
    mode: 'offline',
    modeLabel: '⚡ Local',
    modeTooltip: '100% Offline video and audio timeline muxing.',
    note: 'Fully automated — just run it. Watch the final video once it\'s done to confirm sync looks right.',
  },
];

function fmtElapsed(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

function VerifyGuide({ onClose }) {
  return (
    <div className="verify-guide-backdrop" onClick={onClose}>
      <div className="verify-guide" onClick={(e) => e.stopPropagation()}>
        <div className="verify-guide-head">
          <span>What needs a look vs. what you can just run</span>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={15} />
          </button>
        </div>
        <div className="verify-guide-body">
          {STEPS.map((step) => (
            <div className="verify-row" key={step.id}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span className={`verify-tag ${step.verify ? 'needed' : 'skip'}`}>
                  {step.verify ? 'Verify' : 'Just run'}
                </span>
                <span className={`stepper-mode-badge ${step.mode}`} style={{ fontSize: '8px', textAlign: 'center' }}>
                  {step.modeLabel}
                </span>
              </div>
              <div>
                <div className="verify-row-title">{step.label}</div>
                <div className="verify-row-note">{step.note}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function Stepper({ currentStep, onRunStep, isRunning, stepProgress }) {
  const { logs } = useSSELogs();
  const [showGuide, setShowGuide] = useState(false);
  const [tick, setTick] = useState(0);
  const runStartRef = useRef(null);
  const wasRunningRef = useRef(false);

  const stepStates = useMemo(() => {
    const derived = deriveStepStates(logs);
    // A step whose real output file exists on disk is durably 'ok', no
    // matter what the (window-limited) live log stream currently shows —
    // this is what keeps a finished step looking finished after a refresh.
    if (stepProgress) {
      for (const id of Object.keys(derived)) {
        if (stepProgress[id]) {
          derived[id] = { ...derived[id], status: 'ok' };
        }
      }
    }
    return derived;
  }, [logs, stepProgress]);

  const completed = STEPS.filter((s) => stepStates[s.id].status === 'ok').length;
  const hasError = STEPS.some((s) => stepStates[s.id].status === 'error');
  const activeIndex = STEPS.findIndex((s) => stepStates[s.id].status === 'running');
  const pct = Math.round((completed / STEPS.length) * 100);

  useEffect(() => {
    if (isRunning && !wasRunningRef.current) {
      runStartRef.current = Date.now();
    }
    wasRunningRef.current = isRunning;
  }, [isRunning]);

  useEffect(() => {
    if (!isRunning) return undefined;
    const t = setInterval(() => setTick((n) => n + 1), 500);
    return () => clearInterval(t);
  }, [isRunning]);

  let overallLabel = 'Idle';
  if (hasError) overallLabel = 'Pipeline stopped with an error';
  else if (isRunning && activeIndex >= 0) overallLabel = `Running: ${STEPS[activeIndex].label}`;
  else if (isRunning) overallLabel = 'Running…';
  else if (completed === STEPS.length) overallLabel = 'Pipeline finished';

  const elapsed = runStartRef.current ? fmtElapsed(Date.now() - runStartRef.current) : '00:00';

  return (
    <div className="glass-card">
      <div className="pipeline-overall">
        <div className="overall-top">
          <span className="overall-label">
            Overall pipeline progress
            <button className="icon-btn" onClick={() => setShowGuide(true)} aria-label="What needs verification">
              <Info size={13} />
            </button>
          </span>
          <span className="overall-stat">
            Step {Math.max(completed, activeIndex >= 0 ? activeIndex + 1 : 0)} of {STEPS.length} · {pct}%
          </span>
        </div>
        <div className="overall-track">
          <div
            className={`overall-fill ${hasError ? 'error' : completed === STEPS.length ? 'done' : ''}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="overall-bottom">
          <span>{overallLabel}</span>
          <span>{elapsed}</span>
        </div>
      </div>

      <div className="stepper-container">
        {STEPS.map((step) => {
          const isActive = currentStep === step.id;
          const s = stepStates[step.id];
          return (
            <div
              key={step.id}
              className={`stepper-item ${s.status} ${isActive ? 'active' : ''}`}
              onClick={() => onRunStep(step.id)}
            >
              <div className="stepper-top-row">
                <span className="stepper-circle">{step.circle}</span>
                <span className={`stepper-mode-badge ${step.mode}`} title={step.modeTooltip}>
                  {step.modeLabel}
                </span>
                {s.status === 'ok' ? (
                  <Check size={12} className="stepper-check" />
                ) : s.status === 'error' ? (
                  <X size={12} className="stepper-cross" />
                ) : (
                  <span className="stepper-led" />
                )}
              </div>
              <div className="stepper-label">{step.label}</div>
              <div className="stepper-detail">
                {s.status === 'running' ? (
                  <>
                    <span className="stepper-spinner" />
                    <span>{s.detail || 'Working…'}</span>
                  </>
                ) : s.status === 'ok' ? (
                  <span>Complete{s.time ? ` · ${s.time}` : ''}</span>
                ) : s.status === 'error' ? (
                  <span>Failed{s.time ? ` · ${s.time}` : ''}</span>
                ) : (
                  <span>&nbsp;</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {showGuide && <VerifyGuide onClose={() => setShowGuide(false)} />}
    </div>
  );
}
