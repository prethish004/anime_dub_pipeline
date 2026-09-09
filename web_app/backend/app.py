"""
app.py
======
FastAPI Server for AI Anime Dubbing Web Application with Multi-Video Session Support
"""

import os
import sys

# Prevent OpenMP multiple initialization crash on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional


from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from web_app.backend.pipeline_runner import runner
from web_app.backend.step4_setup import scan_voice_samples

app = FastAPI(title="AI Anime Dubbing Studio API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = os.path.join(PROJECT_ROOT, "web_app", "frontend", "dist")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "web_app", "frontend")
WEB_APP_DIR = os.path.join(PROJECT_ROOT, "web_app")
SESSIONS_DIR = os.path.join(WEB_APP_DIR, "sessions")
UPLOADS_DIR = os.path.join(WEB_APP_DIR, "uploads")
SAMPLE_VOICES_DIR = os.path.join(WEB_APP_DIR, "sample_voices")

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(SAMPLE_VOICES_DIR, exist_ok=True)

# Mount Static Directories
assets_dir = os.path.join(FRONTEND_DIST, "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

app.mount("/web_app/sessions", StaticFiles(directory=SESSIONS_DIR), name="sessions")
app.mount("/web_app/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/web_app/sample_voices", StaticFiles(directory=SAMPLE_VOICES_DIR), name="sample_voices_internal")

# Fallback mounts for backward compatibility
if os.path.exists(os.path.join(PROJECT_ROOT, "work")):
    app.mount("/work", StaticFiles(directory=os.path.join(PROJECT_ROOT, "work")), name="work")
if os.path.exists(os.path.join(PROJECT_ROOT, "input")):
    app.mount("/input", StaticFiles(directory=os.path.join(PROJECT_ROOT, "input")), name="input")
if os.path.exists(os.path.join(PROJECT_ROOT, "sample_voices")):
    app.mount("/sample_voices", StaticFiles(directory=os.path.join(PROJECT_ROOT, "sample_voices")), name="sample_voices")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_dist = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_dist):
        with open(index_dist, "r", encoding="utf-8") as f:
            return f.read()
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Anime Dubbing Pipeline API</h1><p>Frontend index.html not found.</p>"


@app.get("/api/status")
async def get_status():
    return runner.get_state()


@app.get("/api/stream_logs")
async def stream_logs():
    async def event_generator():
        queue = runner.log_streamer.subscribe()
        try:
            while True:
                log_line = await queue.get()
                yield f"data: {json.dumps({'message': log_line})}\n\n"
        except asyncio.CancelledError:
            runner.log_streamer.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/sessions")
async def get_sessions():
    sessions = []
    if os.path.exists(SESSIONS_DIR):
        for fn in os.listdir(SESSIONS_DIR):
            fp = os.path.join(SESSIONS_DIR, fn)
            if os.path.isdir(fp) and fn.endswith("_work"):
                s_name = fn[:-5]
                sessions.append({
                    "name": s_name,
                    "folder": fn,
                    "active": s_name == runner.active_session_name
                })
    if not sessions:
        sessions.append({"name": "default", "folder": "default_work", "active": True})
    return {"sessions": sessions, "active_session": runner.active_session_name}


@app.post("/api/select_session")
async def select_session(payload: Dict[str, Any]):
    s_name = payload.get("session_name", "default")
    runner.set_active_session(s_name)
    return {"status": "selected", "active_session": runner.active_session_name}


@app.post("/api/run_step")
async def run_step(payload: Dict[str, Any]):
    step_name = payload.get("step")
    options = payload.get("options", {})

    if not step_name:
        raise HTTPException(status_code=400, detail="Missing step name")

    try:
        if step_name == "all":
            runner.start_full_pipeline(options)
        else:
            runner.start_step(step_name, options)
        return {"status": "started", "step": step_name, "session": runner.active_session_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/cancel")
async def cancel_pipeline():
    runner.request_cancel()
    return {"status": "cancellation_requested"}


@app.post("/api/upload_video")
async def upload_video(file: UploadFile = File(...), session_name: Optional[str] = Form(None)):
    if not session_name:
        session_name = Path(file.filename).stem
    s_name = session_name.replace(" ", "_").lower()
    runner.set_active_session(s_name)

    v_filename = f"{s_name}.mp4"
    out_path = os.path.join(UPLOADS_DIR, v_filename)
    with open(out_path, "wb") as f:
        content = await file.read()
        f.write(content)

    runner.get_session_work_dir()
    return {
        "status": "success",
        "file": f"web_app/uploads/{v_filename}",
        "session_name": s_name,
        "size_bytes": len(content)
    }


@app.get("/api/transcription")
async def get_transcription():
    w_dir = runner.get_session_work_dir()
    trans_json = os.path.join(w_dir, "transcription_with_speakers.json")
    profiles_json = os.path.join(w_dir, "speaker_profiles.json")
    step3_json = os.path.join(w_dir, "translated_segments_step3.json")

    data = {}
    if os.path.exists(step3_json):
        with open(step3_json, "r", encoding="utf-8") as f:
            data["translations"] = json.load(f)
    elif os.path.exists(trans_json):
        with open(trans_json, "r", encoding="utf-8") as f:
            data["transcription"] = json.load(f)

    if os.path.exists(profiles_json):
        with open(profiles_json, "r", encoding="utf-8") as f:
            data["profiles"] = json.load(f)

    return data


@app.post("/api/save_translation")
async def save_translation(payload: Dict[str, Any]):
    w_dir = runner.get_session_work_dir()
    step3_json = os.path.join(w_dir, "translated_segments_step3.json")

    if not os.path.exists(step3_json):
        data = {
            "timestamp": "",
            "language_mode": payload.get("language_mode", "english"),
            "segments": payload.get("segments", [])
        }
    else:
        with open(step3_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "segments" in payload:
            data["segments"] = payload["segments"]
        if "language_mode" in payload:
            data["language_mode"] = payload["language_mode"]

    with open(step3_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"status": "saved", "segments": len(data.get("segments", []))}


@app.get("/api/voices")
async def get_voices():
    return scan_voice_samples()


@app.get("/api/speaker_config")
async def get_speaker_config():
    w_dir = runner.get_session_work_dir()
    config_json = os.path.join(w_dir, "speaker_config.json")
    if os.path.exists(config_json):
        with open(config_json, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"speaker_configs": {}, "global_toggles": {}}


@app.post("/api/save_speaker_config")
async def save_speaker_config(payload: Dict[str, Any]):
    w_dir = runner.get_session_work_dir()
    config_json = os.path.join(w_dir, "speaker_config.json")
    with open(config_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return {"status": "saved"}


@app.get("/api/outputs")
async def get_outputs():
    w_dir = runner.get_session_work_dir()
    out_dir = os.path.join(w_dir, "output")
    files = []
    if os.path.exists(out_dir):
        for fn in os.listdir(out_dir):
            fp = os.path.join(out_dir, fn)
            if os.path.isfile(fp):
                rel_url = os.path.relpath(fp, str(PROJECT_ROOT)).replace("\\", "/")
                files.append({
                    "filename": fn,
                    "url": f"/{rel_url}",
                    "size_mb": round(os.path.getsize(fp) / 1e6, 2)
                })
    return {"files": files}


@app.get("/api/waveform_comparisons")
async def get_waveform_comparisons():
    w_dir = runner.get_session_work_dir()
    plot_dir = os.path.join(w_dir, "waveform_comparisons")
    files = []
    if os.path.exists(plot_dir):
        for fn in sorted(os.listdir(plot_dir)):
            fp = os.path.join(plot_dir, fn)
            if os.path.isfile(fp) and fn.lower().endswith(".png"):
                rel_url = os.path.relpath(fp, str(PROJECT_ROOT)).replace("\\", "/")
                files.append({"filename": fn, "url": f"/{rel_url}"})
    return {"files": files}


# Serves files copied from frontend/public/ (e.g. logo.png) at the site root.
# Registered last so it only catches paths no route/mount above already claimed.
app.mount("/", StaticFiles(directory=FRONTEND_DIST), name="frontend_public")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app.backend.app:app", host="0.0.0.0", port=8000, reload=True)
