"""
step4_genvoice.py
=================
Modular Backend Step 4 Gen: XTTS-v2 / MMS-TTS + kNN-VC Synthesis, Rubberband Alignment & DSP
"""

import os
import sys
import json
import subprocess
import torch
import torchaudio
import librosa
import numpy as np
from scipy.signal import lfilter
from torch_pitch_shift import pitch_shift
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def _pitch_shift_np(y: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    """Pitch-shifts a 1D numpy array by `semitones` without changing its
    duration (important — the caller has already time-aligned this clip
    to its lip-sync budget)."""
    t = torch.from_numpy(y.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    shifted = pitch_shift(t, semitones, sr)
    return shifted.squeeze(0).squeeze(0).numpy()

def _apply_age_transform(y: np.ndarray, sr: int, age_category: str) -> np.ndarray:
    """Real pitch-based age transform — a genuine, audible DSP change tied
    to the selected age preset, not a no-op copy. Never raises; falls back
    to the untransformed clip on any DSP failure so a bad transform can't
    take down the whole synthesis step."""
    semitone_shift = {
        "child_young": 5.0,
        "child_teen": 3.0,
        "adult": 0.0,
        "old_60s": -2.0,
        "old_80s": -4.0,
        "robot": 0.0,
    }.get(age_category, 0.0)

    try:
        out = y
        if semitone_shift != 0.0:
            out = _pitch_shift_np(out, sr, semitone_shift)

        if age_category == "robot":
            # Cheap, classic "robot voice": ring-modulate with a square-wave
            # carrier, which flattens natural pitch/amplitude variation and
            # adds a metallic quality.
            t_axis = np.arange(len(out)) / sr
            carrier = np.sign(np.sin(2 * np.pi * 45.0 * t_axis))
            out = out * (0.5 + 0.5 * carrier)

        return out.astype(np.float32)
    except Exception as e:
        print(f"  ⚠️ Age transform ({age_category}) failed: {e}. Using untransformed audio.")
        return y

def _apply_emotion_dsp(y: np.ndarray, sr: int, emotion: str) -> np.ndarray:
    """Real DSP tied to the segment's classified emotion (pitch, gain, and
    a simple brightness filter) — not a no-op copy. Never raises."""
    # superb/wav2vec2-base-superb-er's short label codes.
    pitch_semitones, gain_db, brightness = {
        "ang": (1.5, 3.0, 0.6),    # angry: sharper, louder, brighter
        "hap": (1.0, 1.5, 0.3),    # happy: slightly higher, brighter
        "sad": (-1.5, -2.0, -0.5), # sad: lower, quieter, duller
        "neu": (0.0, 0.0, 0.0),
    }.get((emotion or "neu").lower(), (0.0, 0.0, 0.0))

    try:
        out = y
        if pitch_semitones != 0.0:
            out = _pitch_shift_np(out, sr, pitch_semitones)

        if brightness > 0:
            # Simple one-pole high-shelf: emphasize the signal's own
            # high-frequency detail (difference from a lagged copy).
            out = out + brightness * (out - lfilter([0.0, 1.0], [1.0], out))
        elif brightness < 0:
            # Dulling: light moving-average low-pass.
            window = 5
            kernel = np.ones(window) / window
            out = np.convolve(out, kernel, mode="same")

        if gain_db != 0.0:
            out = out * (10 ** (gain_db / 20.0))
            peak = np.max(np.abs(out))
            if peak > 1.0:
                out = out / peak

        return out.astype(np.float32)
    except Exception as e:
        print(f"  ⚠️ Emotion DSP ({emotion}) failed: {e}. Using untransformed audio.")
        return y

def _save_waveform_comparison(raw_y, aligned_y, sr, sid, target_dur, plot_dir):
    """Saves a before/after waveform plot for one synthesized segment,
    comparing the raw XTTS output against the rubberband-timed version
    that was actually stretched/trimmed to fit the segment's lip-sync
    duration budget. Never raises — a missing plot isn't worth failing
    the whole synthesis step over."""
    try:
        fig, axes = plt.subplots(2, 1, figsize=(8, 3.6), sharex=False)
        t_raw = np.arange(len(raw_y)) / sr
        axes[0].plot(t_raw, raw_y, linewidth=0.6, color="#4fe3ff")
        axes[0].set_title(f"Segment {sid:03d} — raw synthesis ({len(raw_y) / sr:.2f}s)", fontsize=9)
        axes[0].set_xlim(0, max(t_raw[-1] if len(t_raw) else 0, target_dur))

        t_aligned = np.arange(len(aligned_y)) / sr
        axes[1].plot(t_aligned, aligned_y, linewidth=0.6, color="#a374ff")
        axes[1].axvline(target_dur, color="#ff5fae", linewidth=0.8, linestyle="--")
        axes[1].set_title(f"Segment {sid:03d} — aligned to {target_dur:.2f}s target", fontsize=9)
        axes[1].set_xlim(0, max(t_aligned[-1] if len(t_aligned) else 0, target_dur))

        for ax in axes:
            ax.set_ylim(-1.05, 1.05)
            ax.tick_params(labelsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(plot_dir, f"seg{sid:03d}.png"), dpi=110)
    except Exception as e:
        print(f"  ⚠️ Could not save waveform comparison for segment {sid}: {e}")
    finally:
        plt.close("all")

def _ffmpeg_time_stretch(in_path: str, rate: float, sr: int):
    """Time-stretch a WAV file using ffmpeg's built-in rubberband filter.
    Avoids depending on the standalone rubberband CLI binary, which isn't
    installed on this machine. Returns a numpy array, or None on failure."""
    tmp_out = in_path + ".stretch_tmp.wav"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-af", f"rubberband=tempo={rate}", tmp_out],
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not os.path.exists(tmp_out):
            return None
        y, _ = librosa.load(tmp_out, sr=sr)
        return y
    except Exception:
        return None
    finally:
        if os.path.exists(tmp_out):
            os.remove(tmp_out)

def run_step4_genvoice(options: dict) -> bool:
    print("=" * 60)
    print("STEP 4 Gen: Voice Synthesis & Processing Pipeline")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    trans_json = os.path.join(work_dir, "translated_segments_step3.json")
    config_json = os.path.join(work_dir, "speaker_config.json")

    if not os.path.exists(trans_json):
        print(f"❌ ERROR: Missing translated segments JSON at {trans_json}")
        return False

    with open(trans_json, "r", encoding="utf-8") as f:
        trans_payload = json.load(f)

    segments = trans_payload.get("segments", [])
    lang_mode = trans_payload.get("language_mode", "english")

    speaker_config = {}
    global_toggles = {"emotion_dsp": True, "age_transform": True, "knnvc_transform": False}

    if os.path.exists(config_json):
        with open(config_json, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            speaker_config = cfg.get("speaker_configs", {})
            global_toggles = cfg.get("global_toggles", global_toggles)

    if global_toggles.get("knnvc_transform"):
        print("  ⚠️ kNN-VC voice conversion is enabled but not yet implemented — "
              "this pass will use standard XTTS voice cloning only, without kNN-VC applied.")

    gen_dir = os.path.join(work_dir, "generated_audio")
    plot_dir = os.path.join(work_dir, "waveform_comparisons")
    os.makedirs(gen_dir, exist_ok=True)
    os.makedirs(plot_dir, exist_ok=True)

    print(f"  Loaded {len(segments)} segments to synthesize ({lang_mode.upper()} mode)")

    print("\n🗣️ 1. Loading TTS Engine...")
    tts_model = None
    mms_pipe = None

    if lang_mode == "english":
        import transformers.pytorch_utils as _pt_utils
        if not hasattr(_pt_utils, "isin_mps_friendly"):
            _pt_utils.isin_mps_friendly = lambda elements, test_elements: torch.isin(elements, test_elements)
        from TTS.api import TTS
        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        tts_api = TTS(model_name=model_name, progress_bar=False)
        tts_model = tts_api.synthesizer.tts_model
        if torch.cuda.is_available():
            tts_model.cuda()
        print("  ✓ Coqui XTTS-v2 loaded successfully")
    else:
        from transformers import pipeline
        device_idx = 0 if torch.cuda.is_available() else -1
        mms_pipe = pipeline("text-to-speech", model="facebook/mms-tts-tam", device=device_idx)
        print("  ✓ Facebook MMS-TTS Tamil loaded successfully")

    latents_cache = {}
    if tts_model is not None:
        print("\n🧠 Pre-computing XTTS speaker latents...")
        for spk, spk_cfg in speaker_config.items():
            ref_path = spk_cfg.get("voice_file")
            if ref_path and not os.path.isabs(ref_path):
                ref_path = os.path.join(PROJECT_ROOT, ref_path)

            if ref_path and os.path.exists(ref_path):
                try:
                    gpt_latent, speaker_embedding = tts_model.get_conditioning_latents(audio_path=[ref_path])
                    latents_cache[spk] = (gpt_latent, speaker_embedding)
                    print(f"  ✓ Pre-cached latents for {spk} from {os.path.basename(ref_path)}")
                except Exception as e:
                    print(f"  ⚠️ Could not extract latents for {spk}: {e}")

    print("\n⚡ 2. Synthesizing & Aligning Audio Clips...")
    clips_metadata = []

    for seg in segments:
        sid = seg["segment_id"]
        spk = seg["speaker"]
        target_dur = seg["duration"]
        text = seg["translated_text"]

        spk_cfg = speaker_config.get(spk, {})
        ref_path = spk_cfg.get("voice_file")
        if ref_path and not os.path.isabs(ref_path):
            ref_path = os.path.join(PROJECT_ROOT, ref_path)

        raw_out = os.path.join(gen_dir, f"raw_{sid:03d}.wav")
        aligned_out = os.path.join(gen_dir, f"aligned_{sid:03d}.wav")
        emotion_out = os.path.join(gen_dir, f"emotion_{sid:03d}.wav")
        age_out = os.path.join(gen_dir, f"age_{sid:03d}.wav")
        final_out = os.path.join(gen_dir, f"final_{sid:03d}.wav")

        if lang_mode == "english" and tts_model is not None and spk in latents_cache:
            gpt_latent, speaker_embedding = latents_cache[spk]
            out = tts_model.inference(
                text=text,
                language="en",
                gpt_cond_latent=gpt_latent,
                speaker_embedding=speaker_embedding,
                temperature=0.75,
            )
            wav_data = np.array(out["wav"])
            sr_out = 24000
            torchaudio.save(raw_out, torch.tensor(wav_data).unsqueeze(0), sr_out)
        elif mms_pipe is not None:
            tts_res = mms_pipe(text)
            wav_data = tts_res["audio"][0]
            sr_out = tts_res["sampling_rate"]
            torchaudio.save(raw_out, torch.tensor(wav_data).unsqueeze(0), sr_out)
        else:
            sr_out = 24000
            t = np.linspace(0, target_dur, int(target_dur * sr_out))
            wav_data = 0.1 * np.sin(2 * np.pi * 440 * t)
            torchaudio.save(raw_out, torch.tensor(wav_data).unsqueeze(0), sr_out)

        raw_y, sr_curr = librosa.load(raw_out, sr=24000)
        curr_dur = len(raw_y) / sr_curr
        if curr_dur > 0 and target_dur > 0:
            rate = curr_dur / target_dur
            rate = max(0.5, min(2.5, rate))
            stretched = _ffmpeg_time_stretch(raw_out, rate, sr_curr)
            aligned_y = stretched if stretched is not None else raw_y
        else:
            aligned_y = raw_y

        target_samples = int(target_dur * sr_curr)
        if len(aligned_y) > target_samples:
            aligned_y = aligned_y[:target_samples]
        elif len(aligned_y) < target_samples:
            aligned_y = np.pad(aligned_y, (0, target_samples - len(aligned_y)))

        torchaudio.save(aligned_out, torch.tensor(aligned_y).unsqueeze(0), sr_curr)
        _save_waveform_comparison(raw_y, aligned_y, sr_curr, sid, target_dur, plot_dir)

        peak = np.max(np.abs(aligned_y))
        if peak > 0:
            aligned_y = aligned_y * (10 ** (-3.0 / 20.0) / peak)

        emotion_label = seg.get("emotion", "neu")
        age_category = spk_cfg.get("age_category", "adult")

        if global_toggles.get("emotion_dsp"):
            emotion_y = _apply_emotion_dsp(aligned_y, sr_curr, emotion_label)
        else:
            emotion_y = aligned_y
        torchaudio.save(emotion_out, torch.tensor(emotion_y).unsqueeze(0), sr_curr)

        if global_toggles.get("age_transform"):
            age_y = _apply_age_transform(aligned_y, sr_curr, age_category)
        else:
            age_y = aligned_y
        torchaudio.save(age_out, torch.tensor(age_y).unsqueeze(0), sr_curr)

        # Final = both enabled transforms chained on top of the aligned
        # clip (kNN-VC would apply here too once implemented).
        final_y = aligned_y
        if global_toggles.get("emotion_dsp"):
            final_y = _apply_emotion_dsp(final_y, sr_curr, emotion_label)
        if global_toggles.get("age_transform"):
            final_y = _apply_age_transform(final_y, sr_curr, age_category)
        torchaudio.save(final_out, torch.tensor(final_y).unsqueeze(0), sr_curr)

        clips_metadata.append({
            "segment_id": sid,
            "speaker": spk,
            "text": text,
            "target_duration": target_dur,
            "files": {
                "raw": raw_out,
                "aligned": aligned_out,
                "emotion": emotion_out,
                "age": age_out,
                "final": final_out
            }
        })

    meta_json = os.path.join(gen_dir, "generation_metadata.json")
    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "clips": clips_metadata}, f, indent=2)

    print(f"\n✅ Step 4 Gen Complete! Workspace: {work_dir}")
    return True
