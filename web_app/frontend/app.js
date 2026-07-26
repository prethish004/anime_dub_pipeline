/* ==========================================================================
   AI ANIME DUBBING STUDIO — FRONTEND LOGIC
   ========================================================================== */

let currentVoices = { female: [], male: [], tamil: [], all: [] };
let currentTranscription = null;
let currentTranslations = [];
let eventSource = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  initSSELogs();
  pollStatus();
  setInterval(pollStatus, 3000);
  await fetchVoices();
  await loadTranscriptionData();
  await loadOutputs();
}

/* ==========================================================================
   1. Real-time Log Streaming (SSE)
   ========================================================================== */
function initSSELogs() {
  const terminalBody = document.getElementById("terminal-body");
  eventSource = new EventSource("/api/stream_logs");

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      appendLog(data.message);
    } catch (e) {
      appendLog(event.data);
    }
  };

  eventSource.onerror = () => {
    // Reconnect silently
  };
}

function appendLog(message) {
  const terminalBody = document.getElementById("terminal-body");
  terminalBody.textContent += message + "\n";
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

function clearLogs() {
  document.getElementById("terminal-body").textContent = "";
}

/* ==========================================================================
   2. Status Polling & Stepper Management
   ========================================================================== */
async function pollStatus() {
  try {
    const res = await fetch("/api/status");
    const state = await res.json();

    const indicator = document.getElementById("status-indicator");
    const statusText = document.getElementById("status-text");
    const btnRunAll = document.getElementById("btn-run-all");
    const btnCancel = document.getElementById("btn-cancel");

    statusText.textContent = state.status.toUpperCase();
    if (state.current_step) {
      statusText.textContent += ` (${state.current_step})`;
    }

    indicator.className = "status-indicator " + state.status;

    if (state.is_running) {
      btnRunAll.disabled = true;
      btnRunAll.style.opacity = "0.5";
      btnCancel.style.display = "inline-flex";
    } else {
      btnRunAll.disabled = false;
      btnRunAll.style.opacity = "1";
      btnCancel.style.display = "none";
    }

    updateStepperUI(state.current_step, state.status);
  } catch (e) {
    console.error("Status poll failed", e);
  }
}

function updateStepperUI(currentStep, status) {
  const steps = ["step-1", "step-2", "step-2b", "step-3", "step-4-setup", "step-4-gen", "step-5"];
  steps.forEach((sId) => {
    const el = document.getElementById(sId);
    if (!el) return;
    el.classList.remove("active");
  });

  if (currentStep) {
    let sId = currentStep.replace("_diarization", "").replace("_complete", "").replace("step1_extract_audio", "step-1").replace("step2_transcribe", "step-2").replace("step2b_gender_confirm", "step-2b").replace("step3_translation", "step-3").replace("step4_setup", "step-4-setup").replace("step4_genvoice", "step-4-gen").replace("step5_assembly", "step-5");
    const activeEl = document.getElementById(sId);
    if (activeEl) {
      activeEl.classList.add("active");
    }
  }
}

/* ==========================================================================
   3. Pipeline Execution Triggers
   ========================================================================== */
async function runFullPipeline() {
  const langMode = document.getElementById("select-language-mode").value;
  try {
    const res = await fetch("/api/run_step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        step: "all",
        options: { language: langMode }
      })
    });
    const data = await res.json();
    appendLog(`🚀 [UI] Started full pipeline run (${langMode})...`);
  } catch (e) {
    alert("Failed to start pipeline: " + e.message);
  }
}

async function runSingleStep(stepName) {
  const langMode = document.getElementById("select-language-mode").value;
  try {
    const res = await fetch("/api/run_step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        step: stepName,
        options: { language: langMode }
      })
    });
    const data = await res.json();
    appendLog(`🚀 [UI] Triggered step: ${stepName}...`);
  } catch (e) {
    alert(`Failed to start step ${stepName}: ` + e.message);
  }
}

async function cancelPipeline() {
  await fetch("/api/cancel", { method: "POST" });
  appendLog("⚠️ [UI] Sent cancellation request.");
}

/* ==========================================================================
   4. Video Upload
   ========================================================================== */
async function uploadVideo(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];

  const formData = new FormData();
  formData.append("file", file);

  appendLog(`⏳ Uploading video: ${file.name}...`);
  try {
    const res = await fetch("/api/upload_video", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    appendLog(`✅ Uploaded video successfully: ${data.file}`);
    document.getElementById("input-video-player").src = "/input/anime.mp4?t=" + Date.now();
  } catch (e) {
    alert("Upload failed: " + e.message);
  }
}

/* ==========================================================================
   5. Voice Catalogue & Speaker Studio
   ========================================================================== */
async function fetchVoices() {
  try {
    const res = await fetch("/api/voices");
    currentVoices = await res.json();
  } catch (e) {
    console.error("Failed to fetch voice catalogue", e);
  }
}

async function loadTranscriptionData() {
  try {
    const res = await fetch("/api/transcription");
    const data = await res.json();

    if (data.profiles) {
      renderSpeakerStudio(data.profiles);
    }
    if (data.translations && data.translations.segments) {
      currentTranslations = data.translations.segments;
      renderTranslationTable(currentTranslations);
    }
  } catch (e) {
    console.error("Failed to load transcription data", e);
  }
}

