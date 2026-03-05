# # # step6_final_assembly.py
# # import json
# # import os
# # import subprocess
# # from pydub import AudioSegment
# # from datetime import datetime

# # # Configuration
# # VIDEO_FILE = "input/anime_sample.mp4"
# # VOICE_CLIPS_METADATA = "work/voice_clips_metadata.json"
# # OUTPUT_VIDEO = "output/anime_dubbed.mp4"
# # TEMP_AUDIO = "work/final_audio.wav"

# # def check_prerequisites():
# #     """Check if required files exist"""
    
# #     if not os.path.exists(VIDEO_FILE):
# #         print(f"❌ Video file not found: {VIDEO_FILE}")
# #         return False
    
# #     if not os.path.exists(VOICE_CLIPS_METADATA):
# #         print(f"❌ Voice clips metadata not found: {VOICE_CLIPS_METADATA}")
# #         print("   Please run step5_voice_generation.py first")
# #         return False
    
# #     # Create output directory
# #     os.makedirs("output", exist_ok=True)
    
# #     return True

# # def load_voice_clips_metadata():
# #     """Load voice clips metadata"""
# #     with open(VOICE_CLIPS_METADATA, 'r', encoding='utf-8') as f:
# #         data = json.load(f)
    
# #     print(f"📄 Loaded metadata for {data['total_clips']} clips")
# #     return data

# # def get_video_duration():
# #     """Get original video duration using ffprobe"""
    
# #     try:
# #         cmd = [
# #             'ffprobe',
# #             '-v', 'error',
# #             '-show_entries', 'format=duration',
# #             '-of', 'default=noprint_wrappers=1:nokey=1',
# #             VIDEO_FILE
# #         ]
        
# #         result = subprocess.run(
# #             cmd,
# #             capture_output=True,
# #             text=True,
# #             check=True
# #         )
        
# #         duration = float(result.stdout.strip())
# #         print(f"🎥 Video duration: {duration:.2f}s")
# #         return duration
    
# #     except Exception as e:
# #         print(f"⚠️  Could not get video duration: {e}")
# #         return None

# # def create_audio_timeline(clips, video_duration):
# #     """Create complete audio timeline with silences"""
    
# #     print("\n🎵 Creating audio timeline...")
    
# #     # Start with silence for entire video duration
# #     if video_duration:
# #         final_audio = AudioSegment.silent(duration=int(video_duration * 1000))
# #         print(f"   Created {video_duration:.1f}s silent base")
# #     else:
# #         # Estimate from last clip
# #         last_clip = max(clips, key=lambda x: x['end'])
# #         final_audio = AudioSegment.silent(duration=int((last_clip['end'] + 1) * 1000))
# #         print(f"   Created {last_clip['end'] + 1:.1f}s silent base")
    
# #     # Overlay each voice clip at correct position
# #     for idx, clip in enumerate(clips, 1):
# #         audio_file = clip['audio_file']
# #         start_time = clip['start']
        
# #         if not os.path.exists(audio_file):
# #             print(f"   ⚠️  Clip {idx} not found: {audio_file}")
# #             continue
        
# #         try:
# #             # Load voice clip
# #             voice_clip = AudioSegment.from_mp3(audio_file)
            
# #             # Calculate position in milliseconds
# #             position_ms = int(start_time * 1000)
            
# #             # Overlay voice clip at correct position
# #             final_audio = final_audio.overlay(voice_clip, position=position_ms)
            
# #             print(f"   [{idx}/{len(clips)}] Added: {os.path.basename(audio_file)} at {start_time:.1f}s")
        
# #         except Exception as e:
# #             print(f"   ❌ Error adding clip {idx}: {e}")
# #             continue
    
# #     return final_audio

# # def save_audio_track(audio, output_path):
# #     """Save combined audio to file"""
    
# #     print(f"\n💾 Saving audio track...")
    
# #     try:
# #         audio.export(
# #             output_path,
# #             format="wav",
# #             parameters=["-ar", "16000"]  # 16kHz sample rate
# #         )
# #         print(f"   ✅ Saved: {output_path}")
# #         return True
# #     except Exception as e:
# #         print(f"   ❌ Error saving audio: {e}")
# #         return False

