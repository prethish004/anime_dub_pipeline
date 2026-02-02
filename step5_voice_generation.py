# # step5_voice_generation.py
# import json
# import os
# import time
# from elevenlabs.client import ElevenLabs
# from elevenlabs import VoiceSettings

# # Configuration
# INPUT_JSON = "work/translated_segments.json"
# OUTPUT_DIR = "work/voice_clips"

# # ElevenLabs API Key
# ELEVENLABS_API_KEY = "sk_13330e107d319d4f75ab5e197f48d174e10520e1e6713e19"  # Get from: https://elevenlabs.io

# # Voice mapping based on speaker profiles
# VOICE_LIBRARY = {
#     # Male voices
#     'male_adult': {
#         'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - Deep male
#         'name': 'Adam',
#         'description': 'Deep, authoritative male voice'
#     },
#     'male_young': {
#         'voice_id': 'yoZ06aMxZJJ28mfd3POQ',  # Sam - Young male
#         'name': 'Sam',
#         'description': 'Young, energetic male voice'
#     },
#     'male_mature': {
#         'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold - Mature male
#         'name': 'Arnold',
#         'description': 'Strong, mature male voice'
#     },
    
#     # Female voices
#     'female_adult': {
#         'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - Adult female
#         'name': 'Rachel',
#         'description': 'Clear, professional female voice'
#     },
#     'female_young': {
#         'voice_id': 'jsCqWAovK2LkecY7zXl4',  # Freya - Young female
#         'name': 'Freya',
#         'description': 'Young, friendly female voice'
#     },
#     'female_teen': {
#         'voice_id': 'XB0fDUnXU5powFXDhCwa',  # Charlotte - Teen female
#         'name': 'Charlotte',
#         'description': 'Youthful, energetic female voice'
#     }
# }

# # Voice settings for anime dubbing
# ANIME_VOICE_SETTINGS = {
#     'stability': 0.6,        # Moderate stability (0.5-0.7 good for anime)
#     'similarity_boost': 0.8, # High similarity for consistency
#     'style': 0.3,            # Some style variation for emotion
#     'use_speaker_boost': True
# }

# def check_prerequisites():
#     """Check if required files and API key exist"""
    
#     if not os.path.exists(INPUT_JSON):
#         print(f"❌ Input file not found: {INPUT_JSON}")
#         print("   Please run step4_translation_free.py first")
#         return False
    
#     if ELEVENLABS_API_KEY == "YOUR_ELEVENLABS_API_KEY_HERE":
#         print("❌ ElevenLabs API key not set!")
#         print("\n📝 To get your API key:")
#         print("   1. Go to: https://elevenlabs.io")
#         print("   2. Sign up (FREE tier: 10,000 chars/month)")
#         print("   3. Go to Profile → API Keys")
#         print("   4. Copy your API key")
#         print("   5. Paste it in step5_voice_generation.py")
#         print("\n💰 Free tier: ~10 minutes of audio per month")
#         print("💰 Starter: $5/month for ~30 minutes")
#         return False
    
#     # Create output directory
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
    
#     return True

# def load_translations():
#     """Load translated segments"""
#     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     print(f"📄 Loaded {data['total_segments']} translated segments")
#     return data

# def select_voice_for_speaker(speaker_profile):
#     """Select appropriate voice based on speaker profile"""
    
#     gender = speaker_profile.get('gender', 'unknown')
#     age_group = speaker_profile.get('age_group', 'adult')
    
#     # Map to voice key
#     if gender == 'male':
#         if 'teen' in age_group or 'young' in age_group:
#             voice_key = 'male_young'
#         elif 'mature' in age_group or 'old' in age_group:
#             voice_key = 'male_mature'
#         else:
#             voice_key = 'male_adult'
#     elif gender == 'female':
#         if 'teen' in age_group:
#             voice_key = 'female_teen'
#         elif 'young' in age_group:
#             voice_key = 'female_young'
#         else:
#             voice_key = 'female_adult'
#     else:
#         # Default to male adult if unknown
#         voice_key = 'male_adult'
    
#     return VOICE_LIBRARY[voice_key]

# def assign_voices_to_speakers(data):
#     """Assign ElevenLabs voices to each speaker"""
    
#     print("\n🎭 Assigning voices to speakers...")
    
#     diarization = data.get('diarization', {})
#     speaker_profiles = diarization.get('speaker_profiles', {})
    
#     voice_assignments = {}
    
