# # # # """
# # # # STEP 4: Voice Generation Pipeline — Complete
# # # # =============================================
# # # # Run step4_setup.py FIRST to configure speakers and install packages.
# # # # This script reads work/speaker_config.json automatically.

# # # # Requirements implemented:
# # # #   1. ✅ Voice library scan + speaker config from step4_setup.py
# # # #   2. ✅ XTTS-v2 voice cloning + generation (HuggingFace coqui/XTTS-v2)
# # # #   3. ✅ Waveform comparison plot — EN vs JP side-by-side PNG
# # # #   4. ✅ Timing enforcement — Rubberband 0.90–1.10x + pad/trim
# # # #   5. ✅ Emotion fine-tuning — user toggle + confidence gate
# # # #   6. ✅ Age/type transformation — child/adult/old/robot
# # # #   7. ✅ Understandability guard — spectral flatness + ZCR check

# # # # Usage:
# # # #     python step4_genvoice_complete.py
# # # # """

# # # # import os
# # # # import json
# # # # import shutil
# # # # import soundfile as sf
# # # # from datetime import datetime
# # # # from pathlib import Path

# # # # import torch
# # # # import librosa
# # # # import numpy as np
# # # # import matplotlib
# # # # matplotlib.use("Agg")
# # # # import matplotlib.pyplot as plt
# # # # import pyrubberband as pyrb
# # # # import parselmouth
# # # # from parselmouth.praat import call
# # # # from scipy.signal import butter, filtfilt
# # # # from TTS.api import TTS

# # # # # ─────────────────────────────────────────────────────────────
# # # # # PATHS
# # # # # ─────────────────────────────────────────────────────────────
# # # # INPUT_JSON    = "work/translated_segments_step3.json"
# # # # CONFIG_PATH   = "work/speaker_config.json"
# # # # OUTPUT_DIR    = "work/generated_audio"
# # # # WAVEFORM_DIR  = "work/waveform_comparisons"
# # # # CROPPED_DIR   = "work/cropped_segments"
# # # # DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

# # # # MIN_RATIO = 0.90
# # # # MAX_RATIO = 1.10

# # # # EMOTION_LOUDNESS = {
# # # #     "angry": -14, "ang": -14,
# # # #     "surprised": -15, "sur": -15,
# # # #     "fearful": -15, "fea": -15,
# # # #     "happy": -16, "hap": -16,
# # # #     "neutral": -18, "neu": -18,
# # # #     "sad": -22,
# # # #     "disgusted": -17, "dis": -17,
# # # #     "unknown": -18,
# # # # }

# # # # AGE_PRESETS = {
# # # #     "adult":       None,
# # # #     "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
# # # #     "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
# # # #     "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
# # # #     "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
# # # #     "robot":       "robot",
# # # # }

# # # # os.makedirs(OUTPUT_DIR,   exist_ok=True)
# # # # os.makedirs(WAVEFORM_DIR, exist_ok=True)

# # # # # ─────────────────────────────────────────────────────────────
# # # # # LOAD SPEAKER CONFIG
# # # # # ─────────────────────────────────────────────────────────────
# # # # def load_speaker_config():
# # # #     if not os.path.exists(CONFIG_PATH):
# # # #         print(f"WARNING: Config not found: {CONFIG_PATH}")
# # # #         print("Run step4_setup.py first to configure speakers.")
# # # #         print("Using default voice for all speakers.\n")
# # # #         return {
# # # #             "options":  {"emotion_enabled": True, "age_enabled": True, "use_knnvc": False},
# # # #             "speakers": {}
# # # #         }

# # # #     with open(CONFIG_PATH, "r", encoding="utf-8") as f:
# # # #         config = json.load(f)

# # # #     print(f"Config loaded: {CONFIG_PATH}")
# # # #     print(f"  Generated : {config.get('generated_at', 'unknown')}")
# # # #     opts = config.get("options", {})
# # # #     print(f"  Emotion   : {'ON' if opts.get('emotion_enabled') else 'OFF'}")
# # # #     print(f"  Age/type  : {'ON' if opts.get('age_enabled') else 'OFF'}")
# # # #     print(f"  Age mode  : {'kNN-VC' if opts.get('use_knnvc') else 'DSP (Parselmouth)'}")
# # # #     for spk, info in sorted(config.get("speakers", {}).items()):
# # # #         voice = info.get("voice_display", os.path.basename(info.get("voice_sample", "?")))
# # # #         print(f"  {spk:<14} -> {voice}  [{info.get('age_category','adult')}]")
# # # #     return config


# # # # print("=" * 60)
# # # # print("STEP 4: Voice Generation Pipeline")
# # # # print("=" * 60)

# # # # _cfg            = load_speaker_config()
# # # # SPEAKER_MAP     = _cfg.get("speakers", {})
# # # # EMOTION_ENABLED = _cfg["options"].get("emotion_enabled", True)
# # # # AGE_ENABLED     = _cfg["options"].get("age_enabled",     True)
# # # # USE_KNNVC       = _cfg["options"].get("use_knnvc",       False)

# # # # # ─────────────────────────────────────────────────────────────
# # # # # LOAD MODELS
# # # # # ─────────────────────────────────────────────────────────────
# # # # device = "cuda" if torch.cuda.is_available() else "cpu"
# # # # print(f"\nLoading models on {device}...")

# # # # tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
# # # #           gpu=(device == "cuda"))
# # # # print("XTTS-v2 loaded")

# # # # knnvc_model = None
# # # # if USE_KNNVC:
# # # #     try:
# # # #         from knnvc import KNN_VC
# # # #         knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
# # # #         print("kNN-VC loaded (bshall/knn-vc)")
# # # #     except ImportError:
# # # #         print("WARNING: kNN-VC not installed — falling back to DSP")
# # # #         USE_KNNVC = False

# # # # # ─────────────────────────────────────────────────────────────
# # # # # LOAD SEGMENTS
# # # # # ─────────────────────────────────────────────────────────────
# # # # with open(INPUT_JSON, "r", encoding="utf-8") as f:
# # # #     data = json.load(f)
# # # # segments = data["segments"]
# # # # print(f"Loaded {len(segments)} segments\n")

# # # # # ─────────────────────────────────────────────────────────────
# # # # # HELPERS
# # # # # ─────────────────────────────────────────────────────────────
# # # # def trim_silence(y, sr, top_db=35):
# # # #     _, idx = librosa.effects.trim(y, top_db=top_db,
# # # #                                    frame_length=512, hop_length=128)
# # # #     lead  = max(0, idx[0] - int(0.02 * sr))
# # # #     trail = min(len(y), idx[1] + int(0.03 * sr))
# # # #     return y[lead:trail]


# # # # def rms_normalise(y, target_dbfs=-18.0):
# # # #     rms = np.sqrt(np.mean(y ** 2))
# # # #     if rms < 1e-6:
# # # #         return y
# # # #     return np.clip(y * (10 ** (target_dbfs / 20.0) / rms), -0.95, 0.95)


# # # # def pad_or_trim(y, sr, target_dur):
# # # #     n = int(target_dur * sr)
# # # #     if len(y) < n:
# # # #         return np.pad(y, (0, n - len(y)))
# # # #     return y[:n]


# # # # def butter_filter(y, sr, cutoff, btype, order=4):
# # # #     b, a = butter(order, min(cutoff / (sr / 2.0), 0.99), btype=btype)
# # # #     return filtfilt(b, a, y)


# # # # # ─────────────────────────────────────────────────────────────
# # # # # REQUIREMENT 3 — WAVEFORM COMPARISON PLOT
# # # # # ─────────────────────────────────────────────────────────────
# # # # def save_waveform_comparison(jp_path, en_y, en_sr,
# # # #                               target_dur, seg_id,
# # # #                               speaker, emotion, stretch_ratio):
# # # #     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
# # # #     fig.patch.set_facecolor("#1a1a2e")

# # # #     def style(ax):
# # # #         ax.set_facecolor("#16213e")
# # # #         ax.spines[:].set_color("#444")
# # # #         ax.tick_params(colors="#aaa", labelsize=8)

# # # #     # JP original
# # # #     if jp_path and os.path.exists(jp_path):
# # # #         y_jp, sr_jp = librosa.load(jp_path, sr=None)
# # # #         ax1.plot(np.linspace(0, len(y_jp)/sr_jp, len(y_jp)),
# # # #                  y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
# # # #     else:
# # # #         ax1.text(0.5, 0.5, "JP source not found",
# # # #                  transform=ax1.transAxes, ha="center", color="#888", fontsize=9)
# # # #     style(ax1)
# # # #     ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
# # # #     ax1.set_title(
# # # #         f"Seg {seg_id:03d} | {speaker} | {emotion} | stretch {stretch_ratio:.3f}x",
# # # #         color="#ddd", fontsize=10, pad=5)

# # # #     # EN generated
# # # #     ax2.plot(np.linspace(0, len(en_y)/en_sr, len(en_y)),
# # # #              en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
# # # #     style(ax2)
# # # #     ax2.set_ylabel("EN generated", color="#aaa", fontsize=9)
# # # #     ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

# # # #     for ax in (ax1, ax2):
# # # #         ax.axvline(x=target_dur, color="#E24B4A", linewidth=1.2,
# # # #                    linestyle="--", alpha=0.8, label=f"target {target_dur:.2f}s")
# # # #         ax.legend(fontsize=8, facecolor="#222", labelcolor="#ccc",
# # # #                   edgecolor="#444", loc="upper right")

# # # #     plt.tight_layout(pad=1.5)
# # # #     out = os.path.join(WAVEFORM_DIR, f"comparison_{seg_id:03d}.png")
# # # #     plt.savefig(out, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
# # # #     plt.close(fig)
# # # #     return out


# # # # # ─────────────────────────────────────────────────────────────
# # # # # REQUIREMENT 7 — UNDERSTANDABILITY CHECK
# # # # # ─────────────────────────────────────────────────────────────
# # # # def check_understandability(y, sr, stretch_ratio):
# # # #     flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
# # # #     zcr_var  = float(np.var(librosa.feature.zero_crossing_rate(y)))
# # # #     quality_ok = True
# # # #     reason     = "ok"
# # # #     if abs(stretch_ratio - 1.0) > 0.08 and flatness > 0.20:
# # # #         quality_ok = False
# # # #         reason = f"spectral_smearing (flatness={flatness:.3f})"
# # # #     if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
# # # #         quality_ok = False
# # # #         reason = f"robotic_periodicity (zcr_var={zcr_var:.2e})"
# # # #     return {
# # # #         "quality_ok": quality_ok, "reason": reason,
# # # #         "spectral_flatness": round(flatness, 4),
# # # #         "zcr_variance": round(zcr_var, 8),
# # # #     }


# # # # # ─────────────────────────────────────────────────────────────
# # # # # REQUIREMENT 6 — AGE / TYPE TRANSFORMATION
# # # # # ─────────────────────────────────────────────────────────────
# # # # def apply_age_transform(audio_path, out_path, age_category, knnvc_ref=None):
# # # #     if age_category == "adult" or age_category is None:
# # # #         shutil.copy(audio_path, out_path)
# # # #         return out_path

# # # #     preset = AGE_PRESETS.get(age_category)
# # # #     if preset is None:
# # # #         shutil.copy(audio_path, out_path)
# # # #         return out_path

# # # #     # ML path: kNN-VC
# # # #     if USE_KNNVC and knnvc_model and knnvc_ref and os.path.exists(knnvc_ref):
# # # #         try:
# # # #             import torchaudio
# # # #             matching = knnvc_model.get_matching_set([knnvc_ref])
# # # #             query    = knnvc_model.get_features(audio_path)
# # # #             out_wav  = knnvc_model.match(query, matching, topk=4)
# # # #             torchaudio.save(out_path, out_wav, 16000)
# # # #             return out_path
# # # #         except Exception as e:
# # # #             print(f"       WARNING: kNN-VC failed ({e}) — using DSP")

# # # #     # Robot
# # # #     if preset == "robot":
# # # #         return _apply_robot(audio_path, out_path)

# # # #     # DSP: Parselmouth Change Gender
# # # #     sound = parselmouth.Sound(audio_path)
# # # #     transformed = call(
# # # #         sound, "Change gender",
# # # #         75, 600,
# # # #         preset["formant_factor"],
# # # #         0,
# # # #         preset["pitch_factor"],
# # # #         preset["rate_factor"],
# # # #     )

# # # #     # Jitter
# # # #     jitter = preset.get("jitter", 0.0)
# # # #     if jitter > 0:
# # # #         y_a  = transformed.as_array().flatten()
# # # #         sr_p = int(transformed.sampling_frequency)
# # # #         y_a  = y_a + np.random.normal(0, jitter, len(y_a)) * np.abs(y_a)
# # # #         transformed = parselmouth.Sound(y_a, sr_p)

# # # #     # Breathiness + HF rolloff
# # # #     breathiness = preset.get("breathiness", 0.0)
# # # #     if breathiness > 0:
# # # #         y_a  = transformed.as_array().flatten()
# # # #         sr_p = int(transformed.sampling_frequency)
# # # #         noise  = np.random.normal(0, 0.015, len(y_a))
# # # #         b, a   = butter(4, 2000 / (sr_p / 2), btype="high")
# # # #         breath = filtfilt(b, a, noise)
# # # #         b2, a2 = butter(2, 4500 / (sr_p / 2), btype="low")
# # # #         y_a    = filtfilt(b2, a2, y_a)
# # # #         y_a    = np.clip(y_a * (1 - breathiness) + breath * breathiness, -0.95, 0.95)
# # # #         transformed = parselmouth.Sound(y_a, sr_p)

# # # #     transformed.save(out_path, "WAV")
# # # #     return out_path


# # # # def _apply_robot(audio_path, out_path):
# # # #     sound   = parselmouth.Sound(audio_path)
# # # #     sr      = int(sound.sampling_frequency)
# # # #     y       = sound.as_array().flatten()
# # # #     pitch   = call(sound, "To Pitch", 0.01, 75, 600)
# # # #     f0_vals = [call(pitch, "Get value at time", t, "Hertz", "Linear")
# # # #                for t in np.arange(0, sound.duration, 0.01)]
# # # #     f0_ok   = [v for v in f0_vals if not np.isnan(v) and v > 0]
# # # #     mean_f0 = float(np.mean(f0_ok)) if f0_ok else 150.0
# # # #     t_arr   = np.arange(len(y)) / sr
# # # #     buzz    = (2 * (t_arr * mean_f0 % 1) - 1) * 0.5 * np.std(y)
# # # #     robot   = np.clip(buzz * 0.7 + y * 0.3, -0.95, 0.95)
# # # #     sf.write(out_path, robot, sr)
# # # #     return out_path


# # # # # ─────────────────────────────────────────────────────────────
# # # # # MAIN LOOP
# # # # # ─────────────────────────────────────────────────────────────
# # # # generated_clips = []
# # # # qc_flags_all    = []

# # # # for i, seg in enumerate(segments):
# # # #     sid          = seg["segment_id"]
# # # #     speaker      = seg["speaker"]
# # # #     english_text = seg["english"]
# # # #     target_dur   = float(seg["duration"])
# # # #     emotion      = seg.get("emotion", "neutral").lower()
# # # #     emotion_conf = float(seg.get("emotion_confidence", 1.0))

# # # #     print(f"\n{'─'*55}")
# # # #     print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | {target_dur:.2f}s")
# # # #     print(f"  text    : {english_text}")
# # # #     print(f"  emotion : {emotion}  (conf {emotion_conf:.2f})")

# # # #     spk_info     = SPEAKER_MAP.get(speaker, {})
# # # #     voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
# # # #     age_category = spk_info.get("age_category", "adult")
# # # #     knnvc_ref    = spk_info.get("knnvc_ref",    None)

# # # #     if not os.path.exists(voice_sample):
# # # #         print(f"  WARNING: voice not found: {voice_sample} — using default")
# # # #         voice_sample = DEFAULT_VOICE
# # # #     print(f"  voice   : {os.path.basename(voice_sample)}  | age: {age_category}")

# # # #     qc_flags   = []
# # # #     raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
# # # #     align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
# # # #     emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
# # # #     age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
# # # #     final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")

# # # #     # ── STAGE 1: XTTS-v2 VOICE CLONING ──────────────────────
# # # #     print("  [1] XTTS-v2 cloning...")
# # # #     tts.tts_to_file(
# # # #         text=english_text,
# # # #         speaker_wav=voice_sample,
# # # #         language="en",
# # # #         file_path=raw_path,
# # # #     )
# # # #     y_raw, sr = librosa.load(raw_path, sr=22050)
# # # #     y_raw     = trim_silence(y_raw, sr)
# # # #     raw_dur   = len(y_raw) / sr
# # # #     print(f"       raw (trimmed): {raw_dur:.3f}s  |  target: {target_dur:.3f}s")

# # # #     # ── STAGE 2: TIMING ALIGNMENT ────────────────────────────
# # # #     print("  [2] Timing alignment...")
# # # #     ratio     = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))
# # # #     # y_aligned = pyrb.time_stretch(y_raw, sr, rate=1.0 / ratio)
# # # #     # y_aligned = librosa.effects.time_stretch(y=y_raw, rate=ratio)
# # # #     from scipy.signal import resample
# # # #     target_samples = int(len(y_raw) / ratio)
# # # #     y_aligned = resample(y_raw, target_samples)
# # # #     y_aligned = pad_or_trim(y_aligned, sr, target_dur)
# # # #     print(f"       ratio: {ratio:.3f}x  |  aligned: {len(y_aligned)/sr:.3f}s")

# # # #     if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
# # # #         qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
# # # #         print(f"       WARNING: HIGH_STRETCH — consider re-translating")

# # # #     sf.write(align_path, y_aligned, sr)

# # # #     # Req 7: understandability
# # # #     quality = check_understandability(y_aligned, sr, ratio)
# # # #     print(f"       quality : {quality['reason']}  flatness={quality['spectral_flatness']:.3f}")
# # # #     if not quality["quality_ok"]:
# # # #         qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

# # # #     # Req 3: waveform plot
# # # #     jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
# # # #     wf_path = save_waveform_comparison(
# # # #         jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
# # # #         target_dur=target_dur, seg_id=sid,
# # # #         speaker=speaker, emotion=emotion, stretch_ratio=ratio,
# # # #     )
# # # #     print(f"       waveform: {wf_path}")

# # # #     # ── STAGE 3: EMOTION FINE-TUNING ─────────────────────────
# # # #     if EMOTION_ENABLED:
# # # #         eff_emotion = emotion if emotion_conf >= 0.30 else "neutral"
# # # #         print(f"  [3] Emotion: {eff_emotion}" +
# # # #               (" (low-conf override)" if eff_emotion != emotion else ""))

# # # #         target_dbfs = EMOTION_LOUDNESS.get(eff_emotion, -18)
# # # #         y_emotion   = rms_normalise(y_aligned, target_dbfs)

# # # #         if eff_emotion in ("sad",):
# # # #             y_emotion = butter_filter(y_emotion, sr, 3500, "low")
# # # #         elif eff_emotion in ("angry", "ang"):
# # # #             y_emotion = butter_filter(y_emotion, sr, 150, "high")
# # # #             y_hf      = butter_filter(y_emotion, sr, 3000, "high")
# # # #             y_emotion = np.clip(y_emotion + 0.15 * y_hf, -0.95, 0.95)
# # # #         elif eff_emotion in ("happy", "hap"):
# # # #             y_hf      = butter_filter(y_emotion, sr, 4000, "high")
# # # #             y_emotion = np.clip(y_emotion + 0.10 * y_hf, -0.95, 0.95)
# # # #         elif eff_emotion in ("fearful", "fea", "surprised", "sur"):
# # # #             noise     = np.random.normal(0, 0.008, len(y_emotion))
# # # #             breath    = butter_filter(noise, sr, 3000, "high")
# # # #             y_emotion = np.clip(y_emotion + breath * 0.12, -0.95, 0.95)
# # # #     else:
# # # #         print("  [3] Emotion: DISABLED")
# # # #         y_emotion   = y_aligned
# # # #         eff_emotion = "disabled"

