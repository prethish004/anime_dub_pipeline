# # # # step5_voice_generation.py
# # # import json
# # # import os
# # # import time
# # # from elevenlabs.client import ElevenLabs
# # # from elevenlabs import VoiceSettings

# # # # Configuration
# # # INPUT_JSON = "work/translated_segments.json"
# # # OUTPUT_DIR = "work/voice_clips"

# # # # ElevenLabs API Key
# # # ELEVENLABS_API_KEY = ""  # Get from: https://elevenlabs.io

# # # # Voice mapping based on speaker profiles
# # # VOICE_LIBRARY = {
# # #     # Male voices
# # #     'male_adult': {
# # #         'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - Deep male
# # #         'name': 'Adam',
# # #         'description': 'Deep, authoritative male voice'
# # #     },
# # #     'male_young': {
# # #         'voice_id': 'yoZ06aMxZJJ28mfd3POQ',  # Sam - Young male
# # #         'name': 'Sam',
# # #         'description': 'Young, energetic male voice'
# # #     },
# # #     'male_mature': {
# # #         'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold - Mature male
# # #         'name': 'Arnold',
# # #         'description': 'Strong, mature male voice'
# # #     },
    
# # #     # Female voices
# # #     'female_adult': {
# # #         'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - Adult female
# # #         'name': 'Rachel',
# # #         'description': 'Clear, professional female voice'
# # #     },
# # #     'female_young': {
# # #         'voice_id': 'jsCqWAovK2LkecY7zXl4',  # Freya - Young female
# # #         'name': 'Freya',
# # #         'description': 'Young, friendly female voice'
# # #     },
# # #     'female_teen': {
# # #         'voice_id': 'XB0fDUnXU5powFXDhCwa',  # Charlotte - Teen female
# # #         'name': 'Charlotte',
# # #         'description': 'Youthful, energetic female voice'
# # #     }
# # # }

# # # # Voice settings for anime dubbing
# # # ANIME_VOICE_SETTINGS = {
# # #     'stability': 0.6,        # Moderate stability (0.5-0.7 good for anime)
# # #     'similarity_boost': 0.8, # High similarity for consistency
# # #     'style': 0.3,            # Some style variation for emotion
# # #     'use_speaker_boost': True
# # # }

# # # def check_prerequisites():
# # #     """Check if required files and API key exist"""
    
# # #     if not os.path.exists(INPUT_JSON):
# # #         print(f"❌ Input file not found: {INPUT_JSON}")
# # #         print("   Please run step4_translation_free.py first")
# # #         return False
    
# # #     if ELEVENLABS_API_KEY == "YOUR_ELEVENLABS_API_KEY_HERE":
# # #         print("❌ ElevenLabs API key not set!")
# # #         print("\n📝 To get your API key:")
# # #         print("   1. Go to: https://elevenlabs.io")
# # #         print("   2. Sign up (FREE tier: 10,000 chars/month)")
# # #         print("   3. Go to Profile → API Keys")
# # #         print("   4. Copy your API key")
# # #         print("   5. Paste it in step5_voice_generation.py")
# # #         print("\n💰 Free tier: ~10 minutes of audio per month")
# # #         print("💰 Starter: $5/month for ~30 minutes")
# # #         return False
    
# # #     # Create output directory
# # #     os.makedirs(OUTPUT_DIR, exist_ok=True)
    
# # #     return True

# # # def load_translations():
# # #     """Load translated segments"""
# # #     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
# # #         data = json.load(f)
    
# # #     print(f"📄 Loaded {data['total_segments']} translated segments")
# # #     return data

# # # def select_voice_for_speaker(speaker_profile):
# # #     """Select appropriate voice based on speaker profile"""
    
# # #     gender = speaker_profile.get('gender', 'unknown')
# # #     age_group = speaker_profile.get('age_group', 'adult')
    
# # #     # Map to voice key
# # #     if gender == 'male':
# # #         if 'teen' in age_group or 'young' in age_group:
# # #             voice_key = 'male_young'
# # #         elif 'mature' in age_group or 'old' in age_group:
# # #             voice_key = 'male_mature'
# # #         else:
# # #             voice_key = 'male_adult'
# # #     elif gender == 'female':
# # #         if 'teen' in age_group:
# # #             voice_key = 'female_teen'
# # #         elif 'young' in age_group:
# # #             voice_key = 'female_young'
# # #         else:
# # #             voice_key = 'female_adult'
# # #     else:
# # #         # Default to male adult if unknown
# # #         voice_key = 'male_adult'
    
# # #     return VOICE_LIBRARY[voice_key]

# # # def assign_voices_to_speakers(data):
# # #     """Assign ElevenLabs voices to each speaker"""
    
# # #     print("\n🎭 Assigning voices to speakers...")
    
# # #     diarization = data.get('diarization', {})
# # #     speaker_profiles = diarization.get('speaker_profiles', {})
    
# # #     voice_assignments = {}
    
# # #     for speaker, profile in speaker_profiles.items():
# # #         voice_info = select_voice_for_speaker(profile)
# # #         voice_assignments[speaker] = voice_info
        
# # #         print(f"   {speaker} ({profile['gender']}, {profile['age_group']})")
# # #         print(f"   → Voice: {voice_info['name']} ({voice_info['description']})")
    
# # #     # If no profiles (fallback)
# # #     if not voice_assignments:
# # #         print("   ⚠️  No speaker profiles found, using default voices")
# # #         voice_assignments['SPEAKER_00'] = VOICE_LIBRARY['male_adult']
    
# # #     return voice_assignments

# # # def estimate_character_count(segments):
# # #     """Estimate total characters for API usage"""
# # #     total_chars = sum(len(seg['translated_text']) for seg in segments)
# # #     return total_chars

# # # def generate_voice_clips(client, segments, voice_assignments):
# # #     """Generate voice clips for all segments"""
    
# # #     print(f"\n🎙️ Generating voice clips...")
    
# # #     # Estimate usage
# # #     total_chars = estimate_character_count(segments)
# # #     print(f"   Estimated characters: {total_chars}")
# # #     print(f"   Estimated duration: ~{total_chars / 160:.1f} minutes")
# # #     print(f"   (ElevenLabs free tier: 10,000 chars/month)")
    
# # #     if total_chars > 10000:
# # #         print(f"\n⚠️  WARNING: This will use {total_chars} characters")
# # #         print(f"   Free tier limit is 10,000 characters")
# # #         response = input("   Continue? (y/n): ")
# # #         if response.lower() != 'y':
# # #             print("   Aborted")
# # #             return []
    
# # #     print("\n⏳ Generating audio (this takes a few minutes)...\n")
    
# # #     generated_clips = []
    
# # #     for idx, seg in enumerate(segments, 1):
# # #         speaker = seg.get('speaker', 'SPEAKER_00')
# # #         text = seg['translated_text']
        
# # #         # Get voice for this speaker
# # #         voice_info = voice_assignments.get(speaker)
# # #         if not voice_info:
# # #             print(f"   ⚠️  No voice assigned to {speaker}, using default")
# # #             voice_info = VOICE_LIBRARY['male_adult']
        
# # #         print(f"[{idx}/{len(segments)}] Speaker: {speaker} ({voice_info['name']})")
# # #         print(f"   Text: {text}")
# # #         print(f"   Duration: {seg['duration']:.1f}s")
        
