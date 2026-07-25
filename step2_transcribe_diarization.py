
# import os
# import json
# import torch
# import torchaudio
# import librosa
# from pyannote.audio import Pipeline
# from transformers import pipeline
# import numpy as np
# from pydub import AudioSegment
# from datetime import datetime

# print("="*60)
# print("STEP 2: Speaker Diarization + Gender Detection")
# print("="*60)

# # CONFIG
# VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio/vocals.wav"
# OUTPUT_JSON = "work/transcription_with_speakers.json"
# SPEAKER_DIR = "work/speaker_segments"
# PROFILES_JSON = "work/speaker_profiles.json"

# os.makedirs(SPEAKER_DIR, exist_ok=True)

# # 🔥 HuggingFace token (get free at huggingface.co/settings/tokens)
# HF_TOKEN = "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"  # Replace with your token

# # Load models
# print("🔄 Loading models...")

# # Pyannote speaker diarization
# diarization_pipeline = Pipeline.from_pretrained(
#     "pyannote/speaker-diarization-3.1",
#     token=HF_TOKEN
# )

# # Whisper transcription
# whisper_pipe = pipeline(
#     "automatic-speech-recognition",
#     model="openai/whisper-large-v3-turbo",
#     device=0 if torch.cuda.is_available() else -1
# )

# # Gender detection
# gender_pipe = pipeline(
#     "audio-classification",
#     model="alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech",
#     device=0 if torch.cuda.is_available() else -1
# )

# print("✅ Models loaded")

# # Load vocals audio
# print(f"\n🎤 Processing: {VOCALS_PATH}")
# audio, sr = librosa.load(VOCALS_PATH, sr=16000)

# # 1. SPEAKER DIARIZATION
# print("\n👥 1. Speaker diarization...")
# import torchaudio

# waveform, sample_rate = torchaudio.load(VOCALS_PATH)

# diarization = diarization_pipeline({
#     "waveform": waveform,
#     "sample_rate": sample_rate
# })
# print(type(diarization))
# print(dir(diarization))
# # speakers = set()
# # segments = []

# # for turn, _, speaker in diarization.itertracks(yield_label=True):
# #     speakers.add(speaker)
# #     segments.append({
# #         "start": float(turn.start),
# #         "end": float(turn.end),
# #         "speaker": speaker,
# #         "duration": float(turn.end - turn.start)
# #     })
# # for segment, track, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
# #     segments.append({
# #         "start": float(segment.start),
# #         "end": float(segment.end),
# #         "speaker": speaker,
# #         "duration": float(segment.end - segment.start)
# #     })
# speakers = set()
# segments = []

# for segment, track, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
#     duration = float(segment.end - segment.start)

#     if duration < 0.2:
#         continue

#     speakers.add(speaker)  # ✅ THIS WAS MISSING / BROKEN

#     segments.append({
#         "start": float(segment.start),
#         "end": float(segment.end),
#         "speaker": speaker,
#         "duration": duration
#     })
# print(f"✅ Found {len(speakers)} speakers: {sorted(speakers)}")
# print(f"✅ {len(segments)} segments")

# # 2. TRANSCRIBE + GENDER PER SEGMENT
# print("\n📝 2. Transcribing segments + gender...")

# transcribed_segments = []
# speaker_profiles = {spk: {"segments": [], "gender": None, "confidence": 0.0} for spk in speakers}

# for i, seg in enumerate(segments):
#     print(f"  Segment {i+1}/{len(segments)}: {seg['speaker']} {seg['start']:.1f}s-{seg['end']:.1f}s")
    
#     # Extract segment audio (1s context before/after)
#     start_pad = max(0, seg['start'] - 0.5)
#     end_pad = min(len(audio), seg['end'] + 0.5)
#     seg_audio = audio[int(start_pad*sr):int(end_pad*sr)]
    