# # def replace_video_audio(video_file, audio_file, output_file):
# #     """Replace video audio track with new dubbed audio"""
    
# #     print(f"\n🎬 Merging audio with video...")
# #     print(f"   Video: {video_file}")
# #     print(f"   Audio: {audio_file}")
# #     print(f"   Output: {output_file}")
    
# #     try:
# #         # FFmpeg command to replace audio
# #         cmd = [
# #             'ffmpeg',
# #             '-i', video_file,      # Input video
# #             '-i', audio_file,      # Input audio
# #             '-c:v', 'copy',        # Copy video stream (no re-encoding)
# #             '-c:a', 'aac',         # Encode audio as AAC
# #             '-b:a', '192k',        # Audio bitrate
# #             '-map', '0:v:0',       # Map video from first input
# #             '-map', '1:a:0',       # Map audio from second input
# #             '-shortest',           # Use shortest stream duration
# #             '-y',                  # Overwrite output
# #             output_file
# #         ]
        
# #         print(f"\n⏳ Running FFmpeg (this may take a minute)...")
        
# #         result = subprocess.run(
# #             cmd,
# #             capture_output=True,
# #             text=True,
# #             check=True
# #         )
        
# #         print(f"✅ Video created successfully!")
# #         return True
    
# #     except subprocess.CalledProcessError as e:
# #         print(f"❌ FFmpeg error:")
# #         print(f"   {e.stderr}")
# #         return False
# #     except Exception as e:
# #         print(f"❌ Error: {e}")
# #         return False

# # def get_file_size(file_path):
# #     """Get human-readable file size"""
# #     size_bytes = os.path.getsize(file_path)
    
# #     for unit in ['B', 'KB', 'MB', 'GB']:
# #         if size_bytes < 1024.0:
# #             return f"{size_bytes:.1f} {unit}"
# #         size_bytes /= 1024.0

# # def display_summary(metadata, output_file):
# #     """Display final summary"""
    
# #     print("\n" + "="*70)
# #     print("🎉 FINAL DUBBED VIDEO COMPLETE!")
# #     print("="*70)
    
# #     print(f"\n📊 Statistics:")
# #     print(f"   Original language: {metadata['source_data']['source_language']}")
# #     print(f"   Dubbed language: {metadata['source_data']['target_language']}")
# #     print(f"   Total voice clips: {metadata['total_clips']}")
    
# #     print(f"\n🎭 Voice Cast:")
# #     for speaker, voice_info in metadata['voice_assignments'].items():
# #         clip_count = sum(1 for c in metadata['clips'] if c.get('speaker') == speaker)
# #         print(f"   {speaker}: {voice_info['name']} ({clip_count} lines)")
    
# #     total_duration = sum(c['duration'] for c in metadata['clips'])
# #     print(f"\n⏱️  Total dialogue: {total_duration:.1f}s")
    
# #     if os.path.exists(output_file):
# #         file_size = get_file_size(output_file)
# #         print(f"\n📁 Output File:")
# #         print(f"   Location: {output_file}")
# #         print(f"   Size: {file_size}")
    
# #     print("\n" + "="*70)
# #     print("✅ All Done! Your anime is now dubbed in English!")
# #     print("="*70)

# # def display_pipeline_summary():
# #     """Display complete pipeline summary"""
    
# #     print("\n" + "="*70)
# #     print("📋 COMPLETE PIPELINE SUMMARY")
# #     print("="*70)
    
# #     pipeline_steps = [
# #         ("Step 1", "Audio Extraction", "work/audio_16k.wav"),
# #         ("Step 2", "Transcription", "work/transcription.json"),
# #         ("Step 3", "Speaker Diarization", "work/transcription_with_speakers.json"),
# #         ("Step 4", "Translation", "work/translated_segments.json"),
# #         ("Step 5", "Voice Generation", "work/voice_clips/"),
# #         ("Step 6", "Final Assembly", OUTPUT_VIDEO)
# #     ]
    
# #     print("\n✅ Completed Steps:")
# #     for step, name, output in pipeline_steps:
# #         status = "✅" if os.path.exists(output) else "⚠️"
# #         print(f"   {status} {step}: {name}")
# #         if os.path.exists(output):
# #             if os.path.isfile(output):
# #                 size = get_file_size(output)
# #                 print(f"      → {output} ({size})")
# #             else:
# #                 file_count = len([f for f in os.listdir(output) if f.endswith('.mp3')])
# #                 print(f"      → {output} ({file_count} files)")

