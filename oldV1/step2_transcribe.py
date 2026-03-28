# # # step2_transcribe.py (Direct Whisper - Windows Compatible)
# # import torch
# # import json
# # import os
# # import librosa
# # import numpy as np
# # from transformers import WhisperProcessor, WhisperForConditionalGeneration
# # from datetime import datetime
# # from pydub import AudioSegment
# # from pydub.silence import detect_nonsilent

# # # Configuration
# # AUDIO_FILE = "separated/htdemucs/audio_16k/vocals.wav"
# # OUTPUT_JSON = "work/transcription.json"
# # MODEL_NAME = "openai/whisper-large-v3"

# # def check_gpu():
# #     """Check if GPU is available"""
# #     if torch.cuda.is_available():
# #         print(f"🎮 GPU detected: {torch.cuda.get_device_name(0)}")
# #         return "cuda", torch.float16
# #     else:
# #         print("💻 Using CPU (this will be slower)")
# #         return "cpu", torch.float32

# # def load_audio(audio_path):
# #     """Load audio using librosa"""
# #     print(f"🎵 Loading audio with librosa...")
    
# #     # Load audio at 16kHz (Whisper's expected sample rate)
# #     audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    
# #     duration = len(audio) / sr
# #     print(f"✅ Audio loaded: {duration:.1f} seconds ({duration/60:.1f} minutes)")
# #     return audio

# # def load_model(device, torch_dtype):
# #     """Load Whisper model and processor"""
# #     print(f"📥 Loading Whisper model: {MODEL_NAME}")
# #     print("   (First time will download ~3GB, please wait...)")
    
# #     try:
# #         # Load processor
# #         processor = WhisperProcessor.from_pretrained(MODEL_NAME)
        
# #         # Load model
# #         model = WhisperForConditionalGeneration.from_pretrained(
# #             MODEL_NAME,
# #             torch_dtype=torch_dtype,
# #             low_cpu_mem_usage=True,
# #             use_safetensors=True
# #         )
# #         model.to(device)
        
# #         print("✅ Model loaded successfully!")
# #         return model, processor
    
# #     except Exception as e:
# #         print(f"❌ Error loading model: {e}")
# #         return None, None

# # def transcribe_audio_direct(model, processor, audio, device):
# #     print("\n🎙️ Transcribing audio with chunking...")
# #     print("⏳ CPU mode – chunk-based processing")

# #     SAMPLE_RATE = 16000
# #     CHUNK_SECONDS = 30
# #     chunk_size = SAMPLE_RATE * CHUNK_SECONDS

# #     forced_decoder_ids = processor.get_decoder_prompt_ids(
# #         language="japanese",
# #         task="transcribe"
# #     )

# #     all_text = []
# #     start_time = datetime.now()

# #     for i in range(0, len(audio), chunk_size):
# #         chunk = audio[i:i + chunk_size]
# #         chunk_start_sec = i / SAMPLE_RATE

# #         print(f"   ▶ Chunk {int(chunk_start_sec)}s – {int(chunk_start_sec + CHUNK_SECONDS)}s")

# #         # inputs = processor(
# #         #     chunk,
# #         #     sampling_rate=16000,
# #         #     return_tensors="pt"
# #         # ).input_features.to(device)

# #         # with torch.no_grad():
# #         #     predicted_ids = model.generate(
# #         #         inputs,
# #         #         forced_decoder_ids=forced_decoder_ids,
# #         #         return_timestamps=True,
# #         #         max_new_tokens=440
# #         #     )
# #         inputs = processor(
# #             chunk,
# #             sampling_rate=16000,
# #             return_tensors="pt"
# #         )

# #         input_features = inputs.input_features.to(device)

# #         with torch.no_grad():
# #             predicted_ids = model.generate(
# #                 input_features,
# #                 task="transcribe",
# #                 language="japanese",
# #                 return_timestamps=True,
# #                 max_new_tokens=440
# #             )

# #         text = processor.decode(
# #             predicted_ids[0],
# #             skip_special_tokens=True,
# #             decode_with_timestamps=True
# #         )