# # #         try:
# # #             audio_stream = client.text_to_speech.convert(
# # #                 voice_id=voice_info["voice_id"],
# # #                 model_id="eleven_multilingual_v2",
# # #                 text=text,
# # #                 voice_settings=VoiceSettings(
# # #                     stability=ANIME_VOICE_SETTINGS["stability"],
# # #                     similarity_boost=ANIME_VOICE_SETTINGS["similarity_boost"],
# # #                     style=ANIME_VOICE_SETTINGS["style"],
# # #                     use_speaker_boost=ANIME_VOICE_SETTINGS["use_speaker_boost"],
# # #                 ),
# # #             )

# # #             # Convert generator → bytes
# # #             audio_bytes = b"".join(chunk for chunk in audio_stream)
# # #             output_filename = f"segment_{idx:03d}_{speaker}.mp3"
# # #             output_path = os.path.join(OUTPUT_DIR, output_filename)

# # #             with open(output_path, "wb") as f:
# # #                 f.write(audio_bytes)

# # #             print(f"   ✅ Saved: {output_filename}")

# # #             clip_info = seg.copy()
# # #             clip_info["audio_file"] = output_path
# # #             clip_info["voice_name"] = voice_info["name"]
# # #             generated_clips.append(clip_info)

# # #             time.sleep(0.5)

# # #         except Exception as e:
# # #             print(f"   ❌ Error: {e}")
# # #             print(f"   Skipping segment {idx}")
# # #             continue
                
# # #     return generated_clips

# # # def save_results(data, generated_clips, voice_assignments):
# # #     """Save generated clips metadata"""
    
# # #     output_data = {
# # #         'source_data': {
# # #             'model': data.get('model', 'unknown'),
# # #             'translation_model': data.get('translation_model', 'unknown'),
# # #             'source_language': data.get('source_language', 'Japanese'),
# # #             'target_language': data.get('target_language', 'English')
# # #         },
# # #         'voice_assignments': voice_assignments,
# # #         'total_clips': len(generated_clips),
# # #         'clips': generated_clips
# # #     }
    
# # #     output_file = "work/voice_clips_metadata.json"
# # #     with open(output_file, 'w', encoding='utf-8') as f:
# # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # #     print(f"\n💾 Metadata saved to: {output_file}")

# # # def display_summary(generated_clips, voice_assignments):
# # #     """Display generation summary"""
    
# # #     print("\n" + "="*70)
# # #     print("📊 VOICE GENERATION SUMMARY")
# # #     print("="*70)
    
# # #     print(f"\n✅ Successfully generated: {len(generated_clips)} clips")
    
# # #     print(f"\n🎭 Voice Assignments:")
# # #     for speaker, voice_info in voice_assignments.items():
# # #         clip_count = sum(1 for c in generated_clips if c.get('speaker') == speaker)
# # #         print(f"   {speaker}: {voice_info['name']} ({clip_count} clips)")
    
# # #     total_duration = sum(c['duration'] for c in generated_clips)
# # #     print(f"\n⏱️  Total audio duration: {total_duration:.1f} seconds")
    
# # #     print(f"\n📁 Audio files saved to: {OUTPUT_DIR}/")
    
# # #     print("\n" + "="*70)
# # #     print("📋 SAMPLE CLIPS (First 3)")
# # #     print("="*70)
    
# # #     for clip in generated_clips[:3]:
# # #         print(f"\n[{clip['start']:.1f}s - {clip['end']:.1f}s] {clip.get('speaker', 'UNKNOWN')}")
# # #         print(f"🇯🇵 Original: {clip.get('original_text', 'N/A')}")
# # #         print(f"🇬🇧 Translated: {clip['translated_text']}")
# # #         print(f"🎙️  Voice: {clip['voice_name']}")
# # #         print(f"📄 File: {os.path.basename(clip['audio_file'])}")

# # # def main():
# # #     print("=" * 70)
# # #     print("STEP 5: Voice Generation with ElevenLabs")
# # #     print("=" * 70)
    
# # #     # Check prerequisites
# # #     if not check_prerequisites():
# # #         return
    
# # #     # Initialize ElevenLabs client
# # #     try:
# # #         client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
# # #         print("✅ ElevenLabs client initialized")
# # #     except Exception as e:
# # #         print(f"❌ Failed to initialize ElevenLabs client: {e}")
# # #         return
    
# # #     # Load translations
# # #     data = load_translations()
    
# # #     # Assign voices based on speaker profiles
# # #     voice_assignments = assign_voices_to_speakers(data)
    
# # #     # Generate voice clips
# # #     generated_clips = generate_voice_clips(
# # #         client,
# # #         data['segments'],
# # #         voice_assignments
# # #     )
    
# # #     if not generated_clips:
# # #         print("❌ No clips were generated")
# # #         return
    
# # #     # Save results
# # #     save_results(data, generated_clips, voice_assignments)
    
# # #     # Display summary
# # #     display_summary(generated_clips, voice_assignments)
    
# # #     print("\n" + "=" * 70)
# # #     print("✅ Step 5 Complete!")
# # #     print("=" * 70)
# # #     print(f"📁 Generated clips: {len(generated_clips)}")
# # #     print(f"📂 Location: {OUTPUT_DIR}/")
# # #     print("\nNext: Run step6_final_assembly.py to combine everything!")

# # # if __name__ == "__main__":
# # #     main()
# # # step5_voice_generation_interactive.py
# # # 🚀 COMPLETE INTERACTIVE VOICE GENERATION WITH AGE & EMOTION CONTROL
# # # Updated: Feb 02, 2026

# # import json
# # import os
# # import time
# # from elevenlabs.client import ElevenLabs
# # from elevenlabs import VoiceSettings

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # CONFIGURATION
# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # INPUT_JSON = "work/translated_segments_interactive.json"  # From step4_translation_interactive.py
# # OUTPUT_DIR = "work/voice_clips"

# # # ElevenLabs API Key (REPLACE WITH YOUR KEY)
# # ELEVENLABS_API_KEY = ""

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # EXPANDED VOICE LIBRARY - 10+ VOICES WITH AGE CATEGORIES
# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # VOICE_LIBRARY = {
# #     # MALE VOICES - 5 age ranges
# #     'male_child': {
# #         'voice_id': 'XrExE9yKIg1WjnnlVkGX',  # Michael
# #         'name': 'Michael (Child 8-12)',
# #         'description': 'Young boy voice - perfect for kid characters',
# #         'age_range': 'child', 'gender': 'male'
# #     },
# #     'male_teen': {
# #         'voice_id': 'yoZ06aMxZJJ28mfd3POQ',  # Sam
# #         'name': 'Sam (Teen 13-17)',
# #         'description': 'Teenage boy - energetic school anime characters',
# #         'age_range': 'teen', 'gender': 'male'
# #     },
# #     'male_young_adult': {
# #         'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam
# #         'name': 'Adam (Young Adult 18-30)',
# #         'description': 'Deep authoritative voice - main heroes',
# #         'age_range': 'young_adult', 'gender': 'male'
# #     },
# #     'male_adult': {
# #         'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold
# #         'name': 'Arnold (Adult 30-50)',
# #         'description': 'Strong mature voice - mentors, villains',
# #         'age_range': 'adult', 'gender': 'male'
# #     },
# #     'male_elderly': {
# #         'voice_id': 'ErXwobaYiN019PkySvjV',  # Antoni
# #         'name': 'Antoni (Elderly 50+)',
# #         'description': 'Wise calm voice - old masters, grandfathers',
# #         'age_range': 'elderly', 'gender': 'male'
# #     },
    