#     for speaker, profile in speaker_profiles.items():
#         voice_info = select_voice_for_speaker(profile)
#         voice_assignments[speaker] = voice_info
        
#         print(f"   {speaker} ({profile['gender']}, {profile['age_group']})")
#         print(f"   → Voice: {voice_info['name']} ({voice_info['description']})")
    
#     # If no profiles (fallback)
#     if not voice_assignments:
#         print("   ⚠️  No speaker profiles found, using default voices")
#         voice_assignments['SPEAKER_00'] = VOICE_LIBRARY['male_adult']
    
#     return voice_assignments

# def estimate_character_count(segments):
#     """Estimate total characters for API usage"""
#     total_chars = sum(len(seg['translated_text']) for seg in segments)
#     return total_chars

# def generate_voice_clips(client, segments, voice_assignments):
#     """Generate voice clips for all segments"""
    
#     print(f"\n🎙️ Generating voice clips...")
    
#     # Estimate usage
#     total_chars = estimate_character_count(segments)
#     print(f"   Estimated characters: {total_chars}")
#     print(f"   Estimated duration: ~{total_chars / 160:.1f} minutes")
#     print(f"   (ElevenLabs free tier: 10,000 chars/month)")
    
#     if total_chars > 10000:
#         print(f"\n⚠️  WARNING: This will use {total_chars} characters")
#         print(f"   Free tier limit is 10,000 characters")
#         response = input("   Continue? (y/n): ")
#         if response.lower() != 'y':
#             print("   Aborted")
#             return []
    
#     print("\n⏳ Generating audio (this takes a few minutes)...\n")
    
#     generated_clips = []
    
#     for idx, seg in enumerate(segments, 1):
#         speaker = seg.get('speaker', 'SPEAKER_00')
#         text = seg['translated_text']
        
#         # Get voice for this speaker
#         voice_info = voice_assignments.get(speaker)
#         if not voice_info:
#             print(f"   ⚠️  No voice assigned to {speaker}, using default")
#             voice_info = VOICE_LIBRARY['male_adult']
        
#         print(f"[{idx}/{len(segments)}] Speaker: {speaker} ({voice_info['name']})")
#         print(f"   Text: {text}")
#         print(f"   Duration: {seg['duration']:.1f}s")
        
#         try:
#             audio_stream = client.text_to_speech.convert(
#                 voice_id=voice_info["voice_id"],
#                 model_id="eleven_multilingual_v2",
#                 text=text,
#                 voice_settings=VoiceSettings(
#                     stability=ANIME_VOICE_SETTINGS["stability"],
#                     similarity_boost=ANIME_VOICE_SETTINGS["similarity_boost"],
#                     style=ANIME_VOICE_SETTINGS["style"],
#                     use_speaker_boost=ANIME_VOICE_SETTINGS["use_speaker_boost"],
#                 ),
#             )

#             # Convert generator → bytes
#             audio_bytes = b"".join(chunk for chunk in audio_stream)
#             output_filename = f"segment_{idx:03d}_{speaker}.mp3"
#             output_path = os.path.join(OUTPUT_DIR, output_filename)

#             with open(output_path, "wb") as f:
#                 f.write(audio_bytes)

#             print(f"   ✅ Saved: {output_filename}")

#             clip_info = seg.copy()
#             clip_info["audio_file"] = output_path
#             clip_info["voice_name"] = voice_info["name"]
#             generated_clips.append(clip_info)

#             time.sleep(0.5)

#         except Exception as e:
#             print(f"   ❌ Error: {e}")
#             print(f"   Skipping segment {idx}")
#             continue
                
#     return generated_clips

# def save_results(data, generated_clips, voice_assignments):
#     """Save generated clips metadata"""
    
#     output_data = {
#         'source_data': {
#             'model': data.get('model', 'unknown'),
#             'translation_model': data.get('translation_model', 'unknown'),
#             'source_language': data.get('source_language', 'Japanese'),
#             'target_language': data.get('target_language', 'English')
#         },
#         'voice_assignments': voice_assignments,
#         'total_clips': len(generated_clips),
#         'clips': generated_clips
#     }
    
#     output_file = "work/voice_clips_metadata.json"
#     with open(output_file, 'w', encoding='utf-8') as f:
#         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
#     print(f"\n💾 Metadata saved to: {output_file}")

# def display_summary(generated_clips, voice_assignments):
#     """Display generation summary"""
    
