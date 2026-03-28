# # # step1_extract_audio.py
# # import ffmpeg
# # import os
# # from pydub import AudioSegment

# # # Configuration
# # INPUT_VIDEO = "input/Seikon no Qwaser - S01E01 - [9DBF3AAE] (online-video-cutter.com).mp4"
# # OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
# # OUTPUT_AUDIO_16K = "work/audio_16k.wav"

# # def extract_audio():
# #     """Extract audio from video file"""
    
# #     if not os.path.exists(INPUT_VIDEO):
# #         print(f"❌ Input video not found: {INPUT_VIDEO}")
# #         print("Please place your anime file in the 'input/' folder")
# #         return False
    
# #     print(f"📹 Processing: {INPUT_VIDEO}")
# #     print("⏳ Extracting audio...")
    
# #     try:
# #         # Extract audio using ffmpeg
# #         stream = ffmpeg.input(INPUT_VIDEO)
# #         stream = ffmpeg.output(
# #             stream, 
# #             OUTPUT_AUDIO_RAW,
# #             acodec='pcm_s16le',  # 16-bit PCM
# #             ar=44100,            # 44.1kHz (will resample later)
# #             ac=2                 # Stereo (will convert to mono later)
# #         )
# #         ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
# #         print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
        
# #     except ffmpeg.Error as e:
# #         print(f"❌ FFmpeg error: {e.stderr.decode()}")
# #         return False
    
# #     return True

# # def resample_audio():
# #     """Convert to mono 16kHz (optimal for speech models)"""
    
# #     print("⏳ Resampling to 16kHz mono...")
    
# #     try:
# #         # Load audio
# #         audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)
        
# #         # Convert to mono
# #         audio = audio.set_channels(1)
        
# #         # Resample to 16kHz
# #         audio = audio.set_frame_rate(16000)
        
# #         # Export
# #         audio.export(OUTPUT_AUDIO_16K, format='wav')
        
# #         # Get duration
# #         duration_sec = len(audio) / 1000
        
# #         print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
# #         print(f"📊 Duration: {duration_sec:.1f} seconds ({duration_sec/60:.1f} minutes)")
# #         print(f"📊 Sample rate: 16000 Hz")
# #         print(f"📊 Channels: 1 (mono)")
        
# #     except Exception as e:
# #         print(f"❌ Resampling error: {e}")
# #         return False
    
# #     return True

# # def main():
# #     print("=" * 60)
# #     print("STEP 1: Audio Extraction & Preprocessing")
# #     print("=" * 60)
    
# #     # Extract audio
# #     if not extract_audio():
# #         return
    
# #     # Resample
# #     if not resample_audio():
# #         return
    
# #     print("\n" + "=" * 60)
# #     print("✅ Step 1 Complete!")
# #     print("=" * 60)
# #     print(f"Next: Run step2_transcribe.py")

# # if __name__ == "__main__":
# #     main()
# # step1_audio_pipeline.py

# import os
# import ffmpeg
# import subprocess
# from pydub import AudioSegment
# import librosa
# import soundfile as sf

# # -------------------------------------------------
# # CONFIGURATION
# # -------------------------------------------------
# INPUT_VIDEO = "input/anime.mp4"
# OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
# OUTPUT_AUDIO_16K = "work/audio_16k.wav"

# # -------------------------------------------------
# # STEP 1: EXTRACT AUDIO FROM VIDEO
# # -------------------------------------------------
# def extract_audio():
#     if not os.path.exists(INPUT_VIDEO):
#         print(f"❌ Input video not found: {INPUT_VIDEO}")
#         return False

#     print(f"📹 Processing: {INPUT_VIDEO}")
#     print("⏳ Extracting audio...")

#     try:
#         stream = ffmpeg.input(INPUT_VIDEO)
#         stream = ffmpeg.output(
#             stream,
#             OUTPUT_AUDIO_RAW,
#             acodec='pcm_s16le',
#             ar=44100,
#             ac=2
#         )
#         ffmpeg.run(stream, overwrite_output=True,
#                    capture_stdout=True, capture_stderr=True)

#         print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
#         return True

