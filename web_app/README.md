# AI Anime Dubbing Studio — Web App

A browser-based front end for the anime dubbing pipeline: upload a video, run
each stage (audio extraction → speaker diarization → translation → voice
cloning → final mux) from a dashboard, watch live logs per step, edit the ADR
script, cast voices per character, and download the finished dub.

This document is a **complete, from-scratch setup guide** — written assuming
you're starting on a brand-new machine with nothing installed. Every command,
every version number, and every workaround below was actually run and
verified on Windows 11 with **no NVIDIA GPU** (Intel integrated graphics
only) — nothing here is theoretical or copy-pasted from a template.

---

## Table of contents

1. [What you need on a fresh machine](#what-you-need-on-a-fresh-machine)
2. [Quick reference: exact versions used](#quick-reference-exact-versions-used)
3. [Step-by-step setup](#step-by-step-setup)
4. [Environment variables reference](#environment-variables-reference)
5. [`.env` configuration](#env-configuration)
6. [Running the app](#running-the-app)
7. [Verifying it actually works](#verifying-it-actually-works)
8. [Architecture](#architecture)
9. [Workflow — how to actually use it](#workflow--how-to-actually-use-it)
10. [What needs a manual check vs. what you can just run](#what-needs-a-manual-check-vs-what-you-can-just-run)
11. [Known issues & limitations](#known-issues--limitations)
12. [Full dependency list (reference)](#full-dependency-list-reference)

---

## What you need on a fresh machine

**Required — nothing here works without these:**

| Software | Version used | Why |
|---|---|---|
| Windows | 10/11 | Setup below is Windows-specific (winget, PowerShell paths). Linux/macOS need equivalent package-manager steps but the same Python/Node versions apply. |
| Python | **3.10.x** (specifically — not 3.11, not 3.9) | One dependency pin only resolves cleanly on 3.10. Confirmed on 3.10.0. |
| Node.js | 24.14.1 (any modern LTS, 18+, should work) | Builds the React frontend. |
| npm | 11.15.0 (ships with Node) | Installs frontend packages. |
| FFmpeg | 8.1 — **the "shared" build specifically**, not just a static `ffmpeg.exe` | Audio/video extraction, the rubberband time-stretch filter, and — critically — its DLLs are required by `torchcodec` (see step 5 below). |
| `winget` | Built into Windows 10 (2004+) / Windows 11 | Used to install FFmpeg. |

**Required for cloud API calls (free to obtain, but you need accounts):**

| Service | Used for |
|---|---|
| OpenAI API key | Step 3's GPT-based ADR translation |
| HuggingFace account + access token | Step 2's speaker-diarization model (gated — see [.env configuration](#env-configuration)) |

**NOT required, despite looking like it should be:**

- ❌ **Visual Studio / Microsoft C++ Build Tools** — the obvious voice-synthesis
  package (`TTS==0.22.0`) needs a C++ compiler to build from source. We
  deliberately use `coqui-tts` instead (a maintained fork with prebuilt
  wheels), so **no compiler is needed at all.**
- ❌ **An NVIDIA GPU / CUDA** — everything runs on CPU. It works, just slowly
  (see [Known issues](#known-issues--limitations)). If you do have a GPU,
  installing CUDA builds of `torch`/`torchaudio` instead would speed things
  up significantly, but that hasn't been set up or tested in this guide.
- ❌ **Conda / Anaconda** — a plain `venv` is all that's used here.

---

## Quick reference: exact versions used

If you just want the version numbers without the explanations, here's every
top-level package this app was verified against. Full transitive-dependency
freeze is in the [appendix](#full-dependency-list-reference).

**Python 3.10.0**, installed into a venv named `anime_env`:

```
torch==2.5.1 → forced to 2.13.0 by pyannote.audio (expected, see step 4)
torchaudio==2.5.1 → forced to 2.11.0
torchcodec==0.16.0
demucs==4.1.0
silero-vad==6.2.1
numpy==2.2.6
soundfile==0.14.0
librosa==0.11.0
transformers==5.15.0
pyannote-audio==4.0.7
python-dotenv==1.2.3
opencv-python==5.0.0.93
openai==3.2.0
pyrubberband==0.4.0
coqui-tts==0.27.5           (NOT TTS==0.22.0 — see step 4)
fastapi==0.141.1
uvicorn==0.52.3
python-multipart==0.0.32
```

**Node.js 24.14.1 / npm 11.15.0**, from `web_app/frontend/package-lock.json`:

```
react==18.3.1
react-dom==18.3.1
lucide-react==0.469.0
vite==6.4.3
```

---

## Step-by-step setup

### 1. Install Python 3.10

Download the Python 3.10 installer from
[python.org/downloads/release](https://www.python.org/downloads/) (any 3.10.x
build) and install it. On Windows, this also registers it with the `py`
launcher, which you'll use to target 3.10 specifically even if a different
Python version is already the system default:

```bash
py -0          # lists all installed Python versions — confirm 3.10 is there
py -3.10 -V    # should print "Python 3.10.x"
```

### 2. Install Node.js

Download and install the LTS build from [nodejs.org](https://nodejs.org/).
Confirm:

```bash
node --version
npm --version
```

### 3. Install FFmpeg (the shared build)

```bash
winget install --id BtbN.FFmpeg.GPL.Shared.8.1 -e --accept-package-agreements --accept-source-agreements
```

This installs `ffmpeg.exe`, `ffprobe.exe`, **and** the shared `.dll` files
(`avcodec-*.dll`, `avformat-*.dll`, `avutil-*.dll`, `swresample-*.dll`,
`swscale-*.dll`, `avfilter-*.dll`, `avdevice-*.dll`) — you need both the
executables and the DLLs, which is why the "shared" variant is specified
instead of a plain static FFmpeg build. Confirm it's on PATH:

```bash
ffmpeg -version
ffprobe -version
```

(If `winget` restarts your shell's PATH, open a new terminal before
continuing.)

### 4. Create the Python virtual environment and install backend dependencies

```bash
cd anime_dub_pipeline
py -3.10 -m venv anime_env
anime_env\Scripts\python.exe -m pip install --upgrade pip
```

Install dependencies **grouped by pipeline step**, in this order. Installing
everything as one `pip install -r requirements.txt` will fail — the exact
pins different libraries want conflict once resolved all at once; installing
per-step and letting pip pick compatible modern versions is what actually
works:

```bash
set PY=anime_env\Scripts\python.exe

:: Step 1 — audio extraction
%PY% -m pip install torch==2.5.1 torchaudio==2.5.1 demucs silero-vad numpy soundfile

:: Step 2 — diarization & transcription
:: NOTE: this will upgrade torch 2.5.1 -> 2.13.0 and torchaudio -> 2.11.0
:: automatically, because pyannote.audio requires torch>=2.8.0. Expected.
%PY% -m pip install librosa transformers pyannote.audio python-dotenv

:: Step 2b — gender confirmation
%PY% -m pip install opencv-python

:: Step 3 — translation
%PY% -m pip install openai

:: Step 4 — voice synthesis
:: Use coqui-tts, NOT the archived TTS==0.22.0 (which needs a C++ compiler
:: to build a Cython extension from source — coqui-tts ships prebuilt
:: wheels under the same `TTS` import name, so no code changes needed).
%PY% -m pip install pyrubberband coqui-tts

:: Web server
%PY% -m pip install fastapi uvicorn python-multipart
```

### 5. Fix the `torchcodec` / FFmpeg DLL requirement

The newer `torchaudio` (pulled in by pyannote.audio in step 4 above) dropped
its old `soundfile`-based backend entirely — `torchaudio.load()` /
`.save()` now **require** `torchcodec`, which needs the FFmpeg shared DLLs
from step 3. Copy them directly into `torchcodec`'s own package folder —
Windows' DLL search order checks the loading DLL's own directory, so this
works with **no PATH changes at all**:

```bash
:: Find where winget installed the shared FFmpeg build, e.g.:
:: %LOCALAPPDATA%\Microsoft\WinGet\Packages\BtbN.FFmpeg.GPL.Shared.8.1_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-n8.1.2-...\bin\

copy "<that bin folder>\avcodec-*.dll"    anime_env\Lib\site-packages\torchcodec\
copy "<that bin folder>\avformat-*.dll"   anime_env\Lib\site-packages\torchcodec\
copy "<that bin folder>\avutil-*.dll"     anime_env\Lib\site-packages\torchcodec\
copy "<that bin folder>\swresample-*.dll" anime_env\Lib\site-packages\torchcodec\
copy "<that bin folder>\swscale-*.dll"    anime_env\Lib\site-packages\torchcodec\
copy "<that bin folder>\avfilter-*.dll"   anime_env\Lib\site-packages\torchcodec\
copy "<that bin folder>\avdevice-*.dll"   anime_env\Lib\site-packages\torchcodec\
```

**Verify this worked** before moving on — run this from the project root
(it loads one of the committed sample voice clips, so no extra test file is
needed):

```bash
anime_env\Scripts\python.exe -c "import torchaudio; wf, sr = torchaudio.load('web_app/sample_voices/female/Amber.mp3'); print('torchaudio load OK', sr, wf.shape)"
```

If this raises `RuntimeError: Could not load libtorchcodec`, the DLL copy
above didn't work — double check the files actually landed in
`anime_env\Lib\site-packages\torchcodec\`.

### 6. Build the frontend

```bash
cd web_app/frontend
npm install
npm run build
cd ../..
```

This produces `web_app/frontend/dist/`, which the backend serves as static
files. **You must re-run `npm run build` after any frontend source change**
— there's no dev-server hot reload wired into the FastAPI server.

### 7. Set up API keys

See [`.env` configuration](#env-configuration) below — do this before first
launch, or Steps 2 and 3 will fail.

### 8. Launch

See [Running the app](#running-the-app) below.

---

## Environment variables reference

These matter and are easy to forget. Set them before launching the server or
running any step script directly:

| Variable | Value | Why |
|---|---|---|
| `PYTHONUTF8` | `1` | Without this, the app crashes immediately with `UnicodeEncodeError` — the step scripts print emoji (🎵 ✅ ❌), and a console defaulting to `cp1252` (common on Windows) can't encode them. |
| `PYTHONIOENCODING` | `utf-8` | Belt-and-suspenders alongside `PYTHONUTF8`. |
| `KMP_DUPLICATE_LIB_OK` | `TRUE` | Prevents an OpenMP crash on Windows when multiple libraries (torch, numpy, etc.) each bundle their own copy of the OpenMP runtime. Already set inside the app's own code (`run_app.py`, `pipeline_runner.py`), but worth knowing about if you run a step script standalone. |
| `HF_HUB_DISABLE_XET` | `1` | Only needed once, while the ~1.9 GB XTTS-v2 model downloads for the first time (see below). `huggingface_hub`'s newer `hf_xet` accelerated-transfer backend was unreliable on this network (silent stalls, hard connection resets); the classic HTTP downloader worked reliably. Not needed after the model is cached locally. |

Set them in `cmd.exe`:
```bash
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
```
or in PowerShell:
```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
```

---

## `.env` configuration

Create a file named `.env` in the **project root** (the same folder as this
repo's root — one level above `web_app/`, not inside it):

```
OPENAI_API_KEY = "sk-..."
HF_TOKEN = "hf_..."
```

- **`OPENAI_API_KEY`** — from <https://platform.openai.com/api-keys>. Used by
  Step 3 for GPT-based ADR translation (model: `gpt-4o-mini`). Costs a small
  amount per run — this is a real, billed API call, not free.
- **`HF_TOKEN`** — from <https://huggingface.co/settings/tokens> (any token
  type works; "Read" access is enough). Used by Step 2 for the gated
  `pyannote/speaker-diarization-3.1` model.

  **Before this token will work**, you must visit both of these pages
  **while logged into the HuggingFace account that owns the token**, and
  click to accept each model's usage terms:
  - <https://huggingface.co/pyannote/speaker-diarization-3.1>
  - <https://huggingface.co/pyannote/segmentation-3.0>

  Skipping this step causes Step 2 to fail with a `401 gated repo` error even
  with an otherwise-valid token.

---

## Running the app

```bash
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
anime_env\Scripts\python.exe web_app\run_app.py
```

This starts the FastAPI backend on **port 8000** and opens
`http://localhost:8000` in your default browser automatically.

To run on a different port instead (`run_app.py` hardcodes 8000), bypass it
and call uvicorn directly:

```bash
anime_env\Scripts\python.exe -m uvicorn web_app.backend.app:app --host 0.0.0.0 --port 8001
```

**After editing any backend `.py` file, you must restart this process.**
Python caches imported modules in memory — editing a file on disk has no
effect on an already-running server until you kill it and relaunch.

The first time you run Step 4 (voice synthesis), it downloads the XTTS-v2
model (~1.9 GB) from HuggingFace automatically. If this stalls or fails
repeatedly, set `HF_HUB_DISABLE_XET=1` before launching (see
[Environment variables](#environment-variables-reference)).

---

## Verifying it actually works

A quick checklist to confirm the environment is genuinely working, cheapest
checks first:

1. **Server starts and responds:**
   ```bash
   curl http://localhost:8000/api/status
   ```
   Should return JSON like `{"status":"idle", ...}`, not a connection error.

2. **Frontend loads:** open `http://localhost:8000` in a browser — you
   should see the dashboard (session selector, step tracker, panels), not a
   blank page or a 404.

3. **Core ML imports work** (catches most environment problems before you
   waste time uploading a video):
   ```bash
   anime_env\Scripts\python.exe -c "import torch, torchaudio, demucs, librosa, transformers, pyannote.audio, cv2, openai, pyrubberband; import transformers.pytorch_utils as pt; pt.isin_mps_friendly = lambda a,b: torch.isin(a,b); from TTS.api import TTS; print('ALL IMPORTS OK')"
   ```
   (The `isin_mps_friendly` line works around a `transformers` 5.x
   compatibility gap — `coqui-tts` expects an internal helper that newer
   `transformers` versions removed; the app patches this in automatically
   at runtime, but a raw import check needs it done manually.)

   If this raises `ModuleNotFoundError`, revisit step 4. If it raises
   anything about `libtorchcodec` or `RuntimeError` on `torchaudio`, revisit
   step 5.

4. **End-to-end**: upload a short (under 2-minute) test video and run Step 1
   only. It should finish in a couple of minutes on CPU and produce
   `web_app/sessions/<name>_work/vocals_clean.wav` and
   `background_full.wav`. This confirms ffmpeg, Demucs, and Silero VAD are
   all working together correctly before you commit to a full run (which,
   without a GPU, can take well over an hour for a real episode).

---

## Architecture

```
web_app/
├── backend/
│   ├── app.py                  FastAPI server — routes, static file mounts
│   ├── app_pure.py             Pure-stdlib fallback server (see Known Issues)
│   ├── pipeline_runner.py      Session state, step execution, SSE log streaming
│   ├── step1_extract_audio.py  Demucs source separation + Silero VAD
│   ├── step2_transcribe.py     PyAnnote diarization + Whisper transcription + gender
│   ├── step2b_gender_confirm.py  Visual gender-confirmation screenshots
│   ├── step3_translation.py    Emotion classification + GPT ADR translation
│   ├── step4_setup.py          Voice sample catalogue + speaker→voice mapping
│   ├── step4_genvoice.py       XTTS-v2 voice synthesis + timing alignment
│   └── step5_assembly.py       Dialogue/background mix + final video mux
├── frontend/                   React + Vite SPA
│   └── src/
│       ├── components/         Navbar, Stepper, VideoWorkspace, VoiceStudio,
│       │                       TranslationEditor, TerminalConsole, MediaCenter
│       ├── hooks/               usePipelineStatus (polls /api/status),
│       │                       useSSELogs (live log stream)
│       ├── services/api.js      Thin fetch wrappers for every backend endpoint
│       └── utils/logGrouping.js Shared log-parsing (groups the log stream by
│                                pipeline step, drives both the terminal panel
│                                and the live per-step progress UI)
├── sessions/<name>_work/       Per-session working directory (all intermediate
│                                and final files for one video live here)
├── uploads/<name>.mp4          Per-session uploaded source video
└── sample_voices/{female,male,tamil}/  Voice-cloning reference clips
```

Each uploaded video gets its own **session** (`sessions/<name>_work/`), so
multiple videos can be worked on independently — switch between them from the
session dropdown in the top bar.

---

## Workflow — how to actually use it

1. **Upload a video** — "Target Input Video" panel → "Upload New Video". This
   creates a new session automatically (named after the file).
2. **Run the pipeline** — either click **"Run Full Dubbing Pipeline"** to run
   all 7 stages back-to-back, or click individual steps in the channel-strip
   stepper to run them one at a time (useful when you want to check/edit
   something between steps — see the next section).
3. **Watch progress live** — the overall progress bar shows which step is
   running and a rolling status line (e.g. "Transcribing segment 14/26...");
   the Live Execution Logs panel groups the full log by step, with a **Copy**
   button per step and a **Copy all** button.
4. **Review and edit before Step 4** (see next section for why):
   - **ADR Script & Translation Editor** — edit any translated line directly
     in the table.
   - **Voice Casting Studio** — reassign which reference voice sample, age
     preset, and tone each detected speaker uses.
5. **Download the result** — once Step 5 finishes, "Dubbed Video Output"
   plays it directly and lists `anime_dubbed_final.mp4`,
   `dialogue_final.wav`, and `mix_final.wav` for download.

Click the **ⓘ** next to "Overall Pipeline Progress" any time for a summary of
which steps are worth checking before moving on.

---

## What needs a manual check vs. what you can just run

| Step | | Why |
|---|---|---|
| 1. Extraction & Demucs | **Just run** | Fully automated, deterministic. |
| 2. Diarization & ASR | **Verify** | Skim the detected speaker count and transcript for obvious mix-ups — everything downstream builds on this. |
| 2b. Gender Check | **Just run** | Currently non-functional (see Known Issues) — nothing to check. |
| 3. Emotion & ADR | **Verify** | Read the translated lines and fix anything awkward in the editor — far cheaper than re-generating voice audio later. |
| 4a. Voice Casting | **Verify** | Confirm the auto-assigned voice actually fits each character before running the slow synthesis step. |
| 4b. Voice Gen & Alignment | **Just run** | Fully automated once casting/text are approved. Slow on CPU — just let it finish. |
| 5. Timeline & Muxing | **Just run** | Fully automated. Worth watching the final video once to confirm sync. |

---

## Known issues & limitations

- **No GPU on this machine** (Intel integrated graphics only) — every ML
  step runs on CPU. Whisper transcription in particular can take many
  minutes per segment; a full real-episode run can take well over an hour.
  If you have an NVIDIA GPU, installing CUDA builds of `torch`/`torchaudio`
  instead would speed this up dramatically — not set up or tested here.
- **Step 2b (Gender Check) always produces 0 screenshots.** Its blur-quality
  filter (`blur > 50.0`, tuned for live-action video) rejects every frame
  from anime footage, whose flatter shading naturally scores lower on the
  same metric. The step "succeeds" but saves nothing. There's also currently
  no frontend UI to display these screenshots even if it did produce them —
  speaker gender is shown only as a text badge (from audio classification),
  not a photo.
- **`waveform_comparisons/` is always empty.** `step4_genvoice.py` creates
  the folder but never writes anything into it — an unfinished feature, not
  something broken.
- **DSP toggles in Voice Casting (emotion/age/kNN-VC transforms) don't
  actually apply.** `step4_genvoice.py` loads these settings from the
  speaker config but the `emotion_out`/`age_out`/`final_out` audio files are
  all identical copies of the raw synthesized clip — the toggles are
  currently no-ops.
- **Live progress can show a finished step as "pending" on very long runs.**
  The per-step progress UI derives state entirely from the live log stream,
  and the server only retains the **last 1000 log lines**
  (`LogStreamer.history` in `pipeline_runner.py`). On a long run, enough
  later logging can push an early step's own "STEP N:" header out of that
  window, making it look unfinished even though its output files are
  actually there. No data is lost — this only affects the progress display.
- **`app_pure.py` (the pure-stdlib fallback server)** is only used if
  FastAPI/uvicorn fail to import. It has known security issues from an
  earlier review — a path-traversal vulnerability in its static file
  handler and a stubbed `/api/upload_video` that never actually saves the
  uploaded file — and hasn't been hardened. As long as `fastapi`/`uvicorn`
  are installed per the setup above, this fallback path is never used.
- **Uploading a video silently switches the active session.** If you're
  working in one session and upload an unrelated file just to check
  something, the backend derives a new session name from that file and
  switches to it — your original session's data is still there, just no
  longer active.

---

## Full dependency list (reference)

This is the exact `pip freeze` output from a fully working `anime_env`,
including every transitive dependency — useful if something drifts and you
need to pin an exact version, but **don't `pip install -r` this whole list
directly** — installing it all at once is what caused the resolver
conflicts that the [step-by-step setup](#step-by-step-setup) above avoids by
installing per pipeline step instead.

<details>
<summary>Click to expand full <code>pip freeze</code> (154 packages)</summary>

```
absl-py==2.5.0
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
alembic==1.19.1
annotated-doc==0.0.5
annotated-types==0.8.0
anyascii==0.3.3
anyio==4.14.2
asteroid-filterbanks==0.4.0
async-timeout==5.0.1
attrs==26.1.0
audioread==3.1.0
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.5.1
click==8.4.2
colorama==0.4.6
colorlog==6.12.0
contourpy==1.3.2
coqpit-config==0.2.5
coqui-tts==0.27.5
coqui-tts-trainer==0.3.3
cycler==0.12.1
decorator==5.3.1
demucs==4.1.0
distro==1.9.0
docopt==0.6.2
einops==0.8.2
exceptiongroup==1.3.1
fastapi==0.141.1
filelock==3.32.3
fonttools==4.63.0
frozenlist==1.8.0
fsspec==2026.7.0
googleapis-common-protos==1.75.1
greenlet==3.5.5
grpcio==1.83.0
h11==0.16.0
hf-xet==1.6.0
httpcore==1.0.9
httpcore2==2.11.0
httpx==0.28.1
httpx2==2.11.0
huggingface_hub==1.27.0
idna==3.18
inflect==7.5.0
Jinja2==3.1.6
jiter==0.16.0
joblib==1.5.3
julius==0.2.8
kiwisolver==1.5.0
ko-speech-tools==0.1.0
lameenc==1.8.4
lazy-loader==0.5
librosa==0.11.0
lightning==2.6.5
lightning-utilities==0.15.3
llvmlite==0.49.0
Mako==1.4.1
Markdown==3.10.3
markdown-it-py==4.2.0
MarkupSafe==3.0.3
matplotlib==3.10.9
mdurl==0.1.2
monotonic-alignment-search==0.2.1
more-itertools==11.1.0
mpmath==1.3.0
msgpack==1.2.1
multidict==6.7.1
networkx==3.4.2
num2words==0.5.14
numba==0.67.0
numpy==2.2.6
openai==3.2.0
opencv-python==5.0.0.93
opentelemetry-api==1.44.0
opentelemetry-exporter-otlp==1.44.0
opentelemetry-exporter-otlp-proto-common==1.44.0
opentelemetry-exporter-otlp-proto-grpc==1.44.0
opentelemetry-exporter-otlp-proto-http==1.44.0
opentelemetry-proto==1.44.0
opentelemetry-sdk==1.44.0
opentelemetry-semantic-conventions==0.65b0
optuna==4.9.0
packaging==26.3
pandas==2.3.3
pillow==12.3.0
platformdirs==4.11.3
pooch==1.9.0
primePy==1.3
propcache==0.5.2
protobuf==7.35.1
psutil==7.2.2
pyannote-audio==4.0.7
pyannote-core==6.0.1
pyannote-database==6.1.1
pyannote-metrics==4.1
pyannote-pipeline==4.0.0
pyannoteai-sdk==0.4.0
pycparser==3.0
pydantic==2.13.4
pydantic_core==2.46.4
Pygments==2.21.0
pyparsing==3.3.2
pyrubberband==0.4.0
pysbd==0.3.4
python-dateutil==2.9.0.post0
python-dotenv==1.2.3
python-multipart==0.0.32
pytorch-lightning==2.6.5
pytorch-metric-learning==2.9.0
pytz==2026.3.post1
PyYAML==6.0.3
regex==2026.7.19
requests==2.34.2
rich==15.0.0
safetensors==0.8.0
scikit-learn==1.7.2
scipy==1.15.3
shellingham==1.5.4
silero-vad==6.2.1
six==1.17.0
sniffio==1.3.1
sortedcontainers==2.4.0
soundfile==0.14.0
soxr==1.1.0
sphn==0.2.1
SQLAlchemy==2.0.52
starlette==1.6.0
sympy==1.14.0
tensorboard==2.21.0
tensorboard-data-server==0.7.2
threadpoolctl==3.6.0
tokenizers==0.22.2
tomli==2.4.1
torch==2.13.0
torch-audiomentations==0.12.0
torch_pitch_shift==1.2.5
torchaudio==2.11.0
torchcodec==0.16.0
torchmetrics==1.9.0
tqdm==4.70.0
transformers==5.15.0
truststore==0.10.4
typeguard==4.6.0
typer==0.27.1
typing-inspection==0.4.4
typing_extensions==4.16.0
tzdata==2026.3
urllib3==2.7.0
uvicorn==0.52.3
Werkzeug==3.1.8
yarl==1.24.5
```

</details>

**Frontend** — exact resolved versions from `web_app/frontend/package-lock.json`:

<details>
<summary>Click to expand frontend dependencies</summary>

```
react==18.3.1
react-dom==18.3.1
lucide-react==0.469.0
vite==6.4.3
@vitejs/plugin-react==^4.3.4
@types/react==^18.3.18
@types/react-dom==^18.3.5
```

Reinstall these exactly with:
```bash
cd web_app/frontend
npm ci        # uses package-lock.json for exact reproducible versions
```

</details>