#     print("\n" + "="*70)
#     print("📊 VOICE GENERATION SUMMARY")
#     print("="*70)
    
#     print(f"\n✅ Successfully generated: {len(generated_clips)} clips")
    
#     print(f"\n🎭 Voice Assignments:")
#     for speaker, voice_info in voice_assignments.items():
#         clip_count = sum(1 for c in generated_clips if c.get('speaker') == speaker)
#         print(f"   {speaker}: {voice_info['name']} ({clip_count} clips)")
    
#     total_duration = sum(c['duration'] for c in generated_clips)
#     print(f"\n⏱️  Total audio duration: {total_duration:.1f} seconds")
    
#     print(f"\n📁 Audio files saved to: {OUTPUT_DIR}/")
    
#     print("\n" + "="*70)
#     print("📋 SAMPLE CLIPS (First 3)")
#     print("="*70)
    
#     for clip in generated_clips[:3]:
#         print(f"\n[{clip['start']:.1f}s - {clip['end']:.1f}s] {clip.get('speaker', 'UNKNOWN')}")
#         print(f"🇯🇵 Original: {clip.get('original_text', 'N/A')}")
#         print(f"🇬🇧 Translated: {clip['translated_text']}")
#         print(f"🎙️  Voice: {clip['voice_name']}")
#         print(f"📄 File: {os.path.basename(clip['audio_file'])}")

# def main():
#     print("=" * 70)
#     print("STEP 5: Voice Generation with ElevenLabs")
#     print("=" * 70)
    
#     # Check prerequisites
#     if not check_prerequisites():
#         return
    
#     # Initialize ElevenLabs client
#     try:
#         client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
#         print("✅ ElevenLabs client initialized")
#     except Exception as e:
#         print(f"❌ Failed to initialize ElevenLabs client: {e}")
#         return
    
#     # Load translations
#     data = load_translations()
    
#     # Assign voices based on speaker profiles
#     voice_assignments = assign_voices_to_speakers(data)
    
#     # Generate voice clips
#     generated_clips = generate_voice_clips(
#         client,
#         data['segments'],
#         voice_assignments
#     )
    
#     if not generated_clips:
#         print("❌ No clips were generated")
#         return
    
#     # Save results
#     save_results(data, generated_clips, voice_assignments)
    
#     # Display summary
#     display_summary(generated_clips, voice_assignments)
    
#     print("\n" + "=" * 70)
#     print("✅ Step 5 Complete!")
#     print("=" * 70)
#     print(f"📁 Generated clips: {len(generated_clips)}")
#     print(f"📂 Location: {OUTPUT_DIR}/")
#     print("\nNext: Run step6_final_assembly.py to combine everything!")

# if __name__ == "__main__":
#     main()
# step5_voice_generation_interactive.py
# 🚀 COMPLETE INTERACTIVE VOICE GENERATION WITH AGE & EMOTION CONTROL
# Updated: Feb 02, 2026

import json
import os
import time
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# ═══════════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════════
INPUT_JSON = "work/translated_segments_interactive.json"  # From step4_translation_interactive.py
OUTPUT_DIR = "work/voice_clips"

