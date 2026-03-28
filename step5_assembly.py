# """
# STEP 5: Assembly — Timeline + Mix + Compare + Mux
# ==================================================
# Reads:
#   work/generated_audio/generation_metadata.json
#   work/translated_segments_step3.json
#   work/background_full.wav
#   input/anime.mp4

# Produces 4 audio tracks × 4 clip types = up to 16 outputs:

# Clip types (one track per type):
#   aligned  — timing-matched, no emotion, no age
#   emotion  — timing + emotion fine-tuning
#   age      — timing + emotion + age/type transform
#   final    — full pipeline output (recommended)

# Per clip type, 4 outputs:
#   1. dialogue_<type>.wav        — voices only, no background
#   2. mix_<type>.wav             — voices + background noise
#   3. comparison_<type>.png      — waveform: EN generated vs JP original
#   4. anime_dubbed_<type>.mp4    — final video with that audio track

# All outputs land in:  work/output/
# """

# import os
# import json
# import subprocess
# from datetime import datetime
# from pathlib import Path

# import numpy as np
# import librosa
# import soundfile as sf
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# from pydub import AudioSegment

# # ─────────────────────────────────────────────────────────────
# # CONFIG
# # ─────────────────────────────────────────────────────────────
# VIDEO_IN      = "input/anime.mp4"
# WORK_DIR      = "work"
# GEN_DIR       = os.path.join(WORK_DIR, "generated_audio")
# BG_PATH       = os.path.join(WORK_DIR, "background_full.wav")
# TRANS_JSON    = os.path.join(WORK_DIR, "translated_segments_step3.json")
# META_JSON     = os.path.join(GEN_DIR,  "generation_metadata.json")
# CROPPED_DIR   = os.path.join(WORK_DIR, "cropped_segments")
# OUT_DIR       = os.path.join(WORK_DIR, "output")

# # Clip types to build tracks for
# # Each maps to the file key in generation_metadata clips[].files
# CLIP_TYPES = ["aligned", "emotion", "age", "final"]

# # Mix levels
# BG_REDUCE_DB  = -6    # lower background this many dB
# DLG_BOOST_DB  = +3    # boost dialogue this many dB

# os.makedirs(OUT_DIR, exist_ok=True)

# # ─────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────
# def load_json(path):
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def ms(seconds):
#     return int(seconds * 1000)


# def get_video_duration_s(video_path):
#     """Use ffprobe to get video duration in seconds."""
#     result = subprocess.run([
#         "ffprobe", "-v", "error",
#         "-show_entries", "format=duration",
#         "-of", "default=noprint_wrappers=1:nokey=1",
#         video_path
#     ], capture_output=True, text=True)
#     try:
#         return float(result.stdout.strip())
#     except ValueError:
#         return None


# def safe_clip_path(clip_meta, clip_type):
#     """
#     Return the file path for a given clip type.
#     Falls back to 'final' if the requested type file doesn't exist.
#     """
#     files = clip_meta.get("files", {})
#     path  = files.get(clip_type)
#     if path and os.path.exists(path):
#         return path
#     # Fallback to final
#     fallback = files.get("final")
#     if fallback and os.path.exists(fallback):
#         return fallback
#     return None


# # ─────────────────────────────────────────────────────────────
# # OUTPUT 1 — BUILD DIALOGUE TRACK (voices only, no background)
# # ─────────────────────────────────────────────────────────────
# def build_dialogue_track(clips_meta, trans_segments, clip_type, total_dur_s):
#     """
#     Place each generated clip at its original Japanese start time.
#     Returns path to the exported dialogue WAV.
#     """
#     print(f"\n── Building dialogue track [{clip_type}] ──")

#     dialogue  = AudioSegment.silent(duration=ms(total_dur_s))
#     placed    = 0
#     missing   = 0

#     # Build lookup: segment_id → clip meta
#     meta_by_id = {c["segment_id"]: c for c in clips_meta}

#     for seg in trans_segments:
#         seg_id   = seg["segment_id"]
#         start_ms = ms(seg["start"])
#         clip_m   = meta_by_id.get(seg_id)