# # # #     sf.write(emot_path, y_emotion, sr)

# # # #     # ── STAGE 4: AGE / TYPE TRANSFORMATION ───────────────────
# # # #     if AGE_ENABLED and age_category != "adult":
# # # #         method = "kNN-VC" if (USE_KNNVC and knnvc_ref) else "DSP"
# # # #         print(f"  [4] Age transform: {age_category}  [{method}]")
# # # #         apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
# # # #         y_final, sr_f = librosa.load(age_path, sr=None)
# # # #         y_final = pad_or_trim(y_final, sr_f, target_dur)
# # # #         sf.write(age_path, y_final, sr_f)
# # # #         sr_final = sr_f
# # # #     else:
# # # #         label = "DISABLED" if not AGE_ENABLED else "pass-through"
# # # #         print(f"  [4] Age transform: {label}")
# # # #         y_final  = y_emotion
# # # #         sr_final = sr

# # # #     sf.write(final_path, y_final, sr_final)
# # # #     final_clip_dur = len(y_final) / sr_final
# # # #     if final_clip_dur < 0.15:
# # # #         qc_flags.append("TOO_SHORT")

# # # #     # ── METADATA ─────────────────────────────────────────────
# # # #     clip_meta = {
# # # #         "segment_id":           sid,
# # # #         "speaker":              speaker,
# # # #         "start":                seg["start"],
# # # #         "end":                  seg["end"],
# # # #         "duration_target":      round(target_dur, 4),
# # # #         "duration_raw_trimmed": round(raw_dur, 4),
# # # #         "duration_final":       round(final_clip_dur, 4),
# # # #         "stretch_ratio":        round(ratio, 4),
# # # #         "voice_sample":         os.path.basename(voice_sample),
# # # #         "emotion":              emotion,
# # # #         "emotion_effective":    eff_emotion if EMOTION_ENABLED else "disabled",
# # # #         "emotion_confidence":   round(emotion_conf, 4),
# # # #         "emotion_enabled":      EMOTION_ENABLED,
# # # #         "age_category":         age_category,
# # # #         "age_enabled":          AGE_ENABLED,
# # # #         "quality_check":        quality,
# # # #         "qc_flags":             qc_flags,
# # # #         "waveform_plot":        wf_path,
# # # #         "files": {
# # # #             "raw":     raw_path,
# # # #             "aligned": align_path,
# # # #             "emotion": emot_path,
# # # #             "age":     age_path if (AGE_ENABLED and age_category != "adult") else None,
# # # #             "final":   final_path,
# # # #         },
# # # #     }
# # # #     generated_clips.append(clip_meta)
# # # #     if qc_flags:
# # # #         qc_flags_all.append((sid, qc_flags))

# # # #     status = "WARNING" if qc_flags else "OK"
# # # #     print(f"  [{status}] Seg {sid:03d} -> {final_path}")

# # # # # ─────────────────────────────────────────────────────────────
# # # # # SAVE METADATA
# # # # # ─────────────────────────────────────────────────────────────
# # # # output_meta = {
# # # #     "timestamp":       datetime.now().isoformat(),
# # # #     "total_clips":     len(generated_clips),
# # # #     "emotion_enabled": EMOTION_ENABLED,
# # # #     "age_enabled":     AGE_ENABLED,
# # # #     "clips":           generated_clips,
# # # # }
# # # # meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
# # # # with open(meta_path, "w", encoding="utf-8") as f:
# # # #     json.dump(output_meta, f, indent=2, ensure_ascii=False)

# # # # # ─────────────────────────────────────────────────────────────
# # # # # QC SUMMARY
# # # # # ─────────────────────────────────────────────────────────────
# # # # print(f"\n{'='*60}")
# # # # print(f"STEP 4 COMPLETE -- {len(generated_clips)} clips generated")
# # # # print(f"Audio         : {OUTPUT_DIR}/")
# # # # print(f"Metadata      : {meta_path}")
# # # # print(f"Waveform plots: {WAVEFORM_DIR}/")

# # # # if qc_flags_all:
# # # #     print(f"\nQC FLAGS -- {len(qc_flags_all)} segments need attention:")
# # # #     for sid, flags in sorted(qc_flags_all):
# # # #         print(f"  [seg {sid:03d}]  {flags}")
# # # # else:
# # # #     print("\nAll segments passed QC")

# # # # print("\nNext -> step5_assembly.py")
# # # """
# # # STEP 4: Voice Generation Pipeline — Complete
# # # =============================================
# # # Run step4_setup.py FIRST to configure speakers.
# # # Reads work/speaker_config.json automatically.

# # # Tamil/Tanglish changes vs previous version:
# # #   - Reads language_mode, tts_language, text_field from speaker_config.json
# # #   - Reads dub text from correct field ("english" or "tamil")
# # #   - Passes TTS_LANGUAGE to tts_to_file (en or ta)
# # #   - All other logic unchanged
# # # """

# # # import os
# # # import json
# # # import shutil
# # # import soundfile as sf
# # # from datetime import datetime
# # # from pathlib import Path

# # # import torch
# # # import librosa
# # # import numpy as np
# # # import matplotlib
# # # matplotlib.use("Agg")
# # # import matplotlib.pyplot as plt
# # # import parselmouth
# # # from parselmouth.praat import call
# # # from scipy.signal import butter, filtfilt, resample
# # # from TTS.api import TTS

# # # # ─────────────────────────────────────────────────────────────
# # # # PATHS
# # # # ─────────────────────────────────────────────────────────────
# # # INPUT_JSON    = "work/translated_segments_step3.json"
# # # CONFIG_PATH   = "work/speaker_config.json"
# # # OUTPUT_DIR    = "work/generated_audio"
# # # WAVEFORM_DIR  = "work/waveform_comparisons"
# # # CROPPED_DIR   = "work/cropped_segments"
# # # DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

# # # MIN_RATIO = 0.90
# # # MAX_RATIO = 1.10

# # # EMOTION_LOUDNESS = {
# # #     "angry": -14, "ang": -14,
# # #     "surprised": -15, "sur": -15,
# # #     "fearful": -15, "fea": -15,
# # #     "happy": -16, "hap": -16,
# # #     "neutral": -18, "neu": -18,
# # #     "sad": -22,
# # #     "disgusted": -17, "dis": -17,
# # #     "unknown": -18,
# # # }

# # # AGE_PRESETS = {
# # #     "adult":       None,
# # #     "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
# # #     "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
# # #     "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
# # #     "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
# # #     "robot":       "robot",
# # # }

# # # os.makedirs(OUTPUT_DIR,   exist_ok=True)
# # # os.makedirs(WAVEFORM_DIR, exist_ok=True)

# # # # ─────────────────────────────────────────────────────────────
# # # # LOAD SPEAKER CONFIG
# # # # ─────────────────────────────────────────────────────────────
# # # def load_speaker_config():
# # #     if not os.path.exists(CONFIG_PATH):
# # #         print(f"WARNING: {CONFIG_PATH} not found — run step4_setup.py first")
# # #         return {
# # #             "options":       {"emotion_enabled": True, "age_enabled": True, "use_knnvc": False},
# # #             "speakers":      {},
# # #             "language_mode": "english",
# # #             "tts_language":  "en",
# # #             "text_field":    "english",
# # #         }
# # #     with open(CONFIG_PATH, "r", encoding="utf-8") as f:
# # #         cfg = json.load(f)
# # #     print(f"Config: {CONFIG_PATH}  [{cfg.get('generated_at','')}]")
# # #     opts = cfg.get("options", {})
# # #     print(f"  Language  : {cfg.get('language_mode','english')}")
# # #     print(f"  TTS code  : {cfg.get('tts_language','en')}")
# # #     print(f"  Text field: {cfg.get('text_field','english')}")
# # #     print(f"  Emotion   : {'ON' if opts.get('emotion_enabled') else 'OFF'}")
# # #     print(f"  Age/type  : {'ON' if opts.get('age_enabled') else 'OFF'}")
# # #     for spk, d in sorted(cfg.get("speakers", {}).items()):
# # #         v = d.get("voice_display", os.path.basename(d.get("voice_sample","?")))
# # #         print(f"  {spk:<14} -> {v}  [{d.get('age_category','adult')}]")
# # #     return cfg


# # # print("=" * 60)
# # # print("STEP 4: Voice Generation Pipeline")
# # # print("=" * 60)

# # # _cfg            = load_speaker_config()
# # # SPEAKER_MAP     = _cfg.get("speakers", {})
# # # EMOTION_ENABLED = _cfg["options"].get("emotion_enabled", True)
# # # AGE_ENABLED     = _cfg["options"].get("age_enabled",     True)
# # # USE_KNNVC       = _cfg["options"].get("use_knnvc",       False)

# # # # ── LANGUAGE CONFIG (Tamil/Tanglish support) ──────────────────
# # # LANGUAGE_MODE   = _cfg.get("language_mode", "english")   # english | tamil | tanglish
# # # TTS_LANGUAGE    = _cfg.get("tts_language",  "en")        # en | ta
# # # TEXT_FIELD      = _cfg.get("text_field",    "english")   # english | tamil

# # # print(f"\nLanguage: {LANGUAGE_MODE}  |  TTS: {TTS_LANGUAGE}  |  Field: {TEXT_FIELD}")

# # # # ─────────────────────────────────────────────────────────────
# # # # LOAD MODELS
# # # # ─────────────────────────────────────────────────────────────
# # # device = "cuda" if torch.cuda.is_available() else "cpu"
# # # print(f"\nLoading XTTS-v2 on {device}...")
# # # tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
# # #           gpu=(device == "cuda"))
# # # print("XTTS-v2 loaded")

# # # knnvc_model = None
# # # if USE_KNNVC:
# # #     try:
# # #         from knnvc import KNN_VC
# # #         knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
# # #         print("kNN-VC loaded")
# # #     except ImportError:
# # #         print("WARNING: kNN-VC not installed — falling back to DSP")
# # #         USE_KNNVC = False

# # # # ─────────────────────────────────────────────────────────────
# # # # LOAD SEGMENTS
# # # # ─────────────────────────────────────────────────────────────
# # # with open(INPUT_JSON, "r", encoding="utf-8") as f:
# # #     data = json.load(f)
# # # segments = data["segments"]
# # # print(f"Loaded {len(segments)} segments\n")

# # # # ─────────────────────────────────────────────────────────────
# # # # HELPERS
# # # # ─────────────────────────────────────────────────────────────
# # # def trim_silence(y, sr, top_db=35):
# # #     _, idx = librosa.effects.trim(y, top_db=top_db,
# # #                                    frame_length=512, hop_length=128)
# # #     lead  = max(0, idx[0] - int(0.02 * sr))
# # #     trail = min(len(y), idx[1] + int(0.03 * sr))
# # #     return y[lead:trail]

# # # def rms_normalise(y, target_dbfs=-18.0):
# # #     rms = np.sqrt(np.mean(y ** 2))
# # #     if rms < 1e-6: return y
# # #     return np.clip(y * (10 ** (target_dbfs / 20.0) / rms), -0.95, 0.95)

# # # def pad_or_trim(y, sr, target_dur):
# # #     n = int(target_dur * sr)
# # #     if len(y) < n: return np.pad(y, (0, n - len(y)))
# # #     return y[:n]

# # # def butter_filter(y, sr, cutoff, btype, order=4):
# # #     b, a = butter(order, min(cutoff / (sr / 2.0), 0.99), btype=btype)
# # #     return filtfilt(b, a, y)

# # # # ─────────────────────────────────────────────────────────────
# # # # WAVEFORM COMPARISON PLOT
# # # # ─────────────────────────────────────────────────────────────
# # # def save_waveform_comparison(jp_path, en_y, en_sr, target_dur,
# # #                               seg_id, speaker, emotion, stretch_ratio):
# # #     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
# # #     fig.patch.set_facecolor("#1a1a2e")

# # #     def style(ax):
# # #         ax.set_facecolor("#16213e")
# # #         ax.spines[:].set_color("#444")
# # #         ax.tick_params(colors="#aaa", labelsize=8)

# # #     if jp_path and os.path.exists(jp_path):
# # #         y_jp, sr_jp = librosa.load(jp_path, sr=None, mono=True)
# # #         ax1.plot(np.linspace(0, len(y_jp)/sr_jp, len(y_jp)),
# # #                  y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
# # #     else:
# # #         ax1.text(0.5, 0.5, "JP source not found", transform=ax1.transAxes,
# # #                  ha="center", color="#888", fontsize=9)
# # #     style(ax1)
# # #     ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
# # #     ax1.set_title(
# # #         f"Seg {seg_id:03d} | {speaker} | {emotion} | "
# # #         f"stretch {stretch_ratio:.3f}x | lang={LANGUAGE_MODE}",
# # #         color="#ddd", fontsize=10, pad=5)

# # #     ax2.plot(np.linspace(0, len(en_y)/en_sr, len(en_y)),
# # #              en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
# # #     style(ax2)
# # #     ax2.set_ylabel(f"Generated [{LANGUAGE_MODE}]", color="#aaa", fontsize=9)
# # #     ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

# # #     for ax in (ax1, ax2):
# # #         ax.axvline(x=target_dur, color="#E24B4A", linewidth=1.2,
# # #                    linestyle="--", alpha=0.8, label=f"target {target_dur:.2f}s")
# # #         ax.legend(fontsize=8, facecolor="#222", labelcolor="#ccc",
# # #                   edgecolor="#444", loc="upper right")

# # #     plt.tight_layout(pad=1.5)
# # #     out = os.path.join(WAVEFORM_DIR, f"comparison_{seg_id:03d}.png")
# # #     plt.savefig(out, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
# # #     plt.close(fig)
# # #     return out

# # # # ─────────────────────────────────────────────────────────────
# # # # UNDERSTANDABILITY CHECK
# # # # ─────────────────────────────────────────────────────────────
# # # def check_understandability(y, sr, stretch_ratio):
# # #     flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
# # #     zcr_var  = float(np.var(librosa.feature.zero_crossing_rate(y)))
# # #     ok = True; reason = "ok"
# # #     if abs(stretch_ratio - 1.0) > 0.08 and flatness > 0.20:
# # #         ok = False; reason = f"spectral_smearing ({flatness:.3f})"
# # #     if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
# # #         ok = False; reason = f"robotic_periodicity ({zcr_var:.2e})"
# # #     return {"quality_ok": ok, "reason": reason,
# # #             "spectral_flatness": round(flatness,4),
# # #             "zcr_variance": round(zcr_var,8)}

# # # # ─────────────────────────────────────────────────────────────
# # # # AGE / TYPE TRANSFORMATION
# # # # ─────────────────────────────────────────────────────────────
# # # def apply_age_transform(audio_path, out_path, age_category, knnvc_ref=None):
# # #     if age_category == "adult" or age_category is None:
# # #         shutil.copy(audio_path, out_path); return out_path
# # #     preset = AGE_PRESETS.get(age_category)
# # #     if preset is None:
# # #         shutil.copy(audio_path, out_path); return out_path

# # #     if USE_KNNVC and knnvc_model and knnvc_ref and os.path.exists(knnvc_ref):
# # #         try:
# # #             import torchaudio
# # #             matching = knnvc_model.get_matching_set([knnvc_ref])
# # #             query    = knnvc_model.get_features(audio_path)
# # #             out_wav  = knnvc_model.match(query, matching, topk=4)
# # #             torchaudio.save(out_path, out_wav, 16000)
# # #             return out_path
# # #         except Exception as e:
# # #             print(f"       kNN-VC failed ({e}) — using DSP")

# # #     if preset == "robot":
# # #         return _apply_robot(audio_path, out_path)

# # #     sound = parselmouth.Sound(audio_path)
# # #     transformed = call(sound, "Change gender", 75, 600,
# # #                        preset["formant_factor"], 0,
# # #                        preset["pitch_factor"], preset["rate_factor"])
# # #     jitter = preset.get("jitter", 0.0)
# # #     if jitter > 0:
# # #         y_a = transformed.as_array().flatten()
# # #         sr_p = int(transformed.sampling_frequency)
# # #         y_a += np.random.normal(0, jitter, len(y_a)) * np.abs(y_a)
# # #         transformed = parselmouth.Sound(y_a, sr_p)

# # #     breathiness = preset.get("breathiness", 0.0)
# # #     if breathiness > 0:
# # #         y_a  = transformed.as_array().flatten()
# # #         sr_p = int(transformed.sampling_frequency)
# # #         noise  = np.random.normal(0, 0.015, len(y_a))
# # #         b, a   = butter(4, 2000/(sr_p/2), btype="high")
# # #         breath = filtfilt(b, a, noise)
# # #         b2,a2  = butter(2, 4500/(sr_p/2), btype="low")
# # #         y_a    = filtfilt(b2, a2, y_a)
# # #         y_a    = np.clip(y_a*(1-breathiness) + breath*breathiness, -0.95, 0.95)
# # #         transformed = parselmouth.Sound(y_a, sr_p)

# # #     transformed.save(out_path, "WAV")
# # #     return out_path

# # # def _apply_robot(audio_path, out_path):
# # #     sound  = parselmouth.Sound(audio_path)
# # #     sr     = int(sound.sampling_frequency)
# # #     y      = sound.as_array().flatten()
# # #     pitch  = call(sound, "To Pitch", 0.01, 75, 600)
# # #     f0_ok  = [call(pitch,"Get value at time",t,"Hertz","Linear")
# # #                for t in np.arange(0, sound.duration, 0.01)]
# # #     f0_ok  = [v for v in f0_ok if not np.isnan(v) and v > 0]
# # #     mean_f0 = float(np.mean(f0_ok)) if f0_ok else 150.0
# # #     t_arr  = np.arange(len(y)) / sr
# # #     buzz   = (2*(t_arr*mean_f0 % 1) - 1) * 0.5 * np.std(y)
# # #     sf.write(out_path, np.clip(buzz*0.7 + y*0.3, -0.95, 0.95), sr)
# # #     return out_path

# # # # ─────────────────────────────────────────────────────────────
# # # # MAIN LOOP
# # # # ─────────────────────────────────────────────────────────────
# # # generated_clips = []
# # # qc_flags_all    = []

# # # for i, seg in enumerate(segments):
# # #     sid          = seg["segment_id"]
# # #     speaker      = seg["speaker"]
# # #     target_dur   = float(seg["duration"])
# # #     emotion      = seg.get("emotion", "neutral").lower()
# # #     emotion_conf = float(seg.get("emotion_confidence", 1.0))

# # #     # ── READ DUB TEXT FROM CORRECT FIELD ─────────────────────
# # #     # TEXT_FIELD is "english" or "tamil" depending on Step 3 choice
# # #     dub_text = (seg.get(TEXT_FIELD)
# # #                 or seg.get("english")
# # #                 or seg.get("tamil", ""))

# # #     if not dub_text:
# # #         print(f"\n  WARNING: No dub text for seg {sid:03d} — skipping")
# # #         continue

# # #     print(f"\n{'─'*55}")
# # #     print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | {target_dur:.2f}s")
# # #     print(f"  [{LANGUAGE_MODE}] : {dub_text}")
# # #     print(f"  emotion : {emotion}  (conf {emotion_conf:.2f})")

# # #     spk_info     = SPEAKER_MAP.get(speaker, {})
# # #     voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
# # #     age_category = spk_info.get("age_category", "adult")
# # #     knnvc_ref    = spk_info.get("knnvc_ref",    None)

# # #     if not os.path.exists(voice_sample):
# # #         print(f"  WARNING: voice not found: {voice_sample} — using default")
# # #         voice_sample = DEFAULT_VOICE
# # #     print(f"  voice   : {os.path.basename(voice_sample)}  | age: {age_category}")

# # #     qc_flags   = []
# # #     raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
# # #     align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
# # #     emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
# # #     age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
# # #     final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")