# ElevenLabs API Key (REPLACE WITH YOUR KEY)
ELEVENLABS_API_KEY = "sk_13330e107d319d4f75ab5e197f48d174e10520e1e6713e19"

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXPANDED VOICE LIBRARY - 10+ VOICES WITH AGE CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════════════
VOICE_LIBRARY = {
    # MALE VOICES - 5 age ranges
    'male_child': {
        'voice_id': 'XrExE9yKIg1WjnnlVkGX',  # Michael
        'name': 'Michael (Child 8-12)',
        'description': 'Young boy voice - perfect for kid characters',
        'age_range': 'child', 'gender': 'male'
    },
    'male_teen': {
        'voice_id': 'yoZ06aMxZJJ28mfd3POQ',  # Sam
        'name': 'Sam (Teen 13-17)',
        'description': 'Teenage boy - energetic school anime characters',
        'age_range': 'teen', 'gender': 'male'
    },
    'male_young_adult': {
        'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam
        'name': 'Adam (Young Adult 18-30)',
        'description': 'Deep authoritative voice - main heroes',
        'age_range': 'young_adult', 'gender': 'male'
    },
    'male_adult': {
        'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold
        'name': 'Arnold (Adult 30-50)',
        'description': 'Strong mature voice - mentors, villains',
        'age_range': 'adult', 'gender': 'male'
    },
    'male_elderly': {
        'voice_id': 'ErXwobaYiN019PkySvjV',  # Antoni
        'name': 'Antoni (Elderly 50+)',
        'description': 'Wise calm voice - old masters, grandfathers',
        'age_range': 'elderly', 'gender': 'male'
    },
    
    # FEMALE VOICES - 5 age ranges
    'female_child': {
        'voice_id': 'jBpfuIE2acCO8z3wKNLl',  # Gigi
        'name': 'Gigi (Child 8-12)',
        'description': 'Young girl voice - perfect for kid characters',
        'age_range': 'child', 'gender': 'female'
    },
    'female_teen': {
        'voice_id': 'XB0fDUnXU5powFXDhCwa',  # Charlotte
        'name': 'Charlotte (Teen 13-17)',
        'description': 'Teenage girl - school anime heroines',
        'age_range': 'teen', 'gender': 'female'
    },
    'female_young_adult': {
        'voice_id': 'jsCqWAovK2LkecY7zXl4',  # Freya
        'name': 'Freya (Young Adult 18-30)',
        'description': 'Friendly energetic - main female leads',
        'age_range': 'young_adult', 'gender': 'female'
    },
    'female_adult': {
        'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel
        'name': 'Rachel (Adult 30-50)',
        'description': 'Clear professional - teachers, mature women',
        'age_range': 'adult', 'gender': 'female'
    },
    'female_elderly': {
        'voice_id': 'MF3mGyEYCl7XYWbV9V6O',  # Elli
        'name': 'Elli (Elderly 50+)',
        'description': 'Warm motherly - grandmothers, wise women',
        'age_range': 'elderly', 'gender': 'female'
    }
}

# ═══════════════════════════════════════════════════════════════════════════════════════
# EMOTION PRESETS - 8 EMOTIONS FOR ANIME DUBBING
# ═══════════════════════════════════════════════════════════════════════════════════════
EMOTION_PRESETS = {
    'neutral': {'stability': 0.65, 'similarity_boost': 0.75, 'style': 0.0, 'desc': 'Normal dialogue'},
    'happy': {'stability': 0.50, 'similarity_boost': 0.80, 'style': 0.5, 'desc': 'Joyful, cheerful'},
    'excited': {'stability': 0.40, 'similarity_boost': 0.85, 'style': 0.7, 'desc': 'Energetic, enthusiastic'},
    'angry': {'stability': 0.35, 'similarity_boost': 0.75, 'style': 0.6, 'desc': 'Intense, aggressive'},
    'sad': {'stability': 0.70, 'similarity_boost': 0.70, 'style': 0.3, 'desc': 'Melancholic, emotional'},
    'fearful': {'stability': 0.30, 'similarity_boost': 0.65, 'style': 0.4, 'desc': 'Scared, nervous'},
    'calm': {'stability': 0.80, 'similarity_boost': 0.75, 'style': 0.1, 'desc': 'Peaceful, wise'},
    'dramatic': {'stability': 0.45, 'similarity_boost': 0.85, 'style': 0.8, 'desc': 'Theatrical, intense'}
}

# ═══════════════════════════════════════════════════════════════════════════════════════
def check_prerequisites():
    """Check if input file exists and API key is set"""
    if not os.path.exists(INPUT_JSON):
        print(f"❌ {INPUT_JSON} not found!")
        print("   Run: python step4_translation_interactive.py first")
        return False
    
    if ELEVENLABS_API_KEY.startswith("sk_") is False:
        print("❌ Set your ElevenLabs API key in line 15!")
        return False
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return True

# ═══════════════════════════════════════════════════════════════════════════════════════
def load_data():
    """Load translated segments"""
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data['segments'])} segments")
    return data

# ═══════════════════════════════════════════════════════════════════════════════════════
def show_voices(gender=None, age=None):
    """Display available voices with filters"""
    print("\n🎤 AVAILABLE VOICES:")
    print("="*60)
    
    count = 0
    for key, voice in VOICE_LIBRARY.items():
        if gender and voice['gender'] != gender: continue
        if age and voice['age_range'] != age: continue
            
        count += 1
        print(f"[{count:2d}] {voice['name']}")
        print(f"     {voice['description']}")
        print()
    
    return list(VOICE_LIBRARY.keys())

