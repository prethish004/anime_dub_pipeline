# # # # step1_extract_audio.py
# # # import ffmpeg
# # # import os
# # # from pydub import AudioSegment

# # # # Configuration
# # # INPUT_VIDEO = "input/Seikon no Qwaser - S01E01 - [9DBF3AAE] (online-video-cutter.com).mp4"
# # # OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
# # # OUTPUT_AUDIO_16K = "work/audio_16k.wav"

# # # def extract_audio():
# # #     """Extract audio from video file"""
    
# # #     if not os.path.exists(INPUT_VIDEO):
# # #         print(f"❌ Input video not found: {INPUT_VIDEO}")
# # #         print("Please place your anime file in the 'input/' folder")
# # #         return False
    
# # #     print(f"📹 Processing: {INPUT_VIDEO}")
# # #     print("⏳ Extracting audio...")
    
# # #     try:
# # #         # Extract audio using ffmpeg
# # #         stream = ffmpeg.input(INPUT_VIDEO)
# # #         stream = ffmpeg.output(
# # #             stream, 
# # #             OUTPUT_AUDIO_RAW,
# # #             acodec='pcm_s16le',  # 16-bit PCM
# # #             ar=44100,            # 44.1kHz (will resample later)
# # #             ac=2                 # Stereo (will convert to mono later)
# # #         )
# # #         ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
# # #         print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
        
# # #     except ffmpeg.Error as e:
# # #         print(f"❌ FFmpeg error: {e.stderr.decode()}")
# # #         return False
    
# # #     return True

# # # def resample_audio():
# # #     """Convert to mono 16kHz (optimal for speech models)"""
    
# # #     print("⏳ Resampling to 16kHz mono...")
    
# # #     try:
# # #         # Load audio
# # #         audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)
        
# # #         # Convert to mono
# # #         audio = audio.set_channels(1)
        
# # #         # Resample to 16kHz
# # #         audio = audio.set_frame_rate(16000)
        
# # #         # Export
# # #         audio.export(OUTPUT_AUDIO_16K, format='wav')
        
# # #         # Get duration
# # #         duration_sec = len(audio) / 1000
        
# # #         print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
# # #         print(f"📊 Duration: {duration_sec:.1f} seconds ({duration_sec/60:.1f} minutes)")
# # #         print(f"📊 Sample rate: 16000 Hz")
# # #         print(f"📊 Channels: 1 (mono)")
        
# # #     except Exception as e:
# # #         print(f"❌ Resampling error: {e}")
# # #         return False
    
# # #     return True

# # # def main():
# # #     print("=" * 60)
# # #     print("STEP 1: Audio Extraction & Preprocessing")
# # #     print("=" * 60)
    
# # #     # Extract audio
# # #     if not extract_audio():
# # #         return
    
# # #     # Resample
# # #     if not resample_audio():
# # #         return
    
# # #     print("\n" + "=" * 60)
# # #     print("✅ Step 1 Complete!")
# # #     print("=" * 60)
# # #     print(f"Next: Run step2_transcribe.py")

# # # if __name__ == "__main__":
# # #     main()
# # # step1_audio_pipeline.py

# # import os
# # import ffmpeg
# # import subprocess
# # from pydub import AudioSegment
# # import librosa
# # import soundfile as sf

# # # -------------------------------------------------
# # # CONFIGURATION
# # # -------------------------------------------------
# # INPUT_VIDEO = "input/anime.mp4"
# # OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
# # OUTPUT_AUDIO_16K = "work/audio_16k.wav"

# # # -------------------------------------------------
# # # STEP 1: EXTRACT AUDIO FROM VIDEO
# # # -------------------------------------------------
# # def extract_audio():
# #     if not os.path.exists(INPUT_VIDEO):
# #         print(f"❌ Input video not found: {INPUT_VIDEO}")
# #         return False

# #     print(f"📹 Processing: {INPUT_VIDEO}")
# #     print("⏳ Extracting audio...")

# #     try:
# #         stream = ffmpeg.input(INPUT_VIDEO)
# #         stream = ffmpeg.output(
# #             stream,
# #             OUTPUT_AUDIO_RAW,
# #             acodec='pcm_s16le',
# #             ar=44100,
# #             ac=2
# #         )
# #         ffmpeg.run(stream, overwrite_output=True,
# #                    capture_stdout=True, capture_stderr=True)

# #         print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
# #         return True

# #     except ffmpeg.Error as e:
# #         print(f"❌ FFmpeg error: {e.stderr.decode()}")
# #         return False


# # # -------------------------------------------------
# # # STEP 2: RESAMPLE TO 16kHz MONO
# # # -------------------------------------------------
# # def resample_audio():
# #     print("⏳ Resampling to 16kHz mono...")

# #     try:
# #         audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)

# #         audio = audio.set_channels(1)
# #         audio = audio.set_frame_rate(16000)

# #         audio.export(OUTPUT_AUDIO_16K, format='wav')

# #         duration_sec = len(audio) / 1000

# #         print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
# #         print(f"📊 Duration: {duration_sec:.1f} sec")
# #         print(f"📊 Sample rate: 16000 Hz")
# #         print(f"📊 Channels: 1 (mono)")

# #         return True

# #     except Exception as e:
# #         print(f"❌ Resampling error: {e}")
# #         return False


# # # -------------------------------------------------
# # # STEP 3: RUN DEMUCS SEPARATION
# # # -------------------------------------------------
# # def run_demucs():
# #     print("🎧 Starting separation with Demucs...")

# #     try:
# #         subprocess.run([
# #             "demucs",
# #             "-n", "htdemucs",
# #             OUTPUT_AUDIO_16K
# #         ], check=True)

# #         print("✅ Separation complete!")
# #         return True