# # #     # ── STAGE 1: XTTS-v2 ─────────────────────────────────────
# # #     print("  [1] XTTS-v2 cloning...")
# # #     tts.tts_to_file(
# # #         text=dub_text,
# # #         speaker_wav=voice_sample,
# # #         language=TTS_LANGUAGE,      # "en" or "ta" — from Step 3 config
# # #         file_path=raw_path,
# # #     )
# # #     y_raw, sr = librosa.load(raw_path, sr=22050)
# # #     y_raw     = trim_silence(y_raw, sr)
# # #     raw_dur   = len(y_raw) / sr
# # #     print(f"       raw: {raw_dur:.3f}s  target: {target_dur:.3f}s")

# # #     # ── STAGE 2: TIMING ──────────────────────────────────────
# # #     print("  [2] Timing alignment...")
# # #     ratio          = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))
# # #     target_samples = int(len(y_raw) / ratio)
# # #     y_aligned      = resample(y_raw, target_samples)
# # #     y_aligned      = pad_or_trim(y_aligned, sr, target_dur)
# # #     print(f"       ratio: {ratio:.3f}x  aligned: {len(y_aligned)/sr:.3f}s")

# # #     if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
# # #         qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
# # #         print(f"       WARNING: HIGH_STRETCH")

# # #     sf.write(align_path, y_aligned, sr)

# # #     quality = check_understandability(y_aligned, sr, ratio)
# # #     print(f"       quality: {quality['reason']}")
# # #     if not quality["quality_ok"]:
# # #         qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

# # #     jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
# # #     wf_path = save_waveform_comparison(
# # #         jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
# # #         target_dur=target_dur, seg_id=sid,
# # #         speaker=speaker, emotion=emotion, stretch_ratio=ratio)
# # #     print(f"       waveform: {wf_path}")

# # #     # ── STAGE 3: EMOTION ─────────────────────────────────────
# # #     if EMOTION_ENABLED:
# # #         eff_emotion = emotion if emotion_conf >= 0.30 else "neutral"
# # #         print(f"  [3] Emotion: {eff_emotion}" +
# # #               (" (low-conf override)" if eff_emotion != emotion else ""))
# # #         target_dbfs = EMOTION_LOUDNESS.get(eff_emotion, -18)
# # #         y_emotion   = rms_normalise(y_aligned, target_dbfs)
# # #         if eff_emotion in ("sad",):
# # #             y_emotion = butter_filter(y_emotion, sr, 3500, "low")
# # #         elif eff_emotion in ("angry","ang"):
# # #             y_emotion = butter_filter(y_emotion, sr, 150, "high")
# # #             y_hf      = butter_filter(y_emotion, sr, 3000, "high")
# # #             y_emotion = np.clip(y_emotion + 0.15*y_hf, -0.95, 0.95)
# # #         elif eff_emotion in ("happy","hap"):
# # #             y_hf      = butter_filter(y_emotion, sr, 4000, "high")
# # #             y_emotion = np.clip(y_emotion + 0.10*y_hf, -0.95, 0.95)
# # #         elif eff_emotion in ("fearful","fea","surprised","sur"):
# # #             noise     = np.random.normal(0, 0.008, len(y_emotion))
# # #             breath    = butter_filter(noise, sr, 3000, "high")
# # #             y_emotion = np.clip(y_emotion + breath*0.12, -0.95, 0.95)
# # #     else:
# # #         print("  [3] Emotion: DISABLED")
# # #         y_emotion   = y_aligned
# # #         eff_emotion = "disabled"
# # #     sf.write(emot_path, y_emotion, sr)

# # #     # ── STAGE 4: AGE ─────────────────────────────────────────
# # #     if AGE_ENABLED and age_category != "adult":
# # #         method = "kNN-VC" if (USE_KNNVC and knnvc_ref) else "DSP"
# # #         print(f"  [4] Age: {age_category}  [{method}]")
# # #         apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
# # #         y_final, sr_f = librosa.load(age_path, sr=None)
# # #         y_final = pad_or_trim(y_final, sr_f, target_dur)
# # #         sf.write(age_path, y_final, sr_f)
# # #         sr_final = sr_f
# # #     else:
# # #         label = "DISABLED" if not AGE_ENABLED else "adult/pass-through"
# # #         print(f"  [4] Age: {label}")
# # #         y_final = y_emotion; sr_final = sr

# # #     sf.write(final_path, y_final, sr_final)
# # #     dur_final = len(y_final) / sr_final
# # #     if dur_final < 0.15: qc_flags.append("TOO_SHORT")

# # #     clip_meta = {
# # #         "segment_id":           sid,
# # #         "speaker":              speaker,
# # #         "start":                seg["start"],
# # #         "end":                  seg["end"],
# # #         "duration_target":      round(target_dur, 4),
# # #         "duration_raw_trimmed": round(raw_dur, 4),
# # #         "duration_final":       round(dur_final, 4),
# # #         "stretch_ratio":        round(ratio, 4),
# # #         "voice_sample":         os.path.basename(voice_sample),
# # #         "language_mode":        LANGUAGE_MODE,
# # #         "tts_language":         TTS_LANGUAGE,
# # #         "text":                 dub_text,
# # #         "emotion":              emotion,
# # #         "emotion_effective":    eff_emotion if EMOTION_ENABLED else "disabled",
# # #         "emotion_confidence":   round(emotion_conf, 4),
# # #         "emotion_enabled":      EMOTION_ENABLED,
# # #         "age_category":         age_category,
# # #         "age_enabled":          AGE_ENABLED,
# # #         "quality_check":        quality,
# # #         "qc_flags":             qc_flags,
# # #         "waveform_plot":        wf_path,
# # #         "files": {
# # #             "raw":     raw_path,
# # #             "aligned": align_path,
# # #             "emotion": emot_path,
# # #             "age":     age_path if (AGE_ENABLED and age_category != "adult") else None,
# # #             "final":   final_path,
# # #         },
# # #     }
# # #     generated_clips.append(clip_meta)
# # #     if qc_flags: qc_flags_all.append((sid, qc_flags))

# # #     status = "WARN" if qc_flags else "OK"
# # #     print(f"  [{status}] Seg {sid:03d} -> {final_path}")

# # # # ─────────────────────────────────────────────────────────────
# # # # SAVE METADATA
# # # # ─────────────────────────────────────────────────────────────
# # # meta = {
# # #     "timestamp":       datetime.now().isoformat(),
# # #     "total_clips":     len(generated_clips),
# # #     "language_mode":   LANGUAGE_MODE,
# # #     "tts_language":    TTS_LANGUAGE,
# # #     "emotion_enabled": EMOTION_ENABLED,
# # #     "age_enabled":     AGE_ENABLED,
# # #     "clips":           generated_clips,
# # # }
# # # meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
# # # with open(meta_path, "w", encoding="utf-8") as f:
# # #     json.dump(meta, f, indent=2, ensure_ascii=False)

# # # print(f"\n{'='*60}")
# # # print(f"STEP 4 COMPLETE -- {len(generated_clips)} clips  [{LANGUAGE_MODE}]")
# # # print(f"Audio    : {OUTPUT_DIR}/")
# # # print(f"Metadata : {meta_path}")
# # # print(f"Waveforms: {WAVEFORM_DIR}/")
# # # if qc_flags_all:
# # #     print(f"\nQC FLAGS ({len(qc_flags_all)} segments):")
# # #     for sid, flags in sorted(qc_flags_all):
# # #         print(f"  [seg {sid:03d}] {flags}")
# # # else:
# # #     print("\nAll segments passed QC")
# # # print("\nNext -> step5_assembly.py")
# # """
# # STEP 4: Voice Generation Pipeline — Complete
# # =============================================
# # Run step4_setup.py FIRST to configure speakers.
# # Reads work/speaker_config.json automatically.

# # Tamil/Tanglish voice generation strategy:
# #   English  → XTTS-v2 with voice cloning (language="en")
# #   Tamil    → facebook/mms-tts-tam (correct Tamil phonemes)
# #              + kNN-VC voice conversion (shifts to reference voice)
# #   Tanglish → Same as Tamil path (MMS + kNN-VC)

# # Install for Tamil support:
# #   pip install transformers accelerate
# #   pip install knnvc

# # Two-step Tamil flow:
# #   1. MMS-TTS generates Tamil speech in its fixed voice
# #      → correct pronunciation, wrong speaker identity
# #   2. kNN-VC shifts the voice toward your reference sample
# #      → partial voice identity transfer, correct pronunciation
# # """

# # import os
# # import json
# # import shutil
# # import soundfile as sf
# # from datetime import datetime
# # from pathlib import Path

# # import torch
# # import torchaudio
# # import librosa
# # import numpy as np
# # import matplotlib
# # matplotlib.use("Agg")
# # import matplotlib.pyplot as plt
# # import parselmouth
# # from parselmouth.praat import call
# # from scipy.signal import butter, filtfilt, resample
# # from TTS.api import TTS

# # # ─────────────────────────────────────────────────────────────
# # # PATHS
# # # ─────────────────────────────────────────────────────────────
# # INPUT_JSON    = "work/translated_segments_step3.json"
# # CONFIG_PATH   = "work/speaker_config.json"
# # OUTPUT_DIR    = "work/generated_audio"
# # WAVEFORM_DIR  = "work/waveform_comparisons"
# # CROPPED_DIR   = "work/cropped_segments"
# # DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

# # MIN_RATIO = 0.90
# # MAX_RATIO = 1.10

# # EMOTION_LOUDNESS = {
# #     "angry": -14, "ang": -14,
# #     "surprised": -15, "sur": -15,
# #     "fearful": -15, "fea": -15,
# #     "happy": -16, "hap": -16,
# #     "neutral": -18, "neu": -18,
# #     "sad": -22,
# #     "disgusted": -17, "dis": -17,
# #     "unknown": -18,
# # }

# # AGE_PRESETS = {
# #     "adult":       None,
# #     "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
# #     "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
# #     "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
# #     "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
# #     "robot":       "robot",
# # }

# # # ADD THIS CONFIG AND FUNCTION:
# # TONE_CONFIG = {
# #     "ecchi":    {"tag": "[moaning][panting]", "pitch": 0,   "lpf": 4500},
# #     "horny":    {"tag": "[moaning][panting]", "pitch": -2,  "lpf": None},
# #     "soft":     {"tag": "[whisper][low voice]", "pitch": 0, "lpf": 3500},
# #     "sexy":     {"tag": "[seductive][whisper]", "pitch": -1, "lpf": None},
# #     "calm":     {"tag": "[calm]",            "pitch": 0,    "lpf": 4000},
# #     "hard":     {"tag": "[shouting][angry]", "pitch": 2,    "lpf": None},
# #     "kid":      {"tag": "[bright]",          "pitch": 12,   "lpf": None}, 
# #     "inner_thought": {"tag": "[whisper]",    "pitch": 0,    "lpf": 3000}
# # }

# # def apply_inner_thought_reverb(y, sr, wet=0.15):
# #     """Simulates a tight 'plate' reverb for internal monologue."""
# #     delay_samples = int(0.03 * sr)
# #     reverb = np.zeros_like(y)
# #     reverb[delay_samples:] = y[:-delay_samples] * 0.4
# #     return np.clip(y * (1 - wet) + reverb * wet, -0.95, 0.95)

# # os.makedirs(OUTPUT_DIR,   exist_ok=True)
# # os.makedirs(WAVEFORM_DIR, exist_ok=True)

# # # ─────────────────────────────────────────────────────────────
# # # LOAD SPEAKER CONFIG
# # # ─────────────────────────────────────────────────────────────
# # def load_speaker_config():
# #     if not os.path.exists(CONFIG_PATH):
# #         print(f"WARNING: {CONFIG_PATH} not found — run step4_setup.py first")
# #         return {
# #             "options":       {"emotion_enabled": True, "age_enabled": True, "use_knnvc": False},
# #             "speakers":      {},
# #             "language_mode": "english",
# #             "tts_language":  "en",
# #             "text_field":    "english",
# #         }
# #     with open(CONFIG_PATH, "r", encoding="utf-8") as f:
# #         cfg = json.load(f)
# #     print(f"Config: {CONFIG_PATH}  [{cfg.get('generated_at','')}]")
# #     opts = cfg.get("options", {})
# #     print(f"  Language  : {cfg.get('language_mode','english')}")
# #     print(f"  TTS code  : {cfg.get('tts_language','en')}")
# #     print(f"  Text field: {cfg.get('text_field','english')}")
# #     print(f"  Emotion   : {'ON' if opts.get('emotion_enabled') else 'OFF'}")
# #     print(f"  Age/type  : {'ON' if opts.get('age_enabled') else 'OFF'}")
# #     for spk, d in sorted(cfg.get("speakers", {}).items()):
# #         v = d.get("voice_display", os.path.basename(d.get("voice_sample","?")))
# #         print(f"  {spk:<14} -> {v}  [{d.get('age_category','adult')}]")
# #     return cfg


# # print("=" * 60)
# # print("STEP 4: Voice Generation Pipeline")
# # print("=" * 60)

# # _cfg            = load_speaker_config()
# # SPEAKER_MAP     = _cfg.get("speakers", {})
# # EMOTION_ENABLED = _cfg["options"].get("emotion_enabled", True)
# # AGE_ENABLED     = _cfg["options"].get("age_enabled",     True)
# # USE_KNNVC       = _cfg["options"].get("use_knnvc",       False)

# # LANGUAGE_MODE = _cfg.get("language_mode", "english")
# # TTS_LANGUAGE  = _cfg.get("tts_language",  "en")
# # TEXT_FIELD    = _cfg.get("text_field",    "english")

# # # Tamil path uses MMS + kNN-VC instead of XTTS
# # IS_TAMIL = LANGUAGE_MODE in ("tamil", "tanglish")

# # print(f"\nLanguage : {LANGUAGE_MODE}  |  TTS path: {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'}")

# # # ─────────────────────────────────────────────────────────────
# # # LOAD MODELS
# # # ─────────────────────────────────────────────────────────────
# # device = "cuda" if torch.cuda.is_available() else "cpu"
# # print(f"\nLoading models on {device}...")

# # # ── XTTS-v2 (always loaded — used for English, and as fallback) ──
# # tts_xtts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
# #                gpu=(device == "cuda"))
# # print("XTTS-v2 loaded")

# # # ── MMS-TTS Tamil (loaded only when Tamil/Tanglish mode) ────────
# # mms_model     = None
# # mms_tokenizer = None
# # if IS_TAMIL:
# #     print("Loading facebook/mms-tts-tam...")
# #     try:
# #         from transformers import VitsModel, AutoTokenizer
# #         mms_model     = VitsModel.from_pretrained("facebook/mms-tts-tam").to(device)
# #         mms_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tam")
# #         mms_model.eval()
# #         print(f"MMS-TTS Tamil loaded  (SR={mms_model.config.sampling_rate})")
# #     except Exception as e:
# #         print(f"WARNING: MMS-TTS Tamil failed to load: {e}")
# #         print("         Tamil segments will use XTTS-v2 with language=hi as fallback")

# # # ── kNN-VC (loaded when Tamil mode AND package available) ────────
# # knnvc_model = None
# # if IS_TAMIL:
# #     print("Loading kNN-VC (bshall/knn-vc)...")
# #     knnvc_model = None
# #     try:
# #         knnvc_model = torch.hub.load(
# #             "bshall/knn-vc", "knn_vc",
# #             prematched=True,
# #             trust_repo=True,
# #             pretrained=True,
# #         )
# #         print("kNN-VC loaded (torch.hub)")
# #     except Exception as e:
# #         print(f"WARNING: kNN-VC failed to load: {e}")
# #         print("         Tamil will use MMS fixed voice without speaker conversion")

# #     # try:
# #     #     from knnvc import KNN_VC
# #     #     knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
# #     #     print("kNN-VC loaded")
# #     # except ImportError:
# #     #     print("WARNING: kNN-VC not installed")
# #     #     print("         Tamil voice will use MMS fixed voice (no speaker cloning)")
# #     #     print("         Install with: pip install knnvc")
# #     # except Exception as e:
# #     #     print(f"WARNING: kNN-VC load failed: {e}")
# # elif USE_KNNVC:
# #     try:
# #         from knnvc import KNN_VC
# #         knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
# #         print("kNN-VC loaded (for age conversion)")
# #     except ImportError:
# #         print("WARNING: kNN-VC not installed — falling back to DSP for age conversion")
# #         USE_KNNVC = False

# # # ─────────────────────────────────────────────────────────────
# # # LOAD SEGMENTS
# # # ─────────────────────────────────────────────────────────────
# # with open(INPUT_JSON, "r", encoding="utf-8") as f:
# #     data = json.load(f)
# # segments = data["segments"]
# # print(f"Loaded {len(segments)} segments\n")

# # # ─────────────────────────────────────────────────────────────
# # # HELPERS
# # # ─────────────────────────────────────────────────────────────
# # def trim_silence(y, sr, top_db=35):
# #     _, idx = librosa.effects.trim(y, top_db=top_db,
# #                                    frame_length=512, hop_length=128)
# #     lead  = max(0, idx[0] - int(0.02 * sr))
# #     trail = min(len(y), idx[1] + int(0.03 * sr))
# #     return y[lead:trail]

# # def rms_normalise(y, target_dbfs=-18.0):
# #     rms = np.sqrt(np.mean(y ** 2))
# #     if rms < 1e-6: return y
# #     return np.clip(y * (10 ** (target_dbfs / 20.0) / rms), -0.95, 0.95)

# # def pad_or_trim(y, sr, target_dur):
# #     n = int(target_dur * sr)
# #     if len(y) < n: return np.pad(y, (0, n - len(y)))
# #     return y[:n]

# # def butter_filter(y, sr, cutoff, btype, order=4):
# #     b, a = butter(order, min(cutoff / (sr / 2.0), 0.99), btype=btype)
# #     return filtfilt(b, a, y)

# # # ─────────────────────────────────────────────────────────────
# # # STAGE 1 HELPERS — TTS generation
# # # ─────────────────────────────────────────────────────────────

# # # Cache kNN-VC matching sets per voice sample path
# # # so we don't recompute for every segment
# # _knnvc_matching_cache: dict = {}

# # def generate_english_xtts(text, voice_sample, out_path):
# #     """XTTS-v2 voice cloning for English."""
# #     tts_xtts.tts_to_file(
# #         text=text,
# #         speaker_wav=voice_sample,
# #         language="en",
# #         file_path=out_path,
# #     )


# # def generate_tamil_mms(text, out_path):
# #     """
# #     Step 1 of Tamil generation: MMS-TTS Tamil.
# #     Produces correct Tamil phonemes in the model's fixed voice.
# #     Output is resampled to 22050 Hz to match the rest of the pipeline.
# #     """
# #     if mms_model is None or mms_tokenizer is None:
# #         raise RuntimeError("MMS-TTS Tamil model not loaded")

# #     inputs = mms_tokenizer(text, return_tensors="pt")
# #     inputs = {k: v.to(device) for k, v in inputs.items()}

# #     with torch.no_grad():
# #         output = mms_model(**inputs)

# #     wav    = output.waveform[0].cpu()           # shape (1, samples) or (samples,)
# #     mms_sr = mms_model.config.sampling_rate     # typically 16000

# #     # Save at native MMS sample rate first
# #     tmp_path = out_path.replace(".wav", "_mms_raw.wav")
# #     if wav.dim() == 1:
# #         wav = wav.unsqueeze(0)                  # ensure (1, samples)
# #     torchaudio.save(tmp_path, wav, mms_sr)

# #     # Resample to 22050 to match XTTS pipeline SR
# #     y, _  = librosa.load(tmp_path, sr=22050, mono=True)
# #     sf.write(out_path, y, 22050)

# #     # Clean up temp file
# #     if os.path.exists(tmp_path):
# #         os.remove(tmp_path)

# #     return out_path


# # def apply_knnvc_voice_conversion(mms_path, voice_sample, out_path, topk=4):
# #     """
# #     Step 2 of Tamil generation: kNN-VC voice conversion.
# #     Shifts the MMS voice toward the speaker's reference sample.