# # def main():
# #     print("=" * 70)
# #     print("STEP 6: Final Video Assembly")
# #     print("=" * 70)
    
# #     # Check prerequisites
# #     if not check_prerequisites():
# #         return
    
# #     # Load voice clips metadata
# #     metadata = load_voice_clips_metadata()
    
# #     # Get video duration
# #     video_duration = get_video_duration()
    
# #     # Create audio timeline
# #     final_audio = create_audio_timeline(metadata['clips'], video_duration)
    
# #     # Save audio track
# #     if not save_audio_track(final_audio, TEMP_AUDIO):
# #         print("❌ Failed to save audio track")
# #         return
    
# #     # Replace video audio
# #     if not replace_video_audio(VIDEO_FILE, TEMP_AUDIO, OUTPUT_VIDEO):
# #         print("❌ Failed to create final video")
# #         return
    
# #     # Display summary
# #     display_summary(metadata, OUTPUT_VIDEO)
    
# #     # Display complete pipeline summary
# #     display_pipeline_summary()
    
# #     print(f"\n🎬 Watch your dubbed video:")
# #     print(f"   {OUTPUT_VIDEO}")
# #     print("\n💡 Next steps:")
# #     print("   - Try with a longer video clip")
# #     print("   - Experiment with different voices")
# #     print("   - Fine-tune translation prompts")
# #     print("   - Add subtitle generation")

# # if __name__ == "__main__":
# #     main()
# # step6_final_assembly.py (UPDATED - Compatible with your metadata)
# import json
# import os
# import subprocess
# from pydub import AudioSegment
# from datetime import datetime


# # Configuration
# VIDEO_FILE ="input/Seikon no Qwaser - S01E01 - [9DBF3AAE] (online-video-cutter.com).mp4"
# VOICE_CLIPS_METADATA = "work/voice_clips_metadata.json"
# OUTPUT_VIDEO = "output/anime_dubbed.mp4"
# TEMP_AUDIO = "work/final_audio.wav"


# def check_prerequisites():
#     """Check if required files exist"""
#     if not os.path.exists(VIDEO_FILE):
#         print(f"❌ Video file not found: {VIDEO_FILE}")
#         print("   Please put your anime clip in input/anime_sample.mp4")
#         return False

#     if not os.path.exists(VOICE_CLIPS_METADATA):
#         print(f"❌ Voice clips metadata not found: {VOICE_CLIPS_METADATA}")
#         print("   Please run step5_voice_generation.py first")
#         return False

#     # Create output directory
#     os.makedirs("output", exist_ok=True)
#     os.makedirs(os.path.dirname(TEMP_AUDIO), exist_ok=True)

#     return True


# def load_voice_clips_metadata():
#     """Load voice clips metadata (handles your exact structure)"""
#     with open(VOICE_CLIPS_METADATA, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     # Handle your exact structure: {'speakers': {...}, 'clips': [...]}
#     clips = data.get('clips', [])
#     speakers = data.get('speakers', data.get('voice_assignments', {}))

#     # Create expected structure
#     metadata = {
#         'total_clips': len(clips),
#         'clips': clips,
#         'voice_assignments': speakers,
#         'source_data': {
#             'model': 'whisper-large-v3',
#             'translation_model': 'gpt-4o-mini',  # from your all_attempts
#             'source_language': 'Japanese',
#             'target_language': 'English'
#         }
#     }

#     print(f"📄 Loaded metadata for {metadata['total_clips']} clips")
#     print(f"   Speakers: {list(speakers.keys())}")
#     return metadata


# def get_video_duration():
#     """Get original video duration using ffprobe"""
#     try:
#         cmd = [
#             'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
#             '-of', 'default=noprint_wrappers=1:nokey=1', VIDEO_FILE
#         ]
#         result = subprocess.run(cmd, capture_output=True, text=True, check=True)
#         duration = float(result.stdout.strip())
#         print(f"🎥 Video duration: {duration:.2f}s")
#         return duration
#     except Exception as e:
#         print(f"⚠️  Could not get video duration: {e}")
#         return None