#     # Whisper transcription
#     whisper_input = seg_audio.astype(np.float32)
#     transcription = whisper_pipe(
#         whisper_input, 
#         generate_kwargs={"language": "ja", "task": "transcribe"}
#     )
#     text = transcription["text"].strip()
    
#     # Gender detection
#     # gender_result = gender_pipe(whisper_input)
#     gender_result = gender_pipe({
#     "array": whisper_input,
#     "sampling_rate": 16000})
#     gender = gender_result[0]['label']  # 'male' or 'female'
#     gender_conf = gender_result[0]['score']
    
#     # Update speaker profile
#     speaker_profiles[seg['speaker']]['gender'] = gender
#     speaker_profiles[seg['speaker']]['confidence'] = max(
#         speaker_profiles[seg['speaker']]['confidence'], gender_conf
#     )
    
#     transcribed_segments.append({
#         "id": i,
#         "start": seg['start'],
#         "end": seg['end'],
#         "duration": seg['duration'],
#         "speaker": seg['speaker'],
#         "text": text,
#         "gender": gender,
#         "gender_confidence": gender_conf
#     })
    
#     print(f"    → '{text[:50]}...' | Gender: {gender} ({gender_conf:.2f})")

# # 3. SAVE INDIVIDUAL SPEAKER AUDIO
# print("\n🎵 3. Saving per-speaker segments...")
# for spk in speakers:
#     spk_segments = [s for s in transcribed_segments if s['speaker'] == spk]
#     spk_audio = []
    
#     for seg in spk_segments:
#         s_idx = int(seg['start'] * sr)
#         e_idx = int(seg['end'] * sr)
#         chunk = audio[s_idx:e_idx]
#         spk_audio.append(chunk)
    
#     if spk_audio:
#         spk_tensor = torch.tensor(np.concatenate(spk_audio)).unsqueeze(0)
#         output_path = os.path.join(SPEAKER_DIR, f"{spk}.wav")
#         torchaudio.save(output_path, spk_tensor, sr)
#         speaker_profiles[spk]['audio_file'] = output_path
#         print(f"✅ {spk}: {len(spk_segments)} segments → {output_path}")

# # 4. SAVE FINAL OUTPUTS
# print("\n💾 4. Saving results...")

# final_output = {
#     "timestamp": datetime.now().isoformat(),
#     "total_segments": len(transcribed_segments),
#     "speakers": list(speakers),
#     "segments": transcribed_segments,
#     "speaker_profiles": speaker_profiles
# }

# with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#     json.dump(final_output, f, ensure_ascii=False, indent=2)

# with open(PROFILES_JSON, 'w') as f:
#     json.dump(speaker_profiles, f, indent=2)

# print(f"\n✅ STEP 2 COMPLETE!")
# print(f"📊 Segments: {len(transcribed_segments)}")
# print(f"📁 Output: {OUTPUT_JSON}")
# print(f"📁 Speakers: {SPEAKER_DIR}/")
# print("="*60)
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
print("STEP 2 v3: Speaker Diarization + Gender + Word Timestamps")
print("="*60)

# CONFIG
VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio_44k/vocals.wav"
OUTPUT_JSON = "work/transcription_with_speakers.json"
SPEAKER_DIR = "work/speaker_segments"
PROFILES_JSON = "work/speaker_profiles.json"

os.makedirs(SPEAKER_DIR, exist_ok=True)

HF_TOKEN = "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"

# Load models
print("🔄 Loading models...")

diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN
)

whisper_pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-large-v3-turbo",
    device=0 if torch.cuda.is_available() else -1
)

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
waveform, sample_rate = torchaudio.load(VOCALS_PATH)
diarization = diarization_pipeline({
    "waveform": waveform,
    "sample_rate": sample_rate
})

speakers = set()
segments = []

for segment, track, speaker in diarization.itertracks(yield_label=True):
    duration = float(segment.end - segment.start)
    if duration < 0.2:
        continue
    speakers.add(speaker)
    segments.append({
        "start": float(segment.start),
        "end": float(segment.end),
        "speaker": speaker,
        "duration": duration
    })

