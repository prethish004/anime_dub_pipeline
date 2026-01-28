# step5_voice_generation.py
import json
import os
import time
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# Configuration
INPUT_JSON = "work/translated_segments.json"
OUTPUT_DIR = "work/voice_clips"

# ElevenLabs API Key
ELEVENLABS_API_KEY = "sk_13330e107d319d4f75ab5e197f48d174e10520e1e6713e19"  # Get from: https://elevenlabs.io

# Voice mapping based on speaker profiles
VOICE_LIBRARY = {
    # Male voices
    'male_adult': {
        'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - Deep male
        'name': 'Adam',
        'description': 'Deep, authoritative male voice'
    },
    'male_young': {
        'voice_id': 'yoZ06aMxZJJ28mfd3POQ',  # Sam - Young male
        'name': 'Sam',
        'description': 'Young, energetic male voice'
    },
    'male_mature': {
        'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold - Mature male
        'name': 'Arnold',
        'description': 'Strong, mature male voice'
    },
    
    # Female voices
    'female_adult': {
        'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - Adult female
        'name': 'Rachel',
        'description': 'Clear, professional female voice'
    },
    'female_young': {
        'voice_id': 'jsCqWAovK2LkecY7zXl4',  # Freya - Young female
        'name': 'Freya',
        'description': 'Young, friendly female voice'
    },
    'female_teen': {
        'voice_id': 'XB0fDUnXU5powFXDhCwa',  # Charlotte - Teen female
        'name': 'Charlotte',
        'description': 'Youthful, energetic female voice'
    }
}

# Voice settings for anime dubbing
ANIME_VOICE_SETTINGS = {
    'stability': 0.6,        # Moderate stability (0.5-0.7 good for anime)
    'similarity_boost': 0.8, # High similarity for consistency
    'style': 0.3,            # Some style variation for emotion
    'use_speaker_boost': True
}

def check_prerequisites():
    """Check if required files and API key exist"""
    
    if not os.path.exists(INPUT_JSON):
        print(f"❌ Input file not found: {INPUT_JSON}")
        print("   Please run step4_translation_free.py first")
        return False
    
    if ELEVENLABS_API_KEY == "YOUR_ELEVENLABS_API_KEY_HERE":
        print("❌ ElevenLabs API key not set!")
        print("\n📝 To get your API key:")
        print("   1. Go to: https://elevenlabs.io")
        print("   2. Sign up (FREE tier: 10,000 chars/month)")
        print("   3. Go to Profile → API Keys")
        print("   4. Copy your API key")
        print("   5. Paste it in step5_voice_generation.py")
        print("\n💰 Free tier: ~10 minutes of audio per month")
        print("💰 Starter: $5/month for ~30 minutes")
        return False
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    return True

def load_translations():
    """Load translated segments"""
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {data['total_segments']} translated segments")
    return data

def select_voice_for_speaker(speaker_profile):
    """Select appropriate voice based on speaker profile"""
    
    gender = speaker_profile.get('gender', 'unknown')
    age_group = speaker_profile.get('age_group', 'adult')
    
    # Map to voice key
    if gender == 'male':
        if 'teen' in age_group or 'young' in age_group:
            voice_key = 'male_young'
        elif 'mature' in age_group or 'old' in age_group:
            voice_key = 'male_mature'
        else:
            voice_key = 'male_adult'
    elif gender == 'female':
        if 'teen' in age_group:
            voice_key = 'female_teen'
        elif 'young' in age_group:
            voice_key = 'female_young'
        else:
            voice_key = 'female_adult'
    else:
        # Default to male adult if unknown
        voice_key = 'male_adult'
    
    return VOICE_LIBRARY[voice_key]

def assign_voices_to_speakers(data):
    """Assign ElevenLabs voices to each speaker"""
    
    print("\n🎭 Assigning voices to speakers...")
    
    diarization = data.get('diarization', {})
    speaker_profiles = diarization.get('speaker_profiles', {})
    
    voice_assignments = {}
    
    for speaker, profile in speaker_profiles.items():
        voice_info = select_voice_for_speaker(profile)
        voice_assignments[speaker] = voice_info
        
        print(f"   {speaker} ({profile['gender']}, {profile['age_group']})")
        print(f"   → Voice: {voice_info['name']} ({voice_info['description']})")
    
    # If no profiles (fallback)
    if not voice_assignments:
        print("   ⚠️  No speaker profiles found, using default voices")
        voice_assignments['SPEAKER_00'] = VOICE_LIBRARY['male_adult']
    
    return voice_assignments

def estimate_character_count(segments):
    """Estimate total characters for API usage"""
    total_chars = sum(len(seg['translated_text']) for seg in segments)
    return total_chars

