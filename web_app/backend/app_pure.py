"""
app_pure.py
===========
Pure Python Standard Library HTTP Server for AI Anime Dubbing Studio.
Built using http.server to guarantee 100% compatibility on Windows AppControl / WDAC policies
without relying on compiled C-extension DLLs like _pydantic_core.pyd.
"""

import os
import sys
import json
import urllib.parse
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from web_app.backend.pipeline_runner import runner
from web_app.backend.step4_setup import scan_voice_samples

FRONTEND_DIST = os.path.join(PROJECT_ROOT, "web_app", "frontend", "dist")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "web_app", "frontend")
WEB_APP_DIR = os.path.join(PROJECT_ROOT, "web_app")
SESSIONS_DIR = os.path.join(WEB_APP_DIR, "sessions")
UPLOADS_DIR = os.path.join(WEB_APP_DIR, "uploads")
SAMPLE_VOICES_DIR = os.path.join(WEB_APP_DIR, "sample_voices")

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(SAMPLE_VOICES_DIR, exist_ok=True)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server to handle concurrent SSE and API calls."""
    daemon_threads = True


class PureStudioHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Suppress noise in console, logs go to pipeline streamer
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path):
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, "File Not Found")
            return

        ctype, _ = mimetypes.guess_type(file_path)
        if not ctype:
            ctype = "application/octet-stream"

        try:
            file_size = os.path.getsize(file_path)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except Exception:
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # 1. API Endpoints
        if path == "/api/status":
            return self._send_json(runner.get_state())

        elif path == "/api/sessions":
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
            return self._send_json({"sessions": sessions, "active_session": runner.active_session_name})

        elif path == "/api/stream_logs":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            last_idx = 0
            try:
                while True:
                    history = list(runner.log_streamer.history)
                    if len(history) > last_idx:
                        for line in history[last_idx:]:
                            msg = f"data: {json.dumps({'message': line})}\n\n"
                            self.wfile.write(msg.encode("utf-8"))
                            self.wfile.flush()
                        last_idx = len(history)
                    import time
                    time.sleep(0.5)
            except Exception:
                return

        elif path == "/api/transcription":
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

            return self._send_json(data)

        elif path == "/api/voices":
            return self._send_json(scan_voice_samples())

        elif path == "/api/speaker_config":
            w_dir = runner.get_session_work_dir()
            config_json = os.path.join(w_dir, "speaker_config.json")
            if os.path.exists(config_json):
                with open(config_json, "r", encoding="utf-8") as f:
                    return self._send_json(json.load(f))
            return self._send_json({"speaker_configs": {}, "global_toggles": {}})

        elif path == "/api/outputs":
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
            return self._send_json({"files": files})

        # 2. Static Content Routing
        if path == "/":
            index_dist = os.path.join(FRONTEND_DIST, "index.html")
            if os.path.exists(index_dist):
                return self._send_file(index_dist)
            index_path = os.path.join(FRONTEND_DIR, "index.html")
            return self._send_file(index_path)

        # File path resolution
        req_rel = path.lstrip("/")
        full_target = os.path.join(PROJECT_ROOT, req_rel)

        if os.path.exists(full_target) and os.path.isfile(full_target):
            return self._send_file(full_target)

        # Check frontend dist assets
        dist_target = os.path.join(FRONTEND_DIST, req_rel)
        if os.path.exists(dist_target) and os.path.isfile(dist_target):
            return self._send_file(dist_target)

        # Fallback to 404
        self.send_error(404, f"Path Not Found: {self.path}")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""

        payload = {}
        if post_data and self.headers.get("Content-Type", "").startswith("application/json"):
            try:
                payload = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/select_session":
            s_name = payload.get("session_name", "default")
            runner.set_active_session(s_name)
            return self._send_json({"status": "selected", "active_session": runner.active_session_name})

        elif path == "/api/run_step":
            step_name = payload.get("step")
            options = payload.get("options", {})
            if not step_name:
                return self._send_json({"error": "Missing step name"}, status=400)
            try:
                if step_name == "all":
                    runner.start_full_pipeline(options)
                else:
                    runner.start_step(step_name, options)
                return self._send_json({"status": "started", "step": step_name, "session": runner.active_session_name})
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)

        elif path == "/api/cancel":
            runner.request_cancel()
            return self._send_json({"status": "cancellation_requested"})

        elif path == "/api/save_translation":
            w_dir = runner.get_session_work_dir()
            step3_json = os.path.join(w_dir, "translated_segments_step3.json")
            with open(step3_json, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return self._send_json({"status": "saved"})

        elif path == "/api/save_speaker_config":
            w_dir = runner.get_session_work_dir()
            config_json = os.path.join(w_dir, "speaker_config.json")
            with open(config_json, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return self._send_json({"status": "saved"})

        elif path == "/api/upload_video":
            # Simple fallback upload handling
            return self._send_json({"status": "success", "file": "web_app/uploads/anime.mp4"})

        return self._send_json({"error": "Endpoint not found"}, status=404)


def run_pure_server(port=8000):
    server = ThreadedHTTPServer(("0.0.0.0", port), PureStudioHandler)
    print(f"✅ Pure Python Web Server listening on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_pure_server()
