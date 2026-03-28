
import os
import json
import torch
import torchaudio
import librosa
from pyannote.audio import Pipeline
from transformers import pipeline
import numpy as np
from pydub import AudioSegment
from datetime import datetime

print("="*60)
print("STEP 2: Speaker Diarization + Gender Detection")
print("="*60)

# CONFIG
VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio/vocals.wav"
OUTPUT_JSON = "work/transcription_with_speakers.json"
SPEAKER_DIR = "work/speaker_segments"
PROFILES_JSON = "work/speaker_profiles.json"

os.makedirs(SPEAKER_DIR, exist_ok=True)

# 🔥 HuggingFace token (get free at huggingface.co/settings/tokens)
HF_TOKEN = "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"  # Replace with your token

# Load models
print("🔄 Loading models...")

# Pyannote speaker diarization
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN
)

# Whisper transcription
whisper_pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-large-v3-turbo",
    device=0 if torch.cuda.is_available() else -1
)

# Gender detection
gender_pipe = pipeline(
    "audio-classification",
    model="alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech",
    device=0 if torch.cuda.is_available() else -1
)

print("✅ Models loaded")

# Load vocals audio
print(f"\n🎤 Processing: {VOCALS_PATH}")
audio, sr = librosa.load(VOCALS_PATH, sr=16000)

# 1. SPEAKER DIARIZATION
print("\n👥 1. Speaker diarization...")
import torchaudio

waveform, sample_rate = torchaudio.load(VOCALS_PATH)

diarization = diarization_pipeline({
    "waveform": waveform,
    "sample_rate": sample_rate
})
print(type(diarization))
print(dir(diarization))
# speakers = set()
# segments = []

# for turn, _, speaker in diarization.itertracks(yield_label=True):
#     speakers.add(speaker)
#     segments.append({
#         "start": float(turn.start),
#         "end": float(turn.end),
#         "speaker": speaker,
#         "duration": float(turn.end - turn.start)
#     })
# for segment, track, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
#     segments.append({
#         "start": float(segment.start),
#         "end": float(segment.end),
#         "speaker": speaker,
#         "duration": float(segment.end - segment.start)
#     })
speakers = set()
segments = []

for segment, track, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
    duration = float(segment.end - segment.start)

    if duration < 0.2:
        continue

    speakers.add(speaker)  # ✅ THIS WAS MISSING / BROKEN

    segments.append({
        "start": float(segment.start),
        "end": float(segment.end),
        "speaker": speaker,
        "duration": duration
    })
print(f"✅ Found {len(speakers)} speakers: {sorted(speakers)}")
print(f"✅ {len(segments)} segments")

# 2. TRANSCRIBE + GENDER PER SEGMENT
print("\n📝 2. Transcribing segments + gender...")

transcribed_segments = []
speaker_profiles = {spk: {"segments": [], "gender": None, "confidence": 0.0} for spk in speakers}

for i, seg in enumerate(segments):
    print(f"  Segment {i+1}/{len(segments)}: {seg['speaker']} {seg['start']:.1f}s-{seg['end']:.1f}s")
    
    # Extract segment audio (1s context before/after)
    start_pad = max(0, seg['start'] - 0.5)
    end_pad = min(len(audio), seg['end'] + 0.5)
    seg_audio = audio[int(start_pad*sr):int(end_pad*sr)]
    
    # Whisper transcription
    whisper_input = seg_audio.astype(np.float32)
    transcription = whisper_pipe(
        whisper_input, 
        generate_kwargs={"language": "ja", "task": "transcribe"}
    )
    text = transcription["text"].strip()
    
    # Gender detection
    # gender_result = gender_pipe(whisper_input)
    gender_result = gender_pipe({
    "array": whisper_input,
    "sampling_rate": 16000})
    gender = gender_result[0]['label']  # 'male' or 'female'
    gender_conf = gender_result[0]['score']
    
    # Update speaker profile
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
        "gender_confidence": gender_conf
    })
    
    print(f"    → '{text[:50]}...' | Gender: {gender} ({gender_conf:.2f})")

# 3. SAVE INDIVIDUAL SPEAKER AUDIO
print("\n🎵 3. Saving per-speaker segments...")
for spk in speakers:
    spk_segments = [s for s in transcribed_segments if s['speaker'] == spk]
    spk_audio = []
    
    for seg in spk_segments:
        s_idx = int(seg['start'] * sr)
        e_idx = int(seg['end'] * sr)
        chunk = audio[s_idx:e_idx]
        spk_audio.append(chunk)
    
    if spk_audio:
        spk_tensor = torch.tensor(np.concatenate(spk_audio)).unsqueeze(0)
        output_path = os.path.join(SPEAKER_DIR, f"{spk}.wav")
        torchaudio.save(output_path, spk_tensor, sr)
        speaker_profiles[spk]['audio_file'] = output_path
        print(f"✅ {spk}: {len(spk_segments)} segments → {output_path}")

# 4. SAVE FINAL OUTPUTS
print("\n💾 4. Saving results...")

final_output = {
    "timestamp": datetime.now().isoformat(),
    "total_segments": len(transcribed_segments),
    "speakers": list(speakers),
    "segments": transcribed_segments,
    "speaker_profiles": speaker_profiles
}

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

with open(PROFILES_JSON, 'w') as f:
    json.dump(speaker_profiles, f, indent=2)

print(f"\n✅ STEP 2 COMPLETE!")
print(f"📊 Segments: {len(transcribed_segments)}")
print(f"📁 Output: {OUTPUT_JSON}")
print(f"📁 Speakers: {SPEAKER_DIR}/")
print("="*60)