#         if clip_m is None:
#             print(f"  ⚠️  No metadata for seg {seg_id:03d} — skipping")
#             missing += 1
#             continue

#         audio_path = safe_clip_path(clip_m, clip_type)
#         if not audio_path:
#             print(f"  ⚠️  Missing audio for seg {seg_id:03d} [{clip_type}] — skipping")
#             missing += 1
#             continue

#         clip     = AudioSegment.from_file(audio_path)
#         clip_dur = len(clip) / 1000.0
#         target   = seg["duration"]

#         # Trim to target if slightly over (never pad here — pad was done in step4)
#         if clip_dur > target + 0.05:
#             clip = clip[:ms(target)]

#         dialogue = dialogue.overlay(clip, position=start_ms)
#         placed  += 1
#         print(f"  [{seg_id:03d}] {seg['start']:.2f}s  {clip_dur:.3f}s  {clip_type}")

#     out_path = os.path.join(OUT_DIR, f"dialogue_{clip_type}.wav")
#     dialogue.export(out_path, format="wav")
#     print(f"  Placed {placed}/{placed+missing} clips → {out_path}")
#     return out_path


# # ─────────────────────────────────────────────────────────────
# # OUTPUT 2 — MIX WITH BACKGROUND
# # ─────────────────────────────────────────────────────────────
# def mix_with_background(dialogue_path, clip_type):
#     """
#     Overlay background noise under the dialogue track.
#     Returns path to mixed WAV.
#     """
#     print(f"\n── Mixing with background [{clip_type}] ──")

#     dlg = AudioSegment.from_file(dialogue_path)

#     if os.path.exists(BG_PATH):
#         bg = AudioSegment.from_file(BG_PATH)

#         # Match background length to dialogue
#         if len(bg) < len(dlg):
#             # Loop background to fill
#             while len(bg) < len(dlg):
#                 bg = bg + bg
#         bg = bg[:len(dlg)]

#         # Adjust levels
#         bg  = bg  + BG_REDUCE_DB
#         dlg = dlg + DLG_BOOST_DB

#         mixed = bg.overlay(dlg)
#         print(f"  Background: {BG_PATH} — applied {BG_REDUCE_DB}dB reduction")
#     else:
#         print(f"  ⚠️  background_full.wav not found — dialogue only")
#         mixed = dlg

#     out_path = os.path.join(OUT_DIR, f"mix_{clip_type}.wav")
#     mixed.export(out_path, format="wav")
#     print(f"  Mixed → {out_path}")
#     return out_path


# # ─────────────────────────────────────────────────────────────
# # OUTPUT 3 — FULL WAVEFORM COMPARISON PLOT
# # ─────────────────────────────────────────────────────────────
# def build_comparison_plot(clips_meta, trans_segments, clip_type, total_dur_s):
#     """
#     Build a full-timeline waveform comparison:
#       TOP    — original Japanese audio (reconstructed from cropped segments)
#       BOTTOM — generated English dialogue track for this clip_type

#     Saves a wide PNG covering the full episode timeline.
#     """
#     print(f"\n── Building waveform comparison [{clip_type}] ──")

#     SR       = 16000
#     n_samps  = int(total_dur_s * SR)
#     jp_full  = np.zeros(n_samps, dtype=np.float32)
#     en_full  = np.zeros(n_samps, dtype=np.float32)

#     meta_by_id = {c["segment_id"]: c for c in clips_meta}

#     for seg in trans_segments:
#         seg_id = seg["segment_id"]
#         start  = seg["start"]
#         dur    = seg["duration"]
#         si     = int(start * SR)

#         # JP: load cropped segment
#         jp_crop = os.path.join(CROPPED_DIR, f"segment_{seg_id:03d}.wav")
#         if os.path.exists(jp_crop):
#             y_jp, _ = librosa.load(jp_crop, sr=SR, mono=True,
#                                    duration=dur + 0.1)
#             end_i = min(si + len(y_jp), n_samps)
#             jp_full[si:end_i] = y_jp[:end_i - si]

