# """
# STEP 2b: Speaker Gender Confirmation via Video Screenshots
# ===========================================================
# Sits between Step 2 (transcription) and Step 3 (translation).

# What it does:
#   1. Reads speaker segments from transcription_with_speakers.json
#   2. For each speaker, randomly picks up to 4 segments
#   3. Extracts one screenshot per selected segment from the video
#      - Tries the midpoint of the segment first
#      - If the frame is too dark/blurry, scans nearby frames within the segment
#   4. Sends the screenshots to Claude Vision API for gender confirmation
#   5. Updates speaker_profiles.json and transcription_with_speakers.json
#      with confirmed gender + confidence

# Input:
#   work/transcription_with_speakers.json   (from Step 2)
#   input/anime.mp4

# Output:
#   work/gender_screenshots/               screenshots per speaker
#   work/transcription_with_speakers.json  (updated — confirmed_gender added)
#   work/speaker_profiles.json             (updated)
# """

# import os
# import cv2
# import json
# import base64
# import random
# import shutil
# import numpy as np
# from pathlib import Path
# from datetime import datetime
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# print("=" * 60)
# print("STEP 2b: Speaker Gender Confirmation (Vision)")
# print("=" * 60)

# # ─────────────────────────────────────────────────────────────
# # CONFIG
# # ─────────────────────────────────────────────────────────────
# VIDEO_FILE      = "input/anime.mp4"
# TRANSCRIPT_JSON = "work/transcription_with_speakers.json"
# PROFILES_JSON   = "work/speaker_profiles.json"
# SCREENSHOT_DIR  = "work/gender_screenshots"

# MAX_SEGMENTS_PER_SPEAKER = 4     # randomly sample up to this many segments
# BLUR_THRESHOLD           = 80.0  # Laplacian variance — below this = blurry frame
# DARK_THRESHOLD           = 40.0  # mean pixel value — below this = too dark
# FRAME_SCAN_STEP_S        = 0.15  # step size when scanning for a clearer frame

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     raise ValueError("Set OPENAI_API_KEY in your .env file")
# client = OpenAI(api_key=OPENAI_API_KEY)

# os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# # ─────────────────────────────────────────────────────────────
# # LOAD TRANSCRIPTION
# # ─────────────────────────────────────────────────────────────
# if not os.path.exists(TRANSCRIPT_JSON):
#     raise FileNotFoundError(f"Not found: {TRANSCRIPT_JSON} — run Step 2 first")

# with open(TRANSCRIPT_JSON, "r", encoding="utf-8") as f:
#     data = json.load(f)

# segments         = data["segments"]
# speaker_profiles = data.get("speaker_profiles", {})
# speakers         = sorted(set(s["speaker"] for s in segments))

# print(f"Speakers found : {speakers}")
# print(f"Total segments : {len(segments)}")

# # ─────────────────────────────────────────────────────────────
# # VIDEO SETUP
# # ─────────────────────────────────────────────────────────────
# if not os.path.exists(VIDEO_FILE):
#     raise FileNotFoundError(f"Video not found: {VIDEO_FILE}")

# cap = cv2.VideoCapture(VIDEO_FILE)
# if not cap.isOpened():
#     raise RuntimeError(f"Cannot open video: {VIDEO_FILE}")

# FPS          = cap.get(cv2.CAP_PROP_FPS)
# TOTAL_FRAMES = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
# DURATION_S   = TOTAL_FRAMES / FPS

# print(f"\nVideo : {VIDEO_FILE}")
# print(f"FPS   : {FPS:.2f}")
# print(f"Total : {TOTAL_FRAMES} frames  ({DURATION_S:.1f}s)\n")

# # ─────────────────────────────────────────────────────────────
# # FRAME QUALITY HELPERS
# # ─────────────────────────────────────────────────────────────
# def frame_quality(frame) -> dict:
#     """Return blur score and brightness for a BGR frame."""
#     gray       = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
#     brightness = float(np.mean(gray))
#     return {"blur": blur_score, "brightness": brightness}

# def is_acceptable(frame) -> bool:
#     q = frame_quality(frame)
#     return q["blur"] >= BLUR_THRESHOLD and q["brightness"] >= DARK_THRESHOLD