# ═══════════════════════════════════════════════════════════════════════════════════════
def show_emotions():
    """Display emotion presets"""
    print("\n😊 EMOTION PRESETS:")
    print("="*60)
    
    count = 0
    for key, preset in EMOTION_PRESETS.items():
        count += 1
        print(f"[{count:2d}] {key.title():8s} | {preset['desc']}")
        print(f"     Stability: {preset['stability']:.1f}  Style: {preset['style']:.1f}")
        print()
    
    return list(EMOTION_PRESETS.keys())

# ═══════════════════════════════════════════════════════════════════════════════════════
def get_choice(options, prompt):
    """Get valid numbered choice from user"""
    while True:
        try:
            choice = input(prompt).strip().lower()
            if choice == 'q': return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"❌ Enter 1-{len(options)} or 'q' to quit")
        except:
            print("❌ Invalid input!")

# ═══════════════════════════════════════════════════════════════════════════════════════
def configure_speaker(speaker_name, segments):
    """Interactive configuration for one speaker"""
    print(f"\n{'='*70}")
    print(f"🎭 CONFIGURE: {speaker_name}")
    print(f"{'='*70}")
    
    # Show speaker stats
    duration = sum(s['duration'] for s in segments)
    print(f"📊 Segments: {len(segments)} | Total time: {duration:.1f}s")
    print(f"📝 Sample: {segments[0]['translated_text'][:80]}...")
    
    # 1. GENDER SELECTION
    print("\n1️⃣ GENDER:")
    print("   [1] Male   [2] Female   [3] Show All")
    gender_choice = input("Choose (1-3): ").strip()
    
    gender_filter = None
    if gender_choice == '1': gender_filter = 'male'
    elif gender_choice == '2': gender_filter = 'female'
    
    # 2. AGE SELECTION  
    age_filter = None
    if gender_filter:
        print(f"\n2️⃣ AGE RANGE ({gender_filter.title()}):")
        print("   [1] Child 8-12    [2] Teen 13-17")
        print("   [3] Young Adult 18-30  [4] Adult 30-50")
        print("   [5] Elderly 50+   [6] Show All Ages")
        age_choice = input("Choose (1-6): ").strip()
        
        age_map = {'1':'child', '2':'teen', '3':'young_adult', '4':'adult', '5':'elderly'}
        age_filter = age_map.get(age_choice)
    
    # 3. VOICE SELECTION
    voice_keys = show_voices(gender_filter, age_filter)
    voice_key = get_choice(voice_keys, f"\n🎤 Select voice (1-{len(voice_keys)}): ")
    if not voice_key: return None
    
    voice_info = VOICE_LIBRARY[voice_key]
    
    # 4. EMOTION SELECTION
    emotion_keys = show_emotions()
    detected_emotion = segments[0].get('emotion', None)
    if detected_emotion:
        print(f"💡 Detected from audio: {detected_emotion.upper()}")
    
    emotion_key = get_choice(emotion_keys, f"\n😊 Select emotion (1-{len(emotion_keys)}): ")
    if not emotion_key: emotion_key = 'neutral'
    
    emotion_preset = EMOTION_PRESETS[emotion_key]
    
    print(f"\n✅ CONFIG SAVED!")
    print(f"   🎤 Voice: {voice_info['name']}")
    print(f"   😊 Emotion: {emotion_key.title()} ({emotion_preset['desc']})")
    
    return {
        'voice_key': voice_key,
        'voice_info': voice_info,
        'emotion_key': emotion_key,
        'emotion_preset': emotion_preset
    }

# ═══════════════════════════════════════════════════════════════════════════════════════
def assign_voices_emotions(data):
    """Interactive voice/emotion assignment for all speakers"""
    print("\n🎯 INTERACTIVE VOICE & EMOTION SETUP")
    print("="*70)
    
    segments = data['segments']
    speakers = sorted(set(s.get('speaker', 'SPEAKER_00') for s in segments))
    
    print(f"👥 Found {len(speakers)} speakers: {', '.join(speakers)}")
    input("\nPress Enter to configure speakers...")
    
    speaker_configs = {}
    for speaker in speakers:
        speaker_segments = [s for s in segments if s.get('speaker') == speaker]
        config = configure_speaker(speaker, speaker_segments)
        if config:
            speaker_configs[speaker] = config
    
    # Per-segment customization?
    print("\n🎛️  PER-SEGMENT CONTROL?")
    print("   [1] Yes (custom emotion per line - SLOWER)")
    print("   [2] No (use defaults - FASTER)")
    choice = input("Choose (1-2): ").strip()
    
    return speaker_configs, choice == '1'

