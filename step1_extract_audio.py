# # step1_extract_audio.py
# import ffmpeg
# import os
# from pydub import AudioSegment

# # Configuration
# INPUT_VIDEO = "input/Seikon no Qwaser - S01E01 - [9DBF3AAE] (online-video-cutter.com).mp4"
# OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
# OUTPUT_AUDIO_16K = "work/audio_16k.wav"

# def extract_audio():
#     """Extract audio from video file"""
    
#     if not os.path.exists(INPUT_VIDEO):
#         print(f"❌ Input video not found: {INPUT_VIDEO}")
#         print("Please place your anime file in the 'input/' folder")
#         return False
    
#     print(f"📹 Processing: {INPUT_VIDEO}")
#     print("⏳ Extracting audio...")
    
#     try:
#         # Extract audio using ffmpeg
#         stream = ffmpeg.input(INPUT_VIDEO)
#         stream = ffmpeg.output(
#             stream, 
#             OUTPUT_AUDIO_RAW,
#             acodec='pcm_s16le',  # 16-bit PCM
#             ar=44100,            # 44.1kHz (will resample later)
#             ac=2                 # Stereo (will convert to mono later)
#         )
#         ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
#         print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
        
#     except ffmpeg.Error as e:
#         print(f"❌ FFmpeg error: {e.stderr.decode()}")
#         return False
    
#     return True

# def resample_audio():
#     """Convert to mono 16kHz (optimal for speech models)"""
    
#     print("⏳ Resampling to 16kHz mono...")
    
#     try:
#         # Load audio
#         audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)
        
#         # Convert to mono
#         audio = audio.set_channels(1)
        
#         # Resample to 16kHz
#         audio = audio.set_frame_rate(16000)
        
#         # Export
#         audio.export(OUTPUT_AUDIO_16K, format='wav')
        
#         # Get duration
#         duration_sec = len(audio) / 1000
        
#         print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
#         print(f"📊 Duration: {duration_sec:.1f} seconds ({duration_sec/60:.1f} minutes)")
#         print(f"📊 Sample rate: 16000 Hz")
#         print(f"📊 Channels: 1 (mono)")
        
#     except Exception as e:
#         print(f"❌ Resampling error: {e}")
#         return False
    
#     return True

# def main():
#     print("=" * 60)
#     print("STEP 1: Audio Extraction & Preprocessing")
#     print("=" * 60)
    
#     # Extract audio
#     if not extract_audio():
#         return
    
#     # Resample
#     if not resample_audio():
#         return
    
#     print("\n" + "=" * 60)
#     print("✅ Step 1 Complete!")
#     print("=" * 60)
#     print(f"Next: Run step2_transcribe.py")

# if __name__ == "__main__":
#     main()
# step1_audio_pipeline.py

import os
import ffmpeg
import subprocess
from pydub import AudioSegment
import librosa
import soundfile as sf

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
INPUT_VIDEO = "input/anime.mp4"
OUTPUT_AUDIO_RAW = "work/audio_raw.wav"
OUTPUT_AUDIO_16K = "work/audio_16k.wav"

# -------------------------------------------------
# STEP 1: EXTRACT AUDIO FROM VIDEO
# -------------------------------------------------
def extract_audio():
    if not os.path.exists(INPUT_VIDEO):
        print(f"❌ Input video not found: {INPUT_VIDEO}")
        return False

    print(f"📹 Processing: {INPUT_VIDEO}")
    print("⏳ Extracting audio...")

    try:
        stream = ffmpeg.input(INPUT_VIDEO)
        stream = ffmpeg.output(
            stream,
            OUTPUT_AUDIO_RAW,
            acodec='pcm_s16le',
            ar=44100,
            ac=2
        )
        ffmpeg.run(stream, overwrite_output=True,
                   capture_stdout=True, capture_stderr=True)

        print(f"✅ Audio extracted: {OUTPUT_AUDIO_RAW}")
        return True

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode()}")
        return False


# -------------------------------------------------
# STEP 2: RESAMPLE TO 16kHz MONO
# -------------------------------------------------
def resample_audio():
    print("⏳ Resampling to 16kHz mono...")

    try:
        audio = AudioSegment.from_wav(OUTPUT_AUDIO_RAW)

        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)

        audio.export(OUTPUT_AUDIO_16K, format='wav')

        duration_sec = len(audio) / 1000

        print(f"✅ Resampled audio: {OUTPUT_AUDIO_16K}")
        print(f"📊 Duration: {duration_sec:.1f} sec")
        print(f"📊 Sample rate: 16000 Hz")
        print(f"📊 Channels: 1 (mono)")

        return True

    except Exception as e:
        print(f"❌ Resampling error: {e}")
        return False


# -------------------------------------------------
# STEP 3: RUN DEMUCS SEPARATION
# -------------------------------------------------
def run_demucs():
    print("🎧 Starting separation with Demucs...")

    try:
        subprocess.run([
            "demucs",
            "-n", "htdemucs",
            OUTPUT_AUDIO_16K
        ], check=True)

        print("✅ Separation complete!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Demucs error: {e}")
        return False


# -------------------------------------------------
# STEP 4: MERGE BACKGROUND TRACKS
# -------------------------------------------------
def merge_background():
    print("🔊 Merging background tracks...")

    file_name = os.path.splitext(os.path.basename(OUTPUT_AUDIO_16K))[0]
    base_output = f"separated/htdemucs/{file_name}/"

    vocals_path = os.path.join(base_output, "vocals.wav")
    drums_path = os.path.join(base_output, "drums.wav")
    bass_path = os.path.join(base_output, "bass.wav")
    other_path = os.path.join(base_output, "other.wav")

    try:
        vocals, sr = librosa.load(vocals_path, sr=None)
        drums, _ = librosa.load(drums_path, sr=None)
        bass, _ = librosa.load(bass_path, sr=None)
        other, _ = librosa.load(other_path, sr=None)

        # Prevent clipping
        background = (drums + bass + other) / 3

        sf.write("background_noise.wav", background, sr)

        print("💾 Saved Outputs:")
        print(f"   - Vocals: {vocals_path}")
        print("   - Background: background_noise.wav")

        return True

    except Exception as e:
        print(f"❌ Background merge error: {e}")
        return False


# -------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------
def main():
    print("=" * 60)
    print("🎬 FULL AUDIO PROCESSING PIPELINE")
    print("=" * 60)

    if not extract_audio():
        return

    if not resample_audio():
        return

    if not run_demucs():
        return

    if not merge_background():
        return

    print("\n" + "=" * 60)
    print("🚀 Pipeline Complete Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()