# #     except subprocess.CalledProcessError as e:
# #         print(f"❌ Demucs error: {e}")
# #         return False


# # # -------------------------------------------------
# # # STEP 4: MERGE BACKGROUND TRACKS
# # # -------------------------------------------------
# # def merge_background():
# #     print("🔊 Merging background tracks...")

# #     file_name = os.path.splitext(os.path.basename(OUTPUT_AUDIO_16K))[0]
# #     base_output = f"separated/htdemucs/{file_name}/"

# #     vocals_path = os.path.join(base_output, "vocals.wav")
# #     drums_path = os.path.join(base_output, "drums.wav")
# #     bass_path = os.path.join(base_output, "bass.wav")
# #     other_path = os.path.join(base_output, "other.wav")

# #     try:
# #         vocals, sr = librosa.load(vocals_path, sr=None)
# #         drums, _ = librosa.load(drums_path, sr=None)
# #         bass, _ = librosa.load(bass_path, sr=None)
# #         other, _ = librosa.load(other_path, sr=None)

# #         # Prevent clipping
# #         background = (drums + bass + other) / 3

# #         sf.write("background_noise.wav", background, sr)

# #         print("💾 Saved Outputs:")
# #         print(f"   - Vocals: {vocals_path}")
# #         print("   - Background: background_noise.wav")

# #         return True

# #     except Exception as e:
# #         print(f"❌ Background merge error: {e}")
# #         return False


# # # -------------------------------------------------
# # # MAIN PIPELINE
# # # -------------------------------------------------
# # def main():
# #     print("=" * 60)
# #     print("🎬 FULL AUDIO PROCESSING PIPELINE")
# #     print("=" * 60)

# #     if not extract_audio():
# #         return

# #     if not resample_audio():
# #         return

# #     if not run_demucs():
# #         return

# #     if not merge_background():
# #         return

# #     print("\n" + "=" * 60)
# #     print("🚀 Pipeline Complete Successfully!")
# #     print("=" * 60)


# # if __name__ == "__main__":
# #     main()

# import os
# import subprocess
# import json
# from pathlib import Path
# import torchaudio
# import torch
# from pydub import AudioSegment
# # from silero_vad.utils import init_jit_model, read_audio, get_speech_timestamps
# from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
# from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
# print("="*60)
# print("STEP 1: Audio Extraction + Source Separation")
# print("="*60)

# # ========================= CONFIG =========================
# VIDEO_FILE = "input/anime.mp4"
# WORK_DIR = "work"
# STEMS_DIR = f"{WORK_DIR}/stems"
# OUTPUT_SPEECH = f"{WORK_DIR}/speech_segments_16k.wav"
# OUTPUT_BG = f"{WORK_DIR}/background_full.wav"

# os.makedirs(WORK_DIR, exist_ok=True)
# os.makedirs(STEMS_DIR, exist_ok=True)

# # ========================= 1. EXTRACT RAW AUDIO =========================
# # print("\n🎵 1. Extracting raw audio from video...")
# # # subprocess.run([
# # #     'ffmpeg', '-i', VIDEO_FILE, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
# # #     f'{WORK_DIR}/raw_audio.wav', '-y'
# # # ], check=True)
# # result = subprocess.run(
# #     [
# #         'ffmpeg', '-i', VIDEO_FILE,
# #         '-vn',
# #         '-acodec', 'pcm_s16le',
# #         '-ar', '16000',   # ✅ better for ML
# #         '-ac', '1',
# #         f'{WORK_DIR}/raw_audio.wav',
# #         '-y'
# #     ],
# #     stdout=subprocess.PIPE,
# #     stderr=subprocess.PIPE,
# #     text=True
# # )

# # print(result.stderr)  # 🔥 CRITICAL

# # if result.returncode != 0:
# #     raise RuntimeError("FFmpeg extraction failed")
# # print("✅ Raw audio extracted")
# # ========================= 1. EXTRACT RAW AUDIO =========================
# print("\n🎵 1. Extracting raw audio from video...")

# # ADD THIS CHECK:
# if not os.path.exists(VIDEO_FILE):
#     print(f"❌ ERROR: Video file not found at {os.path.abspath(VIDEO_FILE)}")
#     sys.exit(1)

# result = subprocess.run(
#     [
#         'ffmpeg', '-y',              # -y comes early usually, forces overwrite
#         '-i', VIDEO_FILE,
#         '-vn',
#         '-acodec', 'pcm_s16le',
#         '-ar', '16000',
#         '-ac', '1',
#         f'{WORK_DIR}/raw_audio.wav'
#     ],
#     capture_output=True, # This is cleaner than stdout/stderr pipes in some cases
#     text=True
# )

# if result.returncode != 0:
#     print("--- FFmpeg Error Output ---")
#     print(result.stderr)
#     print("---------------------------")
#     raise RuntimeError(f"FFmpeg extraction failed with exit code {result.returncode}")

# print("✅ Raw audio extracted")
# import sys

# # ========================= 2. DEMUCS SEPARATION =========================
# print("\n🎼 2. Running Demucs htdemucs_6s...")
# # if not os.path.exists("demucs"):
# #     print("   Installing Demucs...")
# #     subprocess.run(["pip", "install", "demucs"], check=True)

# # subprocess.run([
# #     "python", "-m", "demucs.separate", "--model", "htdemucs_6s",
# #     "-n", "4", "--out", STEMS_DIR, f"{WORK_DIR}/raw_audio.wav"
# # ], check=True)
# # result = subprocess.run(
# #     [
# #         sys.executable, "-m", "demucs.separate",
# #         "--model", "htdemucs_6s",
# #         "-n", "4",
# #         "--out", STEMS_DIR,
# #         f"{WORK_DIR}/raw_audio.wav"
# #     ],
# #     ...
# # )
# import sys
# import subprocess

