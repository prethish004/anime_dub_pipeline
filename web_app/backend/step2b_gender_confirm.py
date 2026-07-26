"""
step2b_gender_confirm.py
========================
Modular Backend Step 2b: Video Frame Extraction for Visual Gender Confirmation
"""

import os
import sys
import json
import cv2
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def calculate_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def calculate_brightness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray.mean()

def run_step2b(options: dict) -> bool:
    print("=" * 60)
    print("STEP 2b: Visual Gender Confirmation Screenshots")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    video_file = options.get("video_file")
    if not video_file or not os.path.exists(video_file):
        video_file = os.path.join(PROJECT_ROOT, "input", "anime.mp4")

    trans_json = os.path.join(work_dir, "transcription_with_speakers.json")
    profiles_json = os.path.join(work_dir, "speaker_profiles.json")

    if not os.path.exists(trans_json) or not os.path.exists(video_file):
        print(f"❌ Missing required inputs in {work_dir}")
        return False

    with open(trans_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(profiles_json, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    segments = data.get("segments", [])
    speakers = data.get("speakers", [])
    output_dir = os.path.join(work_dir, "gender_screenshots")
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(str(video_file))
    fps = cap.get(cv2.CAP_PROP_FPS)

    for speaker in speakers:
        spk_segs = [s for s in segments if s.get("speaker") == speaker]
        spk_dir = os.path.join(output_dir, speaker)
        os.makedirs(spk_dir, exist_ok=True)

        screenshots = []
        sample_segs = spk_segs[:min(4, len(spk_segs))]

        for seg in sample_segs:
            mid_t = (seg["start"] + seg["end"]) / 2.0
            frame_idx = int(mid_t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            blur = calculate_blur(frame)
            brightness = calculate_brightness(frame)

            if blur > 50.0 and brightness > 30.0:
                fn = f"seg{seg['id']:03d}_{mid_t:.1f}s.png"
                out_p = os.path.join(spk_dir, fn)
                cv2.imwrite(out_p, frame)
                screenshots.append(os.path.relpath(out_p, str(PROJECT_ROOT)).replace("\\", "/"))

        profiles[speaker]["screenshots"] = screenshots
        print(f"  ✓ {speaker}: Saved {len(screenshots)} screenshots")

    cap.release()

    with open(profiles_json, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Step 2b Complete! Workspace: {work_dir}")
    return True