print(f"✅ Found {len(speakers)} speakers: {sorted(speakers)}")
print(f"✅ {len(segments)} segments")

# 2. TRANSCRIBE WITH WORD TIMESTAMPS + GENDER
print("\n📝 2. Transcribing with word-level timestamps + gender...")

transcribed_segments = []
speaker_profiles = {spk: {"segments": [], "gender": None, "confidence": 0.0} for spk in speakers}

for i, seg in enumerate(segments):
    print(f"  Segment {i+1}/{len(segments)}: {seg['speaker']} {seg['start']:.2f}s–{seg['end']:.2f}s")

    # Extract segment audio with small padding
    start_pad = max(0, seg['start'] - 0.5)
    end_pad = min(len(audio) / sr, seg['end'] + 0.5)
    seg_audio = audio[int(start_pad * sr):int(end_pad * sr)].astype(np.float32)

    # ✅ v3: Word-level timestamps
    result = whisper_pipe(
        seg_audio,
        return_timestamps="word",                              # KEY CHANGE
        generate_kwargs={"language": "ja", "task": "transcribe"}
    )

    text = result["text"].strip()
    raw_chunks = result.get("chunks", [])   # each chunk = one word with timestamps

    # Offset word times back to absolute audio position
    # (Whisper times are relative to the padded clip start)
    time_offset = start_pad
    words = []
    for chunk in raw_chunks:
        ts = chunk.get("timestamp", (None, None))
        word_start, word_end = ts if ts else (None, None)

        words.append({
            "word": chunk["text"].strip(),
            "start": round(word_start + time_offset, 3) if word_start is not None else None,
            "end":   round(word_end   + time_offset, 3) if word_end   is not None else None,
        })

    # Gender detection
    gender_result = gender_pipe({"array": seg_audio, "sampling_rate": 16000})
    gender = gender_result[0]['label']
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
        "gender_confidence": gender_conf,
        "words": words,           # ✅ NEW in v3
        "word_count": len(words)  # ✅ handy for next steps
    })

    # Pretty print word timing for debugging
    print(f"    → '{text[:50]}' | {len(words)} words | {gender} ({gender_conf:.2f})")
    for w in words[:5]:  # show first 5 words
        print(f"       [{w['start']}s → {w['end']}s] {w['word']}")

# 3. SAVE PER-SPEAKER AUDIO (unchanged from v2)
print("\n🎵 3. Saving per-speaker segments...")
for spk in speakers:
    spk_segments = [s for s in transcribed_segments if s['speaker'] == spk]
    spk_audio = []
    for seg in spk_segments:
        s_idx = int(seg['start'] * sr)
        e_idx = int(seg['end'] * sr)
        spk_audio.append(audio[s_idx:e_idx])

    if spk_audio:
        spk_tensor = torch.tensor(np.concatenate(spk_audio)).unsqueeze(0)
        output_path = os.path.join(SPEAKER_DIR, f"{spk}.wav")
        torchaudio.save(output_path, spk_tensor, sr)
        speaker_profiles[spk]['audio_file'] = output_path
        print(f"✅ {spk}: {len(spk_segments)} segments → {output_path}")

# 4. SAVE OUTPUTS
print("\n💾 4. Saving results...")

final_output = {
    "timestamp": datetime.now().isoformat(),
    "version": "3.0",
    "total_segments": len(transcribed_segments),
    "speakers": list(speakers),
    "segments": transcribed_segments,
    "speaker_profiles": speaker_profiles
}

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

with open(PROFILES_JSON, 'w') as f:
    json.dump(speaker_profiles, f, indent=2)

print(f"\n✅ STEP 2 v3 COMPLETE!")
print(f"📊 Segments: {len(transcribed_segments)}")
print(f"📁 Output: {OUTPUT_JSON}")
print("="*60)