# #     # FEMALE VOICES - 5 age ranges
# #     'female_child': {
# #         'voice_id': 'jBpfuIE2acCO8z3wKNLl',  # Gigi
# #         'name': 'Gigi (Child 8-12)',
# #         'description': 'Young girl voice - perfect for kid characters',
# #         'age_range': 'child', 'gender': 'female'
# #     },
# #     'female_teen': {
# #         'voice_id': 'XB0fDUnXU5powFXDhCwa',  # Charlotte
# #         'name': 'Charlotte (Teen 13-17)',
# #         'description': 'Teenage girl - school anime heroines',
# #         'age_range': 'teen', 'gender': 'female'
# #     },
# #     'female_young_adult': {
# #         'voice_id': 'jsCqWAovK2LkecY7zXl4',  # Freya
# #         'name': 'Freya (Young Adult 18-30)',
# #         'description': 'Friendly energetic - main female leads',
# #         'age_range': 'young_adult', 'gender': 'female'
# #     },
# #     'female_adult': {
# #         'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel
# #         'name': 'Rachel (Adult 30-50)',
# #         'description': 'Clear professional - teachers, mature women',
# #         'age_range': 'adult', 'gender': 'female'
# #     },
# #     'female_elderly': {
# #         'voice_id': 'MF3mGyEYCl7XYWbV9V6O',  # Elli
# #         'name': 'Elli (Elderly 50+)',
# #         'description': 'Warm motherly - grandmothers, wise women',
# #         'age_range': 'elderly', 'gender': 'female'
# #     }
# # }

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # EMOTION PRESETS - 8 EMOTIONS FOR ANIME DUBBING
# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # EMOTION_PRESETS = {
# #     'neutral': {'stability': 0.65, 'similarity_boost': 0.75, 'style': 0.0, 'desc': 'Normal dialogue'},
# #     'happy': {'stability': 0.50, 'similarity_boost': 0.80, 'style': 0.5, 'desc': 'Joyful, cheerful'},
# #     'excited': {'stability': 0.40, 'similarity_boost': 0.85, 'style': 0.7, 'desc': 'Energetic, enthusiastic'},
# #     'angry': {'stability': 0.35, 'similarity_boost': 0.75, 'style': 0.6, 'desc': 'Intense, aggressive'},
# #     'sad': {'stability': 0.70, 'similarity_boost': 0.70, 'style': 0.3, 'desc': 'Melancholic, emotional'},
# #     'fearful': {'stability': 0.30, 'similarity_boost': 0.65, 'style': 0.4, 'desc': 'Scared, nervous'},
# #     'calm': {'stability': 0.80, 'similarity_boost': 0.75, 'style': 0.1, 'desc': 'Peaceful, wise'},
# #     'dramatic': {'stability': 0.45, 'similarity_boost': 0.85, 'style': 0.8, 'desc': 'Theatrical, intense'}
# # }

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def check_prerequisites():
# #     """Check if input file exists and API key is set"""
# #     if not os.path.exists(INPUT_JSON):
# #         print(f"❌ {INPUT_JSON} not found!")
# #         print("   Run: python step4_translation_interactive.py first")
# #         return False
    
# #     if ELEVENLABS_API_KEY.startswith("sk_") is False:
# #         print("❌ Set your ElevenLabs API key in line 15!")
# #         return False
    
# #     os.makedirs(OUTPUT_DIR, exist_ok=True)
# #     return True

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def load_data():
# #     """Load translated segments"""
# #     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
# #         data = json.load(f)
# #     print(f"✅ Loaded {len(data['segments'])} segments")
# #     return data

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def show_voices(gender=None, age=None):
# #     """Display available voices with filters"""
# #     print("\n🎤 AVAILABLE VOICES:")
# #     print("="*60)
    
# #     count = 0
# #     for key, voice in VOICE_LIBRARY.items():
# #         if gender and voice['gender'] != gender: continue
# #         if age and voice['age_range'] != age: continue
            
# #         count += 1
# #         print(f"[{count:2d}] {voice['name']}")
# #         print(f"     {voice['description']}")
# #         print()
    
# #     return list(VOICE_LIBRARY.keys())

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def show_emotions():
# #     """Display emotion presets"""
# #     print("\n😊 EMOTION PRESETS:")
# #     print("="*60)
    
# #     count = 0
# #     for key, preset in EMOTION_PRESETS.items():
# #         count += 1
# #         print(f"[{count:2d}] {key.title():8s} | {preset['desc']}")
# #         print(f"     Stability: {preset['stability']:.1f}  Style: {preset['style']:.1f}")
# #         print()
    
# #     return list(EMOTION_PRESETS.keys())

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def get_choice(options, prompt):
# #     """Get valid numbered choice from user"""
# #     while True:
# #         try:
# #             choice = input(prompt).strip().lower()
# #             if choice == 'q': return None
            
# #             idx = int(choice) - 1
# #             if 0 <= idx < len(options):
# #                 return options[idx]
# #             print(f"❌ Enter 1-{len(options)} or 'q' to quit")
# #         except:
# #             print("❌ Invalid input!")

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def configure_speaker(speaker_name, segments):
# #     """Interactive configuration for one speaker"""
# #     print(f"\n{'='*70}")
# #     print(f"🎭 CONFIGURE: {speaker_name}")
# #     print(f"{'='*70}")
    
# #     # Show speaker stats
# #     duration = sum(s['duration'] for s in segments)
# #     print(f"📊 Segments: {len(segments)} | Total time: {duration:.1f}s")
# #     print(f"📝 Sample: {segments[0]['translated_text'][:80]}...")
    
# #     # 1. GENDER SELECTION
# #     print("\n1️⃣ GENDER:")
# #     print("   [1] Male   [2] Female   [3] Show All")
# #     gender_choice = input("Choose (1-3): ").strip()
    
# #     gender_filter = None
# #     if gender_choice == '1': gender_filter = 'male'
# #     elif gender_choice == '2': gender_filter = 'female'
    
# #     # 2. AGE SELECTION  
# #     age_filter = None
# #     if gender_filter:
# #         print(f"\n2️⃣ AGE RANGE ({gender_filter.title()}):")
# #         print("   [1] Child 8-12    [2] Teen 13-17")
# #         print("   [3] Young Adult 18-30  [4] Adult 30-50")
# #         print("   [5] Elderly 50+   [6] Show All Ages")
# #         age_choice = input("Choose (1-6): ").strip()
        
# #         age_map = {'1':'child', '2':'teen', '3':'young_adult', '4':'adult', '5':'elderly'}
# #         age_filter = age_map.get(age_choice)
    
# #     # 3. VOICE SELECTION
# #     voice_keys = show_voices(gender_filter, age_filter)
# #     voice_key = get_choice(voice_keys, f"\n🎤 Select voice (1-{len(voice_keys)}): ")
# #     if not voice_key: return None
    
# #     voice_info = VOICE_LIBRARY[voice_key]
    
# #     # 4. EMOTION SELECTION
# #     emotion_keys = show_emotions()
# #     detected_emotion = segments[0].get('emotion', None)
# #     if detected_emotion:
# #         print(f"💡 Detected from audio: {detected_emotion.upper()}")
    