# #         # text = processor.batch_decode(
# #         #     predicted_ids,
# #         #     skip_special_tokens=False,
# #         #     decode_with_timestamps=True
# #         # )[0]

# #         # Shift timestamps manually
# #         import re
# #         def shift_timestamp(match):
# #             t = float(match.group(1))
# #             return f"<|{t + chunk_start_sec:.2f}|>"

# #         text = re.sub(r"<\|(\d+\.\d+)\|>", shift_timestamp, text)
# #         all_text.append(text)

# #     duration = (datetime.now() - start_time).total_seconds()
# #     print(f"✅ Transcription complete! ({duration:.1f}s)")

# #     return "".join(all_text)

# # def parse_whisper_output(transcription_text):
# #     """Parse Whisper output with timestamps into segments"""
    
# #     print("\n📊 Processing results...")
    
# #     segments = []
    
# #     # Whisper outputs text like: "<|0.00|>こんにちは<|2.50|>元気ですか<|5.00|>"
# #     # We need to parse this format
    
# #     import re
    
# #     # Pattern to match timestamp tokens: <|X.XX|>
# #     timestamp_pattern = r'<\|(\d+\.\d+)\|>'
    
# #     # Split by timestamps
# #     parts = re.split(timestamp_pattern, transcription_text)
    
# #     # Parts will be: ['', '0.00', 'text1', '2.50', 'text2', '5.00', ...]
# #     # Every odd index is a timestamp, every even index (>0) is text
    
# #     idx = 0
# #     seg_id = 0
    
# #     while idx < len(parts) - 1:
# #         if idx == 0:
# #             idx += 1
# #             continue
        
# #         start_time = float(parts[idx])
# #         idx += 1
        
# #         if idx < len(parts):
# #             text = parts[idx].strip()
# #             idx += 1
            
# #             # Get end time (next timestamp if available)
# #             if idx < len(parts):
# #                 end_time = float(parts[idx])
# #             else:
# #                 end_time = start_time + 2.0  # Fallback
            
# #             if text and not text.startswith('<|'):  # Skip special tokens
# #                 segment = {
# #                     'id': seg_id,
# #                     'start': start_time,
# #                     'end': end_time,
# #                     'text': text,
# #                     'duration': end_time - start_time
# #                 }
# #                 segments.append(segment)
# #                 seg_id += 1
    
# #     # If parsing failed (no timestamps found), create single segment
# #     if not segments:
# #         # Remove special tokens manually
# #         clean_text = re.sub(r'<\|[^|]+\|>', '', transcription_text).strip()
# #         segments.append({
# #             'id': 0,
# #             'start': 0.0,
# #             'end': 0.0,
# #             'text': clean_text,
# #             'duration': 0.0
# #         })
    
# #     print(f"📝 Found {len(segments)} dialogue segments")
    
# #     return segments

# # def save_results(segments):
# #     """Save transcription to JSON"""
    
# #     output_data = {
# #         'model': MODEL_NAME,
# #         'language': 'japanese',
# #         'timestamp': datetime.now().isoformat(),
# #         'total_segments': len(segments),
# #         'segments': segments
# #     }
    
# #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# #     print(f"💾 Saved to: {OUTPUT_JSON}")

# # def refine_segment_timings(segments):
# #     print("🔍 Refining segment timing with silence detection...")

# #     full_audio = AudioSegment.from_wav(AUDIO_FILE)
# #     refined_segments = []

# #     for seg in segments:
# #         start_ms = int(seg["start"] * 1000)
# #         end_ms = int(seg["end"] * 1000)

# #         clip_audio = full_audio[start_ms:end_ms]

# #         nonsilent_parts = detect_nonsilent(
# #             clip_audio,
# #             min_silence_len=200,
# #             silence_thresh=clip_audio.dBFS - 16,
# #         )

# #         if nonsilent_parts:
# #             new_start_offset = nonsilent_parts[0][0]  # first speech
# #             new_start = seg["start"] + (new_start_offset / 1000.0)

