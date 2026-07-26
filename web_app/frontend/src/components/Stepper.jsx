import React from 'react';

const STEPS = [
  { id: 'step1_extract_audio', label: '1. Extraction & Demucs', circle: '1' },
  { id: 'step2_transcribe_diarization', label: '2. Diarization & ASR', circle: '2' },
  { id: 'step2b_gender_confirm', label: '2b. Gender Check', circle: '2b' },
  { id: 'step3_translation', label: '3. Emotion & ADR', circle: '3' },
  { id: 'step4_setup', label: '4a. Voice Casting', circle: '4a' },
  { id: 'step4_genvoice_complete', label: '4b. Voice Gen & Alignment', circle: '4b' },
  { id: 'step5_assembly', label: '5. Timeline & Muxing', circle: '5' },
];

export function Stepper({ currentStep, onRunStep }) {
  return (
    <div className="glass-card">
      <div className="stepper-container">
        {STEPS.map((step) => {
          const isActive = currentStep === step.id;
          return (
            <div
              key={step.id}
              className={`stepper-item ${isActive ? 'active' : ''}`}
              onClick={() => onRunStep(step.id)}
            >
              <div className="stepper-circle">{step.circle}</div>
              <div className="stepper-label">{step.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