# def read_frame_at(cap, timestamp_s: float):
#     """Seek to timestamp and return the frame (or None)."""
#     frame_idx = int(timestamp_s * FPS)
#     frame_idx = max(0, min(frame_idx, TOTAL_FRAMES - 1))
#     cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
#     ret, frame = cap.read()
#     return frame if ret else None

# def best_frame_in_segment(cap, start: float, end: float) -> tuple:
#     """
#     Try the midpoint first. If blurry/dark, scan forward/backward
#     within the segment in FRAME_SCAN_STEP_S steps.
#     Returns (frame, timestamp_used) or (None, None).
#     """
#     mid = (start + end) / 2.0

#     # Try midpoint
#     frame = read_frame_at(cap, mid)
#     if frame is not None and is_acceptable(frame):
#         return frame, mid

#     # Scan outward from midpoint within segment bounds
#     offsets = []
#     step = FRAME_SCAN_STEP_S
#     t = mid + step
#     while t <= end:
#         offsets.append(t); t += step
#     t = mid - step
#     while t >= start:
#         offsets.append(t); t -= step

#     best_frame = frame   # fallback to midpoint even if poor quality
#     best_ts    = mid
#     best_score = 0.0

#     for ts in offsets:
#         f = read_frame_at(cap, ts)
#         if f is None:
#             continue
#         q = frame_quality(f)
#         score = q["blur"] * 0.6 + q["brightness"] * 0.4
#         if is_acceptable(f) and score > best_score:
#             best_frame = f
#             best_ts    = ts
#             best_score = score

#     return best_frame, best_ts

# # ─────────────────────────────────────────────────────────────
# # SCREENSHOT EXTRACTION
# # ─────────────────────────────────────────────────────────────
# def extract_screenshots(speaker_id: str, speaker_segs: list) -> list:
#     """
#     Randomly sample up to MAX_SEGMENTS_PER_SPEAKER segments,
#     extract the best frame from each, save as PNG.
#     Returns list of saved file paths.
#     """
#     spk_dir = os.path.join(SCREENSHOT_DIR, speaker_id)
#     os.makedirs(spk_dir, exist_ok=True)

#     # Random sampling
#     pool    = speaker_segs.copy()
#     random.shuffle(pool)
#     sampled = pool[:MAX_SEGMENTS_PER_SPEAKER]

#     saved = []
#     for seg in sampled:
#         start = seg["start"]
#         end   = seg["end"]
#         sid   = seg["id"]

#         frame, ts_used = best_frame_in_segment(cap, start, end)
#         if frame is None:
#             print(f"    ✗  Seg {sid:03d} [{start:.2f}s–{end:.2f}s] — no frame")
#             continue

#         q        = frame_quality(frame)
#         out_path = os.path.join(spk_dir, f"seg{sid:03d}_{ts_used:.2f}s.png")
#         cv2.imwrite(out_path, frame)
#         saved.append(out_path)
#         print(f"    ✓  Seg {sid:03d} [{start:.2f}s–{end:.2f}s] → "
#               f"{ts_used:.2f}s | blur:{q['blur']:.0f} bright:{q['brightness']:.0f} "
#               f"→ {os.path.basename(out_path)}")

#     return saved

# # ─────────────────────────────────────────────────────────────
# # CLAUDE VISION — GENDER CONFIRMATION
# # ─────────────────────────────────────────────────────────────
# def image_to_b64(path: str) -> str:
#     with open(path, "rb") as f:
#         return base64.b64encode(f.read()).decode("utf-8")

# def confirm_gender_with_vision(speaker_id: str,
#                                  screenshot_paths: list,
#                                  audio_gender: str) -> dict:
#     """
#     Send screenshots to Claude Vision and ask for gender confirmation.
#     Returns: {"confirmed_gender": "male"|"female"|"unknown",
#               "confidence": "high"|"medium"|"low",
#               "reasoning": "...",
#               "votes": {"male": N, "female": N, "unknown": N}}
#     """
#     if not screenshot_paths:
#         return {
#             "confirmed_gender": audio_gender,
#             "confidence":       "low",
#             "reasoning":        "No screenshots available — using audio estimate.",
#             "votes":            {"male": 0, "female": 0, "unknown": 0},
#         }

#     # Build vision message — one image block per screenshot
#     content = []