# # result = subprocess.run(
# #     [
# #         sys.executable, "-m", "demucs.separate",
# #         "-n", "htdemucs_6s",   # ✅ correct flag
# #         "-j", "1",             # safer than -n 4
# #         "-o", STEMS_DIR,
# #         f"{WORK_DIR}/raw_audio.wav"
# #     ],
# #     stdout=subprocess.PIPE,
# #     stderr=subprocess.PIPE,
# #     text=True
# # )
# # Around the Demucs section, ensure you aren't passing unnecessary flags
# result = subprocess.run(
#     [
#         sys.executable, "-m", "demucs.separate",
#         "--name", "htdemucs_6s",  # Use --name instead of -n for clarity
#         "-j", "1", 
#         "-o", STEMS_DIR,
#         f"{WORK_DIR}/raw_audio.wav"
#     ],
#     stdout=subprocess.PIPE,
#     stderr=subprocess.PIPE,
#     text=True
# )
# print(result.stdout)
# print(result.stderr)

# if result.returncode != 0:
#     raise RuntimeError("Demucs separation failed")
# # Expected stems: vocals.wav, drums.wav, bass.wav, other.wav, guitar.wav, piano.wav
# print("✅ Demucs separation complete")

# # ========================= 3. MERGE BACKGROUND =========================
# print("\n🎧 3. Merging background stems...")
# bg_files = [
#     "drums.wav", "bass.wav", "other.wav", "guitar.wav", "piano.wav"
# ]
# bg_paths = [os.path.join(STEMS_DIR, "htdemucs_6s", "raw_audio", f) for f in bg_files]

# bg_audio = None
# for bg_path in bg_paths:
#     if os.path.exists(bg_path):
#         audio = AudioSegment.from_file(bg_path)
#         bg_audio = audio if bg_audio is None else bg_audio.overlay(audio, gain_during_overlay=-6)
#         print(f"   ➕ {os.path.basename(bg_path)}")

# if bg_audio is None:
#     print("   ⚠️ No background stems found, creating silence")
#     bg_audio = AudioSegment.silent(duration=10000)  # 10s placeholder

# bg_audio.export(OUTPUT_BG, format="wav")
# print(f"✅ Background saved: {OUTPUT_BG}")

# # ========================= 4. SILERO VAD on VOCALS =========================
# print("\n🎤 4. Silero VAD on vocals...")
# # Demucs outputs stems under <STEMS_DIR>/htdemucs_6s/raw_audio
# vocals_path = os.path.join(STEMS_DIR, "htdemucs_6s", "raw_audio", "vocals.wav")
# # audio, sr = read_audio(vocals_path, sampling_rate=16000)
# audio = read_audio(vocals_path, sampling_rate=16000)
# sr = 16000
# # model = init_jit_model("silero_vad")
# # speech_timestamps = get_speech_timestamps(
# #     audio, model, sampling_rate=sr,
# #     min_speech_duration_ms=200,  # Ignore breaths
# #     max_speech_duration_s=15.0,  # Max line length
# #     window_size_samples=512
# # )
# model = load_silero_vad()

# # Run VAD
# # speech_timestamps = get_speech_timestamps(
# #     audio,
# #     model,
# #     sampling_rate=sr,
# #     min_speech_duration_ms=200,   # Ignore breaths
# #     max_speech_duration_s=15.0,   # Max line length
# #     window_size_samples=512
# # )
# speech_timestamps = get_speech_timestamps(
#     audio,
#     model,
#     sampling_rate=sr,
#     min_speech_duration_ms=200,
#     max_speech_duration_s=15.0,
#     window_size_samples=512,
#     return_seconds=True   # 🔥 CRITICAL FIX
# )

# vad_data = {
#     "total_voiced_segments": len(speech_timestamps),
#     "segments": [{"start": t["start"], "end": t["end"], "duration": t["end"]-t["start"]} for t in speech_timestamps]
# }
# with open(f"{WORK_DIR}/vad_segments.json", 'w') as f:
#     json.dump(vad_data, f, indent=2)

# print(f"✅ Found {len(speech_timestamps)} voiced segments")

# # ========================= 5. BEATs Event Labeling =========================
# # print("\n🎭 5. BEATs event labeling on speech...")
# # beats = pipeline("audio-classification", model="MIT/ast-finetuned-speech-commands-v2")

# # event_labels = []
# # for i, timestamp in enumerate(speech_timestamps):
# #     start = timestamp["start"]
# #     end = timestamp["end"]
    
# #     # Extract segment (this is where you'd crop in production)
# #     segment_path = f"{WORK_DIR}/temp_segment_{i}.wav"
# #     # audio_segment = audio[int(start*sr):int(end*sr)]
# #     audio_segment = audio[start:end]  
# #     # torchaudio.save(segment_path, torch.tensor(audio_segment).unsqueeze(0), sr)
# #     if not isinstance(audio_segment, torch.Tensor):
# #         audio_segment = torch.tensor(audio_segment)

# #     # Ensure shape = [1, samples]
# #     audio_segment = audio_segment.unsqueeze(0)

# #     # Skip empty segments
# #     if audio_segment.shape[1] < 100:
# #         continue

# #     torchaudio.save(segment_path, audio_segment, sr)
# #     # result = beats(segment_path)
# #     result = beats({"array": audio_segment.numpy(),"sampling_rate": sr})
# #     label = result[0]['label']  # speech, shout, laugh, singing, etc.
# #     confidence = result[0]['score']
    
# #     event_labels.append({
# #         "segment_id": i,
# #         "start": start,
# #         "end": end,
# #         "label": label,
# #         "confidence": confidence
# #     })
    
# #     os.remove(segment_path)

# # with open(f"{WORK_DIR}/event_labels.json", 'w') as f:
# #     json.dump(event_labels, f, indent=2)
# # # print("✅ Event labeling complete")
# # print("\n🎭 5. BEATs event labeling on speech...")

