// API Service layer interfacing with FastAPI backend

export async function getStatus() {
  const res = await fetch('/api/status');
  return res.json();
}

export async function getSessions() {
  const res = await fetch('/api/sessions');
  return res.json();
}

export async function selectSession(sessionName) {
  const res = await fetch('/api/select_session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_name: sessionName })
  });
  return res.json();
}

export async function runStep(stepName, options = {}) {
  const res = await fetch('/api/run_step', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step: stepName, options })
  });
  return res.json();
}

export async function cancelPipeline() {
  const res = await fetch('/api/cancel', { method: 'POST' });
  return res.json();
}

export async function uploadVideo(file, sessionName) {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionName) {
    formData.append('session_name', sessionName);
  }
  const res = await fetch('/api/upload_video', {
    method: 'POST',
    body: formData
  });
  return res.json();
}

export async function getVoices() {
  const res = await fetch('/api/voices');
  return res.json();
}

export async function getTranscription() {
  const res = await fetch('/api/transcription');
  return res.json();
}

export async function saveTranslation(payload) {
  const res = await fetch('/api/save_translation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function getSpeakerConfig() {
  const res = await fetch('/api/speaker_config');
  return res.json();
}

export async function saveSpeakerConfig(payload) {
  const res = await fetch('/api/save_speaker_config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function getOutputs() {
  const res = await fetch('/api/outputs');
  return res.json();
}

export async function getWaveformComparisons() {
  const res = await fetch('/api/waveform_comparisons');
  return res.json();
}
