import json
import os
import gc
from pathlib import Path
import whisperx
import torch
from pydub import AudioSegment
from datetime import datetime

# --- CONFIGURATION ---
AUDIO_FILE = "separated/htdemucs/audio_16k/vocals.wav"
INPUT_JSON = "work/transcription.json"
OUTPUT_JSON = "work/rhythm_pattern.json"
CROPPED_AUDIO_DIR = "work/cropped_segments/"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"
LANGUAGE = "ja"  # Japanese

def create_directories():
    Path(CROPPED_AUDIO_DIR).mkdir(parents=True, exist_ok=True)

def load_transcription():
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_rhythm_blueprint(word_segments, seg_start, seg_end):
    """
    Analyzes word timestamps to find the exact duration of speech and pauses.
    Returns a blueprint array like: [speech, pause, speech...]
    """
    blueprint = []
    current_time = seg_start

    for word in word_segments:
        if 'start' not in word or 'end' not in word:
            continue
        
        word_start = word['start']
        word_end = word['end']
        
        # If there is a gap > 50ms before this word, it's a pause
        pause_duration = round(word_start - current_time, 3)
        if pause_duration > 0.05:
            blueprint.append({
                "type": "pause",
                "duration": pause_duration
            })
        
        # Add the speech segment
        speech_duration = round(word_end - word_start, 3)
        blueprint.append({
            "type": "speech",
            "duration": speech_duration,
            "text_chunk": word.get('word', '').strip()
        })
        
        current_time = word_end

    # Check for trailing pause at the end of the segment
    trailing_pause = round(seg_end - current_time, 3)
    if trailing_pause > 0.05:
        blueprint.append({
            "type": "pause",
            "duration": trailing_pause
        })

    return blueprint

def process_alignment_and_cropping():
    print("="*60)
    print("STEP 2.5: WhisperX Rhythm Alignment & Audio Cropping")
    print("="*60)

    create_directories()
    
    # 1. Load Step 2 Data & Audio
    data = load_transcription()
    segments = data.get("segments", [])
    if not segments:
        print("❌ No segments found in transcription.json")
        return

    print(f"🎵 Loading audio: {AUDIO_FILE}")
    audio_wav = whisperx.load_audio(AUDIO_FILE)
    
    # Load pydub audio for precise cropping (pydub uses milliseconds)
    full_audio = AudioSegment.from_file(AUDIO_FILE)

    # 2. Load WhisperX Alignment Model
    print(f"🧠 Loading WhisperX alignment model for '{LANGUAGE}' on {DEVICE}...")
    model_a, metadata = whisperx.load_align_model(language_code=LANGUAGE, device=DEVICE)

    # 3. Perform Forced Alignment
    print("⏳ Aligning text to audio to extract word-level timestamps...")
    aligned_result = whisperx.align(
        segments, 
        model_a, 
        metadata, 
        audio_wav, 
        DEVICE, 
        return_char_alignments=False
    )
    
    # Cleanup VRAM
    del model_a
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()

    aligned_segments = aligned_result["segments"]
    final_results = []

    print("\n✂️  Processing rhythm blueprints and cropping audio...")
    for idx, seg in enumerate(aligned_segments):
        seg_id = seg.get("id", idx)
        start_time = seg["start"]
        end_time = seg["end"]
        text = seg["text"].strip()
        words = seg.get("words", [])
        
        # Generate Rhythm Blueprint
        blueprint = build_rhythm_blueprint(words, start_time, end_time)
        
        # Create Result Object
        result_seg = {
            "id": seg_id,
            "start": start_time,
            "end": end_time,
            "duration": round(end_time - start_time, 3),
            "text": text,
            "words": words,
            "rhythm_blueprint": blueprint
        }
        final_results.append(result_seg)

        # 4. Crop the Audio using Pydub
        # Pydub works in milliseconds, so we multiply seconds by 1000
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        cropped_audio = full_audio[start_ms:end_ms]
        
        # Save exact cropped segment
        crop_filename = f"segment_{seg_id:03d}.wav"
        crop_filepath = os.path.join(CROPPED_AUDIO_DIR, crop_filename)
        cropped_audio.export(crop_filepath, format="wav")
        
        print(f"  [{seg_id:03d}] {start_time:.2f}s - {end_time:.2f}s | Saved: {crop_filename}")

    # 5. Save the output JSON
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_segments": len(final_results),
        "language": LANGUAGE,
        "segments": final_results
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print(f"✅ STEP 2.5 COMPLETE!")
    print(f"📄 Rhythm data saved to: {OUTPUT_JSON}")
    print(f"📁 Cropped audio saved to: {CROPPED_AUDIO_DIR}")
    print("="*60)

if __name__ == "__main__":
    process_alignment_and_cropping()
# import json
# import os
# import librosa
# from pydub import AudioSegment
# import numpy as np

# def detect_speech_silence_timing(audio_path):
#     """Detect ACTUAL speech/silence timing from the cropped audio file"""
#     y, sr = librosa.load(audio_path, sr=16000)
    
#     # Detect non-silent intervals (precise for clean vocals)
#     intervals = librosa.effects.split(y, top_db=28, frame_length=1024, hop_length=256)
    
#     blueprint = []
#     prev_end = 0.0
    
#     for start_sample, end_sample in intervals:
#         start_time = prev_end
#         end_time = start_sample / sr
        
#         # Add silence if gap exists
#         if end_time - start_time > 0.05:
#             blueprint.append({
#                 "type": "pause",
#                 "duration": round(end_time - start_time, 3)
#             })
        
#         speech_dur = (end_sample - start_sample) / sr
#         blueprint.append({
#             "type": "speech",
#             "duration": round(speech_dur, 3),
#             "text_chunk": ""  # Will be filled by translation step
#         })
#         prev_end = end_sample / sr
    
#     # Trailing silence
#     total_dur = len(y) / sr
#     if total_dur - prev_end > 0.05:
#         blueprint.append({
#             "type": "pause",
#             "duration": round(total_dur - prev_end, 3)
#         })
    
#     return blueprint

# def main():
#     print("🔄 Re-aligning blueprints to actual audio timing...")
    
#     with open("work/transcription_with_speakers.json", "r") as f:
#         data = json.load(f)
    
#     for seg in data["segments"]:
#         seg_id = seg["id"]
#         audio_path = f"work/cropped_segments/segment_{seg_id:03d}.wav"
        
#         if os.path.exists(audio_path):
#             blueprint = detect_speech_silence_timing(audio_path)
#             seg["rhythm_blueprint"] = blueprint
#             print(f"Segment {seg_id}: {len([b for b in blueprint if b['type']=='speech'])} speech blocks")
    
#     # Save corrected alignment
#     with open("work/rhythm_pattern_corrected.json", "w") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)
    
#     print("✅ Blueprint realignment complete!")

# if __name__ == "__main__":
#     main()
