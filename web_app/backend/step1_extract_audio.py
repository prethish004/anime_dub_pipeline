"""
step1_extract_audio.py
======================
Modular Backend Step 1: Audio Extraction + Demucs 6-stem Separation + Silero VAD
"""

import os
import sys
import json
import torch
import torchaudio
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def run_step1(options: dict) -> bool:
    print("=" * 60)
    print("STEP 1: Audio Extraction & Source Separation")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    video_file = options.get("video_file")
    if not video_file or not os.path.exists(video_file):
        video_file = os.path.join(PROJECT_ROOT, "input", "anime.mp4")

    if not os.path.exists(video_file):
        print(f"❌ ERROR: Video file not found at {video_file}")
        return False

    stems_dir = os.path.join(work_dir, "stems")
    os.makedirs(stems_dir, exist_ok=True)

    raw_audio = os.path.join(work_dir, "raw_audio_44k.wav")
    output_vocals = os.path.join(work_dir, "vocals_clean.wav")
    output_bg = os.path.join(work_dir, "background_full.wav")
    metadata_json = os.path.join(work_dir, "step1_metadata.json")

    # 1. Extract raw audio via ffmpeg
    print(f"\n🎵 1. Extracting raw audio from {video_file}...")
    import subprocess
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            raw_audio,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ ffmpeg failed: {result.stderr[-500:]}")
        return False

    info = torchaudio.info(raw_audio)
    raw_duration_s = info.num_frames / info.sample_rate
    print(f"  ✓ Raw audio extracted: {raw_audio} ({raw_duration_s:.2f}s, {info.sample_rate}Hz)")

    model_name = "htdemucs" if not torch.cuda.is_available() else "htdemucs_6s"
    print(f"\n🎼 2. Demucs {model_name} source separation...")
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    demucs_model = get_model(model_name)
    demucs_model.eval()
    if torch.cuda.is_available():
        demucs_model.cuda()
        print("  Running Demucs on GPU ✓")
    else:
        print("  Running Demucs on CPU (Fast Mode) ✓")


    waveform, sr = torchaudio.load(raw_audio)
    if sr != demucs_model.samplerate:
        waveform = torchaudio.functional.resample(waveform, sr, demucs_model.samplerate)
        sr = demucs_model.samplerate

    if waveform.shape[0] == 1:
        waveform = waveform.repeat(2, 1)

    device = next(demucs_model.parameters()).device
    waveform = waveform.to(device)

    print("  Separating sources...")
    with torch.no_grad():
        sources = apply_model(demucs_model, waveform.unsqueeze(0), progress=True, num_workers=0)
    sources = sources.squeeze(0).cpu()

    stem_names = demucs_model.sources
    demucs_out_dir = os.path.join(stems_dir, model_name, "raw_audio_44k")
    os.makedirs(demucs_out_dir, exist_ok=True)

    stem_paths = {}
    for idx, stem in enumerate(stem_names):
        out_p = os.path.join(demucs_out_dir, f"{stem}.wav")
        torchaudio.save(out_p, sources[idx], sr)
        stem_paths[stem] = out_p
        print(f"  ✓ Stem: {stem:<8} -> {out_p}")

    del sources, waveform, demucs_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Silero VAD on Vocals
    print("\n🎤 3. Silero VAD speech detection...")
    from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

    vad_sr = 16000
    vocals_audio = read_audio(stem_paths["vocals"], sampling_rate=vad_sr)
    vad_model = load_silero_vad()

    speech_timestamps = get_speech_timestamps(
        vocals_audio,
        vad_model,
        sampling_rate=vad_sr,
        min_speech_duration_ms=200,
        max_speech_duration_s=15.0,
        window_size_samples=512,
        speech_pad_ms=80,
        return_seconds=True,
    )

    total_speech_s = sum(t["end"] - t["start"] for t in speech_timestamps)
    print(f"  ✓ Found {len(speech_timestamps)} voiced segments ({total_speech_s:.1f}s speech)")

    # 4. Export vocals_clean.wav
    print("\n🎯 4. Building vocals_clean.wav...")
    if not speech_timestamps:
        torchaudio.save(output_vocals, vocals_audio.unsqueeze(0), vad_sr)
    else:
        silence_gap = torch.zeros(int(0.05 * vad_sr))
        chunks = []
        for i, ts in enumerate(speech_timestamps):
            s_idx = max(0, int(ts["start"] * vad_sr))
            e_idx = min(len(vocals_audio), int(ts["end"] * vad_sr))
            chunk = vocals_audio[s_idx:e_idx]
            if chunk.numel() >= int(0.05 * vad_sr):
                chunks.append(chunk)
                if i < len(speech_timestamps) - 1:
                    chunks.append(silence_gap)

        if chunks:
            speech_tensor = torch.cat(chunks)
            peak = speech_tensor.abs().max()
            if peak > 0:
                speech_tensor = speech_tensor * (10 ** (-3.0 / 20.0) / peak)
            torchaudio.save(output_vocals, speech_tensor.unsqueeze(0), vad_sr)
        else:
            torchaudio.save(output_vocals, vocals_audio.unsqueeze(0), vad_sr)

    # 5. Merge Background Stems
    print("\n🎧 5. Building background_full.wav...")
    import gc
    gc.collect()

    bg_stems = ["drums", "bass", "other", "guitar", "piano"]
    bg_tensor = None
    bg_sr = None

    try:
        for stem in bg_stems:
            path = stem_paths.get(stem)
            if not path or not os.path.exists(path):
                continue
            wf, sr_stem = torchaudio.load(path)
            if bg_sr is None:
                bg_sr = sr_stem
            elif sr_stem != bg_sr:
                wf = torchaudio.functional.resample(wf, sr_stem, bg_sr)

            if wf.shape[0] == 1:
                wf = wf.repeat(2, 1)

            if bg_tensor is None:
                bg_tensor = wf
            else:
                max_len = max(bg_tensor.shape[1], wf.shape[1])
                if bg_tensor.shape[1] < max_len:
                    bg_tensor = torch.nn.functional.pad(bg_tensor, (0, max_len - bg_tensor.shape[1]))
                if wf.shape[1] < max_len:
                    wf = torch.nn.functional.pad(wf, (0, max_len - wf.shape[1]))
                bg_tensor = bg_tensor + wf

        if bg_tensor is None:
            bg_sr = 44100
            bg_tensor = torch.zeros(2, int(raw_duration_s * bg_sr))

        peak = bg_tensor.abs().max()
        if peak > 0:
            bg_tensor = bg_tensor * (10 ** (-6.0 / 20.0) / peak)

        torchaudio.save(output_bg, bg_tensor.clamp(-1.0, 1.0), bg_sr)
    except Exception as e:
        print(f"  ⚠️ Warning in background stem merging: {e}. Generating silent background fallback.")
        bg_sr = 44100
        bg_tensor = torch.zeros(2, int(raw_duration_s * bg_sr))
        torchaudio.save(output_bg, bg_tensor, bg_sr)


    metadata = {
        "timestamp": datetime.now().isoformat(),
        "video_file": str(video_file),
        "video_duration_s": round(raw_duration_s, 3),
        "outputs": {
            "vocals_clean": output_vocals,
            "background_full": output_bg,
        },
        "vad": {
            "total_segments": len(speech_timestamps),
            "total_speech_s": round(total_speech_s, 3),
        }
    }
    with open(metadata_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Step 1 Complete! Workspace: {work_dir}")
    return True