#         # EN: load generated clip
#         clip_m = meta_by_id.get(seg_id)
#         if clip_m:
#             en_path = safe_clip_path(clip_m, clip_type)
#             if en_path and os.path.exists(en_path):
#                 y_en, _ = librosa.load(en_path, sr=SR, mono=True,
#                                        duration=dur + 0.1)
#                 end_i = min(si + len(y_en), n_samps)
#                 en_full[si:end_i] = y_en[:end_i - si]

#     # Plot
#     t = np.linspace(0, total_dur_s, n_samps)

#     fig_w = max(20, int(total_dur_s / 5))   # wider for longer episodes
#     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_w, 5), sharex=True)
#     fig.patch.set_facecolor("#1a1a2e")

#     def style(ax, label, color):
#         ax.set_facecolor("#16213e")
#         ax.plot(t, ax.get_lines()[0].get_ydata() if ax.get_lines() else [],
#                 color=color, linewidth=0.4, alpha=0.85)
#         ax.set_ylabel(label, color="#aaa", fontsize=9)
#         ax.tick_params(colors="#aaa", labelsize=7)
#         ax.spines[:].set_color("#444")

#     ax1.plot(t, jp_full, color="#5DCAA5", linewidth=0.4, alpha=0.85)
#     ax1.set_facecolor("#16213e")
#     ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
#     ax1.tick_params(colors="#aaa", labelsize=7)
#     ax1.spines[:].set_color("#444")
#     ax1.set_title(
#         f"Full timeline comparison — {clip_type.upper()} track  "
#         f"({total_dur_s:.1f}s)",
#         color="#ddd", fontsize=11, pad=6
#     )

#     ax2.plot(t, en_full, color="#7F77DD", linewidth=0.4, alpha=0.85)
#     ax2.set_facecolor("#16213e")
#     ax2.set_ylabel(f"EN [{clip_type}]", color="#aaa", fontsize=9)
#     ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)
#     ax2.tick_params(colors="#aaa", labelsize=7)
#     ax2.spines[:].set_color("#444")

#     # Mark each segment boundary
#     for seg in trans_segments:
#         for ax in (ax1, ax2):
#             ax.axvline(x=seg["start"], color="#E24B4A",
#                        linewidth=0.4, alpha=0.35)

#     plt.tight_layout(pad=1.5)
#     out_path = os.path.join(OUT_DIR, f"comparison_{clip_type}.png")
#     plt.savefig(out_path, dpi=120, bbox_inches="tight",
#                 facecolor=fig.get_facecolor())
#     plt.close(fig)
#     print(f"  Comparison plot → {out_path}")
#     return out_path


# # ─────────────────────────────────────────────────────────────
# # OUTPUT 4 — MUX INTO VIDEO
# # ─────────────────────────────────────────────────────────────
# def mux_into_video(audio_path, clip_type):
#     """
#     Replace video audio with the given audio track using ffmpeg.
#     No video re-encode — just copy the video stream.
#     """
#     print(f"\n── Muxing video [{clip_type}] ──")

#     if not os.path.exists(VIDEO_IN):
#         print(f"  ⚠️  Video not found: {VIDEO_IN} — skipping mux")
#         return None

#     out_path = os.path.join(OUT_DIR, f"anime_dubbed_{clip_type}.mp4")
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", VIDEO_IN,
#         "-i", audio_path,
#         "-map", "0:v:0",
#         "-map", "1:a:0",
#         "-c:v", "copy",
#         "-c:a", "aac",
#         "-b:a", "192k",
#         "-shortest",
#         out_path,
#     ]

#     result = subprocess.run(cmd, capture_output=True, text=True)
#     if result.returncode != 0:
#         print(f"  ⚠️  ffmpeg error:\n{result.stderr[-500:]}")
#         return None

#     print(f"  Video → {out_path}")
#     return out_path


# # ─────────────────────────────────────────────────────────────
# # SUMMARY REPORT
# # ─────────────────────────────────────────────────────────────
# def print_summary(results, start_time):
#     elapsed = (datetime.now() - start_time).total_seconds()

