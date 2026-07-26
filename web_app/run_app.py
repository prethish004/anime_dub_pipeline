"""
run_app.py
==========
Single-command launcher script for AI Anime Dubbing Web Application & Backend Server.
Features automatic virtualenv auto-switching to anime_env.

Usage:
    python web_app/run_app.py
"""

import os
import sys
import subprocess
import webbrowser
import threading
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set KMP_DUPLICATE_LIB_OK to prevent OpenMP crashes on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 🔄 Auto-switch to anime_env Python executable if available and not already active
anime_python = PROJECT_ROOT / "anime_env" / "Scripts" / "python.exe"
if anime_python.exists() and sys.executable.lower() != str(anime_python).lower():
    if "ANIME_ENV_AUTO_SWITCHED" not in os.environ:
        os.environ["ANIME_ENV_AUTO_SWITCHED"] = "1"
        print(f"🔄 Auto-switching to anime_env Python interpreter: {anime_python}")
        code = subprocess.call([str(anime_python)] + sys.argv)
        sys.exit(code)


def open_browser():
    time.sleep(1.5)
    url = "http://localhost:8000"
    print(f"\n🌐 Opening Web Application in browser: {url}")
    webbrowser.open(url)


def main():
    print("=" * 65)
    print("🚀 STARTING AI ANIME DUBBING STUDIO WEB APP & BACKEND SERVER")
    print("=" * 65)
    print(f"  Python Exec: {sys.executable}")
    print("  Server URL : http://localhost:8000")
    print("  Frontend   : Glassmorphic React Web UI Studio")
    print("=" * 65)

    # Launch browser thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Try FastAPI Uvicorn Server first
    try:
        import uvicorn
        from web_app.backend.app import app
        uvicorn.run("web_app.backend.app:app", host="0.0.0.0", port=8000, reload=False)
    except Exception as e:
        print(f"\n⚠️  FastAPI/Uvicorn launch failed ({e}).")
        print("⚡ Switching to Pure Python Web Server (AppControl / WDAC Policy Safe)...")
        from web_app.backend.app_pure import run_pure_server
        run_pure_server(port=8000)


if __name__ == "__main__":
    main()