# #     topk: lower = closer to reference voice identity
# #            higher = more natural prosody but less speaker identity
# #            4 is a good balance
# #     """
# #     if knnvc_model is None:
# #         # kNN-VC not available — just copy MMS output as-is
# #         shutil.copy(mms_path, out_path)
# #         return out_path, "mms_only"

# #     try:
# #         # Build matching set from voice sample
# #         # Cache it so we don't recompute for every segment
# #         if voice_sample not in _knnvc_matching_cache:
# #             print(f"       kNN-VC: building matching set for {os.path.basename(voice_sample)}...")
# #             # _knnvc_matching_cache[voice_sample] = knnvc_model.get_matching_set([voice_sample])
# #             ref_16k = voice_sample.replace(".wav", "_16k.wav").replace(".mp3", "_16k.wav")
# #             y_ref, _ = librosa.load(voice_sample, sr=16000, mono=True)
# #             sf.write(ref_16k, y_ref, 16000)
# #             _knnvc_matching_cache[voice_sample] = knnvc_model.get_matching_set([ref_16k])
# #         matching_set = _knnvc_matching_cache[voice_sample]

# #         # Convert MMS voice → target speaker voice
# #         # query_seq = knnvc_model.get_features(mms_path)
# #         src_16k = mms_path.replace(".wav", "_16k.wav")
# #         y_src, _ = librosa.load(mms_path, sr=16000, mono=True)
# #         sf.write(src_16k, y_src, 16000)
# #         query_seq = knnvc_model.get_features(src_16k)

# #         # out_wav   = knnvc_model.match(query_seq, matching_set, topk=topk)

# #         # # kNN-VC outputs at 16000 Hz
# #         # torchaudio.save(out_path, out_wav, 16000)
# #         out_wav = knnvc_model.match(query_seq, matching_set, topk=topk)
# #         # out_wav is (T,) tensor — must unsqueeze to (1, T) for torchaudio
# #         torchaudio.save(out_path, out_wav.unsqueeze(0).cpu(), 16000)

# #         # Resample to 22050 to match pipeline
# #         y, _ = librosa.load(out_path, sr=22050, mono=True)
# #         sf.write(out_path, y, 22050)

# #         return out_path, "mms+knnvc"

# #     except Exception as e:
# #         print(f"       WARNING: kNN-VC conversion failed: {e}")
# #         print("       Falling back to MMS output without voice conversion")
# #         shutil.copy(mms_path, out_path)
# #         return out_path, "mms_only_fallback"


# # def generate_stage1(text, voice_sample, raw_path, is_tamil):
# #     """
# #     Route to correct TTS backend based on language mode.
# #     Returns (output_path, method_used)
# #     """
# #     if not is_tamil:
# #         # English path — XTTS-v2 with full voice cloning
# #         generate_english_xtts(text, voice_sample, raw_path)
# #         return raw_path, "xtts"

# #     # Tamil/Tanglish path — MMS + kNN-VC
# #     mms_path = raw_path.replace(".wav", "_mms.wav")

# #     try:
# #         generate_tamil_mms(text, mms_path)
# #         print(f"       MMS-TTS: generated {os.path.basename(mms_path)}")
# #     except Exception as e:
# #         print(f"       WARNING: MMS-TTS failed: {e}")
# #         print("       Falling back to XTTS-v2 with language=hi")
# #         tts_xtts.tts_to_file(
# #             text=text,
# #             speaker_wav=voice_sample,
# #             language="hi",           # Hindi — closest Indic language XTTS supports
# #             file_path=raw_path,
# #         )
# #         return raw_path, "xtts_hi_fallback"

# #     # Apply kNN-VC voice conversion
# #     final_path, method = apply_knnvc_voice_conversion(
# #         mms_path, voice_sample, raw_path, topk=4
# #     )

# #     # Clean up intermediate MMS file
# #     if os.path.exists(mms_path) and mms_path != raw_path:
# #         os.remove(mms_path)

# #     return final_path, method

# # # ─────────────────────────────────────────────────────────────
# # # WAVEFORM COMPARISON PLOT
# # # ─────────────────────────────────────────────────────────────
# # def save_waveform_comparison(jp_path, en_y, en_sr, target_dur,
# #                               seg_id, speaker, emotion, stretch_ratio, method):
# #     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
# #     fig.patch.set_facecolor("#1a1a2e")

# #     def style(ax):
# #         ax.set_facecolor("#16213e")
# #         ax.spines[:].set_color("#444")
# #         ax.tick_params(colors="#aaa", labelsize=8)

# #     if jp_path and os.path.exists(jp_path):
# #         y_jp, sr_jp = librosa.load(jp_path, sr=None, mono=True)
# #         ax1.plot(np.linspace(0, len(y_jp)/sr_jp, len(y_jp)),
# #                  y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
# #     else:
# #         ax1.text(0.5, 0.5, "JP source not found",
# #                  transform=ax1.transAxes, ha="center", color="#888", fontsize=9)
# #     style(ax1)
# #     ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
# #     ax1.set_title(
# #         f"Seg {seg_id:03d} | {speaker} | {emotion} | "
# #         f"stretch {stretch_ratio:.3f}x | {LANGUAGE_MODE} [{method}]",
# #         color="#ddd", fontsize=10, pad=5)

# #     ax2.plot(np.linspace(0, len(en_y)/en_sr, len(en_y)),
# #              en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
# #     style(ax2)
# #     ax2.set_ylabel(f"Generated [{LANGUAGE_MODE}]", color="#aaa", fontsize=9)
# #     ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

# #     for ax in (ax1, ax2):
# #         ax.axvline(x=target_dur, color="#E24B4A", linewidth=1.2,
# #                    linestyle="--", alpha=0.8, label=f"target {target_dur:.2f}s")
# #         ax.legend(fontsize=8, facecolor="#222", labelcolor="#ccc",
# #                   edgecolor="#444", loc="upper right")

# #     plt.tight_layout(pad=1.5)
# #     out = os.path.join(WAVEFORM_DIR, f"comparison_{seg_id:03d}.png")
# #     plt.savefig(out, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
# #     plt.close(fig)
# #     return out

# # # ─────────────────────────────────────────────────────────────
# # # UNDERSTANDABILITY CHECK
# # # ─────────────────────────────────────────────────────────────
# # def check_understandability(y, sr, stretch_ratio):
# #     flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
# #     zcr_var  = float(np.var(librosa.feature.zero_crossing_rate(y)))
# #     ok = True; reason = "ok"
# #     if abs(stretch_ratio - 1.0) > 0.08 and flatness > 0.20:
# #         ok = False; reason = f"spectral_smearing ({flatness:.3f})"
# #     if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
# #         ok = False; reason = f"robotic_periodicity ({zcr_var:.2e})"
# #     return {"quality_ok": ok, "reason": reason,
# #             "spectral_flatness": round(flatness, 4),
# #             "zcr_variance": round(zcr_var, 8)}

# # # ─────────────────────────────────────────────────────────────
# # # AGE / TYPE TRANSFORMATION
# # # ─────────────────────────────────────────────────────────────
# # def apply_age_transform(audio_path, out_path, age_category, knnvc_ref=None):
# #     if age_category == "adult" or age_category is None:
# #         shutil.copy(audio_path, out_path)
# #         return out_path
# #     preset = AGE_PRESETS.get(age_category)
# #     if preset is None:
# #         shutil.copy(audio_path, out_path)
# #         return out_path

# #     # kNN-VC for age conversion (separate from Tamil voice conversion)
# #     if USE_KNNVC and knnvc_model and knnvc_ref and os.path.exists(knnvc_ref):
# #         try:
# #             if knnvc_ref not in _knnvc_matching_cache:
# #                 _knnvc_matching_cache[knnvc_ref] = knnvc_model.get_matching_set([knnvc_ref])
# #             matching = _knnvc_matching_cache[knnvc_ref]
# #             query    = knnvc_model.get_features(audio_path)
# #             out_wav  = knnvc_model.match(query, matching, topk=4)
# #             torchaudio.save(out_path, out_wav, 16000)
# #             return out_path
# #         except Exception as e:
# #             print(f"       kNN-VC age transform failed ({e}) — using DSP")

# #     if preset == "robot":
# #         return _apply_robot(audio_path, out_path)

# #     sound = parselmouth.Sound(audio_path)
# #     transformed = call(sound, "Change gender", 75, 600,
# #                        preset["formant_factor"], 0,
# #                        preset["pitch_factor"], preset["rate_factor"])

# #     jitter = preset.get("jitter", 0.0)
# #     if jitter > 0:
# #         y_a  = transformed.as_array().flatten()
# #         sr_p = int(transformed.sampling_frequency)
# #         y_a += np.random.normal(0, jitter, len(y_a)) * np.abs(y_a)
# #         transformed = parselmouth.Sound(y_a, sr_p)

# #     breathiness = preset.get("breathiness", 0.0)
# #     if breathiness > 0:
# #         y_a  = transformed.as_array().flatten()
# #         sr_p = int(transformed.sampling_frequency)
# #         noise  = np.random.normal(0, 0.015, len(y_a))
# #         b, a   = butter(4, 2000/(sr_p/2), btype="high")
# #         breath = filtfilt(b, a, noise)
# #         b2, a2 = butter(2, 4500/(sr_p/2), btype="low")
# #         y_a    = filtfilt(b2, a2, y_a)
# #         y_a    = np.clip(y_a*(1-breathiness) + breath*breathiness, -0.95, 0.95)
# #         transformed = parselmouth.Sound(y_a, sr_p)

# #     transformed.save(out_path, "WAV")
# #     return out_path

# # def _apply_robot(audio_path, out_path):
# #     sound   = parselmouth.Sound(audio_path)
# #     sr_p    = int(sound.sampling_frequency)
# #     y       = sound.as_array().flatten()
# #     pitch   = call(sound, "To Pitch", 0.01, 75, 600)
# #     f0_vals = [call(pitch, "Get value at time", t, "Hertz", "Linear")
# #                for t in np.arange(0, sound.duration, 0.01)]
# #     f0_ok   = [v for v in f0_vals if not np.isnan(v) and v > 0]
# #     mean_f0 = float(np.mean(f0_ok)) if f0_ok else 150.0
# #     t_arr   = np.arange(len(y)) / sr_p
# #     buzz    = (2*(t_arr*mean_f0 % 1) - 1) * 0.5 * np.std(y)
# #     sf.write(out_path, np.clip(buzz*0.7 + y*0.3, -0.95, 0.95), sr_p)
# #     return out_path

# # # ─────────────────────────────────────────────────────────────
# # # MAIN LOOP
# # # ─────────────────────────────────────────────────────────────
# # generated_clips = []
# # qc_flags_all    = []

# # for i, seg in enumerate(segments):
# #     sid          = seg["segment_id"]
# #     speaker      = seg["speaker"]
# #     target_dur   = float(seg["duration"])
# #     emotion      = seg.get("emotion", "neutral").lower()
# #     emotion_conf = float(seg.get("emotion_confidence", 1.0))

# #     # Read dub text from the correct field
# #     dub_text = (seg.get(TEXT_FIELD)
# #                 or seg.get("english")
# #                 or seg.get("tamil", ""))

# #     if not dub_text:
# #         print(f"\n  WARNING: No dub text for seg {sid:03d} — skipping")
# #         continue

# #     print(f"\n{'─'*55}")
# #     print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | {target_dur:.2f}s")
# #     print(f"  [{LANGUAGE_MODE}] : {dub_text}")
# #     print(f"  emotion : {emotion}  (conf {emotion_conf:.2f})")

# #     spk_info     = SPEAKER_MAP.get(speaker, {})
# #     voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
# #     age_category = spk_info.get("age_category", "adult")
# #     knnvc_ref    = spk_info.get("knnvc_ref", None)

# #     if not os.path.exists(voice_sample):
# #         print(f"  WARNING: voice not found: {voice_sample} — using default")
# #         voice_sample = DEFAULT_VOICE
# #     print(f"  voice   : {os.path.basename(voice_sample)}  | age: {age_category}")

# #     qc_flags   = []
# #     raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
# #     align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
# #     emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
# #     age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
# #     final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")
# # # ADD THIS BEFORE STAGE 1:
# #     tone_cat = spk_info.get("tone_category", "neutral")
# #     t_cfg = TONE_CONFIG.get(tone_cat, {"tag": "", "pitch": 0, "lpf": None})
    
# #     # if t_cfg["tag"]:
# #     #     dub_text = f"{t_cfg['tag']} {dub_text}"

# #     # Existing STAGE 1 generation code follows...
# #     # print(f"  [1] {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'} generation...")
# #     # ── STAGE 1: TTS GENERATION ──────────────────────────────
# #     # English  → XTTS-v2 (full voice cloning)
# #     # Tamil    → MMS-TTS Tamil → kNN-VC voice conversion
# #     print(f"  [1] {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'} generation...")

# #     _, tts_method = generate_stage1(dub_text, voice_sample, raw_path, IS_TAMIL)
# #     print(f"       method: {tts_method}")

# #     y_raw, sr = librosa.load(raw_path, sr=22050)
# #     y_raw     = trim_silence(y_raw, sr)
# #     raw_dur   = len(y_raw) / sr
# #     print(f"       raw: {raw_dur:.3f}s  target: {target_dur:.3f}s")

# #     # ── STAGE 2: TIMING ALIGNMENT ────────────────────────────
# #     print("  [2] Timing alignment...")
# #     ratio          = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))
# #     target_samples = int(len(y_raw) / ratio)
# #     y_aligned      = resample(y_raw, target_samples)
# #     y_aligned      = pad_or_trim(y_aligned, sr, target_dur)
# #     print(f"       ratio: {ratio:.3f}x  aligned: {len(y_aligned)/sr:.3f}s")

# #     if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
# #         qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
# #         print(f"       WARNING: HIGH_STRETCH")

# #     sf.write(align_path, y_aligned, sr)

# #     quality = check_understandability(y_aligned, sr, ratio)
# #     print(f"       quality: {quality['reason']}")
# #     if not quality["quality_ok"]:
# #         qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

# #     jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
# #     wf_path = save_waveform_comparison(
# #         jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
# #         target_dur=target_dur, seg_id=sid,
# #         speaker=speaker, emotion=emotion,
# #         stretch_ratio=ratio, method=tts_method)
# #     print(f"       waveform: {wf_path}")

# #     # ── STAGE 3: EMOTION FINE-TUNING ─────────────────────────
# #     if EMOTION_ENABLED:
# #         eff_emotion = emotion if emotion_conf >= 0.30 else "neutral"
# #         print(f"  [3] Emotion: {eff_emotion}" +
# #               (" (low-conf override)" if eff_emotion != emotion else ""))
        
# #         target_dbfs = EMOTION_LOUDNESS.get(eff_emotion, -18)
# #         y_emotion   = rms_normalise(y_aligned, target_dbfs)

# #         # ADD THIS TONE-SPECIFIC DSP SECTION:
# #         if t_cfg["lpf"]:
# #             # Create muffled effect for 'soft' or 'inner thought' (bone conduction) [11, 4]
# #             y_emotion = butter_filter(y_emotion, sr, t_cfg["lpf"], "low")
            
# #         if tone_cat == "inner_thought":
# #             # Apply spatial reverb for the 'inside the head' feel
# #             y_emotion = apply_inner_thought_reverb(y_emotion, sr, wet=0.20)
            
# #         if t_cfg["pitch"]!= 0:
# #             # Shift pitch (e.g., +12 for Kid, -2 for Horny)
# #             y_emotion = librosa.effects.pitch_shift(y_emotion, sr=sr, n_steps=t_cfg["pitch"])
# #         if eff_emotion in ("sad",):
# #             y_emotion = butter_filter(y_emotion, sr, 3500, "low")
# #         elif eff_emotion in ("angry", "ang"):
# #             y_emotion = butter_filter(y_emotion, sr, 150, "high")
# #             y_hf      = butter_filter(y_emotion, sr, 3000, "high")
# #             y_emotion = np.clip(y_emotion + 0.15*y_hf, -0.95, 0.95)
# #         elif eff_emotion in ("happy", "hap"):
# #             y_hf      = butter_filter(y_emotion, sr, 4000, "high")
# #             y_emotion = np.clip(y_emotion + 0.10*y_hf, -0.95, 0.95)
# #         elif eff_emotion in ("fearful", "fea", "surprised", "sur"):
# #             noise     = np.random.normal(0, 0.008, len(y_emotion))
# #             breath    = butter_filter(noise, sr, 3000, "high")
# #             y_emotion = np.clip(y_emotion + breath*0.12, -0.95, 0.95)
# #     else:
# #         print("  [3] Emotion: DISABLED")
# #         y_emotion   = y_aligned
# #         eff_emotion = "disabled"
# #     sf.write(emot_path, y_emotion, sr)

# #     # ── STAGE 4: AGE / TYPE TRANSFORMATION ───────────────────
# #     if AGE_ENABLED and age_category != "adult":
# #         method_age = "kNN-VC" if (USE_KNNVC and knnvc_ref) else "DSP"
# #         print(f"  [4] Age: {age_category}  [{method_age}]")
# #         apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
# #         y_final, sr_f = librosa.load(age_path, sr=None)
# #         y_final = pad_or_trim(y_final, sr_f, target_dur)
# #         sf.write(age_path, y_final, sr_f)
# #         sr_final = sr_f
# #     else:
# #         label = "DISABLED" if not AGE_ENABLED else "adult/pass-through"
# #         print(f"  [4] Age: {label}")
# #         y_final  = y_emotion
# #         sr_final = sr

# #     sf.write(final_path, y_final, sr_final)
# #     dur_final = len(y_final) / sr_final
# #     if dur_final < 0.15:
# #         qc_flags.append("TOO_SHORT")

# #     # ── METADATA ─────────────────────────────────────────────
# #     clip_meta = {
# #         "segment_id":           sid,
# #         "speaker":              speaker,
# #         "start":                seg["start"],
# #         "end":                  seg["end"],
# #         "duration_target":      round(target_dur, 4),
# #         "duration_raw_trimmed": round(raw_dur, 4),
# #         "duration_final":       round(dur_final, 4),
# #         "stretch_ratio":        round(ratio, 4),
# #         "voice_sample":         os.path.basename(voice_sample),
# #         "language_mode":        LANGUAGE_MODE,
# #         "tts_method":           tts_method,
# #         "text":                 dub_text,
# #         "emotion":              emotion,
# #         "emotion_effective":    eff_emotion if EMOTION_ENABLED else "disabled",
# #         "emotion_confidence":   round(emotion_conf, 4),
# #         "emotion_enabled":      EMOTION_ENABLED,
# #         "age_category":         age_category,
# #         "age_enabled":          AGE_ENABLED,
# #         "quality_check":        quality,
# #         "qc_flags":             qc_flags,
# #         "waveform_plot":        wf_path,
# #         "files": {
# #             "raw":     raw_path,
# #             "aligned": align_path,
# #             "emotion": emot_path,
# #             "age":     age_path if (AGE_ENABLED and age_category != "adult") else None,
# #             "final":   final_path,
# #         },
# #     }
# #     generated_clips.append(clip_meta)
# #     if qc_flags:
# #         qc_flags_all.append((sid, qc_flags))

# #     status = "WARN" if qc_flags else "OK"
# #     print(f"  [{status}] Seg {sid:03d} -> {final_path}")

# # # ─────────────────────────────────────────────────────────────
# # # SAVE METADATA
# # # ─────────────────────────────────────────────────────────────
# # meta = {
# #     "timestamp":       datetime.now().isoformat(),
# #     "total_clips":     len(generated_clips),
# #     "language_mode":   LANGUAGE_MODE,
# #     "tts_language":    TTS_LANGUAGE,
# #     "emotion_enabled": EMOTION_ENABLED,
# #     "age_enabled":     AGE_ENABLED,
# #     "clips":           generated_clips,
# # }
# # meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
# # with open(meta_path, "w", encoding="utf-8") as f:
# #     json.dump(meta, f, indent=2, ensure_ascii=False)

