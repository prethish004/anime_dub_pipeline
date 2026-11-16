# 🎬 AI Anime Dubbing Pipeline (v3)

An end-to-end, multi-speaker AI Anime Dubbing Pipeline that automatically extracts audio, separates dialogue from background music/SFX, detects speakers and gender, transcribes Japanese speech with word-level timestamps, detects speech emotions, adapts dialogue into lip-synced dubbed scripts (**English**, **Tamil**, or **Tanglish**), clones character voices, applies age/tone audio transformations, and mixes/muxes the final dubbed video.

---

## 📋 Table of Contents
1. [System Prerequisites](#-system-prerequisites)
2. [Environment Setup & Installation](#-environment-setup--installation)
3. [Required Directory Structure](#-required-directory-structure)
4. [API Keys & Tokens Setup](#-api-keys--tokens-setup)
5. [Pipeline Execution Order](#-pipeline-execution-order)
6. [Detailed Step-by-Step Breakdown](#-detailed-step-by-step-breakdown)
   - [Step 1: Audio Extraction & Source Separation](#step-1-audio-extraction--source-separation-step1_extract_audiopy)
   - [Step 2: Speaker Diarization & Transcription](#step-2-speaker-diarization--transcription-step2_transcribe_diarizationpy)
   - [Step 2b: Gender Confirmation & Screenshot Extraction (Optional)](#step-2b-gender-confirmation--screenshot-extraction-optional-step2b_gender_confirrmpy)
   - [Step 3: Emotion Detection & ADR Translation](#step-3-emotion-detection--adr-translation-step3_translationpy)
   - [Step 4 Setup: Voice Library Mapping & Config](#step-4-setup-voice-library-mapping--config-step4_voice_selection_installationpy)
   - [Step 4 Generation: AI Voice Synthesis & Processing](#step-4-generation-ai-voice-synthesis--processing-step4_genvoice_completepy)
   - [Step 5 Assembly: Timeline Mixing & Video Muxing](#step-5-assembly-timeline-mixing--video-muxing-step5_assemblypy)
7. [Troubleshooting & Common Issues](#-troubleshooting--common-issues)

---

## 💻 System Prerequisites

### Hardware Requirements
- **CPU:** 4-core CPU minimum (8-core recommended).
- **RAM:** 16GB+ recommended.
- **GPU:** NVIDIA GPU with CUDA support (8GB+ VRAM recommended for Whisper, PyAnnote, Demucs, and XTTS-v2). CPU execution is supported as a fallback but will be significantly slower.

### System Software Dependencies
1. **Python 3.10+** (Python 3.10 or 3.11 is recommended).
2. **FFmpeg** (Must be installed and added to System PATH).
   - **Windows:** `choco install ffmpeg` or download binaries from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `bin/` to system PATH.
   - **Linux:** `sudo apt install ffmpeg`
   - **macOS:** `brew install ffmpeg`
3. **Rubberband CLI** (High-quality, pitch-preserving time-stretching library used by `pyrubberband`).
   - **Windows:** Download executable binaries from [Breakfast Quay Rubberband](https://breakfastquay.com/rubberband/) and place `rubberband.exe` on System PATH.
   - **Linux:** `sudo apt install rubberband-cli`
   - **macOS:** `brew install rubberband`

---

## 🐍 Environment Setup & Installation

Due to specific dependency constraints between PyTorch, `pyannote.audio`, `whisperx`, and Coqui `TTS`, setting up two virtual environments (or a carefully pinned single environment) is recommended.

### Option A: Recommended Dual Environment Setup

#### 1. Environment for Transcription & Separation (`whisper_env`) — Steps 1, 2, 3
```bash
# Create virtual environment
python -m venv whisper_env

# Activate environment
# Windows (PowerShell):
.\whisper_env\Scripts\Activate.ps1
# Windows (CMD):
.\whisper_env\Scripts\activate.bat
# Linux / macOS:
source whisper_env/bin/activate

# Step A: Install PyTorch 2.5.1 FIRST (avoids pyannote exact pin conflicts & weights_only crash)
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Step B: Install whisperx without letting it upgrade PyTorch
pip install whisperx==3.8.2 --no-deps

# Step C: Install remaining dependencies
pip install -r requirements_whisper_env.txt
```

#### 2. Environment for TTS & Audio Synthesis (`anime_env`) — Steps 4, 5
```bash
# Deactivate previous env
deactivate

# Create TTS virtual environment
python -m venv anime_env

# Activate environment
# Windows:
.\anime_env\Scripts\activate
# Linux / macOS:
source anime_env/bin/activate

# Install PyTorch & Core Dependencies
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Install Coqui TTS and audio processing libraries
pip install TTS praat-parselmouth pyrubberband scipy soundfile librosa matplotlib numpy pyphen transformers accelerate openai python-dotenv opencv-python moviepy

# Optional: Install kNN-VC for advanced voice conversion
pip install knnvc
```

#### 3. Run PyTorch 2.5+/2.6+ Compatibility Patch
If running PyTorch 2.5+ or 2.6+, run the included patch script once in `anime_env` to prevent `weights_only=False` / `fsspec` serialization errors in Coqui TTS:
```bash
python xttspytorch26.py
```

---

## 📁 Required Directory Structure

Before starting the pipeline, set up your project workspace as follows:

```
anime_dub_pipeline/
│
├── .env                              # API Key configuration file
├── input/
│   └── anime.mp4                     # Target input video file
│
├── sample_voices/                    # Reference audio clips for voice cloning (min 10-15s WAV/MP3)
│   ├── female/                       # Female voice samples (e.g. Amber.mp3, Chloe.wav)
│   ├── male/                         # Male voice samples (e.g. Denji.wav, Madara.mp3)
│   └── tamil/                        # Tamil voice samples (used for Tamil/Tanglish dubs)
│
├── step1_extract_audio.py            # Step 1 script
├── step2_transcribe_diarization.py   # Step 2 script
├── Step2b_gender_confirm.py          # Step 2b script (optional)
├── step3_Translation.py              # Step 3 script
├── step4_Voice_Selection_Installation.py # Step 4 Setup script
├── step4_genvoice_complete.py        # Step 4 Generation script
├── step5_assembly.py                 # Step 5 Master Assembly script
├── xttspytorch26.py                  # PyTorch patch script
│
└── work/                             # Auto-generated workspace directory
    ├── stems/                        # Demucs separated stems
    ├── speaker_segments/             # Per-speaker WAV segments
    ├── gender_screenshots/           # Screenshots for manual/vision gender check
    ├── generated_audio/              # Stage 1-4 synthesized voice clips
    ├── waveform_comparisons/         # Plot comparisons (EN vs JP)
    └── output/                       # Final dubbed videos and master audio tracks
```

---

## 🔑 API Keys & Tokens Setup

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY="sk-proj-your-openai-api-key-here"
```

### HuggingFace Token
- Create a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
- Accept the user terms for the PyAnnote models on HuggingFace:
  - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
  - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
- Paste your token into `step2_transcribe_diarization.py` at the `HF_TOKEN` variable:
  ```python
  HF_TOKEN = "hf_your_token_here"
  ```

---

## 🚀 Pipeline Execution Order

To dub an anime video, execute the scripts in the following exact sequence:

| Step | Script | Environment | Description |
| :--- | :--- | :--- | :--- |
| **0** | *(Setup)* | - | Place input video in `input/anime.mp4` & voice samples in `sample_voices/`. |
| **1** | `step1_extract_audio.py` | `whisper_env` | Extracts audio, separates stems with Demucs, applies VAD. |
| **2** | `step2_transcribe_diarization.py` | `whisper_env` | Performs speaker diarization, Whisper transcription with word timestamps, gender detection. |
| **2b** | `Step2b_gender_confirm.py` *(Optional)* | `whisper_env` | Extracts video screenshots per speaker for visual gender verification. |
| **3** | `step3_Translation.py` | `whisper_env` | Detects emotion/style/length bias, performs GPT-4o ADR translation (English/Tamil/Tanglish). |
| **4a**| `step4_Voice_Selection_Installation.py` | `anime_env` | Interactive CLI: maps speakers to voice samples, age presets, and vocal tones. |
| **Patch** | `xttspytorch26.py` *(Run once)* | `anime_env` | Patches Coqui TTS library for PyTorch 2.5+/2.6+ compatibility. |
| **4b**| `step4_genvoice_complete.py` | `anime_env` | Synthesizes voices (XTTS-v2 / MMS+kNN-VC), aligns duration, applies emotion & age DSP. |
| **5** | `step5_assembly.py` | `anime_env` | Master timeline assembly, background noise mixing, comparison plots, video muxing. |

---

## 📖 Detailed Step-by-Step Breakdown

### Step 1: Audio Extraction & Source Separation (`step1_extract_audio.py`)

- **Input:** `input/anime.mp4`
- **What it does:**
  1. **Audio Extraction:** Uses `ffmpeg` to extract raw 44.1kHz stereo PCM audio to `work/raw_audio_44k.wav`.
  2. **Demucs Separation:** Runs `htdemucs_6s` model via PyTorch API to split audio into 6 stems: `vocals`, `drums`, `bass`, `other`, `guitar`, `piano`.
  3. **Silero VAD:** Runs Silero Voice Activity Detection on `vocals.wav` at 16kHz to isolate true dialogue segments (ignoring pops, breaths, and background noise).
  4. **Clean Vocals Export:** Exports `work/vocals_clean.wav` (VAD-gated dialogue, 16kHz mono, peak normalized to -3 dBFS).
  5. **Background Mix Export:** Merges all 5 non-vocal stems (`drums`, `bass`, `other`, `guitar`, `piano`) into `work/background_full.wav` (44.1kHz stereo, normalized to -6 dBFS headroom for background music and SFX).
  6. **Metadata JSON:** Writes timing and VAD segment statistics to `work/step1_metadata.json`.
- **Outputs:**
  - `work/vocals_clean.wav`
  - `work/background_full.wav`
  - `work/step1_metadata.json`
  - `work/stems/htdemucs_6s/raw_audio_44k/`

---

### Step 2: Speaker Diarization & Transcription (`step2_transcribe_diarization.py`)

- **Input:** `work/stems/htdemucs_6s/raw_audio_44k/vocals.wav`
- **What it does:**
  1. **Speaker Diarization:** Uses `pyannote/speaker-diarization-3.1` to detect speaker identity and start/end boundaries for every utterance (`SPEAKER_00`, `SPEAKER_01`, etc.).
  2. **Whisper Transcription:** Transcribes Japanese speech per segment using `openai/whisper-small` with word-level timestamps (`return_timestamps="word"`). Offset word timestamps are saved for precise speech-rate analysis.
  3. **Audio Gender Recognition:** Classifies speaker gender using `alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech` (`male` or `female`) with confidence scoring.
  4. **Per-Speaker Audio Aggregation:** Concatenates audio clips for each speaker and exports `work/speaker_segments/<SPEAKER_ID>.wav`.
  5. **Structured Outputs:** Exports comprehensive transcript and speaker profile metadata.
- **Outputs:**
  - `work/transcription_with_speakers.json`
  - `work/speaker_profiles.json`
  - `work/speaker_segments/SPEAKER_00.wav`, `SPEAKER_01.wav`, etc.

---

### Step 2b: Gender Confirmation & Screenshot Extraction (Optional) (`Step2b_gender_confirm.py`)

- **Inputs:** `input/anime.mp4`, `work/transcription_with_speakers.json`
- **What it does:**
  1. Samples up to 4 segments per speaker from `transcription_with_speakers.json`.
  2. Seeks into `input/anime.mp4` using OpenCV (`cv2`) at segment midpoints.
  3. Filters frames for quality (evaluates blur via Laplacian variance > 80.0 and brightness > 40.0; scans adjacent timestamps if midpoint frame is blurry/dark).
  4. Saves extracted PNG screenshots to `work/gender_screenshots/<SPEAKER_ID>/`.
  5. Updates speaker profiles JSON with screenshot file paths for visual gender verification.
- **Outputs:**
  - `work/gender_screenshots/<SPEAKER_ID>/segNNN_XXs.png`
  - Updated `work/transcription_with_speakers.json` & `work/speaker_profiles.json`.

---

### Step 3: Emotion Detection & ADR Translation (`step3_Translation.py`)

- **Inputs:** `work/transcription_with_speakers.json`, `work/stems/htdemucs_6s/raw_audio_44k/vocals.wav`, `.env` (`OPENAI_API_KEY`)
- **What it does:**
  1. **Interactive Language Selection:** Prompt in terminal allows choosing target dub language:
     - `[1] English ADR`
     - `[2] Tamil ADR`
     - `[3] Tanglish ADR` (Urban Chennai Tamil + English blend)
  2. **Speech Emotion Recognition:** Runs `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` (8-class) or `superb/wav2vec2-base-superb-er` (fallback) to classify segment emotion (`angry`, `happy`, `sad`, `fear`, `surprise`, `neutral`, `disgust`). Saves `work/emotion_detection.json`.
  3. **Dialogue Style & Length Bias Analysis:**
     - Evaluates Japanese text patterns (`STYLE_PATTERNS`) to detect character dialogue style (`tsundere`, `aggressive`, `formal_cool`, `cute`, `reflective`, `neutral`).
     - Evaluates word timestamps to calculate actual speech speed (words/sec) and natural breath pauses.
     - Compares Japanese character density against duration to detect length mismatch (`JP_SHORT`, `EN_SHORT`, or `BALANCED`) and injects adaptation strategies into the LLM prompt.
  4. **GPT-4o ADR Script Adaptation:** Queries OpenAI `gpt-4o-mini` with strict ADR instructions:
     - Enforces target syllable budgets (`~3.5` syl/sec for English, `~2.8` for Tamil, `~3.2` for Tanglish).
     - Enforces labial lip-sync (matching lip closures `m`, `b`, `p` at Japanese phrase endings).
     - Preserves adult/explicit terms literally without sanitization.
  5. Exports structured translated segments.
- **Outputs:**
  - `work/emotion_detection.json`
  - `work/translated_segments_step3.json`

---

### Step 4 Setup: Voice Library Mapping & Config (`step4_Voice_Selection_Installation.py`)

- **Inputs:** `sample_voices/`, `work/translated_segments_step3.json`, `work/transcription_with_speakers.json`
- **What it does:**
  1. **Package Verification:** Checks installation of required libraries (`TTS`, `parselmouth`, `scipy`, `soundfile`, `librosa`, `matplotlib`, `numpy`, `torch`, `torchaudio`, `pyphen`).
  2. **Voice Catalogue Scanning:** Scans `sample_voices/female/`, `sample_voices/male/`, and `sample_voices/tamil/`.
  3. **Interactive Speaker Configuration:**
     - Displays sample line and detected speaker gender from Step 2.
     - Highlights gender-matching voice samples (`★`).
     - Lets user assign a voice sample per speaker.
     - Lets user assign an Age/Type category (`adult`, `child_young`, `child_teen`, `old_60s`, `old_80s`, `robot`).
     - Lets user assign a Vocal Tone/Style (`neutral`, `ecchi`, `horny`, `soft`, `sexy`, `calm`, `hard`, `kid`, `inner_thought`).
     - Lets user assign an optional kNN-VC reference clip.
     - Configures global pipeline toggles (Emotion DSP ON/OFF, Age Transform ON/OFF, kNN-VC ON/OFF).
  4. Exports master speaker mapping configuration.
- **Outputs:**
  - `work/speaker_config.json`

---

### Step 4 Generation: AI Voice Synthesis & Processing (`step4_genvoice_complete.py`)

- **Inputs:** `work/translated_segments_step3.json`, `work/speaker_config.json`, `sample_voices/`
- **What it does:**
  1. **Conditioning Latent Pre-computation:** Computes and caches XTTS conditioning latents (`gpt_cond_latent`, `speaker_embedding`) ONCE per speaker to guarantee 100% voice consistency across all segments (resolving per-call speaker variance).
  2. **Stage 1 (Voice Synthesis):**
     - **English Path:** Synthesizes speech with Coqui XTTS-v2 (`tts_models/multilingual/multi-dataset/xtts_v2`).
     - **Tamil/Tanglish Path:** Synthesizes native Tamil speech with Facebook MMS-TTS (`facebook/mms-tts-tam`) and converts speaker identity to target voice using kNN-VC (`bshall/knn-vc`).
  3. **Stage 2 (Exact Timing Alignment):**
     - Performs pitch-preserving time-stretching via `pyrubberband` to match target segment duration exactly.
     - Enforces exact output length matching `target_dur`.
     - Analyzes spectral flatness and zero-crossing rate variance to detect audio smearing/degradation.
     - Generates waveform comparison plots (`work/waveform_comparisons/comparison_NNN.png`).
  4. **Stage 3 (Emotion & Tone DSP):**
     - Applies RMS target loudness normalization.
     - Applies low-pass/high-pass Butterworth filters for emotion tones (`sad`, `angry`, `happy`, `fearful`).
     - Applies breathiness noise injection, pitch shifting, or plate reverb (`inner_thought` tone).
  5. **Stage 4 (Age/Type Transformation):**
     - Applies Praat Parselmouth `Change gender` formant and pitch scaling for child (`child_young`, `child_teen`), elderly (`old_60s`, `old_80s`), or LPC buzz-wave resynthesis for `robot`.
  6. Exports intermediate and final WAV files per segment and saves generation metadata.
- **Outputs:**
  - `work/generated_audio/raw_NNN.wav`
  - `work/generated_audio/aligned_NNN.wav`
  - `work/generated_audio/emotion_NNN.wav`
  - `work/generated_audio/age_NNN.wav`
  - `work/generated_audio/final_NNN.wav`
  - `work/generated_audio/generation_metadata.json`
  - `work/waveform_comparisons/comparison_NNN.png`

---

### Step 5 Assembly: Timeline Mixing & Video Muxing (`step5_assembly.py`)

- **Inputs:** `input/anime.mp4`, `work/stems/htdemucs_6s/raw_audio_44k/vocals.wav`, `work/background_full.wav`, `work/translated_segments_step3.json`, `work/generated_audio/generation_metadata.json`
- **What it does:**
  1. **Master Dialogue Track Assembly:** Places each generated audio clip at its original Japanese start timestamp on a 44.1kHz master stereo canvas using PyTorch tensor operations (`_place_on_canvas`). Peak-normalizes dialogue track to -3 dBFS.
  2. **Background Track Mixing:** Overlays background audio (`work/background_full.wav`) with the dialogue track at configured gain levels (`BG_REDUCE_DB = -2dB`, `DLG_BOOST_DB = +1dB`). Peak-normalizes mix track to -1 dBFS.
  3. **Timeline & Segment Waveform Plots:**
     - Generates full-timeline waveform comparison plots comparing Japanese original vocals against dubbed audio tracks (`work/output/comparison_<type>.png`).
     - Generates zoomed per-segment waveform comparison plots (`work/output/segments/<type>/comparison_NNN.png`).
  4. **Video Muxing:** Muxes the mixed dubbed audio track with `input/anime.mp4` using `ffmpeg` (stream copying video `-c:v copy`, encoding AAC audio `-c:a aac -b:a 192k`).
  5. Builds tracks for all available clip stages (`aligned`, `emotion`, `age`, `final`).
- **Outputs (in `work/output/`):**
  - `dialogue_final.wav` *(Voices only, no background)*
  - `mix_final.wav` *(Full master mix: voices + background SFX/music)*
  - `comparison_final.png` *(Full episode timeline waveform comparison plot)*
  - `segments/final/comparison_NNN.png` *(Per-segment waveform comparison plots)*
  - `anime_dubbed_final.mp4` *(Final dubbed video ready for playback!)*

---

## ❓ Troubleshooting & Common Issues

### 1. `FFmpeg not found` or `ffprobe error`
- **Cause:** FFmpeg binaries are not installed or not added to System PATH.
- **Fix:** Install FFmpeg and add the `bin/` directory containing `ffmpeg.exe` to your Windows System Environment Variables PATH. Verify by running `ffmpeg -version` in terminal.

### 2. PyTorch `weights_only=False` or `ValueError: I/O operation on closed file` with XTTS
- **Cause:** PyTorch 2.5+ changed `torch.load` security defaults, breaking Coqui TTS checkpoint loading.
- **Fix:** Activate `anime_env` and run the patch script once:
  ```bash
  python xttspytorch26.py
  ```

### 3. HuggingFace `403 Client Error: Forbidden` during Step 2
- **Cause:** PyAnnote models are gated on HuggingFace and require accepting terms.
- **Fix:** Log in to HuggingFace, visit [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1), accept the model license terms, generate a User Access Token, and set `HF_TOKEN` in `step2_transcribe_diarization.py`.

### 4. `pyrubberband / rubberband` Warning or Error in Step 4
- **Cause:** Rubberband CLI executable is missing from System PATH.
- **Fix:** On Windows, download `rubberband.exe` from [Breakfast Quay](https://breakfastquay.com/rubberband/) and place it in a folder listed on your System PATH (e.g. `C:\Windows\System32` or your FFmpeg `bin` folder). On Linux, `sudo apt install rubberband-cli`.

### 5. Open AI API Key Missing Error in Step 3
- **Cause:** `OPENAI_API_KEY` is not defined in `.env`.
- **Fix:** Create a `.env` file in the root directory containing `OPENAI_API_KEY="sk-proj-..."`.

### 6. CUDA Out of Memory (OOM)
- **Cause:** Multiple heavy models loaded simultaneously on GPU.
- **Fix:** The pipeline automatically clears PyTorch CUDA cache between stages (`torch.cuda.empty_cache()`). If OOM persists, force CPU execution or reduce video segment length.

---

<div align="center">
  Made with ❤️ for Anime Lovers & Dubbing Enthusiasts
</div>