# def create_audio_timeline(clips, video_duration):
#     """Create complete audio timeline with silences"""
#     print("\n🎵 Creating audio timeline...")

#     # Start with silence for entire video duration
#     if video_duration:
#         final_audio = AudioSegment.silent(duration=int(video_duration * 1000))
#         print(f"   Created {video_duration:.1f}s silent base")
#     else:
#         # Estimate from last clip
#         last_clip = max(clips, key=lambda x: x.get('end', 0))
#         final_audio = AudioSegment.silent(duration=int((last_clip.get('end', 0) + 2) * 1000))
#         print(f"   Created {last_clip.get('end', 0) + 2:.1f}s silent base")

#     # Overlay each voice clip at correct position
#     for idx, clip in enumerate(clips, 1):
#         audio_file = clip.get('audio_file')
#         start_time = clip.get('start', 0)

#         if not audio_file or not os.path.exists(audio_file):
#             print(f"   ⚠️  Clip {idx} not found: {audio_file}")
#             continue

#         try:
#             voice_clip = AudioSegment.from_mp3(audio_file)
#             position_ms = int(start_time * 1000)
#             final_audio = final_audio.overlay(voice_clip, position=position_ms)
#             print(f"   [{idx}/{len(clips)}] Added: {os.path.basename(audio_file)} at {start_time:.1f}s")
#         except Exception as e:
#             print(f"   ❌ Error adding clip {idx}: {e}")
#             continue

#     return final_audio


# def save_audio_track(audio, output_path):
#     """Save combined audio to file"""
#     print(f"\n💾 Saving audio track...")
#     try:
#         audio.export(output_path, format="wav", parameters=["-ar", "16000"])
#         print(f"   ✅ Saved: {output_path}")
#         return True
#     except Exception as e:
#         print(f"   ❌ Error saving audio: {e}")
#         return False


# def replace_video_audio(video_file, audio_file, output_file):
#     """Replace video audio track with new dubbed audio"""
#     print(f"\n🎬 Merging audio with video...")
#     print(f"   Video: {video_file}")
#     print(f"   Audio: {audio_file}")
#     print(f"   Output: {output_file}")

#     try:
#         cmd = [
#             'ffmpeg', '-i', video_file,
#             '-i', audio_file,
#             '-c:v', 'copy',
#             '-c:a', 'aac',
#             '-b:a', '192k',
#             '-map', '0:v:0',
#             '-map', '1:a:0',
#             '-shortest',
#             '-y',
#             output_file
#         ]

#         print("⏳ Running FFmpeg (this may take a minute)...")
#         result = subprocess.run(cmd, capture_output=True, text=True, check=True)
#         print("✅ Video created successfully!")
#         return True

#     except subprocess.CalledProcessError as e:
#         print("❌ FFmpeg error:")
#         print(f"   {e.stderr}")
#         print("\n💡 FFmpeg not found? Install from: https://ffmpeg.org/download.html")
#         print("   Add ffmpeg/bin to your PATH")
#         return False
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return False


# def get_file_size(file_path):
#     """Get human-readable file size"""
#     if not os.path.exists(file_path):
#         return "N/A"
#     size_bytes = os.path.getsize(file_path)
#     for unit in ['B', 'KB', 'MB', 'GB']:
#         if size_bytes < 1024.0:
#             return f"{size_bytes:.1f} {unit}"
#         size_bytes /= 1024.0
#     return "N/A"


# def display_summary(metadata, output_file):
#     """Display final summary"""
#     print("\n" + "=" * 70)
#     print("🎉 FINAL DUBBED VIDEO COMPLETE!")
#     print("=" * 70)

#     print(f"\n📊 Statistics:")
#     print(f"   Original: {metadata['source_data']['source_language']}")
#     print(f"   Dubbed: {metadata['source_data']['target_language']}")
#     print(f"   Total clips: {metadata['total_clips']}")

#     print("\n🎭 Voice Cast:")
#     for speaker, voice_info in metadata['voice_assignments'].items():
#         clip_count = sum(1 for c in metadata['clips'] if c.get('speaker') == speaker)
#         print(f"   {speaker}: {voice_info.get('name', voice_info.get('voice_name', 'Unknown'))} ({clip_count} lines)")