# ═══════════════════════════════════════════════════════════════════════════════════════
def generate_clips(client, segments, speaker_configs, per_segment_control):
    """Generate all voice clips"""
    print(f"\n{'='*70}")
    print("🎙️  GENERATING VOICE CLIPS")
    print(f"{'='*70}")
    
    total_chars = sum(len(s['translated_text']) for s in segments)
    print(f"📊 {len(segments)} segments | {total_chars} chars | ~{total_chars/160:.1f}min")
    
    if total_chars > 10000:
        if input(f"\n⚠️  Exceeds free tier! Continue? (y/N): ").lower() != 'y':
            return []
    
    input("\nPress Enter to start generation...")
    generated = []
    
    for i, seg in enumerate(segments, 1):
        speaker = seg.get('speaker', 'SPEAKER_00')
        config = speaker_configs.get(speaker)
        
        if not config:
            config = {'voice_info': VOICE_LIBRARY['male_young_adult'], 
                     'emotion_preset': EMOTION_PRESETS['neutral']}
        
        # Per-segment emotion override
        if per_segment_control:
            override = input(f"\n[{i}/{len(segments)}] {speaker} Change emotion? (y/N): ").lower()
            if override == 'y':
                emotion_keys = list(EMOTION_PRESETS.keys())
                new_emotion = get_choice(emotion_keys, "Select new emotion: ")
                config['emotion_preset'] = EMOTION_PRESETS[new_emotion]
        
        text = seg['translated_text']
        # Add emotion tag from detection if available
        if seg.get('emotion_tag'):
            text = f"{seg['emotion_tag']} {text}"
        
        print(f"[{i}/{len(segments)}] {speaker} ({config['voice_info']['name']})")
        print(f"     {text[:60]}...")
        
        try:
            audio = client.text_to_speech.convert(
                voice_id=config['voice_info']['voice_id'],
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=config['emotion_preset']['stability'],
                    similarity_boost=config['emotion_preset']['similarity_boost'],
                    style=config['emotion_preset']['style'],
                    use_speaker_boost=True
                )
            )
            
            filename = f"segment_{i:03d}_{speaker}.mp3"
            path = os.path.join(OUTPUT_DIR, filename)
            
            with open(path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            
            seg_copy = seg.copy()
            seg_copy.update({
                'audio_file': path,
                'voice_name': config['voice_info']['name'],
                'emotion_used': config['emotion_key']
            })
            generated.append(seg_copy)
            
            print(f"   ✅ {filename}")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return generated

# ═══════════════════════════════════════════════════════════════════════════════════════
def save_metadata(data, generated, speaker_configs):
    """Save all configuration and metadata"""
    output = {
        'speakers': {k: {
            'voice': v['voice_info']['name'],
            'age': v['voice_info']['age_range'],
            'emotion': v['emotion_key']
        } for k,v in speaker_configs.items()},
        'clips': generated
    }
    
    with open("work/voice_clips_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("💾 Metadata saved!")

# ═══════════════════════════════════════════════════════════════════════════════════════
def show_summary(generated, speaker_configs):
    """Show final results"""
    print("\n" + "="*70)
    print("🎉 GENERATION COMPLETE!")
    print("="*70)
    
    print(f"✅ {len(generated)} clips generated!")
    total_time = sum(c['duration'] for c in generated)
    print(f"⏱️  Total: {total_time:.1f}s ({total_time/60:.1f}min)")
    
    print("\n🎭 SPEAKER SUMMARY:")
    for speaker, config in speaker_configs.items():
        count = sum(1 for c in generated if c.get('speaker') == speaker)
        print(f"   {speaker}: {config['voice_info']['name']} ({count} clips)")

# ═══════════════════════════════════════════════════════════════════════════════════════
def main():
    print("🚀 INTERACTIVE VOICE GENERATION")
    print("="*70)
    
    if not check_prerequisites(): return
    
    # Initialize ElevenLabs
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    # Load data
    data = load_data()
    
    # Interactive configuration
    speaker_configs, per_segment = assign_voices_emotions(data)
    
    # Generate
    clips = generate_clips(client, data['segments'], speaker_configs, per_segment)
    
    if clips:
        save_metadata(data, clips, speaker_configs)
        show_summary(clips, speaker_configs)
        print(f"\n📁 Files in: {OUTPUT_DIR}/")
        print("🎬 Next: python step6_video_assembly.py")

if __name__ == "__main__":
    main()
