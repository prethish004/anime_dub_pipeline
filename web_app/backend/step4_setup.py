"""
step4_setup.py
==============
Modular Backend Step 4 Setup: Voice Library Scanning & Speaker Config Manager
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def scan_voice_samples() -> dict:
    sample_dir = os.path.join(PROJECT_ROOT, "web_app", "sample_voices")
    if not os.path.exists(sample_dir):
        sample_dir = os.path.join(PROJECT_ROOT, "sample_voices")

    catalogue = {"female": [], "male": [], "tamil": [], "all": []}
    if not os.path.exists(sample_dir):
        return catalogue

    for category in ["female", "male", "tamil"]:
        cat_dir = os.path.join(sample_dir, category)
        if os.path.exists(cat_dir):
            for fname in os.listdir(cat_dir):
                if fname.lower().endswith((".wav", ".mp3", ".flac", ".m4a", ".ogg")):
                    full_p = os.path.join(cat_dir, fname)
                    rel_p = os.path.relpath(full_p, str(PROJECT_ROOT)).replace("\\", "/")
                    item = {"name": fname, "path": rel_p, "category": category}
                    catalogue[category].append(item)
                    catalogue["all"].append(item)

    return catalogue

def run_step4_setup(options: dict) -> bool:
    print("=" * 60)
    print("STEP 4 Setup: Speaker Voice Mapping")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    trans_json = os.path.join(work_dir, "translated_segments_step3.json")
    profiles_json = os.path.join(work_dir, "speaker_profiles.json")
    config_json = os.path.join(work_dir, "speaker_config.json")

    speakers = []
    if os.path.exists(profiles_json):
        with open(profiles_json, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            speakers = list(profiles.keys())
    elif os.path.exists(trans_json):
        with open(trans_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            speakers = list(set(s["speaker"] for s in data.get("segments", [])))

    if not speakers:
        speakers = ["SPEAKER_00"]

    catalogue = scan_voice_samples()
    print(f"  Scanned voice catalogue: {len(catalogue['all'])} voice samples found.")

    custom_mappings = options.get("speaker_mappings", {})

    speaker_configs = {}
    for i, spk in enumerate(speakers):
        cfg = custom_mappings.get(spk, {})

        voice_file = cfg.get("voice_file")
        if not voice_file:
            if catalogue["all"]:
                voice_file = catalogue["all"][i % len(catalogue["all"])]["path"]
            else:
                voice_file = "web_app/sample_voices/female/Amber.mp3"

        speaker_configs[spk] = {
            "voice_file": voice_file,
            "age_category": cfg.get("age_category", "adult"),
            "tone_category": cfg.get("tone_category", "neutral"),
            "knnvc_ref": cfg.get("knnvc_ref", None),
        }
        print(f"  ✓ {spk:<12} -> {voice_file}")

    global_toggles = {
        "emotion_dsp": options.get("emotion_dsp", True),
        "age_transform": options.get("age_transform", True),
        "knnvc_transform": options.get("knnvc_transform", False),
    }

    full_config = {
        "speaker_configs": speaker_configs,
        "global_toggles": global_toggles
    }

    with open(config_json, "w", encoding="utf-8") as f:
        json.dump(full_config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Step 4 Setup Complete! Workspace: {work_dir}")
    return True
