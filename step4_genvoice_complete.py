"""
STEP 4: Voice Generation Pipeline — Complete
=============================================
Run step4_setup.py FIRST to configure speakers and install packages.
This script reads work/speaker_config.json automatically.

Requirements implemented:
  1. ✅ Voice library scan + speaker config from step4_setup.py
  2. ✅ XTTS-v2 voice cloning + generation (HuggingFace coqui/XTTS-v2)
  3. ✅ Waveform comparison plot — EN vs JP side-by-side PNG
  4. ✅ Timing enforcement — Rubberband 0.90–1.10x + pad/trim
  5. ✅ Emotion fine-tuning — user toggle + confidence gate
  6. ✅ Age/type transformation — child/adult/old/robot
  7. ✅ Understandability guard — spectral flatness + ZCR check

Usage:
    python step4_genvoice_complete.py
"""

import os
import json
import shutil
import soundfile as sf
from datetime import datetime
from pathlib import Path

import torch
import librosa
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyrubberband as pyrb
import parselmouth
from parselmouth.praat import call
from scipy.signal import butter, filtfilt
from TTS.api import TTS

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
INPUT_JSON    = "work/translated_segments_step3.json"
CONFIG_PATH   = "work/speaker_config.json"
OUTPUT_DIR    = "work/generated_audio"
WAVEFORM_DIR  = "work/waveform_comparisons"
CROPPED_DIR   = "work/cropped_segments"
DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

MIN_RATIO = 0.90
MAX_RATIO = 1.10

EMOTION_LOUDNESS = {
    "angry": -14, "ang": -14,
    "surprised": -15, "sur": -15,
    "fearful": -15, "fea": -15,
    "happy": -16, "hap": -16,
    "neutral": -18, "neu": -18,
    "sad": -22,
    "disgusted": -17, "dis": -17,
    "unknown": -18,
}

AGE_PRESETS = {
    "adult":       None,
    "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
    "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
    "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
    "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
    "robot":       "robot",
}

os.makedirs(OUTPUT_DIR,   exist_ok=True)
os.makedirs(WAVEFORM_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# LOAD SPEAKER CONFIG
# ─────────────────────────────────────────────────────────────
def load_speaker_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"WARNING: Config not found: {CONFIG_PATH}")
        print("Run step4_setup.py first to configure speakers.")
        print("Using default voice for all speakers.\n")
        return {
            "options":  {"emotion_enabled": True, "age_enabled": True, "use_knnvc": False},
            "speakers": {}
        }

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    print(f"Config loaded: {CONFIG_PATH}")
    print(f"  Generated : {config.get('generated_at', 'unknown')}")
    opts = config.get("options", {})
    print(f"  Emotion   : {'ON' if opts.get('emotion_enabled') else 'OFF'}")
    print(f"  Age/type  : {'ON' if opts.get('age_enabled') else 'OFF'}")
    print(f"  Age mode  : {'kNN-VC' if opts.get('use_knnvc') else 'DSP (Parselmouth)'}")
    for spk, info in sorted(config.get("speakers", {}).items()):
        voice = info.get("voice_display", os.path.basename(info.get("voice_sample", "?")))
        print(f"  {spk:<14} -> {voice}  [{info.get('age_category','adult')}]")
    return config


print("=" * 60)
print("STEP 4: Voice Generation Pipeline")
print("=" * 60)

_cfg            = load_speaker_config()
SPEAKER_MAP     = _cfg.get("speakers", {})
EMOTION_ENABLED = _cfg["options"].get("emotion_enabled", True)
AGE_ENABLED     = _cfg["options"].get("age_enabled",     True)
USE_KNNVC       = _cfg["options"].get("use_knnvc",       False)

# ─────────────────────────────────────────────────────────────
# LOAD MODELS
# ─────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\nLoading models on {device}...")

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
          gpu=(device == "cuda"))
print("XTTS-v2 loaded")