# #     emotion_key = get_choice(emotion_keys, f"\n😊 Select emotion (1-{len(emotion_keys)}): ")
# #     if not emotion_key: emotion_key = 'neutral'
    
# #     emotion_preset = EMOTION_PRESETS[emotion_key]
    
# #     print(f"\n✅ CONFIG SAVED!")
# #     print(f"   🎤 Voice: {voice_info['name']}")
# #     print(f"   😊 Emotion: {emotion_key.title()} ({emotion_preset['desc']})")
    
# #     return {
# #         'voice_key': voice_key,
# #         'voice_info': voice_info,
# #         'emotion_key': emotion_key,
# #         'emotion_preset': emotion_preset
# #     }

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def assign_voices_emotions(data):
# #     """Interactive voice/emotion assignment for all speakers"""
# #     print("\n🎯 INTERACTIVE VOICE & EMOTION SETUP")
# #     print("="*70)
    
# #     segments = data['segments']
# #     speakers = sorted(set(s.get('speaker', 'SPEAKER_00') for s in segments))
    
# #     print(f"👥 Found {len(speakers)} speakers: {', '.join(speakers)}")
# #     input("\nPress Enter to configure speakers...")
    
# #     speaker_configs = {}
# #     for speaker in speakers:
# #         speaker_segments = [s for s in segments if s.get('speaker') == speaker]
# #         config = configure_speaker(speaker, speaker_segments)
# #         if config:
# #             speaker_configs[speaker] = config
    
# #     # Per-segment customization?
# #     print("\n🎛️  PER-SEGMENT CONTROL?")
# #     print("   [1] Yes (custom emotion per line - SLOWER)")
# #     print("   [2] No (use defaults - FASTER)")
# #     choice = input("Choose (1-2): ").strip()
    
# #     return speaker_configs, choice == '1'

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def generate_clips(client, segments, speaker_configs, per_segment_control):
# #     """Generate all voice clips"""
# #     print(f"\n{'='*70}")
# #     print("🎙️  GENERATING VOICE CLIPS")
# #     print(f"{'='*70}")
    
# #     total_chars = sum(len(s['translated_text']) for s in segments)
# #     print(f"📊 {len(segments)} segments | {total_chars} chars | ~{total_chars/160:.1f}min")
    
# #     if total_chars > 10000:
# #         if input(f"\n⚠️  Exceeds free tier! Continue? (y/N): ").lower() != 'y':
# #             return []
    
# #     input("\nPress Enter to start generation...")
# #     generated = []
    
# #     for i, seg in enumerate(segments, 1):
# #         speaker = seg.get('speaker', 'SPEAKER_00')
# #         config = speaker_configs.get(speaker)
        
# #         if not config:
# #             config = {'voice_info': VOICE_LIBRARY['male_young_adult'], 
# #                      'emotion_preset': EMOTION_PRESETS['neutral']}
        
# #         # Per-segment emotion override
# #         if per_segment_control:
# #             override = input(f"\n[{i}/{len(segments)}] {speaker} Change emotion? (y/N): ").lower()
# #             if override == 'y':
# #                 emotion_keys = list(EMOTION_PRESETS.keys())
# #                 new_emotion = get_choice(emotion_keys, "Select new emotion: ")
# #                 config['emotion_preset'] = EMOTION_PRESETS[new_emotion]
        
# #         text = seg['translated_text']
# #         # Add emotion tag from detection if available
# #         if seg.get('emotion_tag'):
# #             text = f"{seg['emotion_tag']} {text}"
        
# #         print(f"[{i}/{len(segments)}] {speaker} ({config['voice_info']['name']})")
# #         print(f"     {text[:60]}...")
        
# #         try:
# #             audio = client.text_to_speech.convert(
# #                 voice_id=config['voice_info']['voice_id'],
# #                 text=text,
# #                 model_id="eleven_multilingual_v2",
# #                 voice_settings=VoiceSettings(
# #                     stability=config['emotion_preset']['stability'],
# #                     similarity_boost=config['emotion_preset']['similarity_boost'],
# #                     style=config['emotion_preset']['style'],
# #                     use_speaker_boost=True
# #                 )
# #             )
            
# #             filename = f"segment_{i:03d}_{speaker}.mp3"
# #             path = os.path.join(OUTPUT_DIR, filename)
            
# #             with open(path, "wb") as f:
# #                 for chunk in audio:
# #                     f.write(chunk)
            
# #             seg_copy = seg.copy()
# #             seg_copy.update({
# #                 'audio_file': path,
# #                 'voice_name': config['voice_info']['name'],
# #                 'emotion_used': config['emotion_key']
# #             })
# #             generated.append(seg_copy)
            
# #             print(f"   ✅ {filename}")
# #             time.sleep(0.5)
            
# #         except Exception as e:
# #             print(f"   ❌ Error: {e}")
    
# #     return generated

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def save_metadata(data, generated, speaker_configs):
# #     """Save all configuration and metadata"""
# #     output = {
# #         'speakers': {k: {
# #             'voice': v['voice_info']['name'],
# #             'age': v['voice_info']['age_range'],
# #             'emotion': v['emotion_key']
# #         } for k,v in speaker_configs.items()},
# #         'clips': generated
# #     }
    
# #     with open("work/voice_clips_metadata.json", 'w', encoding='utf-8') as f:
# #         json.dump(output, f, ensure_ascii=False, indent=2)
# #     print("💾 Metadata saved!")

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def show_summary(generated, speaker_configs):
# #     """Show final results"""
# #     print("\n" + "="*70)
# #     print("🎉 GENERATION COMPLETE!")
# #     print("="*70)
    
# #     print(f"✅ {len(generated)} clips generated!")
# #     total_time = sum(c['duration'] for c in generated)
# #     print(f"⏱️  Total: {total_time:.1f}s ({total_time/60:.1f}min)")
    
# #     print("\n🎭 SPEAKER SUMMARY:")
# #     for speaker, config in speaker_configs.items():
# #         count = sum(1 for c in generated if c.get('speaker') == speaker)
# #         print(f"   {speaker}: {config['voice_info']['name']} ({count} clips)")

# # # ═══════════════════════════════════════════════════════════════════════════════════════
# # def main():
# #     print("🚀 INTERACTIVE VOICE GENERATION")
# #     print("="*70)
    
# #     if not check_prerequisites(): return
    
# #     # Initialize ElevenLabs
# #     client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
# #     # Load data
# #     data = load_data()
    
# #     # Interactive configuration
# #     speaker_configs, per_segment = assign_voices_emotions(data)
    
# #     # Generate
# #     clips = generate_clips(client, data['segments'], speaker_configs, per_segment)
    
# #     if clips:
# #         save_metadata(data, clips, speaker_configs)
# #         show_summary(clips, speaker_configs)
# #         print(f"\n📁 Files in: {OUTPUT_DIR}/")
# #         print("🎬 Next: python step6_video_assembly.py")

# # if __name__ == "__main__":
# #     main()
# # step5_voice_generation_enhanced.py
# # Enhanced voice generation with emotion support and OpenVoice compatibility
# import json
# import os
# import time
# from datetime import datetime
# from elevenlabs.client import ElevenLabs
# from elevenlabs import VoiceSettings
# from pydub import AudioSegment
# from pydub.effects import speedup
# import warnings
# warnings.filterwarnings('ignore')