# # print(f"\n{'='*60}")
# # print(f"STEP 4 COMPLETE -- {len(generated_clips)} clips  [{LANGUAGE_MODE}]")
# # print(f"Audio    : {OUTPUT_DIR}/")
# # print(f"Metadata : {meta_path}")
# # print(f"Waveforms: {WAVEFORM_DIR}/")
# # if qc_flags_all:
# #     print(f"\nQC FLAGS ({len(qc_flags_all)} segments):")
# #     for sid, flags in sorted(qc_flags_all):
# #         print(f"  [seg {sid:03d}] {flags}")
# # else:
# #     print("\nAll segments passed QC")
# # print("\nNext -> step5_assembly.py")
# import os
# import json
# import shutil
# import soundfile as sf
# from datetime import datetime
# from pathlib import Path

# import torch
# import torchaudio
# import librosa
# import numpy as np
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# import parselmouth
# from parselmouth.praat import call
# from scipy.signal import butter, filtfilt, resample
# from TTS.api import TTS
# import pyrubberband as rb

# # ─────────────────────────────────────────────────────────────
# # PATHS
# # ─────────────────────────────────────────────────────────────
# INPUT_JSON    = "work/translated_segments_step3.json"
# CONFIG_PATH   = "work/speaker_config.json"
# OUTPUT_DIR    = "work/generated_audio"
# WAVEFORM_DIR  = "work/waveform_comparisons"
# CROPPED_DIR   = "work/cropped_segments"
# DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

# MIN_RATIO = 0.90
# MAX_RATIO = 1.10

# # ── Lowered by ~6 dB across the board to match JP RMS levels ──
# EMOTION_LOUDNESS = {
#     "angry":     -20, "ang": -20,
#     "surprised": -21, "sur": -21,
#     "fearful":   -21, "fea": -21,
#     "happy":     -22, "hap": -22,
#     "neutral":   -24, "neu": -24,
#     "sad":       -28,
#     "disgusted": -23, "dis": -23,
#     "unknown":   -24,
# }

# AGE_PRESETS = {
#     "adult":       None,
#     "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
#     "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
#     "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
#     "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
#     "robot":       "robot",
# }

# # ── Tone config — tags removed, DSP only ──
# # pitch values increased for sexy/horny to be actually audible
# TONE_CONFIG = {
#     "neutral":      {"pitch": 0,   "lpf": None},
#     "ecchi":        {"pitch": -1,  "lpf": 4500},   # breathiness added in DSP block
#     "horny":        {"pitch": -4,  "lpf": None},   # was -2, now audible
#     "soft":         {"pitch": 0,   "lpf": 3500},
#     "sexy":         {"pitch": -3,  "lpf": None},   # was -1, now audible
#     "calm":         {"pitch": 0,   "lpf": 4000},
#     "hard":         {"pitch": 2,   "lpf": None},
#     "kid":          {"pitch": 12,  "lpf": None},
#     "inner_thought":{"pitch": 0,   "lpf": 3000},
# }


# # ─────────────────────────────────────────────────────────────
# # DTYPE HELPER — fixes numpy float32 / numba ufunc crash
# # Always call this before any librosa.effects.pitch_shift or
# # librosa.effects.time_stretch call.
# # ─────────────────────────────────────────────────────────────
# def to_f64(y: np.ndarray) -> np.ndarray:
#     """Cast audio array to float64 for librosa DSP ops."""
#     return y.astype(np.float64)

# def to_f32(y: np.ndarray) -> np.ndarray:
#     """Cast back to float32 after DSP (matches pipeline dtype)."""
#     return y.astype(np.float32)

# # def safe_pitch_shift(y: np.ndarray, sr: int, n_steps: float) -> np.ndarray:
# #     """pitch_shift with float64 cast to avoid numba ufunc error."""
# #     return to_f32(librosa.effects.pitch_shift(to_f64(y), sr=sr, n_steps=n_steps))
# def safe_pitch_shift(y: np.ndarray, sr: int, n_steps: float) -> np.ndarray:
#     """
#     Pitch shift using Parselmouth/Praat instead of librosa.
#     Avoids the numba _phasor_angles ufunc crash entirely.
#     n_steps: semitones (positive = higher, negative = lower)
#     """
#     try:
#         # Write to temp, process with Praat, read back
#         tmp_in  = "work/_ps_in.wav"
#         tmp_out = "work/_ps_out.wav"
#         sf.write(tmp_in, y.astype(np.float32), sr)

#         sound    = parselmouth.Sound(tmp_in)
#         # Convert semitones to frequency ratio
#         factor   = 2.0 ** (n_steps / 12.0)
#         # Praat "Change gender": formant_shift=1.0 keeps timbre, only pitch changes
#         shifted  = call(sound, "Change gender",
#                         75, 600,          # pitch floor / ceiling (Hz)
#                         1.0,              # formant shift ratio — 1.0 = no timbre change
#                         0.0,              # new pitch median — 0.0 = keep original
#                         factor,           # pitch range ratio = semitone shift
#                         1.0)              # duration factor
#         shifted.save(tmp_out, "WAV")

#         y_out, _ = librosa.load(tmp_out, sr=sr, mono=True)

#         # Clean up
#         for p in (tmp_in, tmp_out):
#             if os.path.exists(p):
#                 os.remove(p)

#         return y_out.astype(np.float32)

#     except Exception as e:
#         print(f"       WARNING: pitch_shift failed ({e}) — returning dry signal")
#         return y.astype(np.float32)
# # def safe_time_stretch(y: np.ndarray, rate: float) -> np.ndarray:
# #     """time_stretch with float64 cast to avoid numba ufunc error."""
# #     return to_f32(librosa.effects.time_stretch(to_f64(y), rate=rate))
# def safe_time_stretch(y: np.ndarray, rate: float) -> np.ndarray:
#     """
#     Time stretch using scipy resample instead of librosa.
#     Avoids numba dependency entirely.
#     rate > 1.0 = faster, rate < 1.0 = slower (same as librosa convention)
#     """
#     try:
#         target_len = int(len(y) / rate)
#         return resample(y.astype(np.float32), target_len)
#     except Exception as e:
#         print(f"       WARNING: time_stretch failed ({e}) — returning dry signal")
#         return y.astype(np.float32)

# def apply_inner_thought_reverb(y: np.ndarray, sr: int, wet: float = 0.15) -> np.ndarray:
#     """Tight plate reverb for internal monologue."""
#     delay_samples = int(0.03 * sr)
#     reverb = np.zeros_like(y)
#     reverb[delay_samples:] = y[:-delay_samples] * 0.4
#     return np.clip(y * (1 - wet) + reverb * wet, -0.95, 0.95)


# os.makedirs(OUTPUT_DIR,   exist_ok=True)
# os.makedirs(WAVEFORM_DIR, exist_ok=True)

# # ─────────────────────────────────────────────────────────────
# # LOAD SPEAKER CONFIG
# # ─────────────────────────────────────────────────────────────
# def load_speaker_config():
#     if not os.path.exists(CONFIG_PATH):
#         print(f"WARNING: {CONFIG_PATH} not found — run step4_setup.py first")
#         return {
#             "options":       {"emotion_enabled": True, "age_enabled": True, "use_knnvc": False},
#             "speakers":      {},
#             "language_mode": "english",
#             "tts_language":  "en",
#             "text_field":    "english",
#         }
#     with open(CONFIG_PATH, "r", encoding="utf-8") as f:
#         cfg = json.load(f)
#     print(f"Config: {CONFIG_PATH}  [{cfg.get('generated_at','')}]")
#     opts = cfg.get("options", {})
#     print(f"  Language  : {cfg.get('language_mode','english')}")
#     print(f"  TTS code  : {cfg.get('tts_language','en')}")
#     print(f"  Text field: {cfg.get('text_field','english')}")
#     print(f"  Emotion   : {'ON' if opts.get('emotion_enabled') else 'OFF'}")
#     print(f"  Age/type  : {'ON' if opts.get('age_enabled') else 'OFF'}")
#     for spk, d in sorted(cfg.get("speakers", {}).items()):
#         v = d.get("voice_display", os.path.basename(d.get("voice_sample", "?")))
#         print(f"  {spk:<14} -> {v}  [{d.get('age_category','adult')}]")
#     return cfg


# print("=" * 60)
# print("STEP 4: Voice Generation Pipeline")
# print("=" * 60)

# _cfg            = load_speaker_config()
# SPEAKER_MAP     = _cfg.get("speakers", {})
# EMOTION_ENABLED = _cfg["options"].get("emotion_enabled", True)
# AGE_ENABLED     = _cfg["options"].get("age_enabled",     True)
# USE_KNNVC       = _cfg["options"].get("use_knnvc",       False)

# LANGUAGE_MODE = _cfg.get("language_mode", "english")
# TTS_LANGUAGE  = _cfg.get("tts_language",  "en")
# TEXT_FIELD    = _cfg.get("text_field",    "english")

# IS_TAMIL = LANGUAGE_MODE in ("tamil", "tanglish")

# print(f"\nLanguage : {LANGUAGE_MODE}  |  TTS path: {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'}")

# # ─────────────────────────────────────────────────────────────
# # LOAD MODELS
# # ─────────────────────────────────────────────────────────────
# device = "cuda" if torch.cuda.is_available() else "cpu"
# print(f"\nLoading models on {device}...")

# tts_xtts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
#                gpu=(device == "cuda"))
# print("XTTS-v2 loaded")

# mms_model     = None
# mms_tokenizer = None
# if IS_TAMIL:
#     print("Loading facebook/mms-tts-tam...")
#     try:
#         from transformers import VitsModel, AutoTokenizer
#         mms_model     = VitsModel.from_pretrained("facebook/mms-tts-tam").to(device)
#         mms_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tam")
#         mms_model.eval()
#         print(f"MMS-TTS Tamil loaded  (SR={mms_model.config.sampling_rate})")
#     except Exception as e:
#         print(f"WARNING: MMS-TTS Tamil failed to load: {e}")
#         print("         Tamil segments will use XTTS-v2 with language=hi as fallback")

# knnvc_model = None
# if IS_TAMIL:
#     print("Loading kNN-VC (bshall/knn-vc)...")
#     try:
#         knnvc_model = torch.hub.load(
#             "bshall/knn-vc", "knn_vc",
#             prematched=True,
#             trust_repo=True,
#             pretrained=True,
#         )
#         print("kNN-VC loaded (torch.hub)")
#     except Exception as e:
#         print(f"WARNING: kNN-VC failed to load: {e}")
#         print("         Tamil will use MMS fixed voice without speaker conversion")
# elif USE_KNNVC:
#     try:
#         from knnvc import KNN_VC
#         knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
#         print("kNN-VC loaded (for age conversion)")
#     except ImportError:
#         print("WARNING: kNN-VC not installed — falling back to DSP for age conversion")
#         USE_KNNVC = False

# # ─────────────────────────────────────────────────────────────
# # LOAD SEGMENTS
# # ─────────────────────────────────────────────────────────────
# with open(INPUT_JSON, "r", encoding="utf-8") as f:
#     data = json.load(f)
# segments = data["segments"]
# print(f"Loaded {len(segments)} segments\n")
# print("\nPre-computing speaker voice embeddings...")
# for spk_id, spk_info in SPEAKER_MAP.items():
#     vs = spk_info.get("voice_sample", DEFAULT_VOICE)
#     if os.path.exists(vs) and not IS_TAMIL:
#         get_speaker_embeddings(vs, spk_id)
#     elif not os.path.exists(vs):
#         print(f"  WARNING: voice not found for {spk_id}: {vs}")
# print("All embeddings cached ✓\n")

# # ─────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────
# def trim_silence(y, sr, top_db=35):
#     _, idx = librosa.effects.trim(y, top_db=top_db,
#                                    frame_length=512, hop_length=128)
#     lead  = max(0, idx[0] - int(0.02 * sr))
#     trail = min(len(y), idx[1] + int(0.03 * sr))
#     return y[lead:trail]

# def rms_normalise(y, target_dbfs=-24.0):
#     rms = np.sqrt(np.mean(y ** 2))
#     if rms < 1e-6:
#         return y
#     return np.clip(y * (10 ** (target_dbfs / 20.0) / rms), -0.95, 0.95)

# def pad_or_trim(y, sr, target_dur):
#     """
#     Trim or pad audio to target_dur.
#     When padding: fade out the last 50ms of speech so silence feels natural
#     rather than cutting abruptly.
#     """
#     n = int(target_dur * sr)
#     if len(y) >= n:
#         return y[:n]
#     # Fade out last 50ms before padding with silence
#     fade_len = min(int(0.05 * sr), len(y))
#     y = y.copy()
#     y[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
#     return np.pad(y, (0, n - len(y)))

# def butter_filter(y, sr, cutoff, btype, order=4):
#     b, a = butter(order, min(cutoff / (sr / 2.0), 0.99), btype=btype)
#     return filtfilt(b, a, y)

# # ─────────────────────────────────────────────────────────────
# # STAGE 1 HELPERS — TTS generation
# # ─────────────────────────────────────────────────────────────
# _knnvc_matching_cache: dict = {}

# # def generate_english_xtts(text, voice_sample, out_path):
# #     tts_xtts.tts_to_file(
# #         text=text,
# #         speaker_wav=voice_sample,
# #         language="en",
# #         file_path=out_path,
# #     )
# # def generate_english_xtts(text: str, voice_sample: str, out_path: str,
# #                            speaker_id: str = "default"):
# #     """
# #     XTTS-v2 voice cloning with deterministic seed per speaker.
# #     Same speaker_id = same voice every time, regardless of segment order.
# #     """
# #     # Derive a stable integer seed from the speaker name
# #     seed = abs(hash(speaker_id)) % (2**31)
# #     torch.manual_seed(seed)
# #     np.random.seed(seed % (2**31))
 
# #     tts_xtts.tts_to_file(
# #         text=text,
# #         speaker_wav=voice_sample,
# #         language="en",
# #         file_path=out_path,
# #     )
# # ─────────────────────────────────────────────────────────────
# # SPEAKER EMBEDDING CACHE — v3 fix for consistent voice
# # Compute gpt_cond_latent + speaker_embedding ONCE per speaker.
# # Reusing the same latent = identical voice every segment.
# # ─────────────────────────────────────────────────────────────
# _embed_cache: dict = {}

# def get_speaker_embeddings(voice_sample: str, speaker_id: str):
#     """Extract XTTS conditioning latents once, cache by speaker_id."""
#     if speaker_id not in _embed_cache:
#         print(f"       Computing voice embeddings for {speaker_id}...")
#         gpt_cond_latent, speaker_embedding = (
#             tts_xtts.synthesizer.tts_model
#             .get_conditioning_latents(audio_path=[voice_sample])
#         )
#         _embed_cache[speaker_id] = (gpt_cond_latent, speaker_embedding)
#         print(f"       Cached embeddings for {speaker_id} ✓")
#     return _embed_cache[speaker_id]


# def generate_english_xtts(text: str, voice_sample: str, out_path: str,
#                            speaker_id: str = "default",
#                            language: str = "en"):
#     """
#     v3: Uses cached conditioning latents — same voice every time.
#     No more per-call speaker_wav re-extraction.
#     """
#     gpt_cond_latent, speaker_embedding = get_speaker_embeddings(voice_sample, speaker_id)

#     out = tts_xtts.synthesizer.tts_model.inference(
#         text=text,
#         language=language,
#         gpt_cond_latent=gpt_cond_latent,
#         speaker_embedding=speaker_embedding,
#         temperature=0.65,
#         length_penalty=1.0,
#         repetition_penalty=10.0,
#         top_k=50,
#         top_p=0.85,
#     )

#     wav = torch.tensor(out["wav"]).unsqueeze(0)
#     torchaudio.save(out_path, wav, tts_xtts.synthesizer.output_sample_rate)

# def generate_tamil_mms(text, out_path):
#     if mms_model is None or mms_tokenizer is None:
#         raise RuntimeError("MMS-TTS Tamil model not loaded")

#     inputs = mms_tokenizer(text, return_tensors="pt")
#     inputs = {k: v.to(device) for k, v in inputs.items()}

#     with torch.no_grad():
#         output = mms_model(**inputs)

#     wav    = output.waveform[0].cpu()
#     mms_sr = mms_model.config.sampling_rate

#     tmp_path = out_path.replace(".wav", "_mms_raw.wav")
#     if wav.dim() == 1:
#         wav = wav.unsqueeze(0)
#     torchaudio.save(tmp_path, wav, mms_sr)

#     y, _ = librosa.load(tmp_path, sr=22050, mono=True)
#     sf.write(out_path, y, 22050)

#     if os.path.exists(tmp_path):
#         os.remove(tmp_path)

#     return out_path

# def apply_knnvc_voice_conversion(mms_path, voice_sample, out_path, topk=4):
#     if knnvc_model is None:
#         shutil.copy(mms_path, out_path)
#         return out_path, "mms_only"

#     try:
#         if voice_sample not in _knnvc_matching_cache:
#             print(f"       kNN-VC: building matching set for {os.path.basename(voice_sample)}...")
#             ref_16k = voice_sample.replace(".wav", "_16k.wav").replace(".mp3", "_16k.wav")
#             y_ref, _ = librosa.load(voice_sample, sr=16000, mono=True)
#             sf.write(ref_16k, y_ref, 16000)
#             _knnvc_matching_cache[voice_sample] = knnvc_model.get_matching_set([ref_16k])
#         matching_set = _knnvc_matching_cache[voice_sample]

#         src_16k = mms_path.replace(".wav", "_16k.wav")
#         y_src, _ = librosa.load(mms_path, sr=16000, mono=True)
#         sf.write(src_16k, y_src, 16000)
#         query_seq = knnvc_model.get_features(src_16k)

#         out_wav = knnvc_model.match(query_seq, matching_set, topk=topk)
#         torchaudio.save(out_path, out_wav.unsqueeze(0).cpu(), 16000)

#         y, _ = librosa.load(out_path, sr=22050, mono=True)
#         sf.write(out_path, y, 22050)

#         return out_path, "mms+knnvc"

#     except Exception as e:
#         print(f"       WARNING: kNN-VC conversion failed: {e}")
#         print("       Falling back to MMS output without voice conversion")
#         shutil.copy(mms_path, out_path)
#         return out_path, "mms_only_fallback"

# # def generate_stage1(text: str, voice_sample: str, raw_path: str,
# #                     is_tamil: bool, speaker_id: str = "default"):
# #     if not is_tamil:
# #         generate_english_xtts(text, voice_sample, raw_path, speaker_id)
# #         return raw_path, "xtts"
 
# #     mms_path = raw_path.replace(".wav", "_mms.wav")
 
# #     try:
# #         generate_tamil_mms(text, mms_path)
# #         print(f"       MMS-TTS: generated {os.path.basename(mms_path)}")
# #     except Exception as e:
# #         print(f"       WARNING: MMS-TTS failed: {e}")
# #         print("       Falling back to XTTS-v2 with language=hi")
# #         tts_xtts.tts_to_file(
# #             text=text,
# #             speaker_wav=voice_sample,
# #             language="hi",
# #             file_path=raw_path,
# #         )
# #         return raw_path, "xtts_hi_fallback"
 
# #     final_path, method = apply_knnvc_voice_conversion(
# #         mms_path, voice_sample, raw_path, topk=4
# #     )
 
# #     if os.path.exists(mms_path) and mms_path != raw_path:
# #         os.remove(mms_path)
 
# #     return final_path, method
# def generate_stage1(text: str, voice_sample: str, raw_path: str,
#                     is_tamil: bool, speaker_id: str = "default"):
#     if not is_tamil:
#         generate_english_xtts(text, voice_sample, raw_path, speaker_id)
#         return raw_path, "xtts"

#     mms_path = raw_path.replace(".wav", "_mms.wav")
#     try:
#         generate_tamil_mms(text, mms_path)
#         print(f"       MMS-TTS: generated {os.path.basename(mms_path)}")
#     except Exception as e:
#         print(f"       WARNING: MMS-TTS failed: {e} — falling back to XTTS hi")
#         generate_english_xtts(text, voice_sample, raw_path,
#                                speaker_id=speaker_id, language="hi")
#         return raw_path, "xtts_hi_fallback"