#     total_duration = sum(c.get('duration', 0) for c in metadata['clips'])
#     print(f"\n⏱️  Total dialogue: {total_duration:.1f}s")

#     if os.path.exists(output_file):
#         file_size = get_file_size(output_file)
#         print(f"\n📁 Output:")
#         print(f"   {output_file}")
#         print(f"   Size: {file_size}")

#     print("\n" + "=" * 70)
#     print("✅ All Done! Your anime is dubbed!")
#     print("=" * 70)


# def display_pipeline_summary():
#     """Display complete pipeline summary"""
#     print("\n" + "=" * 70)
#     print("📋 COMPLETE PIPELINE SUMMARY")
#     print("=" * 70)

#     pipeline_steps = [
#         ("Step 1", "Audio Extraction", "work/audio_16k.wav"),
#         ("Step 2", "Transcription", "work/transcription.json"),
#         ("Step 3", "Diarization", "work/transcription_with_speakers.json"),
#         ("Step 4", "Translation", "work/translated_segments.json"),
#         ("Step 5", "Voice Generation", "work/voice_clips/"),
#         ("Step 6", "Final Assembly", OUTPUT_VIDEO),
#     ]

#     print("\n✅ Completed Steps:")
#     for step, name, output in pipeline_steps:
#         status = "✅" if os.path.exists(output) else "⚠️ "
#         print(f"   {status} {step}: {name}")
#         if os.path.exists(output):
#             if os.path.isfile(output):
#                 size = get_file_size(output)
#                 print(f"      → {output} ({size})")
#             elif os.path.isdir(output):
#                 mp3_count = len([f for f in os.listdir(output) if f.endswith('.mp3')])
#                 print(f"      → {output} ({mp3_count} MP3 files)")


# def main():
#     print("=" * 70)
#     print("STEP 6: Final Video Assembly")
#     print("=" * 70)

#     if not check_prerequisites():
#         return

#     metadata = load_voice_clips_metadata()

#     video_duration = get_video_duration()

#     final_audio = create_audio_timeline(metadata['clips'], video_duration)

#     if not save_audio_track(final_audio, TEMP_AUDIO):
#         print("❌ Failed to save audio track")
#         return

#     if not replace_video_audio(VIDEO_FILE, TEMP_AUDIO, OUTPUT_VIDEO):
#         print("❌ Failed to create final video")
#         return

#     display_summary(metadata, OUTPUT_VIDEO)
#     display_pipeline_summary()

#     print(f"\n🎬 Watch your dubbed video:")
#     print(f"   {OUTPUT_VIDEO}")
#     print("\n💡 Share your results! 🎉")


# if __name__ == "__main__":
#     main()
# step6_final_assembly.py (WITH BACKGROUND NOISE RESTORATION)
import json
import os
import subprocess
from pydub import AudioSegment
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
VIDEO_FILE = "input/anime.mp4"
VOICE_CLIPS_METADATA = "work/voice_clips_metadata.json"
BACKGROUND_NOISE = "background_noise.wav"  # From step0 audio separation
OUTPUT_VIDEO = "output/anime_dubbed.mp4"
TEMP_DUBBED_AUDIO = "work/dubbed_dialogue.wav"
TEMP_FINAL_AUDIO = "work/final_audio_with_bg.wav"


# ═══════════════════════════════════════════════════════════════════════════
# PREREQUISITES
# ═══════════════════════════════════════════════════════════════════════════
def check_prerequisites():
    """Check if required files exist"""
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Video file not found: {VIDEO_FILE}")
        return False

    if not os.path.exists(VOICE_CLIPS_METADATA):
        print(f"❌ Voice clips metadata not found: {VOICE_CLIPS_METADATA}")
        print("   Please run step5_voice_generation.py first")
        return False

    # Check if background noise exists
    if not os.path.exists(BACKGROUND_NOISE):
        print(f"⚠️  Background noise not found: {BACKGROUND_NOISE}")
        print("   Will proceed without background restoration")
        print("   Run step0_audio_separation.py to enable this feature")

    # Create output directory
    os.makedirs("output", exist_ok=True)
    os.makedirs("work", exist_ok=True)

    return True