# #             seg["start"] = round(new_start, 3)
# #             seg["duration"] = round(seg["end"] - seg["start"], 3)

# #         refined_segments.append(seg)

# #     return refined_segments

# # def display_preview(segments):
# #     """Display first few segments"""
    
# #     print("\n" + "="*60)
# #     print("📋 PREVIEW (First 5 segments)")
# #     print("="*60)
    
# #     for seg in segments[:5]:
# #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] ({seg['duration']:.2f}s)")
# #         print(f"  {seg['text']}")
    
# #     if len(segments) > 5:
# #         print(f"\n... and {len(segments) - 5} more segments")

# # def main():
# #     print("=" * 60)
# #     print("STEP 2: Speech-to-Text (Direct Whisper Method)")
# #     print("=" * 60)
    
# #     # Check if audio file exists
# #     if not os.path.exists(AUDIO_FILE):
# #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# #         print("   Please run step1_extract_audio.py first")
# #         return
    
# #     # Check GPU
# #     device, torch_dtype = check_gpu()
    
# #     # Load audio
# #     audio = load_audio(AUDIO_FILE)
    
# #     # Load model
# #     model, processor = load_model(device, torch_dtype)
# #     if model is None or processor is None:
# #         return
    
# #     # Transcribe
# #     transcription_text = transcribe_audio_direct(model, processor, audio, device)
# #     if transcription_text is None:
# #         return
    
# #     # Parse into segments
# #     segments = parse_whisper_output(transcription_text)
# #     segments = refine_segment_timings(segments)
    
# #     # Save to JSON
# #     save_results(segments)
    
# #     # Display preview
# #     display_preview(segments)
    
# #     print("\n" + "=" * 60)
# #     print("✅ Step 2 Complete!")
# #     print("=" * 60)
# #     print(f"📁 Output: {OUTPUT_JSON}")
# #     print(f"📝 Total segments: {len(segments)}")
# #     print("\nNext: Run step3_diarization.py (Speaker Identification)")

# # if __name__ == "__main__":
# #     main()
# import os
# import json
# import whisperx
# import torch
# import gc
# from pydub import AudioSegment
# import librosa

# print("="*60)
# print("STEP 2: WhisperX Transcription + Speaker Diarization")
# print("="*60)

# # ========================= CONFIG =========================
# VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio/vocals.wav"  # From Step 1
# OUTPUT_JSON = "work/transcription_with_speakers.json"
# WORK_DIR = "work"

# # Create output dir
# os.makedirs(WORK_DIR, exist_ok=True)

# # HF token (get from https://huggingface.co/settings/tokens)
# HF_TOKEN = "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"  # Replace with yours!

# device = "cuda" if torch.cuda.is_available() else "cpu"
# batch_size = 16  # Adjust if OOM
# print(f"💻 Using device: {device}\n")

# # ========================= MAIN PIPELINE =========================

# def main():
#     # 1. Load & validate vocals
#     if not os.path.exists(VOCALS_PATH):
#         print(f"❌ {VOCALS_PATH} not found. Run Step 1 first.")
#         return
    
#     print("📹 Loading vocals track...")
#     audio = whisperx.load_audio(VOCALS_PATH)
#     print(f"✅ Loaded {len(audio)/16000:.1f}s audio\n")

#     # 2. Transcribe with Whisper (large-v3 + Japanese)
#     print("🤖 Loading Whisper large-v3...")
#     # model = whisperx.load_model("large-v3", device, compute_type="int8")
#     model = whisperx.load_model(
#     "large-v3",
#     device,
#     compute_type="int8",
#     vad_method="silero")
#     print("📝 Transcribing (Japanese)...")
#     result = model.transcribe(audio, batch_size=batch_size, language="ja")
#     print(f"✅ Language detected: {result['language']}\n")

#     # 3. Align for word-level timestamps
#     print("⏱️  Aligning word timestamps...")
#     model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
#     result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
#     print("✅ Word-level timestamps ready\n")

#     # Clean up Whisper models
#     del model, model_a
#     gc.collect()
#     torch.cuda.empty_cache()