# # device = "cuda" if torch.cuda.is_available() else "cpu"
# # model_id = "MIT/ast-finetuned-speech-commands-v2"

# # feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
# # beats_model = AutoModelForAudioClassification.from_pretrained(model_id).to(device)
# # beats_model.eval()

# # event_labels = []

# # for i, timestamp in enumerate(speech_timestamps):
# #     start = timestamp["start"]
# #     end = timestamp["end"]

# #     audio_segment = audio[start:end]  # already samples at 16k
# #     if not isinstance(audio_segment, torch.Tensor):
# #         audio_segment = torch.tensor(audio_segment, dtype=torch.float32)

# #     if audio_segment.numel() < 1600:  # <0.1s, skip tiny segments
# #         continue

# #     # Prepare model input
# #     inputs = feature_extractor(
# #         audio_segment.numpy(),
# #         sampling_rate=sr,
# #         return_tensors="pt",
# #         padding=True
# #     ).to(device)

# #     with torch.no_grad():
# #         logits = beats_model(**inputs).logits
# #         probs = torch.softmax(logits, dim=-1)[0]
# #         label_id = int(torch.argmax(probs))
# #         label = beats_model.config.id2label[label_id]
# #         confidence = float(probs[label_id])

# #     event_labels.append({
# #         "segment_id": i,
# #         "start": start,
# #         "end": end,
# #         "label": label,
# #         "confidence": confidence
# #     })

# # with open(f"{WORK_DIR}/event_labels.json", "w") as f:
# #     json.dump(event_labels, f, indent=2)

# # print("✅ Event labeling complete")
# print("\n🎭 5. Emotion labeling on speech...")
# import numpy as np
# # Use wav2vec2 for speech/emotion detection (not command detection!)
# model_id = "superb/wav2vec2-base-superb-er"  # Emotion Recognition (angry, happy, sad, neutral)
# device = "cuda" if torch.cuda.is_available() else "cpu"

# feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
# emotion_model = AutoModelForAudioClassification.from_pretrained(model_id).to(device)
# emotion_model.eval()

# event_labels = []
# SEGMENT_DIR = os.path.join(WORK_DIR, "segments")
# os.makedirs(SEGMENT_DIR, exist_ok=True)

# for i, ts in enumerate(speech_timestamps):
#     start_sec = ts["start"]
#     end_sec = ts["end"]
    
#     # Convert seconds → sample indices
#     s_idx = int(start_sec * sr)
#     e_idx = int(end_sec * sr)
    
#     audio_segment = audio[s_idx:e_idx]  # 1D torch tensor
    
#     if not isinstance(audio_segment, torch.Tensor):
#         audio_segment = torch.tensor(audio_segment, dtype=torch.float32)
    
#     if audio_segment.numel() < int(0.1 * sr):  # <100ms → skip
#         continue

#     # 🔊 Save each VAD segment so you can listen
#     seg_path = os.path.join(SEGMENT_DIR, f"segment_{i:03d}.wav")
#     torchaudio.save(seg_path, audio_segment.unsqueeze(0), sr)
    
#     # Model input
#     inputs = feature_extractor(
#         audio_segment.numpy(),
#         sampling_rate=sr,
#         return_tensors="pt",
#         padding=True
#     ).to(device)

# # for i, timestamp in enumerate(speech_timestamps):
# #     start = timestamp["start"]
# #     end = timestamp["end"]
    
# #     audio_segment = audio[start:end]
# #     if not isinstance(audio_segment, torch.Tensor):
# #         audio_segment = torch.tensor(audio_segment, dtype=torch.float32)
    
# #     if audio_segment.numel() < 1600:
# #         continue
    
# #     # Model input
# #     inputs = feature_extractor(
# #         audio_segment.numpy(),
# #         sampling_rate=sr,
# #         return_tensors="pt",
# #         padding=True
# #     ).to(device)
    
#     with torch.no_grad():
#         logits = emotion_model(**inputs).logits
#         probs = torch.softmax(logits, dim=-1)[0]
#         label_id = int(torch.argmax(probs))
#         label = emotion_model.config.id2label[label_id]
#         confidence = float(probs[label_id])
    
#     # ✅ Now you'll get: neutral, angry, happy, sad, surprise
#     event_labels.append({
#         "segment_id": i,
#         "start": start_sec,
#         "end": end_sec,
#         "label": label,
#         "confidence": confidence
#     })
    
#     print(f"Segment {i}: {label} ({confidence:.2f})")

# with open(f"{WORK_DIR}/event_labels.json", 'w') as f:
#     json.dump(event_labels, f, indent=2)

# print("✅ Emotion labeling complete")

# # ========================= 6. FILTER SPEECH → 16kHz MONO =========================
# print("\n🎯 6. Extracting speech segments only...")
# # speech_audio = []

# # # Filter speech + expressive speech (not commands!)
# # for event in event_labels:
# #     if event["confidence"] > 0.3:  # Any confident emotion
# #         start = event["start"]
# #         end = event["end"]
# #         audio_chunk = audio[int(start*sr):int(end*sr)]
# #         speech_audio.append(audio_chunk)

# # if speech_audio:
# #     speech_tensor = torch.tensor(np.concatenate(speech_audio)).unsqueeze(0)
# #     torchaudio.save(OUTPUT_SPEECH, speech_tensor, 16000)
# #     print(f"✅ Speech-only audio saved: {OUTPUT_SPEECH}")
# # else:
# #     print("⚠️ No speech segments found!")
# print("\n🎯 6. Extracting speech segments only...")
# speech_audio = []