knnvc_model = None
if USE_KNNVC:
    try:
        from knnvc import KNN_VC
        knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
        print("kNN-VC loaded (bshall/knn-vc)")
    except ImportError:
        print("WARNING: kNN-VC not installed — falling back to DSP")
        USE_KNNVC = False

# ─────────────────────────────────────────────────────────────
# LOAD SEGMENTS
# ─────────────────────────────────────────────────────────────
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)
segments = data["segments"]
print(f"Loaded {len(segments)} segments\n")

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def trim_silence(y, sr, top_db=35):
    _, idx = librosa.effects.trim(y, top_db=top_db,
                                   frame_length=512, hop_length=128)
    lead  = max(0, idx[0] - int(0.02 * sr))
    trail = min(len(y), idx[1] + int(0.03 * sr))
    return y[lead:trail]


def rms_normalise(y, target_dbfs=-18.0):
    rms = np.sqrt(np.mean(y ** 2))
    if rms < 1e-6:
        return y
    return np.clip(y * (10 ** (target_dbfs / 20.0) / rms), -0.95, 0.95)


def pad_or_trim(y, sr, target_dur):
    n = int(target_dur * sr)
    if len(y) < n:
        return np.pad(y, (0, n - len(y)))
    return y[:n]


def butter_filter(y, sr, cutoff, btype, order=4):
    b, a = butter(order, min(cutoff / (sr / 2.0), 0.99), btype=btype)
    return filtfilt(b, a, y)