#     final_path, method = apply_knnvc_voice_conversion(
#         mms_path, voice_sample, raw_path, topk=4
#     )
#     if os.path.exists(mms_path) and mms_path != raw_path:
#         os.remove(mms_path)
#     return final_path, method
# # ─────────────────────────────────────────────────────────────
# # WAVEFORM COMPARISON PLOT
# # ─────────────────────────────────────────────────────────────
# def save_waveform_comparison(jp_path, en_y, en_sr, target_dur,
#                               seg_id, speaker, emotion, stretch_ratio, method):
#     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
#     fig.patch.set_facecolor("#1a1a2e")

#     def style(ax):
#         ax.set_facecolor("#16213e")
#         ax.spines[:].set_color("#444")
#         ax.tick_params(colors="#aaa", labelsize=8)

#     if jp_path and os.path.exists(jp_path):
#         y_jp, sr_jp = librosa.load(jp_path, sr=None, mono=True)
#         ax1.plot(np.linspace(0, len(y_jp)/sr_jp, len(y_jp)),
#                  y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
#     else:
#         ax1.text(0.5, 0.5, "JP source not found",
#                  transform=ax1.transAxes, ha="center", color="#888", fontsize=9)
#     style(ax1)
#     ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
#     ax1.set_title(
#         f"Seg {seg_id:03d} | {speaker} | {emotion} | "
#         f"stretch {stretch_ratio:.3f}x | {LANGUAGE_MODE} [{method}]",
#         color="#ddd", fontsize=10, pad=5)

#     ax2.plot(np.linspace(0, len(en_y)/en_sr, len(en_y)),
#              en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
#     style(ax2)
#     ax2.set_ylabel(f"Generated [{LANGUAGE_MODE}]", color="#aaa", fontsize=9)
#     ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

#     for ax in (ax1, ax2):
#         ax.axvline(x=target_dur, color="#E24B4A", linewidth=1.2,
#                    linestyle="--", alpha=0.8, label=f"target {target_dur:.2f}s")
#         ax.legend(fontsize=8, facecolor="#222", labelcolor="#ccc",
#                   edgecolor="#444", loc="upper right")

#     plt.tight_layout(pad=1.5)
#     out = os.path.join(WAVEFORM_DIR, f"comparison_{seg_id:03d}.png")
#     plt.savefig(out, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
#     plt.close(fig)
#     return out

# # ─────────────────────────────────────────────────────────────
# # UNDERSTANDABILITY CHECK
# # ─────────────────────────────────────────────────────────────
# def check_understandability(y, sr, stretch_ratio):
#     flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
#     zcr_var  = float(np.var(librosa.feature.zero_crossing_rate(y)))
#     ok = True; reason = "ok"
#     if abs(stretch_ratio - 1.0) > 0.08 and flatness > 0.20:
#         ok = False; reason = f"spectral_smearing ({flatness:.3f})"
#     if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
#         ok = False; reason = f"robotic_periodicity ({zcr_var:.2e})"
#     return {"quality_ok": ok, "reason": reason,
#             "spectral_flatness": round(flatness, 4),
#             "zcr_variance": round(zcr_var, 8)}

# # ─────────────────────────────────────────────────────────────
# # AGE / TYPE TRANSFORMATION
# # ─────────────────────────────────────────────────────────────
# def apply_age_transform(audio_path, out_path, age_category, knnvc_ref=None):
#     if age_category == "adult" or age_category is None:
#         shutil.copy(audio_path, out_path)
#         return out_path
#     preset = AGE_PRESETS.get(age_category)
#     if preset is None:
#         shutil.copy(audio_path, out_path)
#         return out_path

#     if USE_KNNVC and knnvc_model and knnvc_ref and os.path.exists(knnvc_ref):
#         try:
#             if knnvc_ref not in _knnvc_matching_cache:
#                 _knnvc_matching_cache[knnvc_ref] = knnvc_model.get_matching_set([knnvc_ref])
#             matching = _knnvc_matching_cache[knnvc_ref]
#             query    = knnvc_model.get_features(audio_path)
#             out_wav  = knnvc_model.match(query, matching, topk=4)
#             torchaudio.save(out_path, out_wav, 16000)
#             return out_path
#         except Exception as e:
#             print(f"       kNN-VC age transform failed ({e}) — using DSP")

#     if preset == "robot":
#         return _apply_robot(audio_path, out_path)

#     sound = parselmouth.Sound(audio_path)
#     transformed = call(sound, "Change gender", 75, 600,
#                        preset["formant_factor"], 0,
#                        preset["pitch_factor"], preset["rate_factor"])

#     jitter = preset.get("jitter", 0.0)
#     if jitter > 0:
#         y_a  = transformed.as_array().flatten()
#         sr_p = int(transformed.sampling_frequency)
#         y_a += np.random.normal(0, jitter, len(y_a)) * np.abs(y_a)
#         transformed = parselmouth.Sound(y_a, sr_p)

#     breathiness = preset.get("breathiness", 0.0)
#     if breathiness > 0:
#         y_a  = transformed.as_array().flatten()
#         sr_p = int(transformed.sampling_frequency)
#         noise  = np.random.normal(0, 0.015, len(y_a))
#         b, a   = butter(4, 2000/(sr_p/2), btype="high")
#         breath = filtfilt(b, a, noise)
#         b2, a2 = butter(2, 4500/(sr_p/2), btype="low")
#         y_a    = filtfilt(b2, a2, y_a)
#         y_a    = np.clip(y_a*(1-breathiness) + breath*breathiness, -0.95, 0.95)
#         transformed = parselmouth.Sound(y_a, sr_p)

#     transformed.save(out_path, "WAV")
#     return out_path

# def _apply_robot(audio_path, out_path):
#     sound   = parselmouth.Sound(audio_path)
#     sr_p    = int(sound.sampling_frequency)
#     y       = sound.as_array().flatten()
#     pitch   = call(sound, "To Pitch", 0.01, 75, 600)
#     f0_vals = [call(pitch, "Get value at time", t, "Hertz", "Linear")
#                for t in np.arange(0, sound.duration, 0.01)]
#     f0_ok   = [v for v in f0_vals if not np.isnan(v) and v > 0]
#     mean_f0 = float(np.mean(f0_ok)) if f0_ok else 150.0
#     t_arr   = np.arange(len(y)) / sr_p
#     buzz    = (2*(t_arr*mean_f0 % 1) - 1) * 0.5 * np.std(y)
#     sf.write(out_path, np.clip(buzz*0.7 + y*0.3, -0.95, 0.95), sr_p)
#     return 

# # def align_audio(y_raw: np.ndarray, sr: int, target_dur: float,
# #                 min_ratio: float = 0.90, max_ratio: float = 1.10):
# #     """
# #     Align raw TTS audio to target_dur without cropping speech.
 
# #     Returns: (y_aligned, ratio, was_capped)
# #     """
# #     raw_dur  = len(y_raw) / sr
# #     target_n = int(target_dur * sr)
 
# #     # ── Case 1: raw is shorter than slot → pad, no stretch needed ──
# #     if raw_dur <= target_dur:
# #         ratio    = min(max_ratio, target_dur / raw_dur) if raw_dur > 0 else 1.0
# #         # Only stretch UP if ratio is within cap (avoids chipmunk effect)
# #         if ratio <= max_ratio:
# #             target_samples = int(len(y_raw) / ratio)
# #             y_stretched    = resample(y_raw, target_samples)
# #         else:
# #             y_stretched = y_raw
# #         # Pad remaining with silence (with 50ms fade-out at speech end)
# #         fade_len = min(int(0.05 * sr), len(y_stretched))
# #         y_out    = y_stretched.copy()
# #         y_out[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
# #         y_out = np.pad(y_out, (0, max(0, target_n - len(y_out))))
# #         return y_out[:target_n], ratio, False
 
# #     # ── Case 2: raw is longer → compress ──
# #     ideal_ratio = target_dur / raw_dur      # < 1.0 means speed up
# #     capped      = ideal_ratio < min_ratio   # True if we'd need to squeeze too hard
 
# #     ratio          = max(min_ratio, ideal_ratio)
# #     target_samples = int(len(y_raw) / ratio)
# #     y_compressed   = resample(y_raw, target_samples)
 
# #     if len(y_compressed) <= target_n:
# #         # Fits after compression — pad any tiny remainder
# #         y_out = np.pad(y_compressed, (0, max(0, target_n - len(y_compressed))))
# #         return y_out[:target_n], ratio, capped
 
# #     # ── Case 3: still over after compression (ratio was capped) ──
# #     # Instead of hard cut, apply a fade-out over the overlap region
# #     # so the end of speech decays naturally into the next slot
# #     overlap  = len(y_compressed) - target_n
# #     fade_len = min(overlap + int(0.05 * sr), len(y_compressed))
# #     y_out    = y_compressed.copy()
# #     fade     = np.linspace(1.0, 0.0, fade_len)
# #     y_out[-fade_len:] *= fade
# #     return y_out[:target_n], ratio, capped
# # ─────────────────────────────────────────────────────────────
# # ALIGNMENT v3 — rubberband pitch-preserving stretch
# # No ratio cap. Exact sample count guaranteed.
# # ─────────────────────────────────────────────────────────────
# WARN_RATIO_LOW  = 0.60   # log warning but still process
# WARN_RATIO_HIGH = 1.60

# def _exact_length(y: np.ndarray, n: int) -> np.ndarray:
#     """Trim or zero-pad array to exactly n samples."""
#     if len(y) >= n:
#         return y[:n]
#     return np.pad(y, (0, n - len(y)))


# def align_audio(y_raw: np.ndarray, sr: int, target_dur: float,
#                 min_ratio: float = 0.90, max_ratio: float = 1.10):
#     """
#     v3: Pitch-preserving time stretch via pyrubberband.
#     - No hard ratio cap — rubberband handles any ratio cleanly.
#     - Output is EXACTLY target_dur seconds (to the sample).
#     - Returns (y_aligned, ratio, was_warned) to match v2 call signature.
#     """
#     raw_dur  = len(y_raw) / sr
#     target_n = int(target_dur * sr)

#     if raw_dur < 1e-4:
#         return np.zeros(target_n, dtype=np.float32), 1.0, False

#     ratio    = raw_dur / target_dur   # >1 = need to speed up, <1 = slow down
#     was_warn = ratio < WARN_RATIO_LOW or ratio > WARN_RATIO_HIGH

#     if abs(ratio - 1.0) < 0.02:
#         # Within 2% — just pad/trim, no stretch needed
#         y_out = _exact_length(y_raw, target_n)
#         return y_out.astype(np.float32), ratio, was_warn

#     try:
#         # rubberband time_stretch(y, sr, rate) — rate>1 = faster
#         stretch_rate = ratio   # raw_dur/target_dur: if raw is 4s and target is 2s, rate=2.0 (2x faster)
#         y_stretched  = rb.time_stretch(
#             y_raw.astype(np.float64), sr, stretch_rate
#         ).astype(np.float32)
#     except Exception as e:
#         print(f"       WARNING: rubberband failed ({e}) — falling back to scipy resample")
#         target_samples = int(len(y_raw) / ratio)
#         y_stretched = resample(y_raw, target_samples).astype(np.float32)

#     y_out = _exact_length(y_stretched, target_n)
#     return y_out, ratio, was_warn
# # ─────────────────────────────────────────────────────────────
# # TEXT SANITIZER — catches hallucinated/corrupted translations
# # ─────────────────────────────────────────────────────────────
# MAX_CHARS      = 220   # XTTS hard limit is 400 tokens, ~220 chars is safe
# MAX_REPEAT_CHR = 8     # if any single character repeats more than this, it's garbage

# def sanitize_dub_text(text: str, sid: int) -> str | None:
#     """
#     Returns cleaned text, or None if the segment should be skipped.
#     Catches:
#       - Text exceeding XTTS token limit
#       - Hallucinated repetition (マママ... or aaaaa...)
#       - Empty / whitespace only
#       - Raw Japanese left in the english field
#     """
#     if not text or not text.strip():
#         print(f"       SKIP: empty text")
#         return None

#     # Check for repetitive character spam (hallucination)
#     for ch in set(text):
#         if text.count(ch) > MAX_REPEAT_CHR * 3 and len(set(text)) < 10:
#             print(f"       SKIP: repetitive hallucination detected ('{ch}' × {text.count(ch)})")
#             return None

#     # Check if text is mostly Japanese/CJK when we expect English
#     cjk_chars = sum(1 for c in text if '\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef')
#     if cjk_chars > len(text) * 0.3:
#         print(f"       SKIP: text contains {cjk_chars}/{len(text)} CJK chars — untranslated")
#         return None

#     # Truncate if over char limit (with word boundary)
#     if len(text) > MAX_CHARS:
#         truncated = text[:MAX_CHARS].rsplit(" ", 1)[0]
#         print(f"       WARN: text truncated {len(text)} → {len(truncated)} chars")
#         return truncated

#     return text
# # ─────────────────────────────────────────────────────────────
# # MAIN LOOP
# # ─────────────────────────────────────────────────────────────
# generated_clips = []
# qc_flags_all    = []

# for i, seg in enumerate(segments):
#     sid          = seg["segment_id"]
#     speaker      = seg["speaker"]
#     target_dur   = float(seg["duration"])
#     emotion      = seg.get("emotion", "neutral").lower()
#     emotion_conf = float(seg.get("emotion_confidence", 1.0))

#     # dub_text = (seg.get(TEXT_FIELD)
#     #             or seg.get("english")
#     #             or seg.get("tamil", ""))
# # Read dub text from the correct field
#     dub_text = (seg.get(TEXT_FIELD)
#                 or seg.get("english")
#                 or seg.get("tamil", ""))

#     # ── Sanitize before sending to TTS ──
#     dub_text = sanitize_dub_text(dub_text, sid)
#     if not dub_text:
#         print(f"  SKIP Seg {sid:03d} — bad/empty translation (check step3 output)")
#         qc_flags_all.append((sid, ["SKIPPED_BAD_TRANSLATION"]))
#         continue
#     # if not dub_text:
#     #     print(f"\n  WARNING: No dub text for seg {sid:03d} — skipping")
#     #     continue

#     print(f"\n{'─'*55}")
#     print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | {target_dur:.2f}s")
#     print(f"  [{LANGUAGE_MODE}] : {dub_text}")
#     print(f"  emotion : {emotion}  (conf {emotion_conf:.2f})")

#     spk_info     = SPEAKER_MAP.get(speaker, {})
#     voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
#     age_category = spk_info.get("age_category", "adult")
#     knnvc_ref    = spk_info.get("knnvc_ref", None)
#     # tone_category comes from speaker config, defaults to neutral
#     tone_cat     = spk_info.get("tone_category", "neutral")
#     t_cfg        = TONE_CONFIG.get(tone_cat, {"pitch": 0, "lpf": None})

#     if not os.path.exists(voice_sample):
#         print(f"  WARNING: voice not found: {voice_sample} — using default")
#         voice_sample = DEFAULT_VOICE
#     print(f"  voice   : {os.path.basename(voice_sample)}  | age: {age_category}  | tone: {tone_cat}")

#     qc_flags   = []
#     raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
#     align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
#     emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
#     age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
#     final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")

#     # # ── STAGE 1: TTS GENERATION ──────────────────────────────
#     # print(f"  [1] {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'} generation...")

#     # _, tts_method = generate_stage1(dub_text, voice_sample, raw_path, IS_TAMIL)
#     # print(f"       method: {tts_method}")

#     # y_raw, sr = librosa.load(raw_path, sr=22050)
#     # y_raw     = trim_silence(y_raw, sr)
#     # raw_dur   = len(y_raw) / sr
#     # print(f"       raw: {raw_dur:.3f}s  target: {target_dur:.3f}s")

#     # # ── STAGE 2: TIMING ALIGNMENT ────────────────────────────
#     # print("  [2] Timing alignment...")
#     # ratio          = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))
#     # target_samples = int(len(y_raw) / ratio)
#     # y_aligned      = resample(y_raw, target_samples)
#     # y_aligned      = pad_or_trim(y_aligned, sr, target_dur)
#     # print(f"       ratio: {ratio:.3f}x  aligned: {len(y_aligned)/sr:.3f}s")

#     # if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
#     #     qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
#     #     print(f"       WARNING: HIGH_STRETCH")

#     # sf.write(align_path, y_aligned, sr)

#     # quality = check_understandability(y_aligned, sr, ratio)
#     # print(f"       quality: {quality['reason']}")
#     # if not quality["quality_ok"]:
#     #     qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

#     # jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
#     # wf_path = save_waveform_comparison(
#     #     jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
#     #     target_dur=target_dur, seg_id=sid,
#     #     speaker=speaker, emotion=emotion,
#     #     stretch_ratio=ratio, method=tts_method)
#     # print(f"       waveform: {wf_path}")
# #         # ── STAGE 1: TTS ──
# #     _, tts_method = generate_stage1(
# #         dub_text, voice_sample, raw_path, IS_TAMIL,
# #         speaker_id=speaker        # <-- pass speaker name for seeding
# #     )
 
# #     y_raw, sr = librosa.load(raw_path, sr=22050)
# #     y_raw     = trim_silence(y_raw, sr)
# #     raw_dur   = len(y_raw) / sr
# #     print(f"       raw: {raw_dur:.3f}s  target: {target_dur:.3f}s")
 
# #     # ── STAGE 2: ALIGNMENT (no cropping) ──
# #     print("  [2] Timing alignment...")
# #     y_aligned, ratio, was_capped = align_audio(y_raw, sr, target_dur,
# #                                                MIN_RATIO, MAX_RATIO)
# #     print(f"       ratio: {ratio:.3f}x  aligned: {len(y_aligned)/sr:.3f}s"
# #           + ("  [CAPPED]" if was_capped else ""))
 
# #     if was_capped:
# #         qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
# #         print(f"       WARNING: HIGH_STRETCH — speech faded, not cropped")
 
# #     sf.write(align_path, y_aligned, sr)
# # # sf.write(align_path, y_aligned, sr)
# #     quality = check_understandability(y_aligned, sr, ratio)
# #     print(f"       quality: {quality['reason']}")
# #     if not quality["quality_ok"]:
# #         qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")
# #     jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
# #     wf_path = save_waveform_comparison(
# #         jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
# #         target_dur=target_dur, seg_id=sid,
# #         speaker=speaker, emotion=emotion,
# #         stretch_ratio=ratio, method=tts_method)
# #     print(f"       waveform: {wf_path}")
# # ── STAGE 1: TTS ──
#     print(f"  [1] {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'} generation...")
#     _, tts_method = generate_stage1(
#         dub_text, voice_sample, raw_path, IS_TAMIL,
#         speaker_id=speaker
#     )

#     y_raw, sr = librosa.load(raw_path, sr=22050, mono=True)
#     y_raw     = trim_silence(y_raw, sr)
#     raw_dur   = len(y_raw) / sr
#     print(f"       raw: {raw_dur:.3f}s  target: {target_dur:.3f}s  "
#           f"ratio: {raw_dur/target_dur:.3f}x")

#     # ── STAGE 2: ALIGNMENT (pitch-preserving, exact length) ──
#     print("  [2] Timing alignment (rubberband)...")
#     y_aligned, ratio, was_warn = align_audio(y_raw, sr, target_dur)

#     # Verify exact length
#     actual_dur = len(y_aligned) / sr
#     assert abs(actual_dur - target_dur) < 0.01, \
#         f"Length mismatch: got {actual_dur:.3f}s expected {target_dur:.3f}s"

#     print(f"       stretch: {ratio:.3f}x  "
#           f"final: {actual_dur:.4f}s / {target_dur:.4f}s  ✓"
#           + ("  [HIGH_RATIO_WARN]" if was_warn else ""))

#     if was_warn:
#         qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
#         print(f"       NOTE: large stretch ratio — consider re-translating "
#               f"seg {sid:03d} for better timing fit")