# # ═══════════════════════════════════════════════════════════════════════════
# # CONFIGURATION
# # ═══════════════════════════════════════════════════════════════════════════
# INPUT_JSON = "work/translated_segments_interactive.json"  # Or translated_segments_interactive.json
# OUTPUT_DIR = "work/voice_clips"
# METADATA_OUTPUT = "work/voice_clips_metadata.json"

# # ElevenLabs API Key
# ELEVENLABS_API_KEY = ""

# # Voice generation backend: "elevenlabs" or "openvoice"
# VOICE_BACKEND = "openvoice"  # Change to "openvoice" when ready


# # ═══════════════════════════════════════════════════════════════════════════
# # VOICE LIBRARY - EXPANDED WITH AGE RANGES
# # ═══════════════════════════════════════════════════════════════════════════
# VOICE_LIBRARY = {
#     # MALE VOICES
#     'male_child': {
#         'voice_id': 'XrExE9yKIg1WjnnlVkGX',
#         'name': 'Michael (Child 8-12)',
#         'description': 'Young boy voice',
#         'age_range': 'child',
#         'gender': 'male'
#     },
#     'male_teen': {
#         'voice_id': 'yoZ06aMxZJJ28mfd3POQ',
#         'name': 'Sam (Teen 13-17)',
#         'description': 'Teenage boy',
#         'age_range': 'teen',
#         'gender': 'male'
#     },
#     'male_young_adult': {
#         'voice_id': 'pNInz6obpgDQGcFmaJgB',
#         'name': 'Adam (Young Adult 18-30)',
#         'description': 'Deep, authoritative male',
#         'age_range': 'young_adult',
#         'gender': 'male'
#     },
#     'male_adult': {
#         'voice_id': 'VR6AewLTigWG4xSOukaG',
#         'name': 'Arnold (Adult 30-50)',
#         'description': 'Strong, mature male',
#         'age_range': 'adult',
#         'gender': 'male'
#     },
#     'male_elderly': {
#         'voice_id': 'MF3mGyEYCl7XYWbV9V6O',
#         'name': 'Antoni (Elderly 50+)',
#         'description': 'Wise, calm elderly male',
#         'age_range': 'elderly',
#         'gender': 'male'
#     },
    
#     # FEMALE VOICES
#     'female_child': {
#         'voice_id': 'jBpfuIE2acCO8z3wKNLl',
#         'name': 'Gigi (Child 8-12)',
#         'description': 'Young girl voice',
#         'age_range': 'child',
#         'gender': 'female'
#     },
#     'female_teen': {
#         'voice_id': 'XB0fDUnXU5powFXDhCwa',
#         'name': 'Charlotte (Teen 13-17)',
#         'description': 'Teenage girl',
#         'age_range': 'teen',
#         'gender': 'female'
#     },
#     'female_young_adult': {
#         'voice_id': 'jsCqWAovK2LkecY7zXl4',
#         'name': 'Freya (Young Adult 18-30)',
#         'description': 'Friendly, energetic female',
#         'age_range': 'young_adult',
#         'gender': 'female'
#     },
#     'female_adult': {
#         'voice_id': '21m00Tcm4TlvDq8ikWAM',
#         'name': 'Rachel (Adult 30-50)',
#         'description': 'Clear, professional female',
#         'age_range': 'adult',
#         'gender': 'female'
#     },
#     'female_elderly': {
#         'voice_id': 'MF3mGyEYCl7XYWbV9V6O',
#         'name': 'Elli (Elderly 50+)',
#         'description': 'Warm, motherly elderly female',
#         'age_range': 'elderly',
#         'gender': 'female'
#     }
# }


# # ═══════════════════════════════════════════════════════════════════════════
# # EMOTION-BASED VOICE SETTINGS (CRITICAL FIX!)
# # ═══════════════════════════════════════════════════════════════════════════
# EMOTION_VOICE_SETTINGS = {
#     'neutral': {
#         'stability': 0.65,
#         'similarity_boost': 0.75,
#         'style': 0.0,
#         'use_speaker_boost': True
#     },
#     'happy': {
#         'stability': 0.50,
#         'similarity_boost': 0.80,
#         'style': 0.5,
#         'use_speaker_boost': True
#     },
#     'excited': {
#         'stability': 0.40,
#         'similarity_boost': 0.75,
#         'style': 0.7,
#         'use_speaker_boost': True
#     },
#     'angry': {
#         'stability': 0.35,
#         'similarity_boost': 0.70,
#         'style': 0.8,
#         'use_speaker_boost': True
#     },
#     'sad': {
#         'stability': 0.70,
#         'similarity_boost': 0.80,
#         'style': 0.3,
#         'use_speaker_boost': True
#     },
#     'fearful': {
#         'stability': 0.30,
#         'similarity_boost': 0.75,
#         'style': 0.6,
#         'use_speaker_boost': True
#     },
#     'calm': {
#         'stability': 0.80,
#         'similarity_boost': 0.75,
#         'style': 0.1,
#         'use_speaker_boost': True
#     },
#     'surprised': {
#         'stability': 0.35,
#         'similarity_boost': 0.75,
#         'style': 0.7,
#         'use_speaker_boost': True
#     }
# }

# # Emotion to ElevenLabs tag mapping
# EMOTION_TO_TAG = {
#     'angry': '[angry]',
#     'disgust': '[sarcastic]',
#     'fearful': '[nervous]',
#     'happy': '[excited]',
#     'neutral': '',
#     'sad': '[sad]',
#     'surprised': '[surprised]',
#     'calm': '',
#     'excited': '[excited]'
# }


# # ═══════════════════════════════════════════════════════════════════════════
# # PREREQUISITES
# # ═══════════════════════════════════════════════════════════════════════════
# def check_prerequisites():
#     """Check if required files exist"""
#     if not os.path.exists(INPUT_JSON):
#         print(f"❌ Input file not found: {INPUT_JSON}")
#         print("   Please run step4_translation.py first")
#         return False
    
#     if VOICE_BACKEND == "elevenlabs" and ELEVENLABS_API_KEY == "YOUR_ELEVENLABS_API_KEY_HERE":
#         print("❌ ElevenLabs API key not set!")
#         print("\n📝 Get your API key from: https://elevenlabs.io")
#         return False
    
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     return True


# def load_translations():
#     """Load translated segments with emotion data"""
#     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     # Handle both formats: clips array or segments array
#     segments = data.get('clips', data.get('segments', []))
    
#     print(f"📄 Loaded {len(segments)} translated segments")
    
#     # Check if emotion data exists
#     has_emotion = any('emotion' in seg or 'detected_emotion' in seg for seg in segments)
#     print(f"   Emotion data: {'✅ Available' if has_emotion else '⚠️  Not found'}")
    
#     return data, segments


# # ═══════════════════════════════════════════════════════════════════════════
# # VOICE ASSIGNMENT (INTERACTIVE)
# # ═══════════════════════════════════════════════════════════════════════════
# def interactive_voice_selection(speakers):
#     """Let user select voice for each speaker"""
#     print("\n" + "="*70)
#     print("🎭 INTERACTIVE VOICE SELECTION")
#     print("="*70)
    
#     voice_assignments = {}
    
#     for speaker in speakers:
#         print(f"\n📢 Select voice for {speaker}:")
#         print("   [1] Male")
#         print("   [2] Female")
#         print("   [3] Show all voices")
        