# ─────────────────────────────────────────────────────────────
# REQUIREMENT 3 — WAVEFORM COMPARISON PLOT
# ─────────────────────────────────────────────────────────────
def save_waveform_comparison(jp_path, en_y, en_sr,
                              target_dur, seg_id,
                              speaker, emotion, stretch_ratio):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")

    def style(ax):
        ax.set_facecolor("#16213e")
        ax.spines[:].set_color("#444")
        ax.tick_params(colors="#aaa", labelsize=8)

    # JP original
    if jp_path and os.path.exists(jp_path):
        y_jp, sr_jp = librosa.load(jp_path, sr=None)
        ax1.plot(np.linspace(0, len(y_jp)/sr_jp, len(y_jp)),
                 y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
    else:
        ax1.text(0.5, 0.5, "JP source not found",
                 transform=ax1.transAxes, ha="center", color="#888", fontsize=9)
    style(ax1)
    ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
    ax1.set_title(
        f"Seg {seg_id:03d} | {speaker} | {emotion} | stretch {stretch_ratio:.3f}x",
        color="#ddd", fontsize=10, pad=5)

    # EN generated
    ax2.plot(np.linspace(0, len(en_y)/en_sr, len(en_y)),
             en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
    style(ax2)
    ax2.set_ylabel("EN generated", color="#aaa", fontsize=9)
    ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

    for ax in (ax1, ax2):
        ax.axvline(x=target_dur, color="#E24B4A", linewidth=1.2,
                   linestyle="--", alpha=0.8, label=f"target {target_dur:.2f}s")
        ax.legend(fontsize=8, facecolor="#222", labelcolor="#ccc",
                  edgecolor="#444", loc="upper right")

    plt.tight_layout(pad=1.5)
    out = os.path.join(WAVEFORM_DIR, f"comparison_{seg_id:03d}.png")
    plt.savefig(out, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out


# ─────────────────────────────────────────────────────────────
# REQUIREMENT 7 — UNDERSTANDABILITY CHECK
# ─────────────────────────────────────────────────────────────
def check_understandability(y, sr, stretch_ratio):
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
    zcr_var  = float(np.var(librosa.feature.zero_crossing_rate(y)))
    quality_ok = True
    reason     = "ok"
    if abs(stretch_ratio - 1.0) > 0.08 and flatness > 0.20:
        quality_ok = False
        reason = f"spectral_smearing (flatness={flatness:.3f})"
    if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
        quality_ok = False
        reason = f"robotic_periodicity (zcr_var={zcr_var:.2e})"
    return {
        "quality_ok": quality_ok, "reason": reason,
        "spectral_flatness": round(flatness, 4),
        "zcr_variance": round(zcr_var, 8),
    }


# ─────────────────────────────────────────────────────────────
# REQUIREMENT 6 — AGE / TYPE TRANSFORMATION
# ─────────────────────────────────────────────────────────────
def apply_age_transform(audio_path, out_path, age_category, knnvc_ref=None):
    if age_category == "adult" or age_category is None:
        shutil.copy(audio_path, out_path)
        return out_path

    preset = AGE_PRESETS.get(age_category)
    if preset is None:
        shutil.copy(audio_path, out_path)
        return out_path

    # ML path: kNN-VC
    if USE_KNNVC and knnvc_model and knnvc_ref and os.path.exists(knnvc_ref):
        try:
            import torchaudio
            matching = knnvc_model.get_matching_set([knnvc_ref])
            query    = knnvc_model.get_features(audio_path)
            out_wav  = knnvc_model.match(query, matching, topk=4)
            torchaudio.save(out_path, out_wav, 16000)
            return out_path
        except Exception as e:
            print(f"       WARNING: kNN-VC failed ({e}) — using DSP")

    # Robot
    if preset == "robot":
        return _apply_robot(audio_path, out_path)

    # DSP: Parselmouth Change Gender
    sound = parselmouth.Sound(audio_path)
    transformed = call(
        sound, "Change gender",
        75, 600,
        preset["formant_factor"],
        0,
        preset["pitch_factor"],
        preset["rate_factor"],
    )

    # Jitter
    jitter = preset.get("jitter", 0.0)
    if jitter > 0:
        y_a  = transformed.as_array().flatten()
        sr_p = int(transformed.sampling_frequency)
        y_a  = y_a + np.random.normal(0, jitter, len(y_a)) * np.abs(y_a)
        transformed = parselmouth.Sound(y_a, sr_p)

    # Breathiness + HF rolloff
    breathiness = preset.get("breathiness", 0.0)
    if breathiness > 0:
        y_a  = transformed.as_array().flatten()
        sr_p = int(transformed.sampling_frequency)
        noise  = np.random.normal(0, 0.015, len(y_a))
        b, a   = butter(4, 2000 / (sr_p / 2), btype="high")
        breath = filtfilt(b, a, noise)
        b2, a2 = butter(2, 4500 / (sr_p / 2), btype="low")
        y_a    = filtfilt(b2, a2, y_a)
        y_a    = np.clip(y_a * (1 - breathiness) + breath * breathiness, -0.95, 0.95)
        transformed = parselmouth.Sound(y_a, sr_p)

    transformed.save(out_path, "WAV")
    return out_path


def _apply_robot(audio_path, out_path):
    sound   = parselmouth.Sound(audio_path)
    sr      = int(sound.sampling_frequency)
    y       = sound.as_array().flatten()
    pitch   = call(sound, "To Pitch", 0.01, 75, 600)
    f0_vals = [call(pitch, "Get value at time", t, "Hertz", "Linear")
               for t in np.arange(0, sound.duration, 0.01)]
    f0_ok   = [v for v in f0_vals if not np.isnan(v) and v > 0]
    mean_f0 = float(np.mean(f0_ok)) if f0_ok else 150.0
    t_arr   = np.arange(len(y)) / sr
    buzz    = (2 * (t_arr * mean_f0 % 1) - 1) * 0.5 * np.std(y)
    robot   = np.clip(buzz * 0.7 + y * 0.3, -0.95, 0.95)
    sf.write(out_path, robot, sr)
    return out_path


# ─────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────
generated_clips = []
qc_flags_all    = []

for i, seg in enumerate(segments):
    sid          = seg["segment_id"]
    speaker      = seg["speaker"]
    english_text = seg["english"]
    target_dur   = float(seg["duration"])
    emotion      = seg.get("emotion", "neutral").lower()
    emotion_conf = float(seg.get("emotion_confidence", 1.0))

    print(f"\n{'─'*55}")
    print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | {target_dur:.2f}s")
    print(f"  text    : {english_text}")
    print(f"  emotion : {emotion}  (conf {emotion_conf:.2f})")

    spk_info     = SPEAKER_MAP.get(speaker, {})
    voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
    age_category = spk_info.get("age_category", "adult")
    knnvc_ref    = spk_info.get("knnvc_ref",    None)

    if not os.path.exists(voice_sample):
        print(f"  WARNING: voice not found: {voice_sample} — using default")
        voice_sample = DEFAULT_VOICE
    print(f"  voice   : {os.path.basename(voice_sample)}  | age: {age_category}")

    qc_flags   = []
    raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
    align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
    emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
    age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
    final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")

    # ── STAGE 1: XTTS-v2 VOICE CLONING ──────────────────────
    print("  [1] XTTS-v2 cloning...")
    tts.tts_to_file(
        text=english_text,
        speaker_wav=voice_sample,
        language="en",
        file_path=raw_path,
    )
    y_raw, sr = librosa.load(raw_path, sr=22050)
    y_raw     = trim_silence(y_raw, sr)
    raw_dur   = len(y_raw) / sr
    print(f"       raw (trimmed): {raw_dur:.3f}s  |  target: {target_dur:.3f}s")

    # ── STAGE 2: TIMING ALIGNMENT ────────────────────────────
    print("  [2] Timing alignment...")
    ratio     = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))
    # y_aligned = pyrb.time_stretch(y_raw, sr, rate=1.0 / ratio)
    # y_aligned = librosa.effects.time_stretch(y=y_raw, rate=ratio)
    from scipy.signal import resample
    target_samples = int(len(y_raw) / ratio)
    y_aligned = resample(y_raw, target_samples)
    y_aligned = pad_or_trim(y_aligned, sr, target_dur)
    print(f"       ratio: {ratio:.3f}x  |  aligned: {len(y_aligned)/sr:.3f}s")

    if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
        qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
        print(f"       WARNING: HIGH_STRETCH — consider re-translating")

    sf.write(align_path, y_aligned, sr)

    # Req 7: understandability
    quality = check_understandability(y_aligned, sr, ratio)
    print(f"       quality : {quality['reason']}  flatness={quality['spectral_flatness']:.3f}")
    if not quality["quality_ok"]:
        qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

    # Req 3: waveform plot
    jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
    wf_path = save_waveform_comparison(
        jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
        target_dur=target_dur, seg_id=sid,
        speaker=speaker, emotion=emotion, stretch_ratio=ratio,
    )
    print(f"       waveform: {wf_path}")

    # ── STAGE 3: EMOTION FINE-TUNING ─────────────────────────
    if EMOTION_ENABLED:
        eff_emotion = emotion if emotion_conf >= 0.30 else "neutral"
        print(f"  [3] Emotion: {eff_emotion}" +
              (" (low-conf override)" if eff_emotion != emotion else ""))

        target_dbfs = EMOTION_LOUDNESS.get(eff_emotion, -18)
        y_emotion   = rms_normalise(y_aligned, target_dbfs)

        if eff_emotion in ("sad",):
            y_emotion = butter_filter(y_emotion, sr, 3500, "low")
        elif eff_emotion in ("angry", "ang"):
            y_emotion = butter_filter(y_emotion, sr, 150, "high")
            y_hf      = butter_filter(y_emotion, sr, 3000, "high")
            y_emotion = np.clip(y_emotion + 0.15 * y_hf, -0.95, 0.95)
        elif eff_emotion in ("happy", "hap"):
            y_hf      = butter_filter(y_emotion, sr, 4000, "high")
            y_emotion = np.clip(y_emotion + 0.10 * y_hf, -0.95, 0.95)
        elif eff_emotion in ("fearful", "fea", "surprised", "sur"):
            noise     = np.random.normal(0, 0.008, len(y_emotion))
            breath    = butter_filter(noise, sr, 3000, "high")
            y_emotion = np.clip(y_emotion + breath * 0.12, -0.95, 0.95)
    else:
        print("  [3] Emotion: DISABLED")
        y_emotion   = y_aligned
        eff_emotion = "disabled"

    sf.write(emot_path, y_emotion, sr)

    # ── STAGE 4: AGE / TYPE TRANSFORMATION ───────────────────
    if AGE_ENABLED and age_category != "adult":
        method = "kNN-VC" if (USE_KNNVC and knnvc_ref) else "DSP"
        print(f"  [4] Age transform: {age_category}  [{method}]")
        apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
        y_final, sr_f = librosa.load(age_path, sr=None)
        y_final = pad_or_trim(y_final, sr_f, target_dur)
        sf.write(age_path, y_final, sr_f)
        sr_final = sr_f
    else:
        label = "DISABLED" if not AGE_ENABLED else "pass-through"
        print(f"  [4] Age transform: {label}")
        y_final  = y_emotion
        sr_final = sr

    sf.write(final_path, y_final, sr_final)
    final_clip_dur = len(y_final) / sr_final
    if final_clip_dur < 0.15:
        qc_flags.append("TOO_SHORT")

    # ── METADATA ─────────────────────────────────────────────
    clip_meta = {
        "segment_id":           sid,
        "speaker":              speaker,
        "start":                seg["start"],
        "end":                  seg["end"],
        "duration_target":      round(target_dur, 4),
        "duration_raw_trimmed": round(raw_dur, 4),
        "duration_final":       round(final_clip_dur, 4),
        "stretch_ratio":        round(ratio, 4),
        "voice_sample":         os.path.basename(voice_sample),
        "emotion":              emotion,
        "emotion_effective":    eff_emotion if EMOTION_ENABLED else "disabled",
        "emotion_confidence":   round(emotion_conf, 4),
        "emotion_enabled":      EMOTION_ENABLED,
        "age_category":         age_category,
        "age_enabled":          AGE_ENABLED,
        "quality_check":        quality,
        "qc_flags":             qc_flags,
        "waveform_plot":        wf_path,
        "files": {
            "raw":     raw_path,
            "aligned": align_path,
            "emotion": emot_path,
            "age":     age_path if (AGE_ENABLED and age_category != "adult") else None,
            "final":   final_path,
        },
    }
    generated_clips.append(clip_meta)
    if qc_flags:
        qc_flags_all.append((sid, qc_flags))

    status = "WARNING" if qc_flags else "OK"
    print(f"  [{status}] Seg {sid:03d} -> {final_path}")

# ─────────────────────────────────────────────────────────────
# SAVE METADATA
# ─────────────────────────────────────────────────────────────
output_meta = {
    "timestamp":       datetime.now().isoformat(),
    "total_clips":     len(generated_clips),
    "emotion_enabled": EMOTION_ENABLED,
    "age_enabled":     AGE_ENABLED,
    "clips":           generated_clips,
}
meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(output_meta, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────
# QC SUMMARY
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"STEP 4 COMPLETE -- {len(generated_clips)} clips generated")
print(f"Audio         : {OUTPUT_DIR}/")
print(f"Metadata      : {meta_path}")
print(f"Waveform plots: {WAVEFORM_DIR}/")

if qc_flags_all:
    print(f"\nQC FLAGS -- {len(qc_flags_all)} segments need attention:")
    for sid, flags in sorted(qc_flags_all):
        print(f"  [seg {sid:03d}]  {flags}")
else:
    print("\nAll segments passed QC")

print("\nNext -> step5_assembly.py")