#     except ffmpeg.Error as e:
#         print(f"❌ FFmpeg error: {e.stderr.decode()}")
#         return False


# # -------------------------------------------------
# # STEP 2: RESAMPLE TO 16kHz MONO
# # -------------------------------------------------
# def resample_audio():
#     print("⏳ Resampling to 16kHz mono...")

#     try:
#         audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)

#         audio = audio.set_channels(1)
#         audio = audio.set_frame_rate(16000)

#         audio.export(OUTPUT_AUDIO_16K, format='wav')

#         duration_sec = len(audio) / 1000

#         print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
#         print(f"📊 Duration: {duration_sec:.1f} sec")
#         print(f"📊 Sample rate: 16000 Hz")
#         print(f"📊 Channels: 1 (mono)")

#         return True

#     except Exception as e:
#         print(f"❌ Resampling error: {e}")
#         return False


# # -------------------------------------------------
# # STEP 3: RUN DEMUCS SEPARATION
# # -------------------------------------------------
# def run_demucs():
#     print("🎧 Starting separation with Demucs...")

#     try:
#         subprocess.run([
#             "demucs",
#             "-n", "htdemucs",
#             OUTPUT_AUDIO_16K
#         ], check=True)

#         print("✅ Separation complete!")
#         return True

#     except subprocess.CalledProcessError as e:
#         print(f"❌ Demucs error: {e}")
#         return False


# # -------------------------------------------------
# # STEP 4: MERGE BACKGROUND TRACKS
# # -------------------------------------------------
# def merge_background():
#     print("🔊 Merging background tracks...")

#     file_name = os.path.splitext(os.path.basename(OUTPUT_AUDIO_16K))[0]
#     base_output = f"separated/htdemucs/{file_name}/"

#     vocals_path = os.path.join(base_output, "vocals.wav")
#     drums_path = os.path.join(base_output, "drums.wav")
#     bass_path = os.path.join(base_output, "bass.wav")
#     other_path = os.path.join(base_output, "other.wav")

#     try:
#         vocals, sr = librosa.load(vocals_path, sr=None)
#         drums, _ = librosa.load(drums_path, sr=None)
#         bass, _ = librosa.load(bass_path, sr=None)
#         other, _ = librosa.load(other_path, sr=None)

#         # Prevent clipping
#         background = (drums + bass + other) / 3

#         sf.write("background_noise.wav", background, sr)

#         print("💾 Saved Outputs:")
#         print(f"   - Vocals: {vocals_path}")
#         print("   - Background: background_noise.wav")

#         return True

#     except Exception as e:
#         print(f"❌ Background merge error: {e}")
#         return False


# # -------------------------------------------------
# # MAIN PIPELINE
# # -------------------------------------------------
# def main():
#     print("=" * 60)
#     print("🎬 FULL AUDIO PROCESSING PIPELINE")
#     print("=" * 60)

#     if not extract_audio():
#         return

#     if not resample_audio():
#         return

#     if not run_demucs():
#         return

#     if not merge_background():
#         return

#     print("\n" + "=" * 60)
#     print("🚀 Pipeline Complete Successfully!")
#     print("=" * 60)


# if __name__ == "__main__":
#     main()

import os
import subprocess
import json
from pathlib import Path
import torchaudio
import torch
from pydub import AudioSegment
# from silero_vad.utils import init_jit_model, read_audio, get_speech_timestamps
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
print("="*60)
print("STEP 1: Audio Extraction + Source Separation")
print("="*60)

# ========================= CONFIG =========================
VIDEO_FILE = "input/anime.mp4"
WORK_DIR = "work"
STEMS_DIR = f"{WORK_DIR}/stems"
OUTPUT_SPEECH = f"{WORK_DIR}/speech_segments_16k.wav"
OUTPUT_BG = f"{WORK_DIR}/background_full.wav"

os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(STEMS_DIR, exist_ok=True)

