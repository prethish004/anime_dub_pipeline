# step6_final_assembly.py
import json
import os
import subprocess
from pydub import AudioSegment
from datetime import datetime

# Configuration
VIDEO_FILE = "input/anime_sample.mp4"
VOICE_CLIPS_METADATA = "work/voice_clips_metadata.json"
OUTPUT_VIDEO = "output/anime_dubbed.mp4"
TEMP_AUDIO = "work/final_audio.wav"

def check_prerequisites():
    """Check if required files exist"""
    
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Video file not found: {VIDEO_FILE}")
        return False
    
    if not os.path.exists(VOICE_CLIPS_METADATA):
        print(f"❌ Voice clips metadata not found: {VOICE_CLIPS_METADATA}")
        print("   Please run step5_voice_generation.py first")
        return False
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    return True

def load_voice_clips_metadata():
    """Load voice clips metadata"""
    with open(VOICE_CLIPS_METADATA, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded metadata for {data['total_clips']} clips")
    return data

def get_video_duration():
    """Get original video duration using ffprobe"""
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            VIDEO_FILE
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        duration = float(result.stdout.strip())
        print(f"🎥 Video duration: {duration:.2f}s")
        return duration
    
    except Exception as e:
        print(f"⚠️  Could not get video duration: {e}")
        return None

def create_audio_timeline(clips, video_duration):
    """Create complete audio timeline with silences"""
    
    print("\n🎵 Creating audio timeline...")
    
    # Start with silence for entire video duration
    if video_duration:
        final_audio = AudioSegment.silent(duration=int(video_duration * 1000))
        print(f"   Created {video_duration:.1f}s silent base")
    else:
        # Estimate from last clip
        last_clip = max(clips, key=lambda x: x['end'])
        final_audio = AudioSegment.silent(duration=int((last_clip['end'] + 1) * 1000))
        print(f"   Created {last_clip['end'] + 1:.1f}s silent base")
    
    # Overlay each voice clip at correct position
    for idx, clip in enumerate(clips, 1):
        audio_file = clip['audio_file']
        start_time = clip['start']
        
        if not os.path.exists(audio_file):
            print(f"   ⚠️  Clip {idx} not found: {audio_file}")
            continue
        
        try:
            # Load voice clip
            voice_clip = AudioSegment.from_mp3(audio_file)
            
            # Calculate position in milliseconds
            position_ms = int(start_time * 1000)
            
            # Overlay voice clip at correct position
            final_audio = final_audio.overlay(voice_clip, position=position_ms)
            
            print(f"   [{idx}/{len(clips)}] Added: {os.path.basename(audio_file)} at {start_time:.1f}s")
        
        except Exception as e:
            print(f"   ❌ Error adding clip {idx}: {e}")
            continue
    
    return final_audio

def save_audio_track(audio, output_path):
    """Save combined audio to file"""
    
    print(f"\n💾 Saving audio track...")
    
    try:
        audio.export(
            output_path,
            format="wav",
            parameters=["-ar", "16000"]  # 16kHz sample rate
        )
        print(f"   ✅ Saved: {output_path}")
        return True
    except Exception as e:
        print(f"   ❌ Error saving audio: {e}")
        return False

def replace_video_audio(video_file, audio_file, output_file):
    """Replace video audio track with new dubbed audio"""
    
    print(f"\n🎬 Merging audio with video...")
    print(f"   Video: {video_file}")
    print(f"   Audio: {audio_file}")
    print(f"   Output: {output_file}")
    
    try:
        # FFmpeg command to replace audio
        cmd = [
            'ffmpeg',
            '-i', video_file,      # Input video
            '-i', audio_file,      # Input audio
            '-c:v', 'copy',        # Copy video stream (no re-encoding)
            '-c:a', 'aac',         # Encode audio as AAC
            '-b:a', '192k',        # Audio bitrate
            '-map', '0:v:0',       # Map video from first input
            '-map', '1:a:0',       # Map audio from second input
            '-shortest',           # Use shortest stream duration
            '-y',                  # Overwrite output
            output_file
        ]
        
        print(f"\n⏳ Running FFmpeg (this may take a minute)...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Video created successfully!")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error:")
        print(f"   {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_file_size(file_path):
    """Get human-readable file size"""
    size_bytes = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

def display_summary(metadata, output_file):
    """Display final summary"""
    
    print("\n" + "="*70)
    print("🎉 FINAL DUBBED VIDEO COMPLETE!")
    print("="*70)
    
    print(f"\n📊 Statistics:")
    print(f"   Original language: {metadata['source_data']['source_language']}")
    print(f"   Dubbed language: {metadata['source_data']['target_language']}")
    print(f"   Total voice clips: {metadata['total_clips']}")
    
    print(f"\n🎭 Voice Cast:")
    for speaker, voice_info in metadata['voice_assignments'].items():
        clip_count = sum(1 for c in metadata['clips'] if c.get('speaker') == speaker)
        print(f"   {speaker}: {voice_info['name']} ({clip_count} lines)")
    
    total_duration = sum(c['duration'] for c in metadata['clips'])
    print(f"\n⏱️  Total dialogue: {total_duration:.1f}s")
    
    if os.path.exists(output_file):
        file_size = get_file_size(output_file)
        print(f"\n📁 Output File:")
        print(f"   Location: {output_file}")
        print(f"   Size: {file_size}")
    
    print("\n" + "="*70)
    print("✅ All Done! Your anime is now dubbed in English!")
    print("="*70)

def display_pipeline_summary():
    """Display complete pipeline summary"""
    
    print("\n" + "="*70)
    print("📋 COMPLETE PIPELINE SUMMARY")
    print("="*70)
    
    pipeline_steps = [
        ("Step 1", "Audio Extraction", "work/audio_16k.wav"),
        ("Step 2", "Transcription", "work/transcription.json"),
        ("Step 3", "Speaker Diarization", "work/transcription_with_speakers.json"),
        ("Step 4", "Translation", "work/translated_segments.json"),
        ("Step 5", "Voice Generation", "work/voice_clips/"),
        ("Step 6", "Final Assembly", OUTPUT_VIDEO)
    ]
    
    print("\n✅ Completed Steps:")
    for step, name, output in pipeline_steps:
        status = "✅" if os.path.exists(output) else "⚠️"
        print(f"   {status} {step}: {name}")
        if os.path.exists(output):
            if os.path.isfile(output):
                size = get_file_size(output)
                print(f"      → {output} ({size})")
            else:
                file_count = len([f for f in os.listdir(output) if f.endswith('.mp3')])
                print(f"      → {output} ({file_count} files)")

def main():
    print("=" * 70)
    print("STEP 6: Final Video Assembly")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Load voice clips metadata
    metadata = load_voice_clips_metadata()
    
    # Get video duration
    video_duration = get_video_duration()
    
    # Create audio timeline
    final_audio = create_audio_timeline(metadata['clips'], video_duration)
    
    # Save audio track
    if not save_audio_track(final_audio, TEMP_AUDIO):
        print("❌ Failed to save audio track")
        return
    
    # Replace video audio
    if not replace_video_audio(VIDEO_FILE, TEMP_AUDIO, OUTPUT_VIDEO):
        print("❌ Failed to create final video")
        return
    
    # Display summary
    display_summary(metadata, OUTPUT_VIDEO)
    
    # Display complete pipeline summary
    display_pipeline_summary()
    
    print(f"\n🎬 Watch your dubbed video:")
    print(f"   {OUTPUT_VIDEO}")
    print("\n💡 Next steps:")
    print("   - Try with a longer video clip")
    print("   - Experiment with different voices")
    print("   - Fine-tune translation prompts")
    print("   - Add subtitle generation")

if __name__ == "__main__":
    main()
