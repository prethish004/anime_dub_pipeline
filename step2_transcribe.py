# step2_transcribe.py (Direct Whisper - Windows Compatible)
import torch
import json
import os
import librosa
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from datetime import datetime

# Configuration
AUDIO_FILE = "work/audio_16k.wav"
OUTPUT_JSON = "work/transcription.json"
MODEL_NAME = "openai/whisper-large-v3"

def check_gpu():
    """Check if GPU is available"""
    if torch.cuda.is_available():
        print(f"🎮 GPU detected: {torch.cuda.get_device_name(0)}")
        return "cuda", torch.float16
    else:
        print("💻 Using CPU (this will be slower)")
        return "cpu", torch.float32

def load_audio(audio_path):
    """Load audio using librosa"""
    print(f"🎵 Loading audio with librosa...")
    
    # Load audio at 16kHz (Whisper's expected sample rate)
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    
    duration = len(audio) / sr
    print(f"✅ Audio loaded: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    return audio

def load_model(device, torch_dtype):
    """Load Whisper model and processor"""
    print(f"📥 Loading Whisper model: {MODEL_NAME}")
    print("   (First time will download ~3GB, please wait...)")
    
    try:
        # Load processor
        processor = WhisperProcessor.from_pretrained(MODEL_NAME)
        
        # Load model
        model = WhisperForConditionalGeneration.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        model.to(device)
        
        print("✅ Model loaded successfully!")
        return model, processor
    
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None, None

def transcribe_audio_direct(model, processor, audio, device):
    print("\n🎙️ Transcribing audio with chunking...")
    print("⏳ CPU mode – chunk-based processing")

    SAMPLE_RATE = 16000
    CHUNK_SECONDS = 30
    chunk_size = SAMPLE_RATE * CHUNK_SECONDS

    forced_decoder_ids = processor.get_decoder_prompt_ids(
        language="japanese",
        task="transcribe"
    )

    all_text = []
    start_time = datetime.now()

    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        chunk_start_sec = i / SAMPLE_RATE

        print(f"   ▶ Chunk {int(chunk_start_sec)}s – {int(chunk_start_sec + CHUNK_SECONDS)}s")

        inputs = processor(
            chunk,
            sampling_rate=16000,
            return_tensors="pt"
        ).input_features.to(device)

        with torch.no_grad():
            predicted_ids = model.generate(
                inputs,
                forced_decoder_ids=forced_decoder_ids,
                return_timestamps=True,
                max_new_tokens=440
            )

        text = processor.batch_decode(
            predicted_ids,
            skip_special_tokens=False,
            decode_with_timestamps=True
        )[0]

        # Shift timestamps manually
        import re
        def shift_timestamp(match):
            t = float(match.group(1))
            return f"<|{t + chunk_start_sec:.2f}|>"

        text = re.sub(r"<\|(\d+\.\d+)\|>", shift_timestamp, text)
        all_text.append(text)

    duration = (datetime.now() - start_time).total_seconds()
    print(f"✅ Transcription complete! ({duration:.1f}s)")

    return "".join(all_text)

def parse_whisper_output(transcription_text):
    """Parse Whisper output with timestamps into segments"""
    
    print("\n📊 Processing results...")
    
    segments = []
    
    # Whisper outputs text like: "<|0.00|>こんにちは<|2.50|>元気ですか<|5.00|>"
    # We need to parse this format
    
    import re
    
    # Pattern to match timestamp tokens: <|X.XX|>
    timestamp_pattern = r'<\|(\d+\.\d+)\|>'
    
    # Split by timestamps
    parts = re.split(timestamp_pattern, transcription_text)
    
    # Parts will be: ['', '0.00', 'text1', '2.50', 'text2', '5.00', ...]
    # Every odd index is a timestamp, every even index (>0) is text
    
    idx = 0
    seg_id = 0
    
    while idx < len(parts) - 1:
        if idx == 0:
            idx += 1
            continue
        
        start_time = float(parts[idx])
        idx += 1
        
        if idx < len(parts):
            text = parts[idx].strip()
            idx += 1
            
            # Get end time (next timestamp if available)
            if idx < len(parts):
                end_time = float(parts[idx])
            else:
                end_time = start_time + 2.0  # Fallback
            
            if text and not text.startswith('<|'):  # Skip special tokens
                segment = {
                    'id': seg_id,
                    'start': start_time,
                    'end': end_time,
                    'text': text,
                    'duration': end_time - start_time
                }
                segments.append(segment)
                seg_id += 1
    
    # If parsing failed (no timestamps found), create single segment
    if not segments:
        # Remove special tokens manually
        clean_text = re.sub(r'<\|[^|]+\|>', '', transcription_text).strip()
        segments.append({
            'id': 0,
            'start': 0.0,
            'end': 0.0,
            'text': clean_text,
            'duration': 0.0
        })
    
    print(f"📝 Found {len(segments)} dialogue segments")
    
    return segments

def save_results(segments):
    """Save transcription to JSON"""
    
    output_data = {
        'model': MODEL_NAME,
        'language': 'japanese',
        'timestamp': datetime.now().isoformat(),
        'total_segments': len(segments),
        'segments': segments
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved to: {OUTPUT_JSON}")

def display_preview(segments):
    """Display first few segments"""
    
    print("\n" + "="*60)
    print("📋 PREVIEW (First 5 segments)")
    print("="*60)
    
    for seg in segments[:5]:
        print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] ({seg['duration']:.2f}s)")
        print(f"  {seg['text']}")
    
    if len(segments) > 5:
        print(f"\n... and {len(segments) - 5} more segments")

def main():
    print("=" * 60)
    print("STEP 2: Speech-to-Text (Direct Whisper Method)")
    print("=" * 60)
    
    # Check if audio file exists
    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Audio file not found: {AUDIO_FILE}")
        print("   Please run step1_extract_audio.py first")
        return
    
    # Check GPU
    device, torch_dtype = check_gpu()
    
    # Load audio
    audio = load_audio(AUDIO_FILE)
    
    # Load model
    model, processor = load_model(device, torch_dtype)
    if model is None or processor is None:
        return
    
    # Transcribe
    transcription_text = transcribe_audio_direct(model, processor, audio, device)
    if transcription_text is None:
        return
    
    # Parse into segments
    segments = parse_whisper_output(transcription_text)
    
    # Save to JSON
    save_results(segments)
    
    # Display preview
    display_preview(segments)
    
    print("\n" + "=" * 60)
    print("✅ Step 2 Complete!")
    print("=" * 60)
    print(f"📁 Output: {OUTPUT_JSON}")
    print(f"📝 Total segments: {len(segments)}")
    print("\nNext: Run step3_diarization.py (Speaker Identification)")

if __name__ == "__main__":
    main()