#     sf.write(align_path, y_aligned, sr)
#     # ── STAGE 3: EMOTION + TONE DSP ──────────────────────────
#     if EMOTION_ENABLED:
#         eff_emotion = emotion if emotion_conf >= 0.30 else "neutral"
#         print(f"  [3] Emotion: {eff_emotion}" +
#               (" (low-conf override)" if eff_emotion != emotion else ""))

#         target_dbfs = EMOTION_LOUDNESS.get(eff_emotion, -24)
#         y_emotion   = rms_normalise(y_aligned, target_dbfs)

#         # ── Tone DSP (LPF) ────────────────────────────────────
#         if t_cfg["lpf"]:
#             y_emotion = butter_filter(y_emotion, sr, t_cfg["lpf"], "low")

#         # ── Inner thought reverb ──────────────────────────────
#         if tone_cat == "inner_thought":
#             y_emotion = apply_inner_thought_reverb(y_emotion, sr, wet=0.20)

#         # ── Ecchi: breathiness layer ──────────────────────────
#         if tone_cat == "ecchi":
#             noise     = np.random.normal(0, 0.015, len(y_emotion))
#             breath    = butter_filter(noise, sr, 3500, "high")
#             y_emotion = np.clip(y_emotion + breath * 0.25, -0.95, 0.95)

#         # ── Tone DSP (pitch shift) — float64 cast fixes numba ─
#         if t_cfg["pitch"] != 0:
#             y_emotion = safe_pitch_shift(y_emotion, sr, n_steps=t_cfg["pitch"])

#         # ── Emotion-specific DSP ──────────────────────────────
#         if eff_emotion in ("sad",):
#             y_emotion = butter_filter(y_emotion, sr, 3500, "low")

#         elif eff_emotion in ("angry", "ang"):
#             y_emotion = butter_filter(y_emotion, sr, 150, "high")
#             y_hf      = butter_filter(y_emotion, sr, 3000, "high")
#             y_emotion = np.clip(y_emotion + 0.15 * y_hf, -0.95, 0.95)

#         elif eff_emotion in ("happy", "hap"):
#             y_hf      = butter_filter(y_emotion, sr, 4000, "high")
#             y_emotion = np.clip(y_emotion + 0.10 * y_hf, -0.95, 0.95)

#         elif eff_emotion in ("fearful", "fea", "surprised", "sur"):
#             noise     = np.random.normal(0, 0.008, len(y_emotion))
#             breath    = butter_filter(noise, sr, 3000, "high")
#             y_emotion = np.clip(y_emotion + breath * 0.12, -0.95, 0.95)

#     else:
#         print("  [3] Emotion: DISABLED")
#         y_emotion   = y_aligned
#         eff_emotion = "disabled"

#     sf.write(emot_path, y_emotion, sr)

#     # ── STAGE 4: AGE / TYPE TRANSFORMATION ───────────────────
#     if AGE_ENABLED and age_category != "adult":
#         method_age = "kNN-VC" if (USE_KNNVC and knnvc_ref) else "DSP"
#         print(f"  [4] Age: {age_category}  [{method_age}]")
#         apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
#         y_final, sr_f = librosa.load(age_path, sr=None)
#         y_final = pad_or_trim(y_final, sr_f, target_dur)
#         sf.write(age_path, y_final, sr_f)
#         sr_final = sr_f
#     else:
#         label = "DISABLED" if not AGE_ENABLED else "adult/pass-through"
#         print(f"  [4] Age: {label}")
#         y_final  = y_emotion
#         sr_final = sr

#     sf.write(final_path, y_final, sr_final)
#     dur_final = len(y_final) / sr_final
#     if dur_final < 0.15:
#         qc_flags.append("TOO_SHORT")

#     # ── METADATA ─────────────────────────────────────────────
#     clip_meta = {
#         "segment_id":           sid,
#         "speaker":              speaker,
#         "start":                seg["start"],
#         "end":                  seg["end"],
#         "duration_target":      round(target_dur, 4),
#         "duration_raw_trimmed": round(raw_dur, 4),
#         "duration_final":       round(dur_final, 4),
#         "stretch_ratio":        round(ratio, 4),
#         "voice_sample":         os.path.basename(voice_sample),
#         "language_mode":        LANGUAGE_MODE,
#         "tts_method":           tts_method,
#         "text":                 dub_text,
#         "emotion":              emotion,
#         "emotion_effective":    eff_emotion if EMOTION_ENABLED else "disabled",
#         "emotion_confidence":   round(emotion_conf, 4),
#         "emotion_enabled":      EMOTION_ENABLED,
#         "age_category":         age_category,
#         "age_enabled":          AGE_ENABLED,
#         "tone_category":        tone_cat,
#         "quality_check":        quality,
#         "qc_flags":             qc_flags,
#         "waveform_plot":        wf_path,
#         "files": {
#             "raw":     raw_path,
#             "aligned": align_path,
#             "emotion": emot_path,
#             "age":     age_path if (AGE_ENABLED and age_category != "adult") else None,
#             "final":   final_path,
#         },
#     }
#     generated_clips.append(clip_meta)
#     if qc_flags:
#         qc_flags_all.append((sid, qc_flags))

#     status = "WARN" if qc_flags else "OK"
#     print(f"  [{status}] Seg {sid:03d} -> {final_path}")

# # ─────────────────────────────────────────────────────────────
# # SAVE METADATA
# # ─────────────────────────────────────────────────────────────
# meta = {
#     "timestamp":       datetime.now().isoformat(),
#     "total_clips":     len(generated_clips),
#     "language_mode":   LANGUAGE_MODE,
#     "tts_language":    TTS_LANGUAGE,
#     "emotion_enabled": EMOTION_ENABLED,
#     "age_enabled":     AGE_ENABLED,
#     "clips":           generated_clips,
# }
# meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
# with open(meta_path, "w", encoding="utf-8") as f:
#     json.dump(meta, f, indent=2, ensure_ascii=False)

# print(f"\n{'='*60}")
# print(f"STEP 4 COMPLETE -- {len(generated_clips)} clips  [{LANGUAGE_MODE}]")
# print(f"Audio    : {OUTPUT_DIR}/")
# print(f"Metadata : {meta_path}")
# print(f"Waveforms: {WAVEFORM_DIR}/")
# if qc_flags_all:
#     print(f"\nQC FLAGS ({len(qc_flags_all)} segments):")
#     for sid, flags in sorted(qc_flags_all):
#         print(f"  [seg {sid:03d}] {flags}")
# else:
#     print("\nAll segments passed QC")
# print("\nNext -> step5_assembly.py")
"""
STEP 4 v3: Voice Generation Pipeline
=====================================
v3 fixes:
  1. CONSISTENT VOICE PER SPEAKER
     - get_conditioning_latents() called ONCE per speaker before the loop
     - Cached gpt_cond_latent + speaker_embedding reused every segment
     - Eliminates random voice drift between segments

  2. EXACT LENGTH MATCHING TO JAPANESE SEGMENT
     - pyrubberband pitch-preserving time stretch (no chipmunk/slowed effect)
     - No ±10% ratio cap — any ratio handled cleanly
     - _exact_length() guarantees output is exactly target_dur samples

  3. PRE-LOOP EMBEDDING WARMUP
     - All speaker embeddings computed and logged before processing starts
"""

import os
import json
import shutil
import soundfile as sf
from datetime import datetime
from pathlib import Path

import torch
import torchaudio
import librosa
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import parselmouth
from parselmouth.praat import call
from scipy.signal import butter, filtfilt, resample
from TTS.api import TTS

# v3: pitch-preserving time stretch
try:
    import pyrubberband as rb
    HAVE_RUBBERBAND = True
except ImportError:
    print("WARNING: pyrubberband not installed — falling back to scipy resample")
    print("         pip install pyrubberband  +  apt install rubberband-cli")
    HAVE_RUBBERBAND = False

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
INPUT_JSON    = "work/translated_segments_step3.json"
CONFIG_PATH   = "work/speaker_config.json"
OUTPUT_DIR    = "work/generated_audio"
WAVEFORM_DIR  = "work/waveform_comparisons"
CROPPED_DIR   = "work/cropped_segments"
DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

# v3: warn thresholds (no hard cap — rubberband handles any ratio)
WARN_RATIO_LOW  = 0.55   # below this = TTS generated much less than needed
WARN_RATIO_HIGH = 1.80   # above this = TTS generated much more than needed

# ─────────────────────────────────────────────────────────────
# EMOTION LOUDNESS
# ─────────────────────────────────────────────────────────────
EMOTION_LOUDNESS = {
    "angry":     -20, "ang": -20,
    "surprised": -21, "sur": -21,
    "fearful":   -21, "fea": -21,
    "happy":     -22, "hap": -22,
    "neutral":   -24, "neu": -24,
    "sad":       -28,
    "disgusted": -23, "dis": -23,
    "unknown":   -24,
}

# ─────────────────────────────────────────────────────────────
# AGE PRESETS
# ─────────────────────────────────────────────────────────────
AGE_PRESETS = {
    "adult":       None,
    "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
    "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
    "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
    "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
    "robot":       "robot",
}

# ─────────────────────────────────────────────────────────────
# TONE CONFIG
# ─────────────────────────────────────────────────────────────
TONE_CONFIG = {
    "neutral":       {"pitch": 0,   "lpf": None},
    "ecchi":         {"pitch": -1,  "lpf": 4500},
    "horny":         {"pitch": -4,  "lpf": None},
    "soft":          {"pitch": 0,   "lpf": 3500},
    "sexy":          {"pitch": -3,  "lpf": None},
    "calm":          {"pitch": 0,   "lpf": 4000},
    "hard":          {"pitch": 2,   "lpf": None},
    "kid":           {"pitch": 12,  "lpf": None},
    "inner_thought": {"pitch": 0,   "lpf": 3000},
}

# ─────────────────────────────────────────────────────────────
# DTYPE HELPERS
# ─────────────────────────────────────────────────────────────
def to_f64(y: np.ndarray) -> np.ndarray:
    return y.astype(np.float64)

def to_f32(y: np.ndarray) -> np.ndarray:
    return y.astype(np.float32)

# ─────────────────────────────────────────────────────────────
# PITCH SHIFT (Parselmouth — avoids numba crash)
# ─────────────────────────────────────────────────────────────
def safe_pitch_shift(y: np.ndarray, sr: int, n_steps: float) -> np.ndarray:
    try:
        tmp_in  = "work/_ps_in.wav"
        tmp_out = "work/_ps_out.wav"
        sf.write(tmp_in, y.astype(np.float32), sr)
        sound   = parselmouth.Sound(tmp_in)
        factor  = 2.0 ** (n_steps / 12.0)
        shifted = call(sound, "Change gender", 75, 600, 1.0, 0.0, factor, 1.0)
        shifted.save(tmp_out, "WAV")
        y_out, _ = librosa.load(tmp_out, sr=sr, mono=True)
        for p in (tmp_in, tmp_out):
            if os.path.exists(p): os.remove(p)
        return y_out.astype(np.float32)
    except Exception as e:
        print(f"       WARNING: pitch_shift failed ({e}) — returning dry signal")
        return y.astype(np.float32)

# ─────────────────────────────────────────────────────────────
# INNER THOUGHT REVERB
# ─────────────────────────────────────────────────────────────
def apply_inner_thought_reverb(y: np.ndarray, sr: int, wet: float = 0.15) -> np.ndarray:
    delay_samples = int(0.03 * sr)
    reverb = np.zeros_like(y)
    reverb[delay_samples:] = y[:-delay_samples] * 0.4
    return np.clip(y * (1 - wet) + reverb * wet, -0.95, 0.95)

# ─────────────────────────────────────────────────────────────
# DIRECTORIES
# ─────────────────────────────────────────────────────────────
os.makedirs(OUTPUT_DIR,   exist_ok=True)
os.makedirs(WAVEFORM_DIR, exist_ok=True)
os.makedirs("work",       exist_ok=True)

# ─────────────────────────────────────────────────────────────
# LOAD SPEAKER CONFIG
# ─────────────────────────────────────────────────────────────
def load_speaker_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"WARNING: {CONFIG_PATH} not found — run step4_setup.py first")
        return {
            "options":       {"emotion_enabled": True, "age_enabled": True, "use_knnvc": False},
            "speakers":      {},
            "language_mode": "english",
            "tts_language":  "en",
            "text_field":    "english",
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print(f"Config loaded: {CONFIG_PATH}  [{cfg.get('generated_at','')}]")
    opts = cfg.get("options", {})
    print(f"  Language  : {cfg.get('language_mode','english')}")
    print(f"  TTS code  : {cfg.get('tts_language','en')}")
    print(f"  Text field: {cfg.get('text_field','english')}")
    print(f"  Emotion   : {'ON' if opts.get('emotion_enabled') else 'OFF'}")
    print(f"  Age/type  : {'ON' if opts.get('age_enabled') else 'OFF'}")
    for spk, d in sorted(cfg.get("speakers", {}).items()):
        v      = d.get("voice_display", os.path.basename(d.get("voice_sample", "?")))
        gender = d.get("detected_gender", "unknown")
        print(f"  {spk:<14} -> {v}  [{d.get('age_category','adult')}]  [{gender}]")
    return cfg


print("=" * 60)
print("STEP 4 v3: Voice Generation Pipeline")
print("=" * 60)

_cfg            = load_speaker_config()
SPEAKER_MAP     = _cfg.get("speakers", {})
EMOTION_ENABLED = _cfg["options"].get("emotion_enabled", True)
AGE_ENABLED     = _cfg["options"].get("age_enabled",     True)
USE_KNNVC       = _cfg["options"].get("use_knnvc",       False)

LANGUAGE_MODE = _cfg.get("language_mode", "english")
TTS_LANGUAGE  = _cfg.get("tts_language",  "en")
TEXT_FIELD    = _cfg.get("text_field",    "english")
IS_TAMIL      = LANGUAGE_MODE in ("tamil", "tanglish")

print(f"\nLanguage : {LANGUAGE_MODE}  |  TTS: {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'}")
print(f"Rubberband: {'available ✓' if HAVE_RUBBERBAND else 'NOT FOUND — using scipy fallback'}")

# ─────────────────────────────────────────────────────────────
# LOAD MODELS
# ─────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\nLoading models on {device}...")

tts_xtts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
               gpu=(device == "cuda"))
print("XTTS-v2 loaded ✓")

mms_model     = None
mms_tokenizer = None
if IS_TAMIL:
    print("Loading facebook/mms-tts-tam...")
    try:
        from transformers import VitsModel, AutoTokenizer
        mms_model     = VitsModel.from_pretrained("facebook/mms-tts-tam").to(device)
        mms_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-tam")
        mms_model.eval()
        print(f"MMS-TTS Tamil loaded ✓  (SR={mms_model.config.sampling_rate})")
    except Exception as e:
        print(f"WARNING: MMS-TTS Tamil failed: {e}")
        print("         Tamil will use XTTS-v2 with language=hi as fallback")

knnvc_model = None
if IS_TAMIL:
    print("Loading kNN-VC...")
    try:
        knnvc_model = torch.hub.load(
            "bshall/knn-vc", "knn_vc",
            prematched=True, trust_repo=True, pretrained=True,
        )
        print("kNN-VC loaded ✓")
    except Exception as e:
        print(f"WARNING: kNN-VC failed: {e}")
elif USE_KNNVC:
    try:
        from knnvc import KNN_VC
        knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
        print("kNN-VC loaded ✓")
    except ImportError:
        print("WARNING: kNN-VC not installed — DSP fallback for age conversion")
        USE_KNNVC = False

# ─────────────────────────────────────────────────────────────
# LOAD SEGMENTS
# ─────────────────────────────────────────────────────────────
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)
segments = data["segments"]
print(f"\nLoaded {len(segments)} segments from {INPUT_JSON}")

# ─────────────────────────────────────────────────────────────
# ── v3 FIX 1: SPEAKER EMBEDDING CACHE ────────────────────────
# Compute gpt_cond_latent + speaker_embedding ONCE per speaker.
# Reusing the same latent = identical voice every segment.
# tts_to_file(speaker_wav=...) re-extracts randomly each call —
# that's what caused multiple voices per character in v2.
# ─────────────────────────────────────────────────────────────
_embed_cache: dict = {}

def get_speaker_embeddings(voice_sample: str, speaker_id: str):
    """
    Extract XTTS conditioning latents once and cache by speaker_id.
    Same latent tensor reused every segment = consistent voice.
    """
    if speaker_id not in _embed_cache:
        print(f"       Computing embeddings for {speaker_id} "
              f"({os.path.basename(voice_sample)})...")
        gpt_cond_latent, speaker_embedding = (
            tts_xtts.synthesizer.tts_model
            .get_conditioning_latents(audio_path=[voice_sample])
        )
        _embed_cache[speaker_id] = (gpt_cond_latent, speaker_embedding)
        print(f"       Embeddings cached for {speaker_id} ✓")
    return _embed_cache[speaker_id]


def generate_english_xtts(text: str, voice_sample: str, out_path: str,
                           speaker_id: str = "default",
                           language: str = "en"):
    """
    v3: Uses cached conditioning latents — same voice every time.
    No per-call speaker_wav re-extraction.
    """
    gpt_cond_latent, speaker_embedding = get_speaker_embeddings(
        voice_sample, speaker_id
    )

    out = tts_xtts.synthesizer.tts_model.inference(
        text=text,
        language=language,
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=0.65,
        length_penalty=1.0,
        repetition_penalty=10.0,
        top_k=50,
        top_p=0.85,
    )

    wav = torch.tensor(out["wav"]).unsqueeze(0)
    torchaudio.save(out_path, wav, tts_xtts.synthesizer.output_sample_rate)