#     # 4. Speaker diarization (Pyannote)
#     print("👥 Speaker diarization...")
#     from whisperx.diarize import DiarizationPipeline  # ✅ Correct import path
#     # diarize_model = DiarizationPipeline(use_auth_token=HF_TOKEN, device=device)
#     from pyannote.audio import Pipeline

#     diarize_model = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization",
#         token=HF_TOKEN
#     )

#     diarize_model.to(device)
#     # diarize_model = whisperx.DiarizationPipeline(use_auth_token=HF_TOKEN, device=device)
#     diarize_segments = diarize_model(audio)
#     print("✅ Speakers identified\n")

#     # 5. Assign speakers to words
#     print("🔗 Assigning speakers...")
#     result = whisperx.assign_word_speakers(diarize_segments, result)
#     print("✅ Speaker assignment complete\n")

#     # 6. Gender detection per speaker (simple: voice pitch)
#     print("🚻 Detecting speaker gender...")
#     speaker_gender = {}
#     for segment in result["segments"]:
#         speaker = segment.get("speaker", "UNKNOWN")
#         if speaker not in speaker_gender:
#             # Extract speaker audio snippet (first 3s of their speech)
#             start = max(0, segment["start"])
#             end = min(len(audio)/16000, start + 3.0)
#             snippet = audio[int(start*16000):int(end*16000)]
            
#             # Simple pitch-based gender detection
#             pitches, magnitudes, sr = librosa.pyin(snippet, fmin=50, fmax=600)
#             avg_pitch = np.median(pitches[pitches > 0])
            
#             gender = "male" if avg_pitch > 180 else "female" if avg_pitch > 120 else "child"
#             speaker_gender[speaker] = gender
            
#             print(f"  {speaker}: {gender} (pitch: {avg_pitch:.0f}Hz)")
    
#     # 7. Format output with silence gaps
#     print("⏸️  Adding silence gaps...")
#     segments_with_silence = []
#     prev_end = 0
    
#     for i, segment in enumerate(result["segments"]):
#         # Add silence gap before this segment
#         if segment["start"] > prev_end + 0.2:  # >200ms gap
#             segments_with_silence.append({
#                 "id": f"silence_{i}",
#                 "start": prev_end,
#                 "end": segment["start"],
#                 "duration": segment["start"] - prev_end,
#                 "text": "",
#                 "speaker": "SILENCE",
#                 "words": []
#             })
        
#         formatted_segment = {
#             "id": i,
#             "start": segment["start"],
#             "end": segment["end"],
#             "duration": segment["end"] - segment["start"],
#             "text": segment["text"].strip(),
#             "speaker": segment.get("speaker", "UNKNOWN"),
#             "gender": speaker_gender.get(segment.get("speaker", "UNKNOWN"), "unknown"),
#             "words": [
#                 {
#                     "word": word["word"],
#                     "start": word["start"],
#                     "end": word["end"],
#                     "score": word.get("probability", 0.0)
#                 }
#                 for word in segment.get("words", [])
#             ]
#         }
#         segments_with_silence.append(formatted_segment)
#         prev_end = segment["end"]
    
#     # 8. Save final output
#     output_data = {
#         "timestamp": str(torch.cuda.get_device_properties(0) if device == "cuda" else "cpu"),
#         "total_segments": len(segments_with_silence),
#         "language": result["language"],
#         "segments": segments_with_silence,
#         "speakers": list(speaker_gender.keys())
#     }
    
#     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
#     print(f"\n✅ Step 2 Complete: {OUTPUT_JSON}")
#     print(f"📊 {len(segments_with_silence)} segments (incl. silence)")
#     print(f"👥 {len(speaker_gender)} unique speakers detected")
    
#     # Preview first few segments
#     print("\n📋 Preview:")
#     for seg in segments_with_silence[:5]:
#         speaker = seg["speaker"]
#         text = seg["text"][:50] + "..." if len(seg["text"]) > 50 else seg["text"]
#         print(f"  [{seg['id']}] {speaker} ({seg['gender']}): {text}")

# if __name__ == "__main__":
#     main()

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