# for event in event_labels:
#     if event["confidence"] > 0.3:
#         start_sec = event["start"]
#         end_sec = event["end"]
#         s_idx = int(start_sec * sr)
#         e_idx = int(end_sec * sr)
#         chunk = audio[s_idx:e_idx]
#         if chunk.numel() > 0:
#             speech_audio.append(chunk)

# if speech_audio:
#     # Concatenate all chunks
#     speech_tensor = torch.cat(speech_audio).unsqueeze(0).to(torch.float32)

#     # Simple normalization so you can hear it
#     max_val = speech_tensor.abs().max()
#     if max_val > 0:
#         speech_tensor = speech_tensor / max_val

#     torchaudio.save(OUTPUT_SPEECH, speech_tensor, sr)
#     print(f"✅ Speech-only audio saved: {OUTPUT_SPEECH}")
# else:
#     print("⚠️ No speech segments found!")

# print("\n" + "="*60)
# print("✅ STEP 1 COMPLETE!")
# print(f"📤 Ready for Step 2: {OUTPUT_SPEECH}")
# print("="*60)



# # import os
# # import sys
# # import subprocess
# # from pathlib import Path
# # from audio_separator.separator import Separator

# # print("="*60)
# # print("STEP 1: SOTA Source Separation (MelBand Roformer)")
# # print("="*60)

# # # ========================= CONFIG =========================
# # VIDEO_FILE = "input/anime.mp4"
# # WORK_DIR = "work"
# # # Target SR for Step 1 is 44.1kHz to preserve SFX/Transients [User Goal]
# # SAMPLE_RATE = 44100 
# # OUTPUT_VOCALS = os.path.join(WORK_DIR, "vocals_raw.wav")
# # OUTPUT_BG = os.path.join(WORK_DIR, "background_full.wav")

# # os.makedirs(WORK_DIR, exist_ok=True)

# # # 1. EXTRACT RAW AUDIO (at 44.1kHz for High-Fidelity)
# # print(f"\n🎵 1. Extracting raw audio at {SAMPLE_RATE}Hz...")
# # if not os.path.exists(VIDEO_FILE):
# #     print(f"❌ ERROR: Video file not found at {VIDEO_FILE}")
# #     sys.exit(1)

# # raw_audio_path = os.path.join(WORK_DIR, "raw_audio_44k.wav")
# # subprocess.run(["ffmpeg", "-i", VIDEO_FILE, "-ar", str(SAMPLE_RATE), "-ac", "1", raw_audio_path], capture_output=True, text=True)

# # # 2. SEPARATION VIA MELBAND ROFORMER (2025 SDR Champion)
# # # This replaces Demucs for much better background SFX preservation
# # print("\n🎼 2. Running MelBand-Roformer (Highest SDR Separation)...")
# # separator = Separator(
# #     output_dir=WORK_DIR,
# #     output_format="WAV",
# #     sample_rate=SAMPLE_RATE,
# #     normalization_threshold=0.9 # Prevents clipping
# # )

# # # Load the model filename for MelBand Roformer
# # # Note: This will auto-download the model from Hugging Face on first run
# # separator.load_model(model_filename='denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt')

# # # Perform separation: yields Instrumental (Music+SFX) and Vocals
# # output_files = separator.separate(raw_audio_path)

# # # Rename files for consistency in your dubbing pipeline
# # # primary_stem = Instrumental, secondary_stem = Vocals
# # os.rename(os.path.join(WORK_DIR, output_files), OUTPUT_BG)
# # os.rename(os.path.join(WORK_DIR, output_files[1]), OUTPUT_VOCALS)

# # print(f"✅ Background SFX + Music saved: {OUTPUT_BG}")
# # print(f"✅ Isolated Vocals saved: {OUTPUT_VOCALS}")