#     content.append({
#         "type": "text",
#         "text": (
#             f"You are analyzing screenshots from an anime video to confirm the gender "
#             f"of a voice actor's character.\n\n"
#             f"Speaker ID : {speaker_id}\n"
#             f"Audio-based gender estimate : {audio_gender}\n\n"
#             f"Below are {len(screenshot_paths)} screenshot(s) taken during this speaker's "
#             f"dialogue segments. Examine each image carefully.\n\n"
#             f"For EACH image, identify:\n"
#             f"  1. Is a character clearly visible and speaking (open mouth, focused shot)?\n"
#             f"  2. What is the apparent gender of that character?\n\n"
#             f"Then give your FINAL consolidated answer as JSON only — no markdown:\n"
#             '{"confirmed_gender": "male" or "female" or "unknown", '
#             '"confidence": "high" or "medium" or "low", '
#             '"reasoning": "one sentence", '
#             '"per_image": ["male/female/unknown", ...]}\n\n'
#             f"Rules:\n"
#             f"- Use 'unknown' if no character is clearly visible in ANY image.\n"
#             f"- 'high' confidence = 3+ images agree, face clearly visible.\n"
#             f"- 'medium' = 2 images agree or face partially visible.\n"
#             f"- 'low' = only 1 image or conflicting results.\n"
#             f"- Anime characters: judge by visual design cues (hair, face shape, "
#             f"body proportions, clothing) not just hairstyle alone."
#         )
#     })

#     for i, path in enumerate(screenshot_paths):
#         b64 = image_to_b64(path)
#         content.append({
#             "type": "image_url",
#             "image_url": {
#                 "url":    f"data:image/png;base64,{b64}",
#                 "detail": "low"   # saves tokens; faces are still clear
#             }
#         })
#         content.append({
#             "type": "text",
#             "text": f"Image {i+1}: {os.path.basename(path)}"
#         })

#     try:
#         resp = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[{"role": "user", "content": content}],
#             max_tokens=400,
#             temperature=0.1,
#             response_format={"type": "json_object"},
#         )
#         raw  = resp.choices[0].message.content.strip()
#         obj  = json.loads(raw)

#         confirmed = obj.get("confirmed_gender", "unknown").lower()
#         if confirmed not in ("male", "female", "unknown"):
#             confirmed = "unknown"

#         confidence = obj.get("confidence", "low").lower()
#         reasoning  = obj.get("reasoning", "")
#         per_image  = obj.get("per_image", [])

#         votes = {"male": 0, "female": 0, "unknown": 0}
#         for v in per_image:
#             key = v.lower() if v.lower() in votes else "unknown"
#             votes[key] += 1

#         return {
#             "confirmed_gender": confirmed,
#             "confidence":       confidence,
#             "reasoning":        reasoning,
#             "votes":            votes,
#         }

#     except Exception as e:
#         print(f"    WARNING: Vision API failed: {e}")
#         return {
#             "confirmed_gender": audio_gender,
#             "confidence":       "low",
#             "reasoning":        f"Vision API error: {e}",
#             "votes":            {"male": 0, "female": 0, "unknown": 0},
#         }

# # ─────────────────────────────────────────────────────────────
# # MAIN — PER SPEAKER
# # ─────────────────────────────────────────────────────────────
# gender_results = {}

# for spk_id in speakers:
#     print(f"\n{'─'*55}")
#     print(f"Speaker: {spk_id}")

#     spk_segs     = [s for s in segments if s["speaker"] == spk_id]
#     audio_gender = (speaker_profiles.get(spk_id, {})
#                     .get("gender", "unknown"))

#     print(f"  Segments : {len(spk_segs)} total | "
#           f"sampling up to {MAX_SEGMENTS_PER_SPEAKER}")
#     print(f"  Audio gender estimate: {audio_gender}")

#     # 1. Extract screenshots
#     print("  Extracting frames...")
#     screenshots = extract_screenshots(spk_id, spk_segs)
#     print(f"  → {len(screenshots)} screenshots saved")

#     # 2. Vision gender confirmation
#     print("  Confirming gender with Vision API...")
#     result = confirm_gender_with_vision(spk_id, screenshots, audio_gender)

#     confirmed  = result["confirmed_gender"]
#     confidence = result["confidence"]
#     reasoning  = result["reasoning"]
#     votes      = result["votes"]

#     print(f"  Audio estimate  : {audio_gender}")
#     print(f"  Vision confirmed: {confirmed}  [{confidence}]")
#     print(f"  Votes           : {votes}")
#     print(f"  Reasoning       : {reasoning}")