#         gender_choice = input("   Choose gender (1-3): ").strip()
        
#         if gender_choice == '3':
#             # Show all
#             available = list(VOICE_LIBRARY.keys())
#         elif gender_choice == '1':
#             available = [k for k in VOICE_LIBRARY.keys() if 'male' in k and 'female' not in k]
#         else:
#             available = [k for k in VOICE_LIBRARY.keys() if 'female' in k]
        
#         print(f"\n   Available voices:")
#         for i, key in enumerate(available, 1):
#             voice = VOICE_LIBRARY[key]
#             print(f"   [{i}] {voice['name']} - {voice['description']}")
        
#         voice_idx = int(input(f"   Choose voice (1-{len(available)}): ")) - 1
#         selected_key = available[voice_idx]
        
#         voice_assignments[speaker] = VOICE_LIBRARY[selected_key]
#         print(f"   ✅ Assigned: {VOICE_LIBRARY[selected_key]['name']}")
    
#     return voice_assignments


# def auto_voice_assignment(speakers, segments):
#     """Auto-assign voices based on speaker profiles"""
#     print("\n🎭 Auto-assigning voices based on speaker profiles...")
    
#     voice_assignments = {}
    
#     for speaker in speakers:
#         # Find speaker profile if available
#         speaker_segs = [s for s in segments if s.get('speaker') == speaker]
        
#         if speaker_segs:
#             first_seg = speaker_segs[0]
#             gender = first_seg.get('gender', 'unknown')
#             age = first_seg.get('age', 0)
            
#             # Map age to age_range
#             if age < 13:
#                 age_range = 'child'
#             elif age < 18:
#                 age_range = 'teen'
#             elif age < 30:
#                 age_range = 'young_adult'
#             elif age < 50:
#                 age_range = 'adult'
#             else:
#                 age_range = 'elderly'
            
#             # Find matching voice
#             voice_key = f"{gender}_{age_range}"
#             if voice_key in VOICE_LIBRARY:
#                 voice_assignments[speaker] = VOICE_LIBRARY[voice_key]
#                 print(f"   {speaker} → {VOICE_LIBRARY[voice_key]['name']} ({gender}, {age}yo)")
#             else:
#                 # Fallback
#                 fallback_key = 'male_adult' if gender == 'male' else 'female_adult'
#                 voice_assignments[speaker] = VOICE_LIBRARY[fallback_key]
#                 print(f"   {speaker} → {VOICE_LIBRARY[fallback_key]['name']} (fallback)")
#         else:
#             # Default
#             voice_assignments[speaker] = VOICE_LIBRARY['male_adult']
#             print(f"   {speaker} → {VOICE_LIBRARY['male_adult']['name']} (default)")
    
#     return voice_assignments


# # ═══════════════════════════════════════════════════════════════════════════
# # VOICE GENERATION (WITH EMOTION!)
# # ═══════════════════════════════════════════════════════════════════════════
# def prepare_text_with_emotion(segment):
#     """Add emotion tag to text if confidence is high enough"""
#     text = segment.get('translated_text', segment.get('text', ''))
#     emotion = segment.get('emotion', segment.get('detected_emotion', 'neutral'))
#     confidence = segment.get('emotion_confidence', 0.0)
    
#     # Use emotion tag if confidence > 60%
#     if confidence >= 0.6 and emotion in EMOTION_TO_TAG:
#         tag = EMOTION_TO_TAG[emotion]
#         if tag:
#             text_with_emotion = f"{tag} {text}"
#             print(f"      Emotion: {emotion} ({confidence:.1%}) → {tag}")
#             return text_with_emotion, emotion
    
#     return text, 'neutral'


# def get_voice_settings_for_emotion(emotion):
#     """Get voice settings based on emotion"""
#     settings = EMOTION_VOICE_SETTINGS.get(emotion, EMOTION_VOICE_SETTINGS['neutral'])
#     return VoiceSettings(
#         stability=settings['stability'],
#         similarity_boost=settings['similarity_boost'],
#         style=settings['style'],
#         use_speaker_boost=settings['use_speaker_boost']
#     )


# def match_audio_duration(audio_segment, target_duration_s):
#     """Speed up or slow down audio to match exact duration"""
#     current_duration_s = len(audio_segment) / 1000.0
    
#     # Allow 20% variance
#     if abs(current_duration_s - target_duration_s) / target_duration_s < 0.2:
#         return audio_segment  # Close enough
    
#     # Speed adjustment needed
#     ratio = current_duration_s / target_duration_s
    
#     if ratio > 1.2:  # Audio too long, speed up
#         audio_segment = speedup(audio_segment, playback_speed=ratio, chunk_size=50, crossfade=10)
#         print(f"      ⚡ Sped up {ratio:.2f}x to match duration")
#     elif ratio < 0.8:  # Audio too short, add silence
#         silence_ms = int((target_duration_s - current_duration_s) * 1000)
#         audio_segment = audio_segment + AudioSegment.silent(duration=silence_ms)
#         print(f"      🔇 Added {silence_ms}ms silence to match duration")
    
#     return audio_segment


# def generate_with_elevenlabs(client, segment, voice_info):
#     """Generate voice clip using ElevenLabs with emotion support"""
#     # Prepare text with emotion tag
#     text, emotion = prepare_text_with_emotion(segment)
    
#     # Get emotion-specific voice settings
#     voice_settings = get_voice_settings_for_emotion(emotion)
    
#     # Generate audio
#     audio_stream = client.text_to_speech.convert(
#         voice_id=voice_info['voice_id'],
#         model_id="eleven_multilingual_v2",
#         text=text,
#         voice_settings=voice_settings
#     )
    
#     # Convert to bytes
#     audio_bytes = b"".join(chunk for chunk in audio_stream)
    
#     # Convert to AudioSegment for duration matching
#     from io import BytesIO
#     audio_segment = AudioSegment.from_mp3(BytesIO(audio_bytes))
    
#     # Match exact duration if specified
#     target_duration = segment.get('duration', 0)
#     if target_duration > 0:
#         audio_segment = match_audio_duration(audio_segment, target_duration)
    
#     return audio_segment, emotion


# def generate_voice_clips(segments, voice_assignments, backend="elevenlabs"):
#     """Generate voice clips for all segments"""
#     print(f"\n🎙️ Generating voice clips using {backend.upper()}...")
#     print("⏳ This may take a few minutes...\n")
    
#     # Initialize ElevenLabs client if needed
#     client = None
#     if backend == "elevenlabs":
#         client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
#     generated_clips = []
    
#     for idx, seg in enumerate(segments, 1):
#         speaker = seg.get('speaker', 'UNKNOWN')
#         text = seg.get('translated_text', seg.get('text', ''))
        
#         if not text:
#             print(f"[{idx}/{len(segments)}] ⚠️  No text, skipping")
#             continue
        
#         # Get voice for this speaker
#         voice_info = voice_assignments.get(speaker)
#         if not voice_info:
#             print(f"[{idx}/{len(segments)}] ⚠️  No voice for {speaker}, using default")
#             voice_info = VOICE_LIBRARY['male_adult']
        
#         print(f"[{idx}/{len(segments)}] {speaker} ({voice_info['name']})")
#         print(f"      Text: {text[:50]}{'...' if len(text) > 50 else ''}")
        
