# step1_extract_audio.py
import ffmpeg
import os
from pydub import AudioSegment

# Configuration
INPUT_VIDEO = "input/anime_sample.mp4"
OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
OUTPUT_AUDIO_16K = "work/audio_16k.wav"

def extract_audio():
    """Extract audio from video file"""
    
    if not os.path.exists(INPUT_VIDEO):
        print(f"❌ Input video not found: {INPUT_VIDEO}")
        print("Please place your anime file in the 'input/' folder")
        return False
    
    print(f"📹 Processing: {INPUT_VIDEO}")
    print("⏳ Extracting audio...")
    
    try:
        # Extract audio using ffmpeg
        stream = ffmpeg.input(INPUT_VIDEO)
        stream = ffmpeg.output(
            stream, 
            OUTPUT_AUDIO_RAW,
            acodec='pcm_s16le',  # 16-bit PCM
            ar=44100,            # 44.1kHz (will resample later)
            ac=2                 # Stereo (will convert to mono later)
        )
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
        
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode()}")
        return False
    
    return True

def resample_audio():
    """Convert to mono 16kHz (optimal for speech models)"""
    
    print("⏳ Resampling to 16kHz mono...")
    
    try:
        # Load audio
        audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)
        
        # Convert to mono
        audio = audio.set_channels(1)
        
        # Resample to 16kHz
        audio = audio.set_frame_rate(16000)
        
        # Export
        audio.export(OUTPUT_AUDIO_16K, format='wav')
        
        # Get duration
        duration_sec = len(audio) / 1000
        
        print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
        print(f"📊 Duration: {duration_sec:.1f} seconds ({duration_sec/60:.1f} minutes)")
        print(f"📊 Sample rate: 16000 Hz")
        print(f"📊 Channels: 1 (mono)")
        
    except Exception as e:
        print(f"❌ Resampling error: {e}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("STEP 1: Audio Extraction & Preprocessing")
    print("=" * 60)
    
    # Extract audio
    if not extract_audio():
        return
    
    # Resample
    if not resample_audio():
        return
    
    print("\n" + "=" * 60)
    print("✅ Step 1 Complete!")
    print("=" * 60)
    print(f"Next: Run step2_transcribe.py")

if __name__ == "__main__":
    main()