"""
STEP 1 v3: Audio Extraction + Source Separation
=================================================
Input  : input/anime.mp4

Outputs (2 main audio files):
  work/vocals_clean.wav      — pure dialogue only (16kHz mono)
  work/background_full.wav   — all non-vocal stems merged (44.1kHz stereo)

Pipeline:
  1. Extract raw audio from video (ffmpeg)
  2. Demucs htdemucs_6s  → 6 stems: vocals / drums / bass / other / guitar / piano
  3. Silero VAD on vocals → detect actual speech regions
  4. Export vocals_clean.wav  (VAD-gated, silence stripped)
  5. Merge all non-vocal stems → background_full.wav
  6. Save metadata JSON
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Force unbuffered output so every print() appears immediately
sys.stdout.reconfigure(line_buffering=True)

try:
    import numpy as np
    import torch
    import torchaudio
except ImportError as e:
    print(f"ERROR: Missing core dependency: {e}")
    print("Run:  pip install torch torchaudio numpy")
    sys.exit(1)

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None  # not used in the active code path

try:
    from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
except ImportError as e:
    print(f"ERROR: silero_vad not installed: {e}")
    print("Run:  pip install silero-vad")
    sys.exit(1)

print("=" * 60)
print("STEP 1 v3: Audio Extraction + Source Separation")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
VIDEO_FILE   = "input/anime.mp4"
WORK_DIR     = "work"
STEMS_DIR    = os.path.join(WORK_DIR, "stems")

# ── 2 main output files ──
OUTPUT_VOCALS = os.path.join(WORK_DIR, "vocals_clean.wav")      # pure dialogue
OUTPUT_BG     = os.path.join(WORK_DIR, "background_full.wav")   # background music/sfx

RAW_AUDIO     = os.path.join(WORK_DIR, "raw_audio_44k.wav")     # intermediate
METADATA_JSON = os.path.join(WORK_DIR, "step1_metadata.json")

# Demucs paths
DEMUCS_MODEL  = "htdemucs_6s"
DEMUCS_OUT    = os.path.join(STEMS_DIR, DEMUCS_MODEL, "raw_audio_44k")

# 6 stems from htdemucs_6s
ALL_STEMS          = ["vocals", "drums", "bass", "other", "guitar", "piano"]
BACKGROUND_STEMS   = ["drums", "bass", "other", "guitar", "piano"]  # everything except vocals

# VAD settings
VAD_SR                 = 16000
VAD_MIN_SPEECH_MS      = 200    # ignore clips shorter than this (breaths, pops)
VAD_MAX_SPEECH_S       = 15.0   # max single speech segment
VAD_PADDING_MS         = 80     # add padding around each voiced segment
SILENCE_BETWEEN_MS     = 50     # silence gap inserted between voiced segments

os.makedirs(WORK_DIR,  exist_ok=True)
os.makedirs(STEMS_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# STEP 1 — EXTRACT RAW AUDIO FROM VIDEO (44.1kHz stereo)
# ─────────────────────────────────────────────────────────────
# print("\n── Step 1: Extracting raw audio from video ──")

# if not os.path.exists(VIDEO_FILE):
#     print(f"ERROR: Video not found: {os.path.abspath(VIDEO_FILE)}")
#     sys.exit(1)

# result = subprocess.run(
#     [
#         "ffmpeg", "-y",
#         "-i", VIDEO_FILE,
#         "-vn",
#         "-acodec", "pcm_s16le",
#         "-ar", "44100",     # 44.1kHz — Demucs works best at 44.1k
#         "-ac", "2",         # stereo
#         RAW_AUDIO,
#     ],
#     capture_output=True, text=True
# )
print("\n── Step 1: Extracting raw audio from video ──")

if not os.path.exists(VIDEO_FILE):
    print(f"ERROR: Video not found: {os.path.abspath(VIDEO_FILE)}")
    sys.exit(1)

# Use ffmpeg subprocess directly — avoids moviepy/DLL issues
result = subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", VIDEO_FILE,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        RAW_AUDIO,
    ],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print("ERROR: ffmpeg audio extraction failed:")
    print(result.stderr[-2000:])
    sys.exit(1)
info = torchaudio.info(RAW_AUDIO)
raw_duration_s = info.num_frames / info.sample_rate
print(f"  Raw audio : {RAW_AUDIO}")
print(f"  Duration  : {raw_duration_s:.2f}s")
print(f"  Sample rate: {info.sample_rate}Hz  Channels: {info.num_channels}")
print("  ✓ Raw audio extracted")

# # ─────────────────────────────────────────────────────────────
# # STEP 2 — DEMUCS SOURCE SEPARATION (6 stems)
# # ─────────────────────────────────────────────────────────────
# print(f"\n── Step 2: Demucs {DEMUCS_MODEL} separation ──")
# print("  This may take 2-10 minutes depending on video length...")

# result = subprocess.run(
#     [
#         sys.executable, "-m", "demucs.separate",
#         "--name", DEMUCS_MODEL,
#         "-j", "1",          # 1 worker — stable on most machines
#         "-o", STEMS_DIR,
#         RAW_AUDIO,
#     ],
#     capture_output=True, text=True
# )

# if result.returncode != 0:
#     print("Demucs error:")
#     print(result.stderr[-2000:])  # last 2000 chars
#     sys.exit(1)

# # Verify all stems exist
# print("  Verifying stems...")
# stem_paths = {}
# missing = []
# for stem in ALL_STEMS:
#     p = os.path.join(DEMUCS_OUT, f"{stem}.wav")
#     if os.path.exists(p):
#         stem_paths[stem] = p
#         info_s = torchaudio.info(p)
#         dur_s  = info_s.num_frames / info_s.sample_rate
#         print(f"  ✓  {stem:<8} → {p}  ({dur_s:.1f}s)")
#     else:
#         missing.append(stem)
#         print(f"  ✗  {stem:<8} → NOT FOUND: {p}")

# if "vocals" not in stem_paths:
#     print("ERROR: vocals.wav not found — Demucs failed")
#     sys.exit(1)

# if missing:
#     print(f"  WARNING: missing stems: {missing} — they will be skipped in background mix")

# print("  ✓ Demucs separation complete")
# ─────────────────────────────────────────────────────────────
# STEP 2 — DEMUCS SOURCE SEPARATION (Python API — no ffprobe)
# ─────────────────────────────────────────────────────────────
print(f"\n── Step 2: Demucs {DEMUCS_MODEL} separation ──")
print("  Using Python API directly (bypasses ffprobe) ...")
print("  This may take 2-10 minutes depending on video length...")

import torch
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model

# Load model
demucs_model = get_model(DEMUCS_MODEL)
demucs_model.eval()
if torch.cuda.is_available():
    demucs_model.cuda()
    print("  Running on GPU ✓")
else:
    print("  Running on CPU (slower but works)")

# Load the wav file directly with torchaudio — NO ffprobe needed
waveform, sr = torchaudio.load(RAW_AUDIO)    # shape: [channels, samples]
print(f"  Loaded  : {RAW_AUDIO}  {waveform.shape}  {sr}Hz")

# Resample to model's expected sample rate (44100) if needed
if sr != demucs_model.samplerate:
    waveform = torchaudio.functional.resample(waveform, sr, demucs_model.samplerate)
    sr = demucs_model.samplerate
    print(f"  Resampled to {sr}Hz")

# Demucs expects stereo — if mono, duplicate channel
if waveform.shape[0] == 1:
    waveform = waveform.repeat(2, 1)
    print("  Mono → stereo (duplicated)")

# Move to same device as model
device = next(demucs_model.parameters()).device
waveform = waveform.to(device)

# Apply model — returns tensor [1, sources, channels, samples]
# sources order for htdemucs_6s: drums, bass, other, vocals, guitar, piano
print("  Separating sources...")
with torch.no_grad():
    sources = apply_model(
        demucs_model,
        waveform.unsqueeze(0),   # add batch dim → [1, 2, samples]
        progress=True,
        num_workers=0,
    )
sources = sources.squeeze(0).cpu()   # → [n_sources, 2, samples]

# Map source index → stem name (htdemucs_6s order)
stem_names = demucs_model.sources   # e.g. ['drums','bass','other','vocals','guitar','piano']
print(f"  Stems   : {stem_names}")

# Save each stem to the expected directory
os.makedirs(DEMUCS_OUT, exist_ok=True)
stem_paths = {}

for idx, stem in enumerate(stem_names):
    out_path = os.path.join(DEMUCS_OUT, f"{stem}.wav")
    stem_wav = sources[idx]              # shape: [2, samples]
    torchaudio.save(out_path, stem_wav, sr)
    dur_s = stem_wav.shape[1] / sr
    stem_paths[stem] = out_path
    print(f"  ✓  {stem:<8} → {out_path}  ({dur_s:.1f}s)")

# Verify vocals exists
if "vocals" not in stem_paths:
    print("ERROR: vocals stem not produced — check model sources list")
    sys.exit(1)

# Check for any unexpected missing stems
missing = [s for s in ALL_STEMS if s not in stem_paths]
if missing:
    print(f"  WARNING: missing stems: {missing}")

print("  ✓ Demucs separation complete")

# Free GPU memory
del sources, waveform, demucs_model
if torch.cuda.is_available():
    torch.cuda.empty_cache()
# ─────────────────────────────────────────────────────────────
# STEP 3 — SILERO VAD ON VOCALS
# ─────────────────────────────────────────────────────────────
print("\n── Step 3: Silero VAD — detecting speech regions ──")

# Load vocals at 16kHz mono for VAD
vocals_audio = read_audio(stem_paths["vocals"], sampling_rate=VAD_SR)

vad_model = load_silero_vad()

speech_timestamps = get_speech_timestamps(
    vocals_audio,
    vad_model,
    sampling_rate=VAD_SR,
    min_speech_duration_ms=VAD_MIN_SPEECH_MS,
    max_speech_duration_s=VAD_MAX_SPEECH_S,
    window_size_samples=512,
    speech_pad_ms=VAD_PADDING_MS,
    return_seconds=True,
)

total_speech_s = sum(t["end"] - t["start"] for t in speech_timestamps)
print(f"  Found    : {len(speech_timestamps)} voiced segments")
print(f"  Duration : {total_speech_s:.1f}s of speech "
      f"out of {raw_duration_s:.1f}s total ({100*total_speech_s/raw_duration_s:.1f}%)")

# ─────────────────────────────────────────────────────────────
# STEP 4 — EXPORT vocals_clean.wav (VAD-gated, 16kHz mono)
# ─────────────────────────────────────────────────────────────
print(f"\n── Step 4: Building vocals_clean.wav ──")

if not speech_timestamps:
    print("  WARNING: No speech detected — copying raw vocals as fallback")
    torchaudio.save(OUTPUT_VOCALS, vocals_audio.unsqueeze(0), VAD_SR)
else:
    silence_samples = int((SILENCE_BETWEEN_MS / 1000.0) * VAD_SR)
    silence_gap     = torch.zeros(silence_samples)

    chunks = []
    for i, ts in enumerate(speech_timestamps):
        s_idx = int(ts["start"] * VAD_SR)
        e_idx = int(ts["end"]   * VAD_SR)
        s_idx = max(0, s_idx)
        e_idx = min(len(vocals_audio), e_idx)
        chunk = vocals_audio[s_idx:e_idx]

        if chunk.numel() < int(0.05 * VAD_SR):   # skip < 50ms
            continue

        chunks.append(chunk)
        if i < len(speech_timestamps) - 1:
            chunks.append(silence_gap)

    if chunks:
        speech_tensor = torch.cat(chunks)

        # Normalize to -3 dBFS (keeps relative dynamics, prevents clipping)
        peak = speech_tensor.abs().max()
        if peak > 0:
            target_peak = 10 ** (-3.0 / 20.0)   # -3 dBFS
            speech_tensor = speech_tensor * (target_peak / peak)
            speech_tensor = speech_tensor.clamp(-1.0, 1.0)

        torchaudio.save(OUTPUT_VOCALS, speech_tensor.unsqueeze(0), VAD_SR)
        vocals_dur = len(speech_tensor) / VAD_SR
        print(f"  ✓  {OUTPUT_VOCALS}")
        print(f"     {len(chunks)//2 + 1} segments | {vocals_dur:.2f}s | 16kHz mono | "
              f"peak normalized to -3 dBFS")
    else:
        print("  WARNING: All chunks too short — saving raw vocals")
        torchaudio.save(OUTPUT_VOCALS, vocals_audio.unsqueeze(0), VAD_SR)

# # ─────────────────────────────────────────────────────────────
# # STEP 5 — MERGE BACKGROUND STEMS → background_full.wav
# # Overlay all non-vocal stems at original quality (44.1kHz stereo)
# # ─────────────────────────────────────────────────────────────
# print(f"\n── Step 5: Building background_full.wav ──")

# bg_audio   = None
# mixed_stems = []

# for stem in BACKGROUND_STEMS:
#     path = stem_paths.get(stem)
#     if not path:
#         print(f"  skip  {stem} (not found)")
#         continue

#     audio_seg = AudioSegment.from_file(path, format="wav")

#     if bg_audio is None:
#         bg_audio = audio_seg
#     else:
#         # overlay() mixes two AudioSegments sample-accurately
#         bg_audio = bg_audio.overlay(audio_seg)

#     mixed_stems.append(stem)
#     print(f"  +  {stem:<8} ({len(audio_seg)/1000:.1f}s)")

# if bg_audio is None:
#     print("  WARNING: No background stems found — writing silence")
#     bg_audio = AudioSegment.silent(duration=int(raw_duration_s * 1000))

# # Normalize background to -6 dBFS headroom so it sits under dialogue
# bg_peak = bg_audio.max_dBFS
# if bg_peak > -6.0:
#     bg_audio = bg_audio.apply_gain(-6.0 - bg_peak)

# bg_audio.export(OUTPUT_BG, format="wav")
# bg_info = torchaudio.info(OUTPUT_BG)
# bg_dur  = bg_info.num_frames / bg_info.sample_rate

# print(f"  ✓  {OUTPUT_BG}")
# print(f"     stems mixed: {mixed_stems}")
# print(f"     {bg_dur:.2f}s | {bg_info.sample_rate}Hz | "
#       f"{bg_info.num_channels}ch | normalized to -6 dBFS headroom")
# ─────────────────────────────────────────────────────────────
# STEP 5 — MERGE BACKGROUND STEMS (pure torchaudio — no ffprobe)
# ─────────────────────────────────────────────────────────────
print(f"\n── Step 5: Building background_full.wav ──")

bg_tensor    = None
bg_sr        = None
mixed_stems  = []

for stem in BACKGROUND_STEMS:
    path = stem_paths.get(stem)
    if not path or not os.path.exists(path):
        print(f"  skip  {stem} (not found)")
        continue

    wf, sr_stem = torchaudio.load(path)   # [channels, samples]

    # Resample if needed (shouldn't happen — all stems share same sr)
    if bg_sr is None:
        bg_sr = sr_stem
    elif sr_stem != bg_sr:
        wf = torchaudio.functional.resample(wf, sr_stem, bg_sr)

    # Ensure stereo
    if wf.shape[0] == 1:
        wf = wf.repeat(2, 1)

    # Pad / trim to same length before mixing
    if bg_tensor is None:
        bg_tensor = wf
    else:
        # Match lengths
        max_len = max(bg_tensor.shape[1], wf.shape[1])
        if bg_tensor.shape[1] < max_len:
            bg_tensor = torch.nn.functional.pad(bg_tensor, (0, max_len - bg_tensor.shape[1]))
        if wf.shape[1] < max_len:
            wf = torch.nn.functional.pad(wf, (0, max_len - wf.shape[1]))
        bg_tensor = bg_tensor + wf   # sum = mix

    mixed_stems.append(stem)
    dur_s = wf.shape[1] / bg_sr
    print(f"  +  {stem:<8} ({dur_s:.1f}s)")

if bg_tensor is None:
    print("  WARNING: No background stems — writing silence")
    bg_sr     = 44100
    n_samples = int(raw_duration_s * bg_sr)
    bg_tensor = torch.zeros(2, n_samples)

# Normalize to -6 dBFS headroom (won't overpower dialogue in Step 5)
peak = bg_tensor.abs().max()
if peak > 0:
    target_peak = 10 ** (-6.0 / 20.0)   # -6 dBFS
    bg_tensor   = bg_tensor * (target_peak / peak)
bg_tensor = bg_tensor.clamp(-1.0, 1.0)

torchaudio.save(OUTPUT_BG, bg_tensor, bg_sr)
bg_dur = bg_tensor.shape[1] / bg_sr
print(f"  ✓  {OUTPUT_BG}")
print(f"     stems mixed: {mixed_stems}")
print(f"     {bg_dur:.2f}s | {bg_sr}Hz | stereo | normalized to -6 dBFS")
# ─────────────────────────────────────────────────────────────
# STEP 6 — SAVE METADATA
# ─────────────────────────────────────────────────────────────
metadata = {
    "timestamp":        datetime.now().isoformat(),
    "version":          "3.0",
    "video_file":       VIDEO_FILE,
    "video_duration_s": round(raw_duration_s, 3),

    # ── 2 main outputs ──
    "outputs": {
        "vocals_clean":      OUTPUT_VOCALS,     # → Step 2 (transcription)
        "background_full":   OUTPUT_BG,          # → Step 5 (final assembly)
    },

    # ── intermediate stems ──
    "stems": {
        stem: path for stem, path in stem_paths.items()
    },

    # ── VAD info ──
    "vad": {
        "model":            "silero_vad",
        "sample_rate":      VAD_SR,
        "total_segments":   len(speech_timestamps),
        "total_speech_s":   round(total_speech_s, 3),
        "speech_ratio":     round(total_speech_s / raw_duration_s, 4),
        "segments": [
            {
                "id":       i,
                "start":    round(ts["start"], 3),
                "end":      round(ts["end"],   3),
                "duration": round(ts["end"] - ts["start"], 3),
            }
            for i, ts in enumerate(speech_timestamps)
        ],
    },

    # ── background mix info ──
    "background": {
        "stems_mixed":  mixed_stems,
        "stems_missing": [s for s in BACKGROUND_STEMS if s not in mixed_stems],
    },
}

with open(METADATA_JSON, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("STEP 1 v3 COMPLETE")
print(f"{'='*60}")
print(f"\n  Main outputs:")
print(f"  ┌─ VOCALS   → {OUTPUT_VOCALS}")
print(f"  │            16kHz mono | VAD-gated dialogue only")
print(f"  │            → used by Step 2 (transcription + diarization)")
print(f"  │")
print(f"  └─ BACKGROUND → {OUTPUT_BG}")
print(f"               44.1kHz stereo | all music + SFX")
print(f"               → used by Step 5 (final assembly)")
print(f"\n  Metadata  : {METADATA_JSON}")
print(f"  VAD segs  : {len(speech_timestamps)}")
print(f"  Speech    : {total_speech_s:.1f}s / {raw_duration_s:.1f}s total")
print(f"\n  Next → step2_transcribe.py  (input: {OUTPUT_VOCALS})")
print("=" * 60)