#         try:
#             if backend == "elevenlabs":
#                 audio_segment, emotion_used = generate_with_elevenlabs(client, seg, voice_info)
#             else:
#                 # OpenVoice backend (implement later)
#                 print("      ⚠️  OpenVoice not implemented yet")
#                 continue
            
#             # Save to file
#             output_filename = f"segment_{idx:03d}_{speaker}.mp3"
#             output_path = os.path.join(OUTPUT_DIR, output_filename)
#             audio_segment.export(output_path, format="mp3")
            
#             print(f"      ✅ Saved: {output_filename}")
            
#             # Store metadata
#             clip_info = seg.copy()
#             clip_info.update({
#                 'audio_file': output_path,
#                 'voice_name': voice_info['name'],
#                 'emotion_used': emotion_used
#             })
#             generated_clips.append(clip_info)
            
#             time.sleep(0.5)  # Rate limiting
        
#         except Exception as e:
#             print(f"      ❌ Error: {e}")
#             continue
    
#     return generated_clips


# # ═══════════════════════════════════════════════════════════════════════════
# # SAVE & DISPLAY
# # ═══════════════════════════════════════════════════════════════════════════
# def save_metadata(voice_assignments, generated_clips):
#     """Save voice generation metadata"""
#     metadata = {
#         'timestamp': datetime.now().isoformat(),
#         'backend': VOICE_BACKEND,
#         'speakers': voice_assignments,
#         'clips': generated_clips
#     }
    
#     with open(METADATA_OUTPUT, 'w', encoding='utf-8') as f:
#         json.dump(metadata, f, ensure_ascii=False, indent=2)
    
#     print(f"\n💾 Metadata saved: {METADATA_OUTPUT}")


# def display_summary(voice_assignments, generated_clips):
#     """Display generation summary"""
#     print("\n" + "="*70)
#     print("📊 VOICE GENERATION SUMMARY")
#     print("="*70)
    
#     print(f"\n✅ Generated {len(generated_clips)} clips")
    
#     print("\n🎭 Voice Cast:")
#     for speaker, voice_info in voice_assignments.items():
#         count = sum(1 for c in generated_clips if c.get('speaker') == speaker)
#         print(f"   {speaker}: {voice_info['name']} ({count} clips)")
    
#     total_duration = sum(c.get('duration', 0) for c in generated_clips)
#     print(f"\n⏱️  Total audio: {total_duration:.1f}s")
    
#     # Emotion breakdown
#     emotions = {}
#     for clip in generated_clips:
#         emotion = clip.get('emotion_used', 'neutral')
#         emotions[emotion] = emotions.get(emotion, 0) + 1
    
#     if emotions:
#         print("\n😊 Emotion Breakdown:")
#         for emotion, count in emotions.items():
#             print(f"   {emotion}: {count} clips")
    
#     print(f"\n📁 Files in: {OUTPUT_DIR}/")
#     print("🎬 Next: python step6_final_assembly.py")


# # ═══════════════════════════════════════════════════════════════════════════
# # MAIN
# # ═══════════════════════════════════════════════════════════════════════════
# def main():
#     print("="*70)
#     print("STEP 5: Enhanced Voice Generation (Emotion + Timing)")
#     print("="*70)
    
#     if not check_prerequisites():
#         return
    
#     # Load data
#     data, segments = load_translations()
    
#     # Get unique speakers
#     speakers = sorted(set(seg.get('speaker', 'UNKNOWN') for seg in segments))
#     print(f"\n👥 Found {len(speakers)} speakers: {', '.join(speakers)}")
    
#     # Voice assignment
#     print("\n🎭 Voice Assignment:")
#     print("   [1] Interactive (choose manually)")
#     print("   [2] Auto-assign (based on profiles)")
    
#     choice = input("\nChoose mode (1-2, default=2): ").strip() or '2'
    
#     if choice == '1':
#         voice_assignments = interactive_voice_selection(speakers)
#     else:
#         voice_assignments = auto_voice_assignment(speakers, segments)
    
#     # Generate clips
#     generated_clips = generate_voice_clips(segments, voice_assignments, VOICE_BACKEND)
    
#     if not generated_clips:
#         print("❌ No clips generated")
#         return
    
#     # Save metadata
#     save_metadata(voice_assignments, generated_clips)
    
#     # Display summary
#     display_summary(voice_assignments, generated_clips)
    
#     print("\n" + "="*70)
#     print("✅ Step 5 Complete!")
#     print("="*70)


# if __name__ == "__main__":
#     main()
# step5_voice_generation_xtts.py
# Voice cloning & TTS with XTTS-v2 (English + Tamil, emotion-aware)
import os
import json
import time
from datetime import datetime

import torch
from TTS.api import TTS
from pydub import AudioSegment
from pydub.effects import speedup


# ==============================
# CONFIG
# ==============================
TRANSLATED_JSON = "work/translated_segments.json"   # must include segments with 'translated_text', 'speaker', 'start', 'end', 'duration', 'emotion'
OUTPUT_DIR = "work/voice_clips"
METADATA_OUT = "work/voice_clips_metadata.json"

SAMPLE_ROOT = "sample_voices"  # sample_voices/male/*.wav, sample_voices/female/*.wav

# Language mapping for XTTS-v2 (supports 17 languages incl. English and Hindi) [web:438][web:454]
LANG_CODE_EN = "en"
LANG_CODE_TA = "en"  # Tamil is not officially supported in XTTS-v2; you can still pass ta text but quality may vary.
# If you want best quality for Tamil, you may need a Tamil-specific TTS model separately.

# Emotion → text tags / style hints (XTTS-v2 uses emotion conditioning via text/style; explicit emotion is partial) [web:456][web:453]
EMOTION_TAGS = {
    "angry": "<angry>",
    "happy": "<happy>",
    "sad": "<sad>",
    "fearful": "<fearful>",
    "surprised": "<surprised>",
    "calm": "<calm>",
    "neutral": "",
    "disgust": "<sarcastic>",
}

# ==============================
# UTILITIES
# ==============================
def check_prerequisites():
    if not os.path.exists(TRANSLATED_JSON):
        print(f"❌ Missing: {TRANSLATED_JSON} (run translation first)")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return True


def load_segments():
    with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments", data.get("clips", []))
    print(f"📄 Loaded {len(segments)} segments for voice generation")
    return segments


def list_voice_samples():
    """Scan sample_voices/male & sample_voices/female and return dict."""
    samples = {"male": [], "female": []}
    for gender in ["male", "female"]:
        folder = os.path.join(SAMPLE_ROOT, gender)
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith((".wav", ".mp3", ".flac", ".ogg")):
                samples[gender].append(os.path.join(folder, fname))
    return samples
def flatten_samples(samples_dict):
    """Return a flat list of all sample paths."""
    return samples_dict.get("male", []) + samples_dict.get("female", [])