#     print("\n" + "=" * 60)
#     print("STEP 5 COMPLETE")
#     print(f"Time: {elapsed:.1f}s")
#     print("=" * 60)

#     print(f"\n{'Type':<10} {'Dialogue':30} {'Mix':30}")
#     print("─" * 72)
#     for clip_type, r in results.items():
#         dlg = os.path.basename(r.get("dialogue", "—"))
#         mix = os.path.basename(r.get("mix",      "—"))
#         print(f"{clip_type:<10} {dlg:<30} {mix:<30}")

#     print(f"\n{'Type':<10} {'Comparison plot':40} {'Video':30}")
#     print("─" * 82)
#     for clip_type, r in results.items():
#         cmp = os.path.basename(r.get("comparison", "—"))
#         vid = os.path.basename(r.get("video",      "—"))
#         print(f"{clip_type:<10} {cmp:<40} {vid:<30}")

#     print(f"\nAll outputs in: {OUT_DIR}/")
#     print("\nQuick file list:")
#     for f in sorted(Path(OUT_DIR).iterdir()):
#         size_mb = f.stat().st_size / 1_000_000
#         print(f"  {f.name:<45} {size_mb:>6.1f} MB")


# # ─────────────────────────────────────────────────────────────
# # MAIN
# # ─────────────────────────────────────────────────────────────
# def main():
#     start_time = datetime.now()

#     print("=" * 60)
#     print("STEP 5: Assembly — Timeline + Mix + Compare + Mux")
#     print("=" * 60)

#     # ── Load data ─────────────────────────────────────────────
#     print(f"\nLoading metadata...")
#     trans_data  = load_json(TRANS_JSON)
#     meta_data   = load_json(META_JSON)
#     trans_segs  = trans_data["segments"]
#     clips_meta  = meta_data["clips"]

#     print(f"  Segments     : {len(trans_segs)}")
#     print(f"  Generated clips: {len(clips_meta)}")

#     # ── Determine total duration ───────────────────────────────
#     video_dur = get_video_duration_s(VIDEO_IN)
#     if video_dur:
#         total_dur = video_dur
#         print(f"  Video duration : {total_dur:.2f}s")
#     else:
#         total_dur = max(s["end"] for s in trans_segs) + 2.0
#         print(f"  Total duration (from segments): {total_dur:.2f}s")

#     # ── Filter available clip types ────────────────────────────
#     # Only process types where at least one file actually exists
#     available_types = []
#     for ct in CLIP_TYPES:
#         exists = any(
#             safe_clip_path(c, ct) is not None for c in clips_meta
#         )
#         if exists:
#             available_types.append(ct)
#         else:
#             print(f"  Skipping '{ct}' — no files found")

#     print(f"\n  Processing clip types: {available_types}")

#     # ── Process each clip type ─────────────────────────────────
#     results = {}

#     for clip_type in available_types:
#         print(f"\n{'═'*60}")
#         print(f"  CLIP TYPE: {clip_type.upper()}")
#         print(f"{'═'*60}")

#         r = {}

#         # Output 1: dialogue track (voices only)
#         r["dialogue"] = build_dialogue_track(
#             clips_meta, trans_segs, clip_type, total_dur
#         )

#         # Output 2: mix with background
#         r["mix"] = mix_with_background(r["dialogue"], clip_type)

#         # Output 3: full waveform comparison plot
#         r["comparison"] = build_comparison_plot(
#             clips_meta, trans_segs, clip_type, total_dur
#         )

#         # Output 4: dubbed video (using the mix track)
#         r["video"] = mux_into_video(r["mix"], clip_type)

#         results[clip_type] = r

#     # ── Summary ───────────────────────────────────────────────
#     print_summary(results, start_time)