def generate_tamil_mms(text: str, out_path: str):
    if mms_model is None or mms_tokenizer is None:
        raise RuntimeError("MMS-TTS Tamil model not loaded")
    inputs = mms_tokenizer(text, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        output = mms_model(**inputs)
    wav    = output.waveform[0].cpu()
    mms_sr = mms_model.config.sampling_rate
    tmp    = out_path.replace(".wav", "_mms_raw.wav")
    if wav.dim() == 1:
        wav = wav.unsqueeze(0)
    torchaudio.save(tmp, wav, mms_sr)
    y, _ = librosa.load(tmp, sr=22050, mono=True)
    sf.write(out_path, y, 22050)
    if os.path.exists(tmp): os.remove(tmp)
    return out_path


_knnvc_matching_cache: dict = {}

def apply_knnvc_voice_conversion(mms_path: str, voice_sample: str,
                                  out_path: str, topk: int = 4):
    if knnvc_model is None:
        shutil.copy(mms_path, out_path)
        return out_path, "mms_only"
    try:
        if voice_sample not in _knnvc_matching_cache:
            print(f"       kNN-VC: building matching set for "
                  f"{os.path.basename(voice_sample)}...")
            ref_16k = voice_sample.replace(".wav","_16k.wav").replace(".mp3","_16k.wav")
            y_ref, _ = librosa.load(voice_sample, sr=16000, mono=True)
            sf.write(ref_16k, y_ref, 16000)
            _knnvc_matching_cache[voice_sample] = (
                knnvc_model.get_matching_set([ref_16k])
            )
        matching_set = _knnvc_matching_cache[voice_sample]
        src_16k = mms_path.replace(".wav", "_16k.wav")
        y_src, _ = librosa.load(mms_path, sr=16000, mono=True)
        sf.write(src_16k, y_src, 16000)
        query_seq = knnvc_model.get_features(src_16k)
        out_wav   = knnvc_model.match(query_seq, matching_set, topk=topk)
        torchaudio.save(out_path, out_wav.unsqueeze(0).cpu(), 16000)
        y, _ = librosa.load(out_path, sr=22050, mono=True)
        sf.write(out_path, y, 22050)
        return out_path, "mms+knnvc"
    except Exception as e:
        print(f"       WARNING: kNN-VC failed ({e}) — using MMS output")
        shutil.copy(mms_path, out_path)
        return out_path, "mms_only_fallback"


def generate_stage1(text: str, voice_sample: str, raw_path: str,
                    is_tamil: bool, speaker_id: str = "default"):
    if not is_tamil:
        generate_english_xtts(text, voice_sample, raw_path, speaker_id)
        return raw_path, "xtts"

    mms_path = raw_path.replace(".wav", "_mms.wav")
    try:
        generate_tamil_mms(text, mms_path)
        print(f"       MMS-TTS: generated {os.path.basename(mms_path)}")
    except Exception as e:
        print(f"       WARNING: MMS-TTS failed: {e} — falling back to XTTS hi")
        generate_english_xtts(text, voice_sample, raw_path,
                               speaker_id=speaker_id, language="hi")
        return raw_path, "xtts_hi_fallback"

    final_path, method = apply_knnvc_voice_conversion(
        mms_path, voice_sample, raw_path, topk=4
    )
    if os.path.exists(mms_path) and mms_path != raw_path:
        os.remove(mms_path)
    return final_path, method


# ─────────────────────────────────────────────────────────────
# ── v3 FIX 2: EXACT LENGTH ALIGNMENT ─────────────────────────
# pyrubberband: pitch-preserving at any stretch ratio.
# No ±10% cap. Output is exactly target_dur to the sample.
# ─────────────────────────────────────────────────────────────

def _exact_length(y: np.ndarray, n: int) -> np.ndarray:
    """Trim or zero-pad to exactly n samples."""
    if len(y) >= n:
        return y[:n].astype(np.float32)
    return np.pad(y, (0, n - len(y))).astype(np.float32)


def align_audio(y_raw: np.ndarray, sr: int, target_dur: float,
                min_ratio: float = 0.90, max_ratio: float = 1.10):
    """
    v3: Pitch-preserving time stretch via pyrubberband.
    - No hard ratio cap — rubberband handles any ratio without artifacts.
    - Output is EXACTLY target_dur seconds (guaranteed by _exact_length).
    - Returns (y_aligned, ratio, was_warned) — same signature as v2.

    ratio convention (rubberband):
      ratio = raw_dur / target_dur
      ratio > 1 → speech is too long → speed up
      ratio < 1 → speech is too short → slow down
    """
    raw_dur  = len(y_raw) / sr
    target_n = int(target_dur * sr)

    if raw_dur < 1e-4:
        return np.zeros(target_n, dtype=np.float32), 1.0, False

    ratio    = raw_dur / target_dur
    was_warn = ratio < WARN_RATIO_LOW or ratio > WARN_RATIO_HIGH

    # Within 2% — just pad/trim, no stretch needed
    if abs(ratio - 1.0) < 0.02:
        return _exact_length(y_raw, target_n), ratio, was_warn

    # ── Rubberband (preferred) ──
    if HAVE_RUBBERBAND:
        try:
            # time_stretch(y, sr, rate): rate=ratio speeds up by that factor
            y_stretched = rb.time_stretch(
                y_raw.astype(np.float64), sr, ratio
            ).astype(np.float32)
            return _exact_length(y_stretched, target_n), ratio, was_warn
        except Exception as e:
            print(f"       WARNING: rubberband failed ({e}) — scipy fallback")

    # ── scipy fallback (no pitch preservation) ──
    target_samples = int(len(y_raw) / ratio)
    y_stretched    = resample(y_raw.astype(np.float32), target_samples)
    return _exact_length(y_stretched, target_n), ratio, was_warn


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def trim_silence(y, sr, top_db=35):
    _, idx = librosa.effects.trim(y, top_db=top_db,
                                   frame_length=512, hop_length=128)
    lead  = max(0, idx[0] - int(0.02 * sr))
    trail = min(len(y), idx[1] + int(0.03 * sr))
    return y[lead:trail]


def rms_normalise(y, target_dbfs=-24.0):
    rms = np.sqrt(np.mean(y ** 2))
    if rms < 1e-6: return y
    return np.clip(y * (10 ** (target_dbfs / 20.0) / rms), -0.95, 0.95)


def butter_filter(y, sr, cutoff, btype, order=4):
    b, a = butter(order, min(cutoff / (sr / 2.0), 0.99), btype=btype)
    return filtfilt(b, a, y)


def pad_or_trim(y, sr, target_dur):
    n = int(target_dur * sr)
    if len(y) >= n:
        return y[:n]
    fade_len = min(int(0.05 * sr), len(y))
    y = y.copy()
    y[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
    return np.pad(y, (0, n - len(y)))


# ─────────────────────────────────────────────────────────────
# TEXT SANITIZER
# ─────────────────────────────────────────────────────────────
MAX_CHARS      = 220
MAX_REPEAT_CHR = 8

def sanitize_dub_text(text: str, sid: int):
    if not text or not text.strip():
        print(f"       SKIP: empty text"); return None

    for ch in set(text):
        if text.count(ch) > MAX_REPEAT_CHR * 3 and len(set(text)) < 10:
            print(f"       SKIP: hallucination ('{ch}' × {text.count(ch)})")
            return None

    cjk = sum(1 for c in text if '\u3000' <= c <= '\u9fff' or '\uff00' <= c <= '\uffef')
    if cjk > len(text) * 0.3:
        print(f"       SKIP: {cjk}/{len(text)} CJK chars — untranslated"); return None

    if len(text) > MAX_CHARS:
        truncated = text[:MAX_CHARS].rsplit(" ", 1)[0]
        print(f"       WARN: truncated {len(text)} → {len(truncated)} chars")
        return truncated

    return text


# ─────────────────────────────────────────────────────────────
# WAVEFORM COMPARISON PLOT
# ─────────────────────────────────────────────────────────────
def save_waveform_comparison(jp_path, en_y, en_sr, target_dur,
                              seg_id, speaker, emotion, stretch_ratio, method):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")

    def style(ax):
        ax.set_facecolor("#16213e")
        ax.spines[:].set_color("#444")
        ax.tick_params(colors="#aaa", labelsize=8)

    if jp_path and os.path.exists(jp_path):
        y_jp, sr_jp = librosa.load(jp_path, sr=None, mono=True)
        ax1.plot(np.linspace(0, len(y_jp)/sr_jp, len(y_jp)),
                 y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
    else:
        ax1.text(0.5, 0.5, "JP source not found",
                 transform=ax1.transAxes, ha="center", color="#888", fontsize=9)
    style(ax1)
    ax1.set_ylabel("JP original", color="#aaa", fontsize=9)
    ax1.set_title(
        f"Seg {seg_id:03d} | {speaker} | {emotion} | "
        f"stretch {stretch_ratio:.3f}x | {LANGUAGE_MODE} [{method}]",
        color="#ddd", fontsize=10, pad=5)

    ax2.plot(np.linspace(0, len(en_y)/en_sr, len(en_y)),
             en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
    style(ax2)
    ax2.set_ylabel(f"Generated [{LANGUAGE_MODE}]", color="#aaa", fontsize=9)
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
# UNDERSTANDABILITY CHECK
# ─────────────────────────────────────────────────────────────
def check_understandability(y, sr, stretch_ratio):
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
    zcr_var  = float(np.var(librosa.feature.zero_crossing_rate(y)))
    ok = True; reason = "ok"
    if abs(stretch_ratio - 1.0) > 0.08 and flatness > 0.20:
        ok = False; reason = f"spectral_smearing ({flatness:.3f})"
    if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
        ok = False; reason = f"robotic_periodicity ({zcr_var:.2e})"
    return {"quality_ok": ok, "reason": reason,
            "spectral_flatness": round(flatness, 4),
            "zcr_variance": round(zcr_var, 8)}


# ─────────────────────────────────────────────────────────────
# AGE / TYPE TRANSFORMATION
# ─────────────────────────────────────────────────────────────
def apply_age_transform(audio_path, out_path, age_category, knnvc_ref=None):
    if age_category == "adult" or age_category is None:
        shutil.copy(audio_path, out_path); return out_path
    preset = AGE_PRESETS.get(age_category)
    if preset is None:
        shutil.copy(audio_path, out_path); return out_path

    if USE_KNNVC and knnvc_model and knnvc_ref and os.path.exists(knnvc_ref):
        try:
            if knnvc_ref not in _knnvc_matching_cache:
                _knnvc_matching_cache[knnvc_ref] = knnvc_model.get_matching_set([knnvc_ref])
            matching = _knnvc_matching_cache[knnvc_ref]
            query    = knnvc_model.get_features(audio_path)
            out_wav  = knnvc_model.match(query, matching, topk=4)
            torchaudio.save(out_path, out_wav, 16000)
            return out_path
        except Exception as e:
            print(f"       kNN-VC age transform failed ({e}) — using DSP")

    if preset == "robot":
        return _apply_robot(audio_path, out_path)

    sound       = parselmouth.Sound(audio_path)
    transformed = call(sound, "Change gender", 75, 600,
                       preset["formant_factor"], 0,
                       preset["pitch_factor"], preset["rate_factor"])

    jitter = preset.get("jitter", 0.0)
    if jitter > 0:
        y_a  = transformed.as_array().flatten()
        sr_p = int(transformed.sampling_frequency)
        y_a += np.random.normal(0, jitter, len(y_a)) * np.abs(y_a)
        transformed = parselmouth.Sound(y_a, sr_p)

    breathiness = preset.get("breathiness", 0.0)
    if breathiness > 0:
        y_a  = transformed.as_array().flatten()
        sr_p = int(transformed.sampling_frequency)
        noise  = np.random.normal(0, 0.015, len(y_a))
        b, a   = butter(4, 2000/(sr_p/2), btype="high")
        breath = filtfilt(b, a, noise)
        b2, a2 = butter(2, 4500/(sr_p/2), btype="low")
        y_a    = filtfilt(b2, a2, y_a)
        y_a    = np.clip(y_a*(1-breathiness) + breath*breathiness, -0.95, 0.95)
        transformed = parselmouth.Sound(y_a, sr_p)

    transformed.save(out_path, "WAV")
    return out_path


def _apply_robot(audio_path, out_path):
    sound   = parselmouth.Sound(audio_path)
    sr_p    = int(sound.sampling_frequency)
    y       = sound.as_array().flatten()
    pitch   = call(sound, "To Pitch", 0.01, 75, 600)
    f0_vals = [call(pitch, "Get value at time", t, "Hertz", "Linear")
               for t in np.arange(0, sound.duration, 0.01)]
    f0_ok   = [v for v in f0_vals if not np.isnan(v) and v > 0]
    mean_f0 = float(np.mean(f0_ok)) if f0_ok else 150.0
    t_arr   = np.arange(len(y)) / sr_p
    buzz    = (2*(t_arr*mean_f0 % 1) - 1) * 0.5 * np.std(y)
    sf.write(out_path, np.clip(buzz*0.7 + y*0.3, -0.95, 0.95), sr_p)
    return out_path


# ─────────────────────────────────────────────────────────────
# ── v3 FIX 3: PRE-LOOP EMBEDDING WARMUP ──────────────────────
# Compute and cache all speaker embeddings before processing.
# Avoids mid-loop delays and makes the log clean.
# ─────────────────────────────────────────────────────────────
if not IS_TAMIL:
    print("\n── Pre-computing speaker voice embeddings ──")
    for spk_id, spk_info in sorted(SPEAKER_MAP.items()):
        vs = spk_info.get("voice_sample", DEFAULT_VOICE)
        if os.path.exists(vs):
            get_speaker_embeddings(vs, spk_id)
        else:
            print(f"  WARNING: voice not found for {spk_id}: {vs}")
    print(f"All embeddings ready: {list(_embed_cache.keys())} ✓\n")

# ─────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────
generated_clips = []
qc_flags_all    = []

for i, seg in enumerate(segments):
    sid          = seg["segment_id"]
    speaker      = seg["speaker"]
    target_dur   = float(seg["duration"])
    emotion      = seg.get("emotion", "neutral").lower()
    emotion_conf = float(seg.get("emotion_confidence", 1.0))

    dub_text = (seg.get(TEXT_FIELD)
                or seg.get("english")
                or seg.get("tamil", ""))

    dub_text = sanitize_dub_text(dub_text, sid)
    if not dub_text:
        print(f"  SKIP Seg {sid:03d} — bad/empty translation")
        qc_flags_all.append((sid, ["SKIPPED_BAD_TRANSLATION"]))
        continue

    print(f"\n{'─'*55}")
    print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | "
          f"target: {target_dur:.3f}s")
    print(f"  text    : {dub_text}")
    print(f"  emotion : {emotion}  (conf {emotion_conf:.2f})")

    spk_info     = SPEAKER_MAP.get(speaker, {})
    voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
    age_category = spk_info.get("age_category", "adult")
    knnvc_ref    = spk_info.get("knnvc_ref", None)
    tone_cat     = spk_info.get("tone_category", "neutral")
    t_cfg        = TONE_CONFIG.get(tone_cat, {"pitch": 0, "lpf": None})

    if not os.path.exists(voice_sample):
        print(f"  WARNING: voice not found: {voice_sample} — using default")
        voice_sample = DEFAULT_VOICE

    print(f"  voice   : {os.path.basename(voice_sample)} | "
          f"age: {age_category} | tone: {tone_cat}")

    qc_flags   = []
    raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
    align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
    emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
    age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
    final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")

    # ── STAGE 1: TTS GENERATION ──────────────────────────────
    print(f"  [1] {'MMS+kNN-VC' if IS_TAMIL else 'XTTS-v2'} generation...")
    _, tts_method = generate_stage1(
        dub_text, voice_sample, raw_path, IS_TAMIL,
        speaker_id=speaker
    )
    print(f"       method: {tts_method}")

    y_raw, sr = librosa.load(raw_path, sr=22050, mono=True)
    y_raw     = trim_silence(y_raw, sr)
    raw_dur   = len(y_raw) / sr
    print(f"       raw: {raw_dur:.3f}s  target: {target_dur:.3f}s  "
          f"need: {raw_dur/target_dur:.3f}x stretch")

    # ── STAGE 2: TIMING ALIGNMENT (v3 — rubberband, exact length) ──
    print(f"  [2] Alignment ({'rubberband' if HAVE_RUBBERBAND else 'scipy'})...")
    y_aligned, ratio, was_warn = align_audio(y_raw, sr, target_dur)

    actual_dur = len(y_aligned) / sr
    drift_ms   = abs(actual_dur - target_dur) * 1000

    print(f"       stretch: {ratio:.4f}x | "
          f"aligned: {actual_dur:.4f}s | target: {target_dur:.4f}s | "
          f"drift: {drift_ms:.1f}ms"
          + (" ⚠ HIGH_RATIO" if was_warn else " ✓"))

    if was_warn:
        qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
        print(f"       NOTE: large ratio — segment {sid:03d} may benefit from "
              f"re-translation with tighter syllable budget")

    if drift_ms > 10:
        qc_flags.append(f"DRIFT_{drift_ms:.0f}ms")
        print(f"       WARNING: {drift_ms:.0f}ms drift — check rubberband install")

    sf.write(align_path, y_aligned, sr)

    quality = check_understandability(y_aligned, sr, ratio)
    print(f"       quality: {quality['reason']}")
    if not quality["quality_ok"]:
        qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

    jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
    wf_path = save_waveform_comparison(
        jp_path=jp_crop, en_y=y_aligned, en_sr=sr,
        target_dur=target_dur, seg_id=sid,
        speaker=speaker, emotion=emotion,
        stretch_ratio=ratio, method=tts_method)
    print(f"       waveform: {wf_path}")

    # ── STAGE 3: EMOTION + TONE DSP ──────────────────────────
    if EMOTION_ENABLED:
        eff_emotion = emotion if emotion_conf >= 0.30 else "neutral"
        print(f"  [3] Emotion: {eff_emotion}"
              + (" (low-conf override)" if eff_emotion != emotion else ""))

        target_dbfs = EMOTION_LOUDNESS.get(eff_emotion, -24)
        y_emotion   = rms_normalise(y_aligned, target_dbfs)

        if t_cfg["lpf"]:
            y_emotion = butter_filter(y_emotion, sr, t_cfg["lpf"], "low")

        if tone_cat == "inner_thought":
            y_emotion = apply_inner_thought_reverb(y_emotion, sr, wet=0.20)

        if tone_cat == "ecchi":
            noise     = np.random.normal(0, 0.015, len(y_emotion))
            breath    = butter_filter(noise, sr, 3500, "high")
            y_emotion = np.clip(y_emotion + breath * 0.25, -0.95, 0.95)

        if t_cfg["pitch"] != 0:
            y_emotion = safe_pitch_shift(y_emotion, sr, n_steps=t_cfg["pitch"])

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

    # Ensure emotion stage doesn't change the length
    y_emotion = _exact_length(y_emotion, int(target_dur * sr))
    sf.write(emot_path, y_emotion, sr)

    # ── STAGE 4: AGE / TYPE TRANSFORMATION ───────────────────
    if AGE_ENABLED and age_category != "adult":
        method_age = "kNN-VC" if (USE_KNNVC and knnvc_ref) else "DSP"
        print(f"  [4] Age: {age_category}  [{method_age}]")
        apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
        y_final, sr_f = librosa.load(age_path, sr=None, mono=True)
        # Re-align to exact length after age transform (Praat may shift length slightly)
        y_final = _exact_length(y_final, int(target_dur * sr_f))
        sf.write(age_path, y_final, sr_f)
        sr_final = sr_f
    else:
        label = "DISABLED" if not AGE_ENABLED else "adult/pass-through"
        print(f"  [4] Age: {label}")
        y_final  = y_emotion
        sr_final = sr

    sf.write(final_path, y_final, sr_final)
    dur_final = len(y_final) / sr_final

    if dur_final < 0.15:
        qc_flags.append("TOO_SHORT")

    # Final length verification
    final_drift_ms = abs(dur_final - target_dur) * 1000
    print(f"  ✓  final: {dur_final:.4f}s / {target_dur:.4f}s  "
          f"(drift: {final_drift_ms:.1f}ms)")

    # ── METADATA ─────────────────────────────────────────────
    clip_meta = {
        "segment_id":           sid,
        "speaker":              speaker,
        "start":                seg["start"],
        "end":                  seg["end"],
        "duration_target":      round(target_dur, 4),
        "duration_raw_trimmed": round(raw_dur, 4),
        "duration_final":       round(dur_final, 4),
        "duration_drift_ms":    round(final_drift_ms, 2),
        "stretch_ratio":        round(ratio, 4),
        "stretch_engine":       "rubberband" if HAVE_RUBBERBAND else "scipy",
        "voice_sample":         os.path.basename(voice_sample),
        "language_mode":        LANGUAGE_MODE,
        "tts_method":           tts_method,
        "text":                 dub_text,
        "emotion":              emotion,
        "emotion_effective":    eff_emotion if EMOTION_ENABLED else "disabled",
        "emotion_confidence":   round(emotion_conf, 4),
        "emotion_enabled":      EMOTION_ENABLED,
        "age_category":         age_category,
        "age_enabled":          AGE_ENABLED,
        "tone_category":        tone_cat,
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
        print(f"  [WARN] {qc_flags}")
    else:
        print(f"  [OK]")

# ─────────────────────────────────────────────────────────────
# SAVE METADATA
# ─────────────────────────────────────────────────────────────
meta = {
    "timestamp":       datetime.now().isoformat(),
    "version":         "3.0",
    "total_clips":     len(generated_clips),
    "language_mode":   LANGUAGE_MODE,
    "tts_language":    TTS_LANGUAGE,
    "stretch_engine":  "rubberband" if HAVE_RUBBERBAND else "scipy",
    "emotion_enabled": EMOTION_ENABLED,
    "age_enabled":     AGE_ENABLED,
    "clips":           generated_clips,
}
meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"STEP 4 v3 COMPLETE — {len(generated_clips)} clips  [{LANGUAGE_MODE}]")
print(f"Audio     : {OUTPUT_DIR}/")
print(f"Metadata  : {meta_path}")
print(f"Waveforms : {WAVEFORM_DIR}/")

if qc_flags_all:
    print(f"\nQC FLAGS ({len(qc_flags_all)} segments):")
    for sid, flags in sorted(qc_flags_all):
        print(f"  [seg {sid:03d}] {flags}")
else:
    print("\nAll segments passed QC ✓")

print("\nNext → step5_assembly.py")