def interactive_voice_selection(per_speaker_genders, samples):
    """Let user select one sample per speaker (from male/female folders)."""
    assignments = {}
    print("\n🎭 XTTS Voice Cloning – Sample Selection")
    for speaker in per_speaker_genders:
        gender = per_speaker_genders[speaker]
        if gender not in ["male", "female"] or not samples[gender]:
            print(f"\n{speaker}: gender={gender}, but no samples found. Using first male sample as fallback.")
            fallback_gender = "male" if samples["male"] else "female"
            assignments[speaker] = samples[fallback_gender][0]
            continue

        options = samples[gender]
        print(f"\nSpeaker: {speaker} (gender: {gender})")
        for i, path in enumerate(options, 1):
            print(f"  [{i}] {os.path.basename(path)}")
        choice = input(f"Choose sample [1-{len(options)}] (default=1): ").strip()
        idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(options) else 0
        assignments[speaker] = options[idx]
        print(f"  ✅ {speaker} → {os.path.basename(options[idx])}")
    return assignments

def choose_voice_for_segment(seg, sample_list):
    """Ask user to choose voice for a single segment."""
    print("\n🎙 Segment Voice Selection")
    print(f"Speaker: {seg.get('speaker','UNKNOWN')}")
    print(f"Text: {seg.get('translated_text', seg.get('text',''))}")

    for i, path in enumerate(sample_list, 1):
        print(f"[{i}] {os.path.basename(path)}")

    choice = input("Choose voice number: ").strip()
    while not choice.isdigit() or not (1 <= int(choice) <= len(sample_list)):
        choice = input("Invalid choice. Choose again: ").strip()

    return sample_list[int(choice) - 1]

def infer_speaker_genders(segments):
    """Infer speaker gender from metadata if available, else default."""
    genders = {}
    for seg in segments:
        spk = seg.get("speaker", "UNKNOWN")
        gender = seg.get("gender") or seg.get("speaker_gender")
        if gender is None:
            # fallback: first time set unknown, will choose later
            gender = "male"
        genders.setdefault(spk, gender.lower())
    return genders


def prepare_text_with_emotion(seg, lang_code):
    """Add soft emotion control using tags & punctuation."""
    text = seg.get("translated_text", seg.get("text", ""))
    emotion = seg.get("emotion") or seg.get("detected_emotion") or "neutral"
    conf = seg.get("emotion_confidence", 0.0)

    tag = ""
    if conf >= 0.6 and emotion in EMOTION_TAGS:
        tag = EMOTION_TAGS[emotion]

    # Simple style prompt injection
    if tag:
        full_text = f"{tag} {text}"
    else:
        full_text = text

    # Tiny language-specific tweaks if needed
    # For now, we just return as is.
    return full_text, emotion


def match_duration_pydub(audio_seg: AudioSegment, target_sec: float) -> AudioSegment:
    """Roughly match target duration by speed / silence pad."""
    if target_sec <= 0:
        return audio_seg
    cur = len(audio_seg) / 1000.0
    if cur <= 0:
        return audio_seg

    # If within ±20%, keep as is
    if abs(cur - target_sec) / target_sec < 0.2:
        return audio_seg

    if cur > target_sec:  # too long → speed up
        ratio = cur / target_sec
        audio_seg = speedup(audio_seg, playback_speed=ratio, chunk_size=50, crossfade=10)
    else:  # too short → pad with silence
        pad_ms = int((target_sec - cur) * 1000)
        audio_seg = audio_seg + AudioSegment.silent(duration=pad_ms)
    return audio_seg


# ==============================
# XTTS INITIALIZATION
# ==============================
def load_xtts():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🧠 Loading XTTS-v2 on {device}...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)  [web:446][web:452]
    print("✅ XTTS-v2 loaded")
    return tts, device


# ==============================
# MAIN GENERATION
# ==============================
def generate_voice_clips_xtts():
    if not check_prerequisites():
        return

    segments = load_segments()
    xtts, device = load_xtts()
    samples = list_voice_samples()
    sample_list = flatten_samples(samples)
    print("\nVoice assignment mode:")
    print("1 - Speaker based")
    print("2 - Segment based")
    print("3 - Speaker + override")
    mode = input("Choose mode: ").strip()
    speaker_genders = infer_speaker_genders(segments)

    # Interactive mapping speaker → sample file
    # speaker_to_sample = interactive_voice_selection(speaker_genders, samples)
    speaker_to_sample = {}

    if mode in ["1", "3"]:
        speaker_to_sample = interactive_voice_selection(speaker_genders, samples)
    clips_meta = []

    print("\n🎙 Generating voice clips with XTTS-v2...")
    for idx, seg in enumerate(segments, 1):
        speaker = seg.get("speaker", "UNKNOWN")
        lang = seg.get("target_lang", "en")  # you can store "en" / "ta" per segment
        lang_code = LANG_CODE_EN if lang == "en" else LANG_CODE_TA

        # speaker_sample = speaker_to_sample.get(speaker)
        # Mode 2 → choose voice for every segment
        if mode == "2":
            speaker_sample = choose_voice_for_segment(seg, sample_list)

        # Mode 3 → speaker default but allow override
        elif mode == "3":
            speaker_sample = speaker_to_sample.get(speaker)
            override = input(f"Segment {idx} override voice? (y/n): ").lower()
            if override == "y":
                speaker_sample = choose_voice_for_segment(seg, sample_list)

        # Mode 1 → pure speaker mapping
        else:
            speaker_sample = speaker_to_sample.get(speaker)
        if not speaker_sample or not os.path.exists(speaker_sample):
            print(f"[{idx}/{len(segments)}] ⚠️ No valid sample for {speaker}, skipping.")
            continue

        text, emotion = prepare_text_with_emotion(seg, lang_code)
        if not text.strip():
            print(f"[{idx}/{len(segments)}] ⚠️ Empty text, skipping.")
            continue

        print(f"[{idx}/{len(segments)}] {speaker} ({lang})")
        print(f"   Voice: {os.path.basename(speaker_sample)}")
        print(f"   Emotion: {emotion}")
        print(f"   Text: {text[:60]}{'...' if len(text) > 60 else ''}")

        # Output path
        out_name = f"segment_{idx:03d}_{speaker}.wav"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        try:
            # XTTS-v2 synthesis [web:438][web:446][web:443]
            xtts.tts_to_file(
                text=text,
                file_path=out_path,
                speaker_wav=[speaker_sample],
                language=lang_code,
            )
        except Exception as e:
            print(f"   ❌ XTTS error: {e}")
            continue

        # Duration post‑matching
        try:
            target_dur = seg.get("duration", 0.0)
            audio_seg = AudioSegment.from_file(out_path)
            if target_dur > 0:
                audio_seg = match_duration_pydub(audio_seg, target_dur)
                audio_seg.export(out_path, format="wav")
        except Exception as e:
            print(f"   ⚠️ Duration adjust failed: {e}")

        seg_meta = dict(seg)
        seg_meta.update(
            {
                "audio_file": out_path,
                "voice_sample": speaker_sample,
                "emotion_used": emotion,
                "language": lang,
            }
        )
        clips_meta.append(seg_meta)
        time.sleep(0.1)

    # Save metadata compatible with your step6
    meta = {
        "timestamp": datetime.now().isoformat(),
        "backend": "xtts_v2",
        "speakers": {
            spk: {"sample_path": path, "gender": speaker_genders.get(spk, "unknown")}
            for spk, path in speaker_to_sample.items()
        },
        "clips": clips_meta,
    }
    with open(METADATA_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Generated {len(clips_meta)} clips")
    print(f"💾 Metadata: {METADATA_OUT}")
    print(f"📁 Audio: {OUTPUT_DIR}")
    print("\nNext: python step6_final_assembly.py")


if __name__ == "__main__":
    generate_voice_clips_xtts()