# ========================= 1. EXTRACT RAW AUDIO =========================
print("\n🎵 1. Extracting raw audio from video...")
# subprocess.run([
#     'ffmpeg', '-i', VIDEO_FILE, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
#     f'{WORK_DIR}/raw_audio.wav', '-y'
# ], check=True)
result = subprocess.run(
    [
        'ffmpeg', '-i', VIDEO_FILE,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',   # ✅ better for ML
        '-ac', '1',
        f'{WORK_DIR}/raw_audio.wav',
        '-y'
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print(result.stderr)  # 🔥 CRITICAL

if result.returncode != 0:
    raise RuntimeError("FFmpeg extraction failed")
print("✅ Raw audio extracted")
import sys

# ========================= 2. DEMUCS SEPARATION =========================
print("\n🎼 2. Running Demucs htdemucs_6s...")
# if not os.path.exists("demucs"):
#     print("   Installing Demucs...")
#     subprocess.run(["pip", "install", "demucs"], check=True)

# subprocess.run([
#     "python", "-m", "demucs.separate", "--model", "htdemucs_6s",
#     "-n", "4", "--out", STEMS_DIR, f"{WORK_DIR}/raw_audio.wav"
# ], check=True)
# result = subprocess.run(
#     [
#         sys.executable, "-m", "demucs.separate",
#         "--model", "htdemucs_6s",
#         "-n", "4",
#         "--out", STEMS_DIR,
#         f"{WORK_DIR}/raw_audio.wav"
#     ],
#     ...
# )
import sys
import subprocess

result = subprocess.run(
    [
        sys.executable, "-m", "demucs.separate",
        "-n", "htdemucs_6s",   # ✅ correct flag
        "-j", "1",             # safer than -n 4
        "-o", STEMS_DIR,
        f"{WORK_DIR}/raw_audio.wav"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print(result.stdout)
print(result.stderr)

if result.returncode != 0:
    raise RuntimeError("Demucs separation failed")
# Expected stems: vocals.wav, drums.wav, bass.wav, other.wav, guitar.wav, piano.wav
print("✅ Demucs separation complete")

# ========================= 3. MERGE BACKGROUND =========================
print("\n🎧 3. Merging background stems...")
bg_files = [
    "drums.wav", "bass.wav", "other.wav", "guitar.wav", "piano.wav"
]
bg_paths = [os.path.join(STEMS_DIR, "htdemucs_6s", "raw_audio", f) for f in bg_files]

bg_audio = None
for bg_path in bg_paths:
    if os.path.exists(bg_path):
        audio = AudioSegment.from_file(bg_path)
        bg_audio = audio if bg_audio is None else bg_audio.overlay(audio, gain_during_overlay=-6)
        print(f"   ➕ {os.path.basename(bg_path)}")

if bg_audio is None:
    print("   ⚠️ No background stems found, creating silence")
    bg_audio = AudioSegment.silent(duration=10000)  # 10s placeholder

bg_audio.export(OUTPUT_BG, format="wav")
print(f"✅ Background saved: {OUTPUT_BG}")

# ========================= 4. SILERO VAD on VOCALS =========================
print("\n🎤 4. Silero VAD on vocals...")
# Demucs outputs stems under <STEMS_DIR>/htdemucs_6s/raw_audio
vocals_path = os.path.join(STEMS_DIR, "htdemucs_6s", "raw_audio", "vocals.wav")
# audio, sr = read_audio(vocals_path, sampling_rate=16000)
audio = read_audio(vocals_path, sampling_rate=16000)
sr = 16000
# model = init_jit_model("silero_vad")
# speech_timestamps = get_speech_timestamps(
#     audio, model, sampling_rate=sr,
#     min_speech_duration_ms=200,  # Ignore breaths
#     max_speech_duration_s=15.0,  # Max line length
#     window_size_samples=512
# )
model = load_silero_vad()

# Run VAD
# speech_timestamps = get_speech_timestamps(
#     audio,
#     model,
#     sampling_rate=sr,
#     min_speech_duration_ms=200,   # Ignore breaths
#     max_speech_duration_s=15.0,   # Max line length
#     window_size_samples=512
# )
speech_timestamps = get_speech_timestamps(
    audio,
    model,
    sampling_rate=sr,
    min_speech_duration_ms=200,
    max_speech_duration_s=15.0,
    window_size_samples=512,
    return_seconds=True   # 🔥 CRITICAL FIX
)

vad_data = {
    "total_voiced_segments": len(speech_timestamps),
    "segments": [{"start": t["start"], "end": t["end"], "duration": t["end"]-t["start"]} for t in speech_timestamps]
}
with open(f"{WORK_DIR}/vad_segments.json", 'w') as f:
    json.dump(vad_data, f, indent=2)

print(f"✅ Found {len(speech_timestamps)} voiced segments")

# ========================= 5. BEATs Event Labeling =========================
# print("\n🎭 5. BEATs event labeling on speech...")
# beats = pipeline("audio-classification", model="MIT/ast-finetuned-speech-commands-v2")

# event_labels = []
# for i, timestamp in enumerate(speech_timestamps):
#     start = timestamp["start"]
#     end = timestamp["end"]
    
#     # Extract segment (this is where you'd crop in production)
#     segment_path = f"{WORK_DIR}/temp_segment_{i}.wav"
#     # audio_segment = audio[int(start*sr):int(end*sr)]
#     audio_segment = audio[start:end]  
#     # torchaudio.save(segment_path, torch.tensor(audio_segment).unsqueeze(0), sr)
#     if not isinstance(audio_segment, torch.Tensor):
#         audio_segment = torch.tensor(audio_segment)

#     # Ensure shape = [1, samples]
#     audio_segment = audio_segment.unsqueeze(0)

#     # Skip empty segments
#     if audio_segment.shape[1] < 100:
#         continue

#     torchaudio.save(segment_path, audio_segment, sr)
#     # result = beats(segment_path)
#     result = beats({"array": audio_segment.numpy(),"sampling_rate": sr})
#     label = result[0]['label']  # speech, shout, laugh, singing, etc.
#     confidence = result[0]['score']
    
#     event_labels.append({
#         "segment_id": i,
#         "start": start,
#         "end": end,
#         "label": label,
#         "confidence": confidence
#     })
    
#     os.remove(segment_path)

# with open(f"{WORK_DIR}/event_labels.json", 'w') as f:
#     json.dump(event_labels, f, indent=2)
# # print("✅ Event labeling complete")
# print("\n🎭 5. BEATs event labeling on speech...")

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model_id = "MIT/ast-finetuned-speech-commands-v2"

# feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
# beats_model = AutoModelForAudioClassification.from_pretrained(model_id).to(device)
# beats_model.eval()

# event_labels = []

# for i, timestamp in enumerate(speech_timestamps):
#     start = timestamp["start"]
#     end = timestamp["end"]

#     audio_segment = audio[start:end]  # already samples at 16k
#     if not isinstance(audio_segment, torch.Tensor):
#         audio_segment = torch.tensor(audio_segment, dtype=torch.float32)

#     if audio_segment.numel() < 1600:  # <0.1s, skip tiny segments
#         continue

#     # Prepare model input
#     inputs = feature_extractor(
#         audio_segment.numpy(),
#         sampling_rate=sr,
#         return_tensors="pt",
#         padding=True
#     ).to(device)

#     with torch.no_grad():
#         logits = beats_model(**inputs).logits
#         probs = torch.softmax(logits, dim=-1)[0]
#         label_id = int(torch.argmax(probs))
#         label = beats_model.config.id2label[label_id]
#         confidence = float(probs[label_id])

#     event_labels.append({
#         "segment_id": i,
#         "start": start,
#         "end": end,
#         "label": label,
#         "confidence": confidence
#     })

# with open(f"{WORK_DIR}/event_labels.json", "w") as f:
#     json.dump(event_labels, f, indent=2)

# print("✅ Event labeling complete")
print("\n🎭 5. Emotion labeling on speech...")
import numpy as np
# Use wav2vec2 for speech/emotion detection (not command detection!)
model_id = "superb/wav2vec2-base-superb-er"  # Emotion Recognition (angry, happy, sad, neutral)
device = "cuda" if torch.cuda.is_available() else "cpu"

feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
emotion_model = AutoModelForAudioClassification.from_pretrained(model_id).to(device)
emotion_model.eval()

event_labels = []
SEGMENT_DIR = os.path.join(WORK_DIR, "segments")
os.makedirs(SEGMENT_DIR, exist_ok=True)

for i, ts in enumerate(speech_timestamps):
    start_sec = ts["start"]
    end_sec = ts["end"]
    
    # Convert seconds → sample indices
    s_idx = int(start_sec * sr)
    e_idx = int(end_sec * sr)
    
    audio_segment = audio[s_idx:e_idx]  # 1D torch tensor
    
    if not isinstance(audio_segment, torch.Tensor):
        audio_segment = torch.tensor(audio_segment, dtype=torch.float32)
    
    if audio_segment.numel() < int(0.1 * sr):  # <100ms → skip
        continue

    # 🔊 Save each VAD segment so you can listen
    seg_path = os.path.join(SEGMENT_DIR, f"segment_{i:03d}.wav")
    torchaudio.save(seg_path, audio_segment.unsqueeze(0), sr)
    
    # Model input
    inputs = feature_extractor(
        audio_segment.numpy(),
        sampling_rate=sr,
        return_tensors="pt",
        padding=True
    ).to(device)

# for i, timestamp in enumerate(speech_timestamps):
#     start = timestamp["start"]
#     end = timestamp["end"]
    
#     audio_segment = audio[start:end]
#     if not isinstance(audio_segment, torch.Tensor):
#         audio_segment = torch.tensor(audio_segment, dtype=torch.float32)
    
#     if audio_segment.numel() < 1600:
#         continue
    
#     # Model input
#     inputs = feature_extractor(
#         audio_segment.numpy(),
#         sampling_rate=sr,
#         return_tensors="pt",
#         padding=True
#     ).to(device)
    
    with torch.no_grad():
        logits = emotion_model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        label_id = int(torch.argmax(probs))
        label = emotion_model.config.id2label[label_id]
        confidence = float(probs[label_id])
    
    # ✅ Now you'll get: neutral, angry, happy, sad, surprise
    event_labels.append({
        "segment_id": i,
        "start": start_sec,
        "end": end_sec,
        "label": label,
        "confidence": confidence
    })
    
    print(f"Segment {i}: {label} ({confidence:.2f})")

with open(f"{WORK_DIR}/event_labels.json", 'w') as f:
    json.dump(event_labels, f, indent=2)

print("✅ Emotion labeling complete")

# ========================= 6. FILTER SPEECH → 16kHz MONO =========================
print("\n🎯 6. Extracting speech segments only...")
# speech_audio = []

# # Filter speech + expressive speech (not commands!)
# for event in event_labels:
#     if event["confidence"] > 0.3:  # Any confident emotion
#         start = event["start"]
#         end = event["end"]
#         audio_chunk = audio[int(start*sr):int(end*sr)]
#         speech_audio.append(audio_chunk)

# if speech_audio:
#     speech_tensor = torch.tensor(np.concatenate(speech_audio)).unsqueeze(0)
#     torchaudio.save(OUTPUT_SPEECH, speech_tensor, 16000)
#     print(f"✅ Speech-only audio saved: {OUTPUT_SPEECH}")
# else:
#     print("⚠️ No speech segments found!")
print("\n🎯 6. Extracting speech segments only...")
speech_audio = []

for event in event_labels:
    if event["confidence"] > 0.3:
        start_sec = event["start"]
        end_sec = event["end"]
        s_idx = int(start_sec * sr)
        e_idx = int(end_sec * sr)
        chunk = audio[s_idx:e_idx]
        if chunk.numel() > 0:
            speech_audio.append(chunk)

if speech_audio:
    # Concatenate all chunks
    speech_tensor = torch.cat(speech_audio).unsqueeze(0).to(torch.float32)

    # Simple normalization so you can hear it
    max_val = speech_tensor.abs().max()
    if max_val > 0:
        speech_tensor = speech_tensor / max_val

    torchaudio.save(OUTPUT_SPEECH, speech_tensor, sr)
    print(f"✅ Speech-only audio saved: {OUTPUT_SPEECH}")
else:
    print("⚠️ No speech segments found!")

print("\n" + "="*60)
print("✅ STEP 1 COMPLETE!")
print(f"📤 Ready for Step 2: {OUTPUT_SPEECH}")
print("="*60)
