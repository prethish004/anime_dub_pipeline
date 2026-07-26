"""
step5_assembly.py
=================
Modular Backend Step 5: Master Timeline Assembly + Background Mixing + Video Muxing
"""

import os
import sys
import json
import torch
import torchaudio
import torchaudio.functional as AF
import numpy as np
import librosa
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MIX_SR = 44100
BG_REDUCE_DB = -2.0
DLG_BOOST_DB = +1.0

def run_step5(options: dict) -> bool:
    print("=" * 60)
    print("STEP 5: Master Assembly & Video Muxing")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    gen_dir = os.path.join(work_dir, "generated_audio")
    out_dir = os.path.join(work_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    video_in = options.get("video_file")
    if not video_in or not os.path.exists(video_in):
        video_in = os.path.join(PROJECT_ROOT, "input", "anime.mp4")

    trans_json = os.path.join(work_dir, "translated_segments_step3.json")
    meta_json = os.path.join(gen_dir, "generation_metadata.json")
    bg_path = os.path.join(work_dir, "background_full.wav")

    if not os.path.exists(trans_json) or not os.path.exists(meta_json):
        print(f"❌ ERROR: Missing required inputs in {work_dir}")
        return False

    with open(trans_json, "r", encoding="utf-8") as f:
        trans_segs = json.load(f).get("segments", [])

    with open(meta_json, "r", encoding="utf-8") as f:
        clips_meta = json.load(f).get("clips", [])

    total_dur = 0.0
    try:
        info = torchaudio.info(str(video_in))
        total_dur = info.num_frames / info.sample_rate
    except Exception:
        total_dur = max(s["end"] for s in trans_segs) + 2.0

    print(f"  Total Video Duration: {total_dur:.2f}s")
    n_samples = int(total_dur * MIX_SR)
    dialogue_canvas = torch.zeros(2, n_samples)

    cm_by_id = {c["segment_id"]: c for c in clips_meta}
    placed = 0

    print("\n🎧 1. Assembling 44.1kHz dialogue track timeline...")
    for seg in trans_segs:
        sid = seg["segment_id"]
        cm = cm_by_id.get(sid)
        if not cm:
            continue

        clip_p = cm.get("files", {}).get("final")
        if not clip_p or not os.path.exists(clip_p):
            continue

        wf, sr = torchaudio.load(clip_p)
        if sr != MIX_SR:
            wf = AF.resample(wf, sr, MIX_SR)

        if wf.shape[0] == 1:
            wf = wf.repeat(2, 1)

        start_s = int(seg["start"] * MIX_SR)
        end_s = min(start_s + wf.shape[1], n_samples)
        if start_s < n_samples and end_s > start_s:
            dialogue_canvas[:, start_s:end_s] += wf[:, :end_s - start_s]
            placed += 1

    peak = dialogue_canvas.abs().max()
    if peak > 0:
        dialogue_canvas = dialogue_canvas * (10 ** (-3.0 / 20.0) / peak)

    dlg_path = os.path.join(out_dir, "dialogue_final.wav")
    torchaudio.save(dlg_path, dialogue_canvas, MIX_SR)

    print("\n🎶 2. Mixing dialogue with background music/SFX...")
    if os.path.exists(bg_path):
        bg_wf, bg_sr = torchaudio.load(bg_path)
        if bg_sr != MIX_SR:
            bg_wf = AF.resample(bg_wf, bg_sr, MIX_SR)
        if bg_wf.shape[0] == 1:
            bg_wf = bg_wf.repeat(2, 1)

        if bg_wf.shape[1] < n_samples:
            repeats = (n_samples // bg_wf.shape[1]) + 1
            bg_wf = bg_wf.repeat(1, repeats)
        bg_wf = bg_wf[:, :n_samples]

        bg_gain = 10 ** (BG_REDUCE_DB / 20.0)
        dlg_gain = 10 ** (DLG_BOOST_DB / 20.0)
        mixed_wf = (bg_wf * bg_gain) + (dialogue_canvas * dlg_gain)
    else:
        mixed_wf = dialogue_canvas

    peak = mixed_wf.abs().max()
    if peak > 0:
        mixed_wf = mixed_wf * (10 ** (-1.0 / 20.0) / peak)

    mix_path = os.path.join(out_dir, "mix_final.wav")
    torchaudio.save(mix_path, mixed_wf.clamp(-1.0, 1.0), MIX_SR)

    print("\n🎬 3. Muxing dubbed audio into output video via FFmpeg...")
    final_video = os.path.join(out_dir, "anime_dubbed_final.mp4")

    import shutil
    import subprocess
    ffmpeg_exe = shutil.which("ffmpeg") or "ffmpeg"

    res = subprocess.run(
        [
            ffmpeg_exe, "-y",
            "-i", str(video_in),
            "-i", mix_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            final_video
        ],
        capture_output=True,
        text=True
    )

    if res.returncode == 0 and os.path.exists(final_video):
        sz_mb = os.path.getsize(final_video) / 1e6
        print(f"\n🎉 SUCCESS! Final dubbed video created: {final_video} ({sz_mb:.1f} MB)")
        return True
    else:
        print(f"❌ FFmpeg muxing failed: {res.stderr[-500:]}")
        return False
