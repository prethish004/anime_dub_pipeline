"""
pipeline_runner.py
==================
Asynchronous orchestrator for managing execution of anime dubbing pipeline steps.
Provides real-time log capturing, SSE log streaming, progress tracking, and session workspace control.
"""

import sys
import os

# Prevent OpenMP multiple initialization crash on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import time
import asyncio
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class LogStreamer:
    """Thread-safe log queue for Server-Sent Events (SSE)."""
    def __init__(self):
        self.listeners = []
        self.history: List[str] = []
        self._lock = threading.Lock()

    def emit(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        with self._lock:
            self.history.append(log_line)
            if len(self.history) > 1000:
                self.history.pop(0)
            for queue in self.listeners:
                queue.put_nowait(log_line)

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        with self._lock:
            for line in self.history[-100:]:
                queue.put_nowait(line)
            self.listeners.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        with self._lock:
            if queue in self.listeners:
                self.listeners.remove(queue)

    def clear(self):
        with self._lock:
            self.history.clear()


class OutputRedirector:
    """Redirects stdout and stderr to the log streamer."""
    def __init__(self, streamer: LogStreamer, original_stream):
        self.streamer = streamer
        self.original_stream = original_stream

    def write(self, text):
        if self.original_stream:
            self.original_stream.write(text)
            self.original_stream.flush()
        if text.strip():
            for line in text.splitlines():
                if line.strip():
                    self.streamer.emit(line.strip())

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()


class PipelineRunner:
    """Master Pipeline Manager."""
    def __init__(self):
        self.log_streamer = LogStreamer()
        self.status = "idle"  # "idle" | "running" | "completed" | "error" | "cancelled"
        self.current_step = None
        self.progress_percent = 0
        self.error_message = None
        self.active_thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        self.active_session_name = "default"

    def set_active_session(self, session_name: str):
        self.active_session_name = session_name.replace(" ", "_").lower()

    def get_session_work_dir(self) -> str:
        s_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", f"{self.active_session_name}_work")

        os.makedirs(s_dir, exist_ok=True)
        return s_dir

    def get_session_video_file(self) -> str:
        # 1. Look in web_app/uploads/<session_name>.mp4
        up_v = os.path.join(PROJECT_ROOT, "web_app", "uploads", f"{self.active_session_name}.mp4")
        if os.path.exists(up_v):
            return up_v

        # 2. Look for any video in web_app/uploads/
        up_dir = os.path.join(PROJECT_ROOT, "web_app", "uploads")
        if os.path.exists(up_dir):
            for fn in os.listdir(up_dir):
                if fn.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
                    return os.path.join(up_dir, fn)

        # 3. Fallback to input/anime.mp4
        return os.path.join(PROJECT_ROOT, "input", "anime.mp4")

    def get_session_video_url(self) -> Optional[str]:
        """URL for the active session's own uploaded video, or None if it hasn't
        uploaded one yet. Unlike get_session_video_file(), this never falls back
        to another session's upload or the legacy input/anime.mp4 default."""
        up_v = os.path.join(PROJECT_ROOT, "web_app", "uploads", f"{self.active_session_name}.mp4")
        if os.path.exists(up_v):
            return f"/web_app/uploads/{self.active_session_name}.mp4"
        return None

    def get_state(self) -> Dict:
        return {
            "status": self.status,
            "current_step": self.current_step,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "is_running": self.status == "running",
            "active_session": self.active_session_name,
            "work_dir": self.get_session_work_dir(),
            "video_file": self.get_session_video_file(),
            "video_url": self.get_session_video_url()
        }

    def start_step(self, step_name: str, options: Optional[Dict] = None):
        if self.status == "running":
            raise RuntimeError("Pipeline is already running a task.")

        self.status = "running"
        self.current_step = step_name
        self.progress_percent = 5
        self.error_message = None
        self._cancel_requested = False

        opts = options or {}
        opts.setdefault("work_dir", self.get_session_work_dir())
        opts.setdefault("video_file", self.get_session_video_file())

        self.active_thread = threading.Thread(
            target=self._run_step_thread,
            args=(step_name, opts),
            daemon=True
        )
        self.active_thread.start()

    def start_full_pipeline(self, options: Optional[Dict] = None):
        if self.status == "running":
            raise RuntimeError("Pipeline is already running.")

        self.status = "running"
        self.current_step = "all"
        self.progress_percent = 0
        self.error_message = None
        self._cancel_requested = False

        opts = options or {}
        opts.setdefault("work_dir", self.get_session_work_dir())
        opts.setdefault("video_file", self.get_session_video_file())

        self.active_thread = threading.Thread(
            target=self._run_full_pipeline_thread,
            args=(opts,),
            daemon=True
        )
        self.active_thread.start()

    def request_cancel(self):
        if self.status == "running":
            self._cancel_requested = True
            self.log_streamer.emit("⚠️ Cancellation requested by user...")

    def _run_step_thread(self, step_name: str, options: Dict):
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        sys.stdout = OutputRedirector(self.log_streamer, orig_stdout)
        sys.stderr = OutputRedirector(self.log_streamer, orig_stderr)

        try:
            self.log_streamer.emit(f"🚀 Starting step: {step_name} [Session: {self.active_session_name}]")
            success = self._execute_step(step_name, options)

            if success:
                self.status = "completed"
                self.progress_percent = 100
                self.log_streamer.emit(f"✅ Step {step_name} completed successfully!")
            else:
                self.status = "error"
                self.error_message = f"Step {step_name} returned non-zero status"
                self.log_streamer.emit(f"❌ Step {step_name} failed.")
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            self.log_streamer.emit(f"❌ Exception in {step_name}: {e}")
            self.log_streamer.emit(traceback.format_exc())
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr

    def _run_full_pipeline_thread(self, options: Dict):
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        sys.stdout = OutputRedirector(self.log_streamer, orig_stdout)
        sys.stderr = OutputRedirector(self.log_streamer, orig_stderr)

        steps = [
            "step1_extract_audio",
            "step2_transcribe_diarization",
            "step3_translation",
            "step4_setup",
            "step4_genvoice_complete",
            "step5_assembly"
        ]


        try:
            total_steps = len(steps)
            for idx, step_name in enumerate(steps):
                if self._cancel_requested:
                    self.status = "cancelled"
                    self.log_streamer.emit("🛑 Pipeline execution cancelled.")
                    return

                self.current_step = step_name
                self.progress_percent = int((idx / total_steps) * 100)
                self.log_streamer.emit(f"🚀 [Step {idx+1}/{total_steps}] Starting {step_name}...")

                success = self._execute_step(step_name, options)
                if not success:
                    self.status = "error"
                    self.error_message = f"Pipeline failed at {step_name}"
                    self.log_streamer.emit(f"❌ Pipeline stopped due to failure in {step_name}")
                    return

            self.status = "completed"
            self.progress_percent = 100
            self.current_step = None
            self.log_streamer.emit("🎉 Full Dubbing Pipeline completed successfully!")

        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            self.log_streamer.emit(f"❌ Exception in full pipeline: {e}")
            self.log_streamer.emit(traceback.format_exc())
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr

    def _execute_step(self, step_name: str, options: Dict) -> bool:
        os.chdir(str(PROJECT_ROOT))

        if step_name == "step1_extract_audio":
            import web_app.backend.step1_extract_audio as s1
            return s1.run_step1(options)

        elif step_name == "step2_transcribe_diarization":
            import web_app.backend.step2_transcribe as s2
            return s2.run_step2(options)

        elif step_name == "step2b_gender_confirm":
            import web_app.backend.step2b_gender_confirm as s2b
            return s2b.run_step2b(options)

        elif step_name == "step3_translation":
            import web_app.backend.step3_translation as s3
            return s3.run_step3(options)

        elif step_name == "step4_setup":
            import web_app.backend.step4_setup as s4s
            return s4s.run_step4_setup(options)

        elif step_name == "step4_genvoice_complete":
            import web_app.backend.step4_genvoice as s4g
            return s4g.run_step4_genvoice(options)

        elif step_name == "step5_assembly":
            import web_app.backend.step5_assembly as s5
            return s5.run_step5(options)

        else:
            raise ValueError(f"Unknown step: {step_name}")


runner = PipelineRunner()