#     if audio_gender != confirmed and confirmed != "unknown":
#         print(f"  ⚠  GENDER MISMATCH — audio said '{audio_gender}', "
#               f"vision says '{confirmed}' [{confidence}]")
#     elif confirmed == "unknown":
#         print(f"  ?  Could not confirm visually — keeping audio estimate: {audio_gender}")
#         confirmed = audio_gender

#     gender_results[spk_id] = {
#         "audio_gender":     audio_gender,
#         "confirmed_gender": confirmed,
#         "confidence":       confidence,
#         "reasoning":        reasoning,
#         "votes":            votes,
#         "screenshots":      screenshots,
#         "segments_sampled": MAX_SEGMENTS_PER_SPEAKER,
#     }

# # ─────────────────────────────────────────────────────────────
# # UPDATE speaker_profiles in transcription JSON
# # ─────────────────────────────────────────────────────────────
# print(f"\n{'─'*55}")
# print("Updating speaker profiles...")

# for spk_id, result in gender_results.items():
#     if spk_id not in speaker_profiles:
#         speaker_profiles[spk_id] = {}

#     speaker_profiles[spk_id]["gender"]           = result["confirmed_gender"]
#     speaker_profiles[spk_id]["gender_audio"]     = result["audio_gender"]
#     speaker_profiles[spk_id]["gender_confirmed"] = result["confirmed_gender"]
#     speaker_profiles[spk_id]["gender_confidence"]= result["confidence"]
#     speaker_profiles[spk_id]["gender_reasoning"] = result["reasoning"]
#     speaker_profiles[spk_id]["gender_votes"]     = result["votes"]
#     speaker_profiles[spk_id]["gender_method"]    = "vision+audio"
#     speaker_profiles[spk_id]["screenshots"]      = result["screenshots"]

# # Also update gender on each segment
# for seg in segments:
#     spk = seg["speaker"]
#     if spk in gender_results:
#         seg["gender"]           = gender_results[spk]["confirmed_gender"]
#         seg["gender_confirmed"] = True

# # Save updated transcription JSON
# data["speaker_profiles"] = speaker_profiles
# data["segments"]         = segments
# data["gender_confirmed"] = True
# data["gender_confirmed_at"] = datetime.now().isoformat()

# with open(TRANSCRIPT_JSON, "w", encoding="utf-8") as f:
#     json.dump(data, f, ensure_ascii=False, indent=2)
# print(f"  Updated: {TRANSCRIPT_JSON}")

# # Save updated profiles JSON
# with open(PROFILES_JSON, "w", encoding="utf-8") as f:
#     json.dump(speaker_profiles, f, ensure_ascii=False, indent=2)
# print(f"  Updated: {PROFILES_JSON}")

# # ─────────────────────────────────────────────────────────────
# # SUMMARY
# # ─────────────────────────────────────────────────────────────
# cap.release()

# print(f"\n{'='*60}")
# print("STEP 2b COMPLETE — Gender Confirmation Summary")
# print(f"{'='*60}")
# print(f"{'Speaker':<14} {'Audio':>8} {'Vision':>8} {'Conf':>8} {'Match':>6}")
# print(f"{'─'*50}")
# for spk_id, r in sorted(gender_results.items()):
#     match = "✓" if r["audio_gender"] == r["confirmed_gender"] else "⚠"
#     if r["confirmed_gender"] == "unknown": match = "?"
#     print(f"{spk_id:<14} {r['audio_gender']:>8} "
#           f"{r['confirmed_gender']:>8} {r['confidence']:>8} {match:>6}")

# print(f"\nScreenshots: {SCREENSHOT_DIR}/")
# print("Next → step3_translate.py")
# print("=" * 60)
"""
STEP 2b: Manual Speaker Verification (Screenshots Only)
======================================================
1. Reads speaker segments from transcription_with_speakers.json
2. Randomly picks up to 4 segments per speaker
3. Extracts the best (clearest/brightest) frame from those segments
4. Saves them to work/gender_screenshots/ for you to look at
5. Updates JSONs with "pending" status so you can fill them in manually
"""

import os
import cv2
import json
import random
import numpy as np
from datetime import datetime