def load_voice_clips_metadata():
    """Load voice clips metadata"""
    with open(VOICE_CLIPS_METADATA, 'r', encoding='utf-8') as f:
        data = json.load(f)

    clips = data.get('clips', [])
    speakers = data.get('speakers', data.get('voice_assignments', {}))

    metadata = {
        'total_clips': len(clips),
        'clips': clips,
        'voice_assignments': speakers,
        'source_data': {
            'model': 'whisper-large-v3',
            'translation_model': 'gpt-4o-mini',
            'source_language': 'Japanese',
            'target_language': 'English'
        }
    }

    print(f"📄 Loaded metadata for {metadata['total_clips']} clips")
    print(f"   Speakers: {list(speakers.keys())}")
    return metadata


def get_video_duration():
    """Get original video duration using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', VIDEO_FILE
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        print(f"🎥 Video duration: {duration:.2f}s")
        return duration
    except Exception as e:
        print(f"⚠️  Could not get video duration: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# AUDIO TIMELINE CREATION (DUBBED DIALOGUE ONLY)
# ═══════════════════════════════════════════════════════════════════════════
def create_dialogue_timeline(clips, video_duration):
    """Create dubbed dialogue timeline (without background yet)"""
    print("\n🎵 Creating dubbed dialogue timeline...")

    # Start with silence for entire video duration
    if video_duration:
        dialogue_audio = AudioSegment.silent(duration=int(video_duration * 1000))
        print(f"   Created {video_duration:.1f}s silent base")
    else:
        last_clip = max(clips, key=lambda x: x.get('end', 0))
        dialogue_audio = AudioSegment.silent(duration=int((last_clip.get('end', 0) + 2) * 1000))
        print(f"   Created {last_clip.get('end', 0) + 2:.1f}s silent base")

    # Overlay each voice clip at correct position
    overlaps_detected = 0
    previous_end = 0

    for idx, clip in enumerate(clips, 1):
        audio_file = clip.get('audio_file')
        start_time = clip.get('start', 0)
        end_time = clip.get('end', 0)

        if not audio_file or not os.path.exists(audio_file):
            print(f"   ⚠️  [{idx}/{len(clips)}] Clip not found: {audio_file}")
            continue

        # Detect overlap with previous clip
        if start_time < previous_end:
            gap = previous_end - start_time
            print(f"   ⚠️  [{idx}/{len(clips)}] Overlap detected: {gap:.2f}s gap")
            overlaps_detected += 1
            # Shift forward to avoid overlap
            start_time = previous_end + 0.1

        try:
            voice_clip = AudioSegment.from_mp3(audio_file)
            position_ms = int(start_time * 1000)
            dialogue_audio = dialogue_audio.overlay(voice_clip, position=position_ms)
            print(f"   ✅ [{idx}/{len(clips)}] {os.path.basename(audio_file)} at {start_time:.1f}s")
            previous_end = start_time + (len(voice_clip) / 1000.0)
        except Exception as e:
            print(f"   ❌ [{idx}/{len(clips)}] Error: {e}")
            continue

    if overlaps_detected > 0:
        print(f"\n   ⚠️  Fixed {overlaps_detected} timing overlaps")

    return dialogue_audio


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND NOISE RESTORATION (NEW!)
# ═══════════════════════════════════════════════════════════════════════════
# def mix_dialogue_with_background(dialogue_audio, background_path, video_duration):
#     """Mix dubbed dialogue with original background noise/music/SFX"""
#     print("\n🔊 Restoring background noise (music + SFX)...")

#     if not os.path.exists(background_path):
#         print("   ⚠️  Background file not found, skipping restoration")
#         return dialogue_audio

#     try:
#         # Load background noise
#         background = AudioSegment.from_wav(background_path)
#         print(f"   ✅ Loaded background: {len(background)/1000:.1f}s")

#         # Match durations
#         dialogue_duration_ms = len(dialogue_audio)
#         background_duration_ms = len(background)

#         if background_duration_ms < dialogue_duration_ms:
#             # Loop background if too short
#             loops_needed = (dialogue_duration_ms // background_duration_ms) + 1
#             background = background * loops_needed
#             print(f"   🔁 Looped background {loops_needed}x to match duration")

#         # Trim to exact length
#         background = background[:dialogue_duration_ms]

#         # Mix: dialogue at full volume, background at reduced volume
#         # Adjust background volume (reduce by 8dB so dialogue is clear)
#         background_reduced = background - 8
#         print(f"   🔉 Reduced background volume by 8dB")

#         # Overlay dialogue on top of background
#         final_audio = background_reduced.overlay(dialogue_audio)
#         print(f"   ✅ Mixed dialogue + background")

#         return final_audio

#     except Exception as e:
#         print(f"   ❌ Error mixing background: {e}")
#         print("   Proceeding with dialogue only")
#         return dialogue_audio
def match_loudness(target, reference):
    """Rough loudness matching by RMS level"""
    target_rms = target.rms
    ref_rms = reference.rms

    if target_rms == 0:
        return target

    ratio = ref_rms / target_rms
    db_change = 20 * math.log10(ratio)

    return target + db_change


def mix_dialogue_with_background(dialogue_audio, background_path, video_duration):
    print("\n🔊 Restoring background music + SFX...")

    if not os.path.exists(background_path):
        print("   ⚠ Background missing. Skipping mix.")
        return dialogue_audio, dialogue_audio

    background = AudioSegment.from_wav(background_path)

    # Match lengths
    dialogue_len = len(dialogue_audio)
    if len(background) < dialogue_len:
        loops = (dialogue_len // len(background)) + 1
        background = background * loops

    background = background[:dialogue_len]

    # Normalize both tracks
    dialogue_audio = dialogue_audio.normalize()
    background = background.normalize()

    # Reduce background slightly (dynamic safe range)
    background = background - 6   # instead of -8 fixed

    # Create with-bg mix
    final_with_bg = background.overlay(dialogue_audio)

    # Final master normalize (keeps volume similar to original feel)
    final_with_bg = final_with_bg.normalize()

    print("   ✅ Mixed + normalized")

    return final_with_bg, dialogue_audio

def save_audio_track(audio, output_path):
    """Save combined audio to file"""
    print(f"\n💾 Saving final audio track...")
    try:
        audio.export(output_path, format="wav", parameters=["-ar", "16000"])
        print(f"   ✅ Saved: {output_path}")
        file_size = get_file_size(output_path)
        print(f"   Size: {file_size}")
        return True
    except Exception as e:
        print(f"   ❌ Error saving audio: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# VIDEO ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════
def replace_video_audio(video_file, audio_file, output_file):
    """Replace video audio track with new dubbed audio (with background)"""
    print(f"\n🎬 Merging final audio with video...")
    print(f"   Video: {video_file}")
    print(f"   Audio: {audio_file}")
    print(f"   Output: {output_file}")

    try:
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-i', audio_file,
            '-c:v', 'copy',       # Copy video (no re-encode)
            '-c:a', 'aac',        # Encode audio as AAC
            '-b:a', '192k',       # Audio bitrate
            '-map', '0:v:0',      # Video from first input
            '-map', '1:a:0',      # Audio from second input
            '-shortest',          # Match shortest stream
            '-y',                 # Overwrite
            output_file
        ]

        print("⏳ Running FFmpeg (this may take a minute)...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Video created successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg error:")
        print(f"   {e.stderr}")
        print("\n💡 Install FFmpeg: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════
def get_file_size(file_path):
    """Get human-readable file size"""
    if not os.path.exists(file_path):
        return "N/A"
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return "N/A"


def display_summary(metadata, output_file):
    """Display final summary"""
    print("\n" + "=" * 70)
    print("🎉 FINAL DUBBED VIDEO COMPLETE!")
    print("=" * 70)

    print(f"\n📊 Statistics:")
    print(f"   Original: {metadata['source_data']['source_language']}")
    print(f"   Dubbed: {metadata['source_data']['target_language']}")
    print(f"   Total clips: {metadata['total_clips']}")

    print("\n🎭 Voice Cast:")
    # for speaker, voice_info in metadata['voice_assignments'].items():
    #     clip_count = sum(1 for c in metadata['clips'] if c.get('speaker') == speaker)
    #     voice_name = voice_info.get('name', voice_info.get('voice_name', 'Unknown'))
    #     print(f"   {speaker}: {voice_name} ({clip_count} lines)")
    for speaker, voice_info in metadata['voice_assignments'].items():
        clip_count = sum(1 for c in metadata['clips'] if c.get('speaker') == speaker)

        # Handle both string and dict formats
        if isinstance(voice_info, dict):
            voice_name = voice_info.get('name') or voice_info.get('voice_name') or 'Unknown'
        else:
            voice_name = os.path.basename(str(voice_info))

        print(f"   {speaker}: {voice_name} ({clip_count} lines)")

    total_duration = sum(c.get('duration', 0) for c in metadata['clips'])
    print(f"\n⏱️  Total dialogue: {total_duration:.1f}s")

    if os.path.exists(output_file):
        file_size = get_file_size(output_file)
        print(f"\n📁 Output:")
        print(f"   {output_file}")
        print(f"   Size: {file_size}")

    print("\n✨ Features:")
    print("   ✅ Dubbed dialogue")
    if os.path.exists(BACKGROUND_NOISE):
        print("   ✅ Original background music/SFX restored")
    else:
        print("   ⚠️  No background restoration (run step0 for this)")
    print("   ✅ Perfect timing sync")

    print("\n" + "=" * 70)
    print("✅ All Done! Your anime is dubbed!")
    print("=" * 70)


def display_pipeline_summary():
    """Display complete pipeline summary"""
    print("\n" + "=" * 70)
    print("📋 COMPLETE PIPELINE SUMMARY")
    print("=" * 70)

    pipeline_steps = [
        ("Step 0", "Audio Separation", BACKGROUND_NOISE),
        ("Step 1", "Audio Extraction", "work/audio_16k.wav"),
        ("Step 2", "Transcription", "work/transcription.json"),
        ("Step 3", "Diarization", "work/translated_segments_interactive.json"),
        ("Step 4", "Translation", "work/translated_segments.json"),
        ("Step 5", "Voice Generation", "work/voice_clips/"),
        ("Step 6", "Final Assembly", OUTPUT_VIDEO),
    ]

    print("\n✅ Completed Steps:")
    for step, name, output in pipeline_steps:
        exists = os.path.exists(output)
        status = "✅" if exists else "⚠️ "
        print(f"   {status} {step}: {name}")
        if exists:
            if os.path.isfile(output):
                size = get_file_size(output)
                print(f"      → {output} ({size})")
            elif os.path.isdir(output):
                mp3_count = len([f for f in os.listdir(output) if f.endswith('.mp3')])
                print(f"      → {output} ({mp3_count} MP3 files)")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("STEP 6: Final Video Assembly (with Background Restoration)")
    print("=" * 70)

    if not check_prerequisites():
        return

    # Load metadata
    metadata = load_voice_clips_metadata()

    # Get video duration
    video_duration = get_video_duration()

    # Step 1: Create dubbed dialogue timeline
    dialogue_audio = create_dialogue_timeline(metadata['clips'], video_duration)

    # Step 2: Mix with original background (music/SFX)
    # final_audio = mix_dialogue_with_background(
    #     dialogue_audio,
    #     BACKGROUND_NOISE,
    #     video_duration
    # )

    final_audio_with_bg, final_audio_without_bg = mix_dialogue_with_background(
    dialogue_audio,
    BACKGROUND_NOISE,
    video_duration)

    # Step 3: Save final audio
    # if not save_audio_track(final_audio, TEMP_FINAL_AUDIO):
    #     print("❌ Failed to save audio track")
    #     return
    save_audio_track(final_audio_with_bg, TEMP_FINAL_AUDIO)

    # Save audio WITHOUT background
    save_audio_track(final_audio_without_bg, "work/final_audio_without_bg.wav")
    # Step 4: Replace video audio
    if not replace_video_audio(VIDEO_FILE, TEMP_FINAL_AUDIO, OUTPUT_VIDEO):
        print("❌ Failed to create final video")
        return

    # Display summary
    display_summary(metadata, OUTPUT_VIDEO)
    display_pipeline_summary()

    print(f"\n🎬 Watch your dubbed video:")
    print(f"   {OUTPUT_VIDEO}")
    print("\n💡 Share your results! 🎉")


if __name__ == "__main__":
    main()