def generate_voice_clips(client, segments, voice_assignments):
    """Generate voice clips for all segments"""
    
    print(f"\n🎙️ Generating voice clips...")
    
    # Estimate usage
    total_chars = estimate_character_count(segments)
    print(f"   Estimated characters: {total_chars}")
    print(f"   Estimated duration: ~{total_chars / 160:.1f} minutes")
    print(f"   (ElevenLabs free tier: 10,000 chars/month)")
    
    if total_chars > 10000:
        print(f"\n⚠️  WARNING: This will use {total_chars} characters")
        print(f"   Free tier limit is 10,000 characters")
        response = input("   Continue? (y/n): ")
        if response.lower() != 'y':
            print("   Aborted")
            return []
    
    print("\n⏳ Generating audio (this takes a few minutes)...\n")
    
    generated_clips = []
    
    for idx, seg in enumerate(segments, 1):
        speaker = seg.get('speaker', 'SPEAKER_00')
        text = seg['translated_text']
        
        # Get voice for this speaker
        voice_info = voice_assignments.get(speaker)
        if not voice_info:
            print(f"   ⚠️  No voice assigned to {speaker}, using default")
            voice_info = VOICE_LIBRARY['male_adult']
        
        print(f"[{idx}/{len(segments)}] Speaker: {speaker} ({voice_info['name']})")
        print(f"   Text: {text}")
        print(f"   Duration: {seg['duration']:.1f}s")
        
        try:
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_info["voice_id"],
                model_id="eleven_multilingual_v2",
                text=text,
                voice_settings=VoiceSettings(
                    stability=ANIME_VOICE_SETTINGS["stability"],
                    similarity_boost=ANIME_VOICE_SETTINGS["similarity_boost"],
                    style=ANIME_VOICE_SETTINGS["style"],
                    use_speaker_boost=ANIME_VOICE_SETTINGS["use_speaker_boost"],
                ),
            )

            # Convert generator → bytes
            audio_bytes = b"".join(chunk for chunk in audio_stream)
            output_filename = f"segment_{idx:03d}_{speaker}.mp3"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            print(f"   ✅ Saved: {output_filename}")

            clip_info = seg.copy()
            clip_info["audio_file"] = output_path
            clip_info["voice_name"] = voice_info["name"]
            generated_clips.append(clip_info)

            time.sleep(0.5)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   Skipping segment {idx}")
            continue
                
    return generated_clips

def save_results(data, generated_clips, voice_assignments):
    """Save generated clips metadata"""
    
    output_data = {
        'source_data': {
            'model': data.get('model', 'unknown'),
            'translation_model': data.get('translation_model', 'unknown'),
            'source_language': data.get('source_language', 'Japanese'),
            'target_language': data.get('target_language', 'English')
        },
        'voice_assignments': voice_assignments,
        'total_clips': len(generated_clips),
        'clips': generated_clips
    }
    
    output_file = "work/voice_clips_metadata.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Metadata saved to: {output_file}")

def display_summary(generated_clips, voice_assignments):
    """Display generation summary"""
    
    print("\n" + "="*70)
    print("📊 VOICE GENERATION SUMMARY")
    print("="*70)
    
    print(f"\n✅ Successfully generated: {len(generated_clips)} clips")
    
    print(f"\n🎭 Voice Assignments:")
    for speaker, voice_info in voice_assignments.items():
        clip_count = sum(1 for c in generated_clips if c.get('speaker') == speaker)
        print(f"   {speaker}: {voice_info['name']} ({clip_count} clips)")
    
    total_duration = sum(c['duration'] for c in generated_clips)
    print(f"\n⏱️  Total audio duration: {total_duration:.1f} seconds")
    
    print(f"\n📁 Audio files saved to: {OUTPUT_DIR}/")
    
    print("\n" + "="*70)
    print("📋 SAMPLE CLIPS (First 3)")
    print("="*70)
    
    for clip in generated_clips[:3]:
        print(f"\n[{clip['start']:.1f}s - {clip['end']:.1f}s] {clip.get('speaker', 'UNKNOWN')}")
        print(f"🇯🇵 Original: {clip.get('original_text', 'N/A')}")
        print(f"🇬🇧 Translated: {clip['translated_text']}")
        print(f"🎙️  Voice: {clip['voice_name']}")
        print(f"📄 File: {os.path.basename(clip['audio_file'])}")

def main():
    print("=" * 70)
    print("STEP 5: Voice Generation with ElevenLabs")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Initialize ElevenLabs client
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("✅ ElevenLabs client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ElevenLabs client: {e}")
        return
    
    # Load translations
    data = load_translations()
    
    # Assign voices based on speaker profiles
    voice_assignments = assign_voices_to_speakers(data)
    
    # Generate voice clips
    generated_clips = generate_voice_clips(
        client,
        data['segments'],
        voice_assignments
    )
    
    if not generated_clips:
        print("❌ No clips were generated")
        return
    
    # Save results
    save_results(data, generated_clips, voice_assignments)
    
    # Display summary
    display_summary(generated_clips, voice_assignments)
    
    print("\n" + "=" * 70)
    print("✅ Step 5 Complete!")
    print("=" * 70)
    print(f"📁 Generated clips: {len(generated_clips)}")
    print(f"📂 Location: {OUTPUT_DIR}/")
    print("\nNext: Run step6_final_assembly.py to combine everything!")

if __name__ == "__main__":
    main()