print("=" * 60)
print("STEP 2b: Screenshot Extraction (Manual Verification Mode)")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
VIDEO_FILE      = "input/anime.mp4"
TRANSCRIPT_JSON = "work/transcription_with_speakers.json"
PROFILES_JSON   = "work/speaker_profiles.json"
SCREENSHOT_DIR  = "work/gender_screenshots"

MAX_SEGMENTS_PER_SPEAKER = 4 
BLUR_THRESHOLD           = 80.0  
DARK_THRESHOLD           = 40.0  
FRAME_SCAN_STEP_S         = 0.15  

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# LOAD TRANSCRIPTION
# ─────────────────────────────────────────────────────────────
if not os.path.exists(TRANSCRIPT_JSON):
    raise FileNotFoundError(f"Not found: {TRANSCRIPT_JSON}")

with open(TRANSCRIPT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

segments         = data["segments"]
speaker_profiles = data.get("speaker_profiles", {})
speakers         = sorted(set(s["speaker"] for s in segments))

# ─────────────────────────────────────────────────────────────
# VIDEO SETUP
# ─────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(VIDEO_FILE)
FPS = cap.get(cv2.CAP_PROP_FPS)
TOTAL_FRAMES = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# ─────────────────────────────────────────────────────────────
# FRAME QUALITY HELPERS
# ─────────────────────────────────────────────────────────────
def frame_quality(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(np.mean(gray))
    return {"blur": blur_score, "brightness": brightness}

def is_acceptable(frame):
    q = frame_quality(frame)
    return q["blur"] >= BLUR_THRESHOLD and q["brightness"] >= DARK_THRESHOLD

def read_frame_at(cap, timestamp_s):
    frame_idx = int(timestamp_s * FPS)
    frame_idx = max(0, min(frame_idx, TOTAL_FRAMES - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    return frame if ret else None

def best_frame_in_segment(cap, start, end):
    mid = (start + end) / 2.0
    frame = read_frame_at(cap, mid)
    if frame is not None and is_acceptable(frame):
        return frame, mid

    # Scan for better frame if midpoint is bad
    offsets = []
    step = FRAME_SCAN_STEP_S
    t = mid + step
    while t <= end: offsets.append(t); t += step
    t = mid - step
    while t >= start: offsets.append(t); t -= step

    best_f, best_ts, best_score = frame, mid, 0.0
    for ts in offsets:
        f = read_frame_at(cap, ts)
        if f is None: continue
        q = frame_quality(f)
        score = q["blur"] * 0.6 + q["brightness"] * 0.4
        if is_acceptable(f) and score > best_score:
            best_f, best_ts, best_score = f, ts, score
    return best_f, best_ts

# ─────────────────────────────────────────────────────────────
# EXTRACTION LOOP
# ─────────────────────────────────────────────────────────────
for spk_id in speakers:
    print(f"\nProcessing Speaker: {spk_id}")
    spk_dir = os.path.join(SCREENSHOT_DIR, spk_id)
    os.makedirs(spk_dir, exist_ok=True)

    spk_segs = [s for s in segments if s["speaker"] == spk_id]
    random.shuffle(spk_segs)
    sampled = spk_segs[:MAX_SEGMENTS_PER_SPEAKER]

    saved_paths = []
    for seg in sampled:
        frame, ts_used = best_frame_in_segment(cap, seg["start"], seg["end"])
        if frame is not None:
            out_path = os.path.join(spk_dir, f"seg{seg['id']:03d}_{ts_used:.2f}s.png")
            cv2.imwrite(out_path, frame)
            saved_paths.append(out_path)
    
    # Update Profile with Placeholder
    if spk_id not in speaker_profiles:
        speaker_profiles[spk_id] = {}
    
    speaker_profiles[spk_id].update({
        "gender_status": "WAITING_FOR_MANUAL_CHECK",
        "screenshots": saved_paths,
        "manual_verify_url": os.path.abspath(spk_dir)
    })
    print(f"  → Saved {len(saved_paths)} screenshots to {spk_id}/")

# Save updated files
data["speaker_profiles"] = speaker_profiles
with open(TRANSCRIPT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
with open(PROFILES_JSON, "w", encoding="utf-8") as f:
    json.dump(speaker_profiles, f, indent=2)

cap.release()
print("\n" + "="*60)
print("DONE! Check work/gender_screenshots/ to verify genders.")
print("="*60)