# if __name__ == "__main__":
#     main()
"""
STEP 5: Assembly — Timeline + Mix + Compare + Mux
==================================================
Key fixes:
  1. JP audio extracted directly from vocals.wav using start/end
     times from transcription JSON — fixes flat/silent JP waveform
  2. EN clips placed at exact Japanese start position on the timeline
  3. Per-segment AND full-timeline comparison plots
  4. 4 outputs per clip type: dialogue / mix / comparison / video

Inputs:
  input/anime.mp4
  work/stems/htdemucs_6s/raw_audio/vocals.wav
  work/background_full.wav
  work/translated_segments_step3.json
  work/generated_audio/generation_metadata.json

Outputs (work/output/):
  dialogue_<type>.wav
  mix_<type>.wav
  comparison_<type>.png
  segments/<type>/comparison_NNN.png
  anime_dubbed_<type>.mp4
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pydub import AudioSegment

# ─────────────────────────────────────────────────────────────
# CONFIG  — adjust paths if your folder structure differs
# ─────────────────────────────────────────────────────────────
VIDEO_IN       = "input/anime.mp4"
WORK_DIR       = "work"
GEN_DIR        = os.path.join(WORK_DIR, "generated_audio")
BG_PATH        = os.path.join(WORK_DIR, "background_full.wav")
JP_VOCALS_PATH = os.path.join(WORK_DIR, "stems", "htdemucs_6s", "raw_audio", "vocals.wav")
TRANS_JSON     = os.path.join(WORK_DIR, "translated_segments_step3.json")
META_JSON      = os.path.join(GEN_DIR,  "generation_metadata.json")
OUT_DIR        = os.path.join(WORK_DIR, "output")

CLIP_TYPES     = ["aligned", "emotion", "age", "final"]
PLOT_SR        = 16000       # sample rate used for all waveform plots
# BG_REDUCE_DB   = -6
# DLG_BOOST_DB   = +3
BG_REDUCE_DB  = -2    # background almost full volume
DLG_BOOST_DB  = +1    # dialogue barely boosted
os.makedirs(OUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ms(s):
    return int(s * 1000)


def get_video_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def safe_clip_path(clip_meta, clip_type):
    files = clip_meta.get("files", {})
    p = files.get(clip_type)
    if p and os.path.exists(p):
        return p
    fb = files.get("final")
    if fb and os.path.exists(fb):
        return fb
    return None


# ─────────────────────────────────────────────────────────────
# LOAD JP VOCALS
# ─────────────────────────────────────────────────────────────
def load_jp_vocals():
    """
    Load vocals.wav as mono float32 at PLOT_SR.
    librosa.load with mono=True correctly averages stereo channels —
    avoids the silent-track bug caused by phase cancellation when
    only channel 0 is taken from an out-of-phase stereo file.
    """
    if not os.path.exists(JP_VOCALS_PATH):
        print(f"  WARNING: JP vocals not found: {JP_VOCALS_PATH}")
        return None, None

    y, sr = librosa.load(JP_VOCALS_PATH, sr=PLOT_SR, mono=True)
    rms   = float(np.sqrt(np.mean(y ** 2)))

    if rms < 1e-5:
        print(f"  WARNING: JP vocals loaded but RMS={rms:.8f} — signal appears silent")
        print(f"           Verify the file has audio: {JP_VOCALS_PATH}")
    else:
        dur = len(y) / sr
        print(f"  JP vocals: {dur:.1f}s  RMS={rms:.5f}  SR={sr}")

    return y, sr


def extract_segment(jp_audio, jp_sr, start_s, end_s):
    """Slice jp_audio numpy array from start_s to end_s seconds."""
    si = max(0, int(start_s * jp_sr))
    ei = min(len(jp_audio), int(end_s * jp_sr))
    return jp_audio[si:ei]


# ─────────────────────────────────────────────────────────────
# OUTPUT 1 — DIALOGUE TRACK
# ─────────────────────────────────────────────────────────────
def build_dialogue_track(clips_meta, trans_segs, clip_type, total_dur):
    print(f"\n  [dialogue] building track: {clip_type}")

    canvas     = AudioSegment.silent(duration=ms(total_dur))
    meta_by_id = {c["segment_id"]: c for c in clips_meta}
    placed = missing = 0

    for seg in trans_segs:
        sid  = seg["segment_id"]
        cm   = meta_by_id.get(sid)
        if cm is None:
            missing += 1
            continue

        path = safe_clip_path(cm, clip_type)
        if not path:
            print(f"    ⚠️  seg {sid:03d} [{clip_type}] not found")
            missing += 1
            continue

        clip       = AudioSegment.from_file(path)
        target_ms  = ms(seg["duration"])
        start_ms   = ms(seg["start"])

        # Trim to segment slot if clip is longer
        if len(clip) > target_ms + 50:
            clip = clip[:target_ms]

        # Place at original Japanese start time
        canvas = canvas.overlay(clip, position=start_ms)
        placed += 1

    out = os.path.join(OUT_DIR, f"dialogue_{clip_type}.wav")
    canvas.export(out, format="wav")
    print(f"    {placed} placed, {missing} missing → {out}")
    return out


# ─────────────────────────────────────────────────────────────
# OUTPUT 2 — MIX WITH BACKGROUND
# ─────────────────────────────────────────────────────────────
def mix_with_background(dialogue_path, clip_type):
    print(f"\n  [mix] {clip_type}")

    dlg = AudioSegment.from_file(dialogue_path)

    if os.path.exists(BG_PATH):
        bg = AudioSegment.from_file(BG_PATH)
        while len(bg) < len(dlg):
            bg = bg + bg
        bg = bg[:len(dlg)]
        mixed = (bg + BG_REDUCE_DB).overlay(dlg + DLG_BOOST_DB)
        print(f"    BG {BG_REDUCE_DB}dB + DLG +{DLG_BOOST_DB}dB")
    else:
        print("    ⚠️  background_full.wav not found — dialogue only")
        mixed = dlg

    out = os.path.join(OUT_DIR, f"mix_{clip_type}.wav")
    mixed.export(out, format="wav")
    print(f"    → {out}")
    return out


# ─────────────────────────────────────────────────────────────
# OUTPUT 3a — FULL TIMELINE COMPARISON PLOT
# ─────────────────────────────────────────────────────────────
def build_full_comparison(jp_audio, jp_sr, clips_meta, trans_segs, clip_type, total_dur):
    """
    Full-episode waveform comparison.
    JP is reconstructed by placing each extracted segment at its
    correct position on a zero-padded canvas — same approach as
    the EN track — so both plots are on identical time axes.
    """
    print(f"\n  [comparison full] {clip_type}")

    sr      = PLOT_SR
    n       = int(total_dur * sr)
    jp_full = np.zeros(n, dtype=np.float32)
    en_full = np.zeros(n, dtype=np.float32)

    meta_by_id = {c["segment_id"]: c for c in clips_meta}

    for seg in trans_segs:
        sid   = seg["segment_id"]
        start = seg["start"]
        end   = seg["end"]
        si    = int(start * sr)

        # JP — slice from vocals array
        if jp_audio is not None:
            y_jp  = extract_segment(jp_audio, jp_sr, start, end)
            ei    = min(si + len(y_jp), n)
            if ei > si:
                jp_full[si:ei] = y_jp[:ei - si]

        # EN — load generated clip
        cm = meta_by_id.get(sid)
        if cm:
            p = safe_clip_path(cm, clip_type)
            if p:
                y_en, _ = librosa.load(p, sr=sr, mono=True)
                ei = min(si + len(y_en), n)
                if ei > si:
                    en_full[si:ei] = y_en[:ei - si]

    jp_rms = float(np.sqrt(np.mean(jp_full ** 2)))
    en_rms = float(np.sqrt(np.mean(en_full ** 2)))
    print(f"    JP RMS={jp_rms:.5f}  EN RMS={en_rms:.5f}")

    t = np.linspace(0, total_dur, n)
    fig_w = max(22, int(total_dur / 4))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_w, 5), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")

    def draw(ax, y, label, color):
        ax.set_facecolor("#16213e")
        ax.plot(t, y, color=color, linewidth=0.35, alpha=0.9)
        ax.set_ylabel(label, color="#aaa", fontsize=9)
        ax.tick_params(colors="#aaa", labelsize=7)
        ax.spines[:].set_color("#444")
        pk = max(np.max(np.abs(y)), 1e-4)
        ax.set_ylim(-pk * 1.2, pk * 1.2)

    draw(ax1, jp_full, "JP original", "#5DCAA5")
    ax1.set_title(
        f"Full timeline — {clip_type.upper()}   "
        f"JP RMS={jp_rms:.4f}  EN RMS={en_rms:.4f}  ({total_dur:.1f}s)",
        color="#ddd", fontsize=10, pad=5
    )
    draw(ax2, en_full, f"EN [{clip_type}]", "#7F77DD")
    ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

    # Segment boundary markers
    for seg in trans_segs:
        for ax in (ax1, ax2):
            ax.axvline(x=seg["start"], color="#E24B4A",
                       linewidth=0.4, alpha=0.25, zorder=0)

    plt.tight_layout(pad=1.5)
    out = os.path.join(OUT_DIR, f"comparison_{clip_type}.png")
    plt.savefig(out, dpi=130, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    print(f"    → {out}")
    return out


# ─────────────────────────────────────────────────────────────
# OUTPUT 3b — PER-SEGMENT COMPARISON PLOTS
# ─────────────────────────────────────────────────────────────
def build_per_segment_comparisons(jp_audio, jp_sr, clips_meta, trans_segs, clip_type):
    """
    One zoomed plot per segment — JP on top, EN below.
    Both scaled to their actual amplitude so neither looks flat.
    """
    seg_dir    = os.path.join(OUT_DIR, "segments", clip_type)
    os.makedirs(seg_dir, exist_ok=True)
    meta_by_id = {c["segment_id"]: c for c in clips_meta}
    sr         = PLOT_SR
    saved      = 0

    for seg in trans_segs:
        sid   = seg["segment_id"]
        start = seg["start"]
        end   = seg["end"]
        dur   = seg["duration"]

        # JP slice
        y_jp = None
        if jp_audio is not None:
            y_jp = extract_segment(jp_audio, jp_sr, start, end)

        # EN clip
        y_en = None
        cm   = meta_by_id.get(sid)
        if cm:
            p = safe_clip_path(cm, clip_type)
            if p and os.path.exists(p):
                y_en, _ = librosa.load(p, sr=sr, mono=True)

        # Skip if both empty
        if (y_jp is None or len(y_jp) == 0) and (y_en is None or len(y_en) == 0):
            continue

        jp_rms = float(np.sqrt(np.mean(y_jp ** 2))) if y_jp is not None and len(y_jp) > 0 else 0
        en_rms = float(np.sqrt(np.mean(y_en ** 2))) if y_en is not None and len(y_en) > 0 else 0

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 3.5))
        fig.patch.set_facecolor("#1a1a2e")

        def plot_seg(ax, y, label, color):
            ax.set_facecolor("#16213e")
            ax.tick_params(colors="#aaa", labelsize=7)
            ax.spines[:].set_color("#444")
            ax.set_ylabel(label, color="#aaa", fontsize=8)
            if y is not None and len(y) > 0:
                t = np.linspace(0, len(y) / sr, len(y))
                ax.plot(t, y, color=color, linewidth=0.8, alpha=0.9)
                pk = max(np.max(np.abs(y)), 1e-4)
                ax.set_ylim(-pk * 1.3, pk * 1.3)   # scale to signal, not fixed ±1
                ax.axvline(x=dur, color="#E24B4A", linewidth=1.0,
                           linestyle="--", alpha=0.7, label=f"target {dur:.3f}s")
                ax.legend(fontsize=7, facecolor="#222", labelcolor="#ccc",
                          edgecolor="#444", loc="upper right")
            else:
                ax.text(0.5, 0.5, "no audio",
                        transform=ax.transAxes, ha="center",
                        color="#E24B4A", fontsize=9)

        jp_text  = seg.get("text",    "")
        en_text  = seg.get("english", cm.get("text", "") if cm else "")
        plot_seg(ax1, y_jp, "JP original", "#5DCAA5")
        ax1.set_title(
            f"Seg {sid:03d} | {seg.get('speaker','?')} | "
            f"\"{jp_text}\" → \"{en_text[:35]}\"  "
            f"JP={jp_rms:.4f}  EN={en_rms:.4f}",
            color="#ddd", fontsize=8, pad=4
        )
        plot_seg(ax2, y_en, f"EN [{clip_type}]", "#7F77DD")
        ax2.set_xlabel("Time (s)", color="#aaa", fontsize=8)

        plt.tight_layout(pad=1.2)
        out = os.path.join(seg_dir, f"comparison_{sid:03d}.png")
        plt.savefig(out, dpi=110, bbox_inches="tight", facecolor="#1a1a2e")
        plt.close(fig)
        saved += 1

    print(f"    Per-segment [{clip_type}]: {saved} plots → {seg_dir}/")
    return seg_dir


# ─────────────────────────────────────────────────────────────
# OUTPUT 4 — MUX VIDEO
# ─────────────────────────────────────────────────────────────
def mux_video(audio_path, clip_type):
    print(f"\n  [video] {clip_type}")
    if not os.path.exists(VIDEO_IN):
        print(f"    ⚠️  {VIDEO_IN} not found")
        return None
    out = os.path.join(OUT_DIR, f"anime_dubbed_{clip_type}.mp4")
    r = subprocess.run([
        "ffmpeg", "-y",
        "-i", VIDEO_IN, "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", out
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    ⚠️  ffmpeg: {r.stderr[-300:]}")
        return None
    print(f"    → {out}")
    return out


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    t0 = datetime.now()
    print("=" * 65)
    print("STEP 5: Assembly")
    print("=" * 65)

    trans_data = load_json(TRANS_JSON)
    meta_data  = load_json(META_JSON)
    trans_segs = trans_data["segments"]
    clips_meta = meta_data["clips"]

    # Merge english text into seg dicts for plot labels
    cm_by_id = {c["segment_id"]: c for c in clips_meta}
    for seg in trans_segs:
        cm = cm_by_id.get(seg["segment_id"])
        if cm:
            seg["english"] = cm.get("text", "")

    print(f"\n  Segments        : {len(trans_segs)}")
    print(f"  Generated clips : {len(clips_meta)}")

    vid_dur   = get_video_duration(VIDEO_IN)
    total_dur = vid_dur if vid_dur else max(s["end"] for s in trans_segs) + 2.0
    print(f"  Total duration  : {total_dur:.2f}s")

    # Load JP vocals once — reused for all clip types
    print(f"\n  Loading JP vocals...")
    jp_audio, jp_sr = load_jp_vocals()

    # Determine which clip types have files
    available = [
        ct for ct in CLIP_TYPES
        if any(safe_clip_path(c, ct) is not None for c in clips_meta)
    ]
    print(f"  Available types : {available}")

    results = {}
    for ct in available:
        print(f"\n{'═'*65}")
        print(f"  PROCESSING: {ct.upper()}")
        print(f"{'═'*65}")

        r = {}
        r["dialogue"]        = build_dialogue_track(clips_meta, trans_segs, ct, total_dur)
        r["mix"]             = mix_with_background(r["dialogue"], ct)
        r["comparison_full"] = build_full_comparison(jp_audio, jp_sr, clips_meta, trans_segs, ct, total_dur)
        r["comparison_segs"] = build_per_segment_comparisons(jp_audio, jp_sr, clips_meta, trans_segs, ct)
        r["video"]           = mux_video(r["mix"], ct)
        results[ct] = r

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"\n{'='*65}")
    print(f"STEP 5 COMPLETE  ({elapsed:.1f}s)")
    print(f"{'='*65}")
    for ct, r in results.items():
        print(f"\n  [{ct.upper()}]")
        for k, v in r.items():
            if v:
                sz = os.path.getsize(v) / 1e6 if os.path.isfile(v) else 0
                print(f"    {k:<20} {os.path.basename(v):<42} {sz:.1f}MB")
    print(f"\n  All outputs: {OUT_DIR}/")


if __name__ == "__main__":
    main()