"""
step2_transcribe.py
===================
Modular Backend Step 2: PyAnnote Diarization + Whisper Word Timestamps + Gender Classification
"""

import os
import sys
import json
import torch
import torchaudio
import librosa
import numpy as np
from pathlib import Path
from datetime import datetime
from transformers import pipeline
from pyannote.audio import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def run_step2(options: dict) -> bool:
    print("=" * 60)
    print("STEP 2: Diarization + Transcription + Gender Detection")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    vocals_path = os.path.join(work_dir, "stems", "htdemucs_6s", "raw_audio_44k", "vocals.wav")
    if not os.path.exists(vocals_path):
        vocals_path = os.path.join(work_dir, "stems", "htdemucs", "raw_audio_44k", "vocals.wav")
    if not os.path.exists(vocals_path):
        vocals_path = os.path.join(work_dir, "vocals_clean.wav")
    if not os.path.exists(vocals_path):
        vocals_path = os.path.join(work_dir, "raw_audio_44k.wav")


    if not os.path.exists(vocals_path):
        print(f"❌ ERROR: Vocals track not found at {vocals_path}")
        return False

    output_json = os.path.join(work_dir, "transcription_with_speakers.json")
    profiles_json = os.path.join(work_dir, "speaker_profiles.json")
    speaker_dir = os.path.join(work_dir, "speaker_segments")
    os.makedirs(speaker_dir, exist_ok=True)

    hf_token = options.get("hf_token", "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")

    print("🔄 Loading ML models (PyAnnote, Whisper Turbo, Wav2Vec2 Gender)...")
    device_idx = 0 if torch.cuda.is_available() else -1

    try:
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
    except Exception:
        try:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1"
            )
        except Exception as e:
            print(f"❌ Error loading PyAnnote pipeline: {e}")
            return False


    try:
        whisper_pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small",
            device=device_idx
        )
    except Exception:
        whisper_pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-tiny",
            device=device_idx
        )


    gender_pipe = pipeline(
        "audio-classification",
        model="alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech",
        device=device_idx
    )

    audio_np, sr = librosa.load(vocals_path, sr=16000)
    waveform, sample_rate = torchaudio.load(vocals_path)

    print("\n👥 1. Running speaker diarization...")
    diarization = diarization_pipeline({
        "waveform": waveform,
        "sample_rate": sample_rate
    })

    speakers = set()
    segments = []
    for segment, track, speaker in diarization.itertracks(yield_label=True):
        dur = float(segment.end - segment.start)
        if dur < 0.2:
            continue
        speakers.add(speaker)
        segments.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "speaker": speaker,
            "duration": round(dur, 3)
        })

    print(f"  ✓ Found {len(speakers)} speakers: {sorted(speakers)}")

    print("\n📝 2. Transcribing with word timestamps + gender classification...")
    transcribed_segments = []
    speaker_profiles = {spk: {"segments": [], "gender": "unknown", "confidence": 0.0} for spk in speakers}

    for i, seg in enumerate(segments):
        start_pad = max(0, seg['start'] - 0.5)
        end_pad = min(len(audio_np) / sr, seg['end'] + 0.5)
        seg_audio = audio_np[int(start_pad * sr):int(end_pad * sr)].astype(np.float32)

        result = whisper_pipe(
            seg_audio,
            return_timestamps="word",
            generate_kwargs={"language": "ja", "task": "transcribe"}
        )
        text = result["text"].strip()
        raw_chunks = result.get("chunks", [])

        words = []
        for chunk in raw_chunks:
            ts = chunk.get("timestamp", (None, None))
            w_start, w_end = ts if ts else (None, None)
            words.append({
                "word": chunk["text"].strip(),
                "start": round(w_start + start_pad, 3) if w_start is not None else None,
                "end": round(w_end + start_pad, 3) if w_end is not None else None,
            })

        gender_res = gender_pipe({"array": seg_audio, "sampling_rate": 16000})
        gender = gender_res[0]['label']
        gender_conf = float(gender_res[0]['score'])

        speaker_profiles[seg['speaker']]['gender'] = gender
        speaker_profiles[seg['speaker']]['confidence'] = max(
            speaker_profiles[seg['speaker']]['confidence'], gender_conf
        )

        transcribed_segments.append({
            "id": i,
            "start": seg['start'],
            "end": seg['end'],
            "duration": seg['duration'],
            "speaker": seg['speaker'],
            "text": text,
            "gender": gender,
            "gender_confidence": round(gender_conf, 3),
            "words": words,
            "word_count": len(words)
        })

    print("\n🎵 3. Saving per-speaker segment audio...")
    for spk in speakers:
        spk_segs = [s for s in transcribed_segments if s['speaker'] == spk]
        spk_chunks = [audio_np[int(s['start']*sr):int(s['end']*sr)] for s in spk_segs]
        if spk_chunks:
            spk_tensor = torch.tensor(np.concatenate(spk_chunks)).unsqueeze(0)
            out_p = os.path.join(speaker_dir, f"{spk}.wav")
            torchaudio.save(out_p, spk_tensor, sr)
            speaker_profiles[spk]['audio_file'] = os.path.relpath(out_p, str(PROJECT_ROOT)).replace("\\", "/")

    final_output = {
        "timestamp": datetime.now().isoformat(),
        "total_segments": len(transcribed_segments),
        "speakers": list(speakers),
        "segments": transcribed_segments,
        "speaker_profiles": speaker_profiles
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    with open(profiles_json, 'w', encoding='utf-8') as f:
        json.dump(speaker_profiles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Step 2 Complete! Workspace: {work_dir}")
    return True