function renderSpeakerStudio(profiles) {
  const container = document.getElementById("speakers-container");
  container.innerHTML = "";

  const speakers = Object.keys(profiles);
  if (speakers.length === 0) {
    container.innerHTML = '<p style="font-size: 13px; color: var(--text-muted);">No speakers loaded.</p>';
    return;
  }

  speakers.forEach((spk) => {
    const prof = profiles[spk];
    const gender = prof.gender || "unknown";

    const card = document.createElement("div");
    card.className = "speaker-card";

    let voiceOptionsHTML = currentVoices.all.map((v) => {
      return `<option value="${v.path}">${v.name} (${v.category})</option>`;
    }).join("");

    card.innerHTML = `
      <div class="speaker-header">
        <strong style="font-size: 15px;">${spk}</strong>
        <span class="speaker-badge ${gender}">${gender}</span>
      </div>
      ${prof.audio_file ? `<audio controls src="/${prof.audio_file}" style="width: 100%; height: 32px; margin: 4px 0;"></audio>` : ''}
      <div class="form-group">
        <label>Voice Clone Sample:</label>
        <select class="select-input" id="voice-${spk}">
          ${voiceOptionsHTML}
        </select>
      </div>
      <div class="form-group" style="display: flex; gap: 8px;">
        <div style="flex: 1;">
          <label>Age Preset:</label>
          <select class="select-input" id="age-${spk}">
            <option value="adult">Adult</option>
            <option value="child_young">Young Child</option>
            <option value="child_teen">Teenager</option>
            <option value="old_60s">Elderly (60s)</option>
            <option value="old_80s">Elderly (80s)</option>
            <option value="robot">Robot LPC</option>
          </select>
        </div>
        <div style="flex: 1;">
          <label>Vocal Tone:</label>
          <select class="select-input" id="tone-${spk}">
            <option value="neutral">Neutral</option>
            <option value="ecchi">Ecchi / Soft</option>
            <option value="sexy">Sexy / Whisper</option>
            <option value="calm">Calm / Cool</option>
            <option value="hard">Hard / Shouting</option>
            <option value="kid">Kid Voice</option>
          </select>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

async function saveSpeakerConfig() {
  const container = document.getElementById("speakers-container");
  const cards = container.querySelectorAll(".speaker-card");

  const speakerConfigs = {};
  cards.forEach((card) => {
    const spkName = card.querySelector("strong").textContent.trim();
    const voiceFile = document.getElementById(`voice-${spkName}`).value;
    const ageCategory = document.getElementById(`age-${spkName}`).value;
    const toneCategory = document.getElementById(`tone-${spkName}`).value;

    speakerConfigs[spkName] = {
      voice_file: voiceFile,
      age_category: ageCategory,
      tone_category: toneCategory
    };
  });

  const payload = {
    speaker_configs: speakerConfigs,
    global_toggles: { emotion_dsp: true, age_transform: true }
  };

  try {
    await fetch("/api/save_speaker_config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    appendLog("💾 [UI] Saved speaker configuration!");
  } catch (e) {
    alert("Failed to save speaker config: " + e.message);
  }
}

/* ==========================================================================
   6. Translation Table & ADR Editor
   ========================================================================== */
function renderTranslationTable(segments) {
  const tbody = document.getElementById("translation-table-body");
  tbody.innerHTML = "";

  if (!segments || segments.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No segments available.</td></tr>';
    return;
  }

  segments.forEach((seg, idx) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${seg.segment_id}</td>
      <td><strong>${seg.speaker}</strong></td>
      <td>${seg.duration}s</td>
      <td><span style="font-size: 11px; padding: 2px 6px; background: rgba(255,255,255,0.06); border-radius: 4px;">${seg.emotion || 'neutral'}</span></td>
      <td style="color: var(--text-secondary); max-width: 200px;">${seg.japanese_text || ''}</td>
      <td>
        <div contenteditable="true" class="editable-cell" data-idx="${idx}">
          ${seg.translated_text || ''}
        </div>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

async function saveTranslations() {
  const cells = document.querySelectorAll(".editable-cell");
  cells.forEach((cell) => {
    const idx = parseInt(cell.getAttribute("data-idx"));
    if (currentTranslations[idx]) {
      currentTranslations[idx].translated_text = cell.textContent.trim();
    }
  });

  const langMode = document.getElementById("select-language-mode").value;
  try {
    await fetch("/api/save_translation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language_mode: langMode,
        segments: currentTranslations
      })
    });
    appendLog("💾 [UI] Saved ADR translation script updates!");
  } catch (e) {
    alert("Failed to save translations: " + e.message);
  }
}

/* ==========================================================================
   7. Media Outputs
   ========================================================================== */
async function loadOutputs() {
  try {
    const res = await fetch("/api/outputs");
    const data = await res.json();
    const container = document.getElementById("outputs-list");
    container.innerHTML = "";

    if (!data.files || data.files.length === 0) {
      container.innerHTML = '<p style="font-size: 12px; color: var(--text-muted);">No outputs generated yet.</p>';
      return;
    }

    data.files.forEach((f) => {
      const item = document.createElement("div");
      item.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 8px; font-size: 12px;";
      item.innerHTML = `
        <span>📄 <strong>${f.filename}</strong> (${f.size_mb} MB)</span>
        <a href="${f.url}" download class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;">Download</a>
      `;
      container.appendChild(item);
    });
  } catch (e) {
    console.error("Failed to load outputs", e);
  }
}
