# # step4_translation.py
# import json
# import os
# from openai import OpenAI
# from datetime import datetime
# import time
# # 
# # Configuration
# INPUT_JSON = "work/transcription_with_speakers.json"
# OUTPUT_JSON = "work/translated_segments.json"

# # OpenAI API Key
# OPENAI_API_KEY = "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"  # Replace with your key

# # Translation settings
# TARGET_LANGUAGE = "English"
# SOURCE_LANGUAGE = "Japanese"

# def check_prerequisites():
#     """Check if required files and API key exist"""
    
#     if not os.path.exists(INPUT_JSON):
#         print(f"❌ Input file not found: {INPUT_JSON}")
#         print("   Please run step3_diarization_simple.py first")
#         return False
    
#     if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
#         print("❌ OpenAI API key not set!")
#         print("\n📝 To get your API key:")
#         print("   1. Go to: https://platform.openai.com/api-keys")
#         print("   2. Click 'Create new secret key'")
#         print("   3. Copy the key (starts with sk-...)")
#         print("   4. Paste it in step4_translation.py (OPENAI_API_KEY variable)")
#         print("\n💰 Cost estimate: ~$0.50 per episode")
#         print("\n💡 Alternative: Use free option (I'll provide code if needed)")
#         return False
    
#     return True

# def load_data():
#     """Load transcription with speakers"""
#     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     print(f"📄 Loaded {data['total_segments']} segments")
#     return data

# def estimate_speech_duration(text, words_per_second=2.5):
#     """Estimate how long text will take to speak in English"""
#     # Average English speech: ~150 words/minute = 2.5 words/second
#     word_count = len(text.split())
#     estimated_duration = word_count / words_per_second
#     return estimated_duration

# def translate_text(client, text, target_duration=None):
#     """Translate Japanese to English with optional duration constraint"""
    
#     try:
#         if target_duration is None:
#             # Simple translation
#             response = client.chat.completions.create(
#                 model="gpt-4o-mini",  # Cheaper and faster than gpt-4
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You are a professional anime translator. Translate Japanese dialogue to natural, conversational English suitable for dubbing. Keep translations concise and natural-sounding."
#                     },
#                     {
#                         "role": "user",
#                         "content": f"Translate this Japanese dialogue to English:\n{text}"
#                     }
#                 ],
#                 temperature=0.7,
#                 max_tokens=100
#             )
#         else:
#             # Translation with duration constraint
#             target_words = int(target_duration * 2.5)  # 2.5 words per second
            
#             response = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You are a professional anime dubbing translator. Translate Japanese to English while keeping the translation SHORT enough to fit the original timing."
#                     },
#                     {
#                         "role": "user",
#                         "content": f"Translate this Japanese dialogue to English. The translation MUST fit in {target_duration:.1f} seconds of speech (approximately {target_words} words max):\n\n{text}\n\nProvide ONLY the English translation, nothing else."
#                     }
#                 ],
#                 temperature=0.7,
#                 max_tokens=100
#             )
        
#         translation = response.choices[0].message.content.strip()
#         return translation
    
#     except Exception as e:
#         print(f"❌ Translation error: {e}")
#         return None

# def process_segments(client, segments):
#     """Translate all segments with duration matching"""
    
#     print(f"\n🌍 Translating {len(segments)} segments...")
#     print("⏳ This will take a few minutes...")
    
#     translated_segments = []
    
#     for idx, seg in enumerate(segments, 1):
#         japanese_text = seg['text']
#         original_duration = seg['duration']
        
#         print(f"\n[{idx}/{len(segments)}] Translating...")
#         print(f"   JP: {japanese_text}")
        
#         # First translation attempt
#         english_text = translate_text(client, japanese_text)
        
#         if english_text is None:
#             print("   ⚠️  Translation failed, skipping")
#             continue
        
#         # Check if duration fits
#         estimated_duration = estimate_speech_duration(english_text)
#         duration_ratio = estimated_duration / original_duration if original_duration > 0 else 1.0
        
#         # If translation is too long (>20% over), compress it
#         if duration_ratio > 1.2:
#             print(f"   ⚠️  Too long ({estimated_duration:.1f}s vs {original_duration:.1f}s), compressing...")
            
#             compressed_text = translate_text(client, japanese_text, target_duration=original_duration)
            
#             if compressed_text:
#                 english_text = compressed_text
#                 estimated_duration = estimate_speech_duration(english_text)
#                 print(f"   ✅ Compressed: {english_text}")
#             else:
#                 print(f"   ⚠️  Compression failed, using original translation")
        
#         print(f"   EN: {english_text}")
#         print(f"   Duration: {original_duration:.1f}s → ~{estimated_duration:.1f}s")
        
#         # Save translation
#         translated_seg = seg.copy()
#         translated_seg['original_text'] = japanese_text
#         translated_seg['translated_text'] = english_text
#         translated_seg['estimated_duration'] = estimated_duration
#         translated_seg['duration_ratio'] = duration_ratio
        
#         translated_segments.append(translated_seg)
        
#         # Rate limiting (avoid API throttling)
#         time.sleep(0.5)
    
#     return translated_segments

# def save_results(data, translated_segments):
#     """Save translated segments"""
    
#     output_data = {
#         'model': data.get('model', 'unknown'),
#         'source_language': SOURCE_LANGUAGE,
#         'target_language': TARGET_LANGUAGE,
#         'timestamp': datetime.now().isoformat(),
#         'total_segments': len(translated_segments),
#         'segments': translated_segments,
#         'diarization': data.get('diarization', {})
#     }
    
#     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
#     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# def display_summary(segments):
#     """Display translation summary"""
    
#     print("\n" + "="*60)
#     print("📊 TRANSLATION SUMMARY")
#     print("="*60)
    
#     total_segments = len(segments)
#     avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
#     over_limit = sum(1 for s in segments if s['duration_ratio'] > 1.2)
    
#     print(f"Total segments: {total_segments}")
#     print(f"Average duration ratio: {avg_ratio:.2f}x")
#     print(f"Segments over limit (>1.2x): {over_limit}")
    
#     print("\n" + "="*60)
#     print("📋 SAMPLE TRANSLATIONS (First 3)")
#     print("="*60)
    
#     for seg in segments[:3]:
#         print(f"\n[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
#         print(f"🇯🇵 {seg['original_text']}")
#         print(f"🇬🇧 {seg['translated_text']}")
#         print(f"⏱️  {seg['duration']:.1f}s → ~{seg['estimated_duration']:.1f}s ({seg['duration_ratio']:.2f}x)")

# def main():
#     print("=" * 60)
#     print("STEP 4: Translation with Duration Matching")
#     print("=" * 60)
    
#     # Check prerequisites
#     if not check_prerequisites():
#         return
    
#     # Initialize OpenAI client
#     try:
#         client = OpenAI(api_key=OPENAI_API_KEY)
#         print("✅ OpenAI client initialized")
#     except Exception as e:
#         print(f"❌ Failed to initialize OpenAI client: {e}")
#         return
    
#     # Load data
#     data = load_data()
    
#     # Process segments
#     translated_segments = process_segments(client, data['segments'])
    
#     if not translated_segments:
#         print("❌ No segments were translated")
#         return
    
#     # Save results
#     save_results(data, translated_segments)
    
#     # Display summary
#     display_summary(translated_segments)
    
#     print("\n" + "=" * 60)
#     print("✅ Step 4 Complete!")
#     print("=" * 60)
#     print(f"📁 Output: {OUTPUT_JSON}")
#     print(f"📝 Translated: {len(translated_segments)} segments")
#     print("\nNext: Run step5_voice_generation.py")

# if __name__ == "__main__":
#     main()
# # step4_translation_gemini.py (FREE with Google Gemini)
# # import json
# # import os
# # import google.generativeai as genai
# # from datetime import datetime
# # import time

# # # Configuration
# # INPUT_JSON = "work/transcription_with_speakers.json"
# # OUTPUT_JSON = "work/translated_segments.json"

# # # Google Gemini API Key (FREE!)
# # GEMINI_API_KEY = "AIzaSyDsh5rO_zdkYtfe52g_HoaDzqe0VL6VqHU"  # Replace with your key

# # # Translation settings
# # TARGET_LANGUAGE = "English"
# # SOURCE_LANGUAGE = "Japanese"

# # def check_prerequisites():
# #     """Check if required files and API key exist"""
    
# #     if not os.path.exists(INPUT_JSON):
# #         print(f"❌ Input file not found: {INPUT_JSON}")
# #         print("   Please run step3_diarization_simple.py first")
# #         return False
    
# #     if GEMINI_API_KEY == "AIzaSyDsh5rO_zdkYtfe52g_HoaDzqe0VL6VqHU":
# #         print("❌ Gemini API key not set!")
# #         print("\n📝 To get your FREE API key:")
# #         print("   1. Go to: https://aistudio.google.com/app/apikey")
# #         print("   2. Click 'Create API key'")
# #         print("   3. Copy the key")
# #         print("   4. Paste it in step4_translation_gemini.py (GEMINI_API_KEY variable)")
# #         print("\n💰 Cost: 100% FREE (1500 requests/day limit)")
# #         return False
    
# #     return True

# # def load_data():
# #     """Load transcription with speakers"""
# #     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
# #         data = json.load(f)
    
# #     print(f"📄 Loaded {data['total_segments']} segments")
# #     return data

# # def estimate_speech_duration(text, words_per_second=2.5):
# #     """Estimate how long text will take to speak in English"""
# #     word_count = len(text.split())
# #     estimated_duration = word_count / words_per_second
# #     return estimated_duration

# # def translate_text(model, text, target_duration=None):
# #     """Translate Japanese to English with optional duration constraint"""
    
# #     try:
# #         if target_duration is None:
# #             # Simple translation
# #             prompt = f"""You are a professional anime translator. Translate this Japanese dialogue to natural, conversational English suitable for dubbing. Keep it concise and natural-sounding.

# # Japanese: {text}

# # Provide ONLY the English translation, nothing else."""
# #         else:
# #             # Translation with duration constraint
# #             target_words = int(target_duration * 2.5)  # 2.5 words per second
            
# #             prompt = f"""You are a professional anime dubbing translator. Translate this Japanese to English while keeping it SHORT to fit the timing.

# # Japanese: {text}

# # Requirements:
# # - Must fit in {target_duration:.1f} seconds of speech (max {target_words} words)
# # - Keep the meaning accurate
# # - Sound natural when spoken

# # Provide ONLY the English translation, nothing else."""
        
# #         response = model.generate_content(prompt)
# #         translation = response.text.strip()
        
# #         # Clean up common issues
# #         translation = translation.replace('"', '').replace("'", "")
        
# #         return translation
    
# #     except Exception as e:
# #         print(f"❌ Translation error: {e}")
# #         return None

# # def process_segments(model, segments):
# #     """Translate all segments with duration matching"""
    
# #     print(f"\n🌍 Translating {len(segments)} segments...")
# #     print("⏳ This will take a few minutes...")
    
# #     translated_segments = []
    
# #     for idx, seg in enumerate(segments, 1):
# #         japanese_text = seg['text']
# #         original_duration = seg['duration']
        
# #         print(f"\n[{idx}/{len(segments)}] Translating...")
# #         print(f"   JP: {japanese_text}")
        
# #         # First translation attempt
# #         english_text = translate_text(model, japanese_text)
        
# #         if english_text is None:
# #             print("   ⚠️  Translation failed, skipping")
# #             continue
        
# #         # Check if duration fits
# #         estimated_duration = estimate_speech_duration(english_text)
# #         duration_ratio = estimated_duration / original_duration if original_duration > 0 else 1.0
        
# #         # If translation is too long (>20% over), compress it
# #         if duration_ratio > 1.2:
# #             print(f"   ⚠️  Too long ({estimated_duration:.1f}s vs {original_duration:.1f}s), compressing...")
            
# #             compressed_text = translate_text(model, japanese_text, target_duration=original_duration)
            
# #             if compressed_text:
# #                 english_text = compressed_text
# #                 estimated_duration = estimate_speech_duration(english_text)
# #                 print(f"   ✅ Compressed: {english_text}")
# #             else:
# #                 print(f"   ⚠️  Compression failed, using original translation")
        
# #         print(f"   EN: {english_text}")
# #         print(f"   Duration: {original_duration:.1f}s → ~{estimated_duration:.1f}s")
        
# #         # Save translation
# #         translated_seg = seg.copy()
# #         translated_seg['original_text'] = japanese_text
# #         translated_seg['translated_text'] = english_text
# #         translated_seg['estimated_duration'] = estimated_duration
# #         translated_seg['duration_ratio'] = duration_ratio
        
# #         translated_segments.append(translated_seg)
        
# #         # Rate limiting (be nice to free API)
# #         time.sleep(1)
    
# #     return translated_segments

# # def save_results(data, translated_segments):
# #     """Save translated segments"""
    
# #     output_data = {
# #         'model': data.get('model', 'unknown'),
# #         'translation_model': 'google-gemini-pro',
# #         'source_language': SOURCE_LANGUAGE,
# #         'target_language': TARGET_LANGUAGE,
# #         'timestamp': datetime.now().isoformat(),
# #         'total_segments': len(translated_segments),
# #         'segments': translated_segments,
# #         'diarization': data.get('diarization', {})
# #     }
    
# #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # def display_summary(segments):
# #     """Display translation summary"""
    
# #     print("\n" + "="*60)
# #     print("📊 TRANSLATION SUMMARY")
# #     print("="*60)
    
# #     total_segments = len(segments)
# #     avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
# #     over_limit = sum(1 for s in segments if s['duration_ratio'] > 1.2)
    
# #     print(f"Total segments: {total_segments}")
# #     print(f"Average duration ratio: {avg_ratio:.2f}x")
# #     print(f"Segments over limit (>1.2x): {over_limit}")
    
# #     print("\n" + "="*60)
# #     print("📋 SAMPLE TRANSLATIONS (First 3)")
# #     print("="*60)
    
# #     for seg in segments[:3]:
# #         print(f"\n[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
# #         print(f"🇯🇵 {seg['original_text']}")
# #         print(f"🇬🇧 {seg['translated_text']}")
# #         print(f"⏱️  {seg['duration']:.1f}s → ~{seg['estimated_duration']:.1f}s ({seg['duration_ratio']:.2f}x)")

# # def main():
# #     print("=" * 60)
# #     print("STEP 4: Translation with Google Gemini (FREE)")
# #     print("=" * 60)
    
# #     # Check prerequisites
# #     if not check_prerequisites():
# #         return
    
# #     # Initialize Gemini
# #     try:
# #         genai.configure(api_key=GEMINI_API_KEY)
# #         model = genai.GenerativeModel('gemini-1.5-flash')
# #         print("✅ Google Gemini initialized (FREE)")
# #     except Exception as e:
# #         print(f"❌ Failed to initialize Gemini: {e}")
# #         return
    
# #     # Load data
# #     data = load_data()
    
# #     # Process segments
# #     translated_segments = process_segments(model, data['segments'])
    
# #     if not translated_segments:
# #         print("❌ No segments were translated")
# #         return
    
# #     # Save results
# #     save_results(data, translated_segments)
    
# #     # Display summary
# #     display_summary(translated_segments)
    
# #     print("\n" + "=" * 60)
# #     print("✅ Step 4 Complete!")
# #     print("=" * 60)
# #     print(f"📁 Output: {OUTPUT_JSON}")
# #     print(f"📝 Translated: {len(translated_segments)} segments")
# #     print(f"💰 Cost: $0.00 (FREE!)")
# #     print("\nNext: Run step5_voice_generation.py")

# # if __name__ == "__main__":
# #     main()
# step4_translation_enhanced.py (Enhanced Duration Matching)
import json
import os
from openai import OpenAI
from datetime import datetime
import time
import re

# Configuration
INPUT_JSON = "work/transcription_with_speakers.json"
OUTPUT_JSON = "work/translated_segments.json"

# OpenAI API Key
OPENAI_API_KEY = "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"

# Translation settings
TARGET_LANGUAGE = "English"
SOURCE_LANGUAGE = "Japanese"

# Duration matching thresholds
TARGET_RATIO_MIN = 0.85  # Minimum 85% of original duration
TARGET_RATIO_MAX = 1.15  # Maximum 115% of original duration
IDEAL_RATIO = 1.0        # Perfect match

# Syllable rate for English (syllables per second)
SYLLABLES_PER_SECOND = 4.5  # Average for natural speech


def check_prerequisites():
    """Check if required files and API key exist"""
    
    if not os.path.exists(INPUT_JSON):
        print(f"❌ Input file not found: {INPUT_JSON}")
        print("   Please run step3_diarization.py first")
        return False
    
    if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
        print("❌ OpenAI API key not set!")
        print("\n📝 To get your API key:")
        print("   1. Go to: https://platform.openai.com/api-keys")
        print("   2. Click 'Create new secret key'")
        print("   3. Copy the key (starts with sk-...)")
        print("   4. Paste it in step4_translation_enhanced.py")
        print("\n💰 Cost estimate: ~$0.50-1.00 per episode")
        return False
    
    return True


def load_data():
    """Load transcription with speakers"""
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {data['total_segments']} segments")
    return data


def count_syllables(word):
    """Count syllables in a word (English)"""
    word = word.lower()
    
    # Handle special cases
    if len(word) <= 3:
        return 1
    
    # Count vowel groups
    vowels = "aeiouy"
    syllable_count = 0
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel
    
    # Adjust for silent 'e'
    if word.endswith('e'):
        syllable_count -= 1
    
    # Adjust for 'le' ending
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        syllable_count += 1
    
    # Ensure at least 1 syllable
    return max(1, syllable_count)


def estimate_speech_duration_syllables(text):
    """Estimate speech duration based on syllables (more accurate)"""
    
    # Remove punctuation and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count total syllables
    total_syllables = sum(count_syllables(word) for word in words)
    
    # Calculate duration (syllables / syllables_per_second)
    estimated_duration = total_syllables / SYLLABLES_PER_SECOND
    
    return estimated_duration, total_syllables


def translate_with_duration_matching(client, japanese_text, target_duration, speaker_info=None):
    """
    Translate with iterative duration matching
    Attempts up to 3 times to get duration within acceptable range
    """
    
    # Get speaker context if available
    gender = speaker_info.get('gender', 'unknown') if speaker_info else 'unknown'
    age_group = speaker_info.get('age_group', 'adult') if speaker_info else 'adult'
    
    # Calculate target syllable count
    target_syllables = int(target_duration * SYLLABLES_PER_SECOND)
    syllable_min = int(target_syllables * TARGET_RATIO_MIN)
    syllable_max = int(target_syllables * TARGET_RATIO_MAX)
    
    best_translation = None
    best_ratio = float('inf')
    
    # Attempt 1: Natural anime-style translation
    print(f"   🔄 Attempt 1: Natural translation...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a professional anime dubbing translator. 
                
Rules:
1. Translate Japanese to natural, punchy English anime dialogue
2. Keep the dramatic anime tone and style
3. Use short, impactful phrases (anime characters speak dramatically)
4. Match character personality (gender: {gender}, age: {age_group})
5. Provide ONLY the English translation, no quotes or explanations

Examples:
- "痛みを知れ" → "Know pain"
- "お前はもう死んでいる" → "You're already dead"
- "これが俺の力だ" → "This is my power"
""".format(gender=gender, age_group=age_group)
            },
            {
                "role": "user",
                "content": f"Translate to English (anime style):\n{japanese_text}"
            }
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    translation = response.choices[0].message.content.strip()
    translation = translation.strip('"\'')  # Remove quotes if present
    
    estimated_duration, syllable_count = estimate_speech_duration_syllables(translation)
    duration_ratio = estimated_duration / target_duration if target_duration > 0 else 1.0
    
    print(f"      Result: \"{translation}\"")
    print(f"      Syllables: {syllable_count} (target: {target_syllables})")
    print(f"      Duration: {estimated_duration:.2f}s (target: {target_duration:.2f}s)")
    print(f"      Ratio: {duration_ratio:.2f}x")
    
    # Check if it's within acceptable range
    if TARGET_RATIO_MIN <= duration_ratio <= TARGET_RATIO_MAX:
        print(f"      ✅ Duration match acceptable!")
        return translation, estimated_duration, duration_ratio
    
    best_translation = translation
    best_ratio = abs(duration_ratio - IDEAL_RATIO)
    
    # Attempt 2: Adjust for duration
    print(f"   🔄 Attempt 2: Adjusting for duration...")
    
    if duration_ratio < TARGET_RATIO_MIN:
        # Too short - need to expand
        adjustment_prompt = f"""The previous translation "{translation}" is too short ({estimated_duration:.1f}s vs target {target_duration:.1f}s).

Provide a LONGER alternative with the SAME meaning that takes approximately {target_duration:.1f} seconds to say.
Add descriptive words or rephrase to be slightly longer while keeping anime style.

Target: {target_syllables} syllables (currently {syllable_count})

Provide ONLY the revised English translation."""
    else:
        # Too long - need to compress
        adjustment_prompt = f"""The previous translation "{translation}" is too long ({estimated_duration:.1f}s vs target {target_duration:.1f}s).

Provide a SHORTER alternative with the SAME meaning that takes approximately {target_duration:.1f} seconds to say.
Use fewer words or more concise phrasing while keeping anime style.

Target: {target_syllables} syllables (currently {syllable_count})

Provide ONLY the revised English translation."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a professional anime dubbing translator focused on precise timing."
            },
            {
                "role": "user",
                "content": adjustment_prompt
            }
        ],
        temperature=0.8,
        max_tokens=100
    )
    
    translation2 = response.choices[0].message.content.strip()
    translation2 = translation2.strip('"\'')
    
    estimated_duration2, syllable_count2 = estimate_speech_duration_syllables(translation2)
    duration_ratio2 = estimated_duration2 / target_duration if target_duration > 0 else 1.0
    
    print(f"      Result: \"{translation2}\"")
    print(f"      Syllables: {syllable_count2} (target: {target_syllables})")
    print(f"      Duration: {estimated_duration2:.2f}s (target: {target_duration:.2f}s)")
    print(f"      Ratio: {duration_ratio2:.2f}x")
    
    # Check if improved
    if TARGET_RATIO_MIN <= duration_ratio2 <= TARGET_RATIO_MAX:
        print(f"      ✅ Duration match achieved!")
        return translation2, estimated_duration2, duration_ratio2
    
    # Track best result
    ratio_diff2 = abs(duration_ratio2 - IDEAL_RATIO)
    if ratio_diff2 < best_ratio:
        best_translation = translation2
        best_ratio = ratio_diff2
        estimated_duration = estimated_duration2
        duration_ratio = duration_ratio2
    
    # Attempt 3: Final refinement with explicit syllable target
    print(f"   🔄 Attempt 3: Final refinement...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at creating perfectly-timed anime translations."
            },
            {
                "role": "user",
                "content": f"""Japanese: {japanese_text}

Previous attempts:
1. "{translation}" ({syllable_count} syllables, {estimated_duration:.1f}s)
2. "{translation2}" ({syllable_count2} syllables, {estimated_duration2:.1f}s)

Create a final translation that:
- Has EXACTLY {target_syllables} syllables (±2 syllables acceptable)
- Takes approximately {target_duration:.1f} seconds to say
- Keeps the same meaning
- Maintains anime dialogue style

Provide ONLY the final English translation."""
            }
        ],
        temperature=0.9,
        max_tokens=100
    )
    
    translation3 = response.choices[0].message.content.strip()
    translation3 = translation3.strip('"\'')
    
    estimated_duration3, syllable_count3 = estimate_speech_duration_syllables(translation3)
    duration_ratio3 = estimated_duration3 / target_duration if target_duration > 0 else 1.0
    
    print(f"      Result: \"{translation3}\"")
    print(f"      Syllables: {syllable_count3} (target: {target_syllables})")
    print(f"      Duration: {estimated_duration3:.2f}s (target: {target_duration:.2f}s)")
    print(f"      Ratio: {duration_ratio3:.2f}x")
    
    # Check if improved
    ratio_diff3 = abs(duration_ratio3 - IDEAL_RATIO)
    if ratio_diff3 < best_ratio:
        best_translation = translation3
        estimated_duration = estimated_duration3
        duration_ratio = duration_ratio3
    
    # Return best result
    if TARGET_RATIO_MIN <= duration_ratio <= TARGET_RATIO_MAX:
        print(f"      ✅ Best match achieved!")
    else:
        print(f"      ⚠️  Using best attempt (ratio: {duration_ratio:.2f}x)")
    
    return best_translation, estimated_duration, duration_ratio


def process_segments(client, segments, speaker_profiles):
    """Translate all segments with enhanced duration matching"""
    
    print(f"\n🌍 Translating {len(segments)} segments...")
    print("⏳ This will take several minutes (3 attempts per segment)...\n")
    
    translated_segments = []
    
    for idx, seg in enumerate(segments, 1):
        japanese_text = seg['text']
        original_duration = seg['duration']
        speaker = seg.get('speaker', 'UNKNOWN')
        
        # Get speaker info
        speaker_info = speaker_profiles.get(speaker, {})
        
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(segments)}] Segment {idx}")
        print(f"{'='*60}")
        print(f"   Speaker: {speaker}")
        print(f"   Japanese: \"{japanese_text}\"")
        print(f"   Target Duration: {original_duration:.2f}s")
        
        try:
            # Translate with duration matching
            english_text, estimated_duration, duration_ratio = translate_with_duration_matching(
                client,
                japanese_text,
                original_duration,
                speaker_info
            )
            
            print(f"\n   ✅ Final Translation: \"{english_text}\"")
            print(f"   📊 Duration Match: {duration_ratio:.2f}x ({estimated_duration:.2f}s / {original_duration:.2f}s)")
            
            # Quality indicator
            if 0.95 <= duration_ratio <= 1.05:
                print(f"   🎯 EXCELLENT match!")
            elif TARGET_RATIO_MIN <= duration_ratio <= TARGET_RATIO_MAX:
                print(f"   ✅ Good match")
            else:
                print(f"   ⚠️  Acceptable (best effort)")
            
            # Save translation
            translated_seg = seg.copy()
            translated_seg['original_text'] = japanese_text
            translated_seg['translated_text'] = english_text
            translated_seg['estimated_duration'] = estimated_duration
            translated_seg['duration_ratio'] = duration_ratio
            
            translated_segments.append(translated_seg)
            
            # Rate limiting
            time.sleep(1.0)  # Longer delay due to multiple requests
        
        except Exception as e:
            print(f"\n   ❌ Translation error: {e}")
            print(f"   Skipping segment {idx}")
            continue
    
    return translated_segments


def save_results(data, translated_segments):
    """Save translated segments"""
    
    output_data = {
        'model': data.get('model', 'unknown'),
        'source_language': SOURCE_LANGUAGE,
        'target_language': TARGET_LANGUAGE,
        'timestamp': datetime.now().isoformat(),
        'total_segments': len(translated_segments),
        'translation_method': 'enhanced_duration_matching',
        'segments': translated_segments,
        'diarization': data.get('diarization', {})
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to: {OUTPUT_JSON}")


def display_summary(segments):
    """Display translation summary"""
    
    print("\n" + "="*70)
    print("📊 TRANSLATION SUMMARY")
    print("="*70)
    
    total_segments = len(segments)
    avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
    
    # Quality bins
    excellent = sum(1 for s in segments if 0.95 <= s['duration_ratio'] <= 1.05)
    good = sum(1 for s in segments if TARGET_RATIO_MIN <= s['duration_ratio'] <= TARGET_RATIO_MAX)
    acceptable = total_segments - good
    
    print(f"\nTotal segments: {total_segments}")
    print(f"Average duration ratio: {avg_ratio:.2f}x")
    print(f"\nQuality Distribution:")
    print(f"  🎯 Excellent (0.95-1.05x): {excellent}")
    print(f"  ✅ Good (0.85-1.15x): {good}")
    print(f"  ⚠️  Acceptable (other): {acceptable}")
    
    print("\n" + "="*70)
    print("📋 ALL TRANSLATIONS")
    print("="*70)
    
    for seg in segments:
        quality = "🎯" if 0.95 <= seg['duration_ratio'] <= 1.05 else "✅" if TARGET_RATIO_MIN <= seg['duration_ratio'] <= TARGET_RATIO_MAX else "⚠️"
        
        print(f"\n{quality} [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
        print(f"   🇯🇵 {seg['original_text']}")
        print(f"   🇬🇧 {seg['translated_text']}")
        print(f"   ⏱️  {seg['duration']:.2f}s → {seg['estimated_duration']:.2f}s (ratio: {seg['duration_ratio']:.2f}x)")


def main():
    print("=" * 70)
    print("STEP 4: Enhanced Translation with Duration Matching")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return
    
    # Load data
    data = load_data()
    
    # Get speaker profiles
    speaker_profiles = data.get('diarization', {}).get('speaker_profiles', {})
    
    # Process segments
    translated_segments = process_segments(
        client,
        data['segments'],
        speaker_profiles
    )
    
    if not translated_segments:
        print("❌ No segments were translated")
        return
    
    # Save results
    save_results(data, translated_segments)
    
    # Display summary
    display_summary(translated_segments)
    
    print("\n" + "=" * 70)
    print("✅ Step 4 Complete!")
    print("=" * 70)
    print(f"📁 Output: {OUTPUT_JSON}")
    print(f"📝 Translated: {len(translated_segments)} segments")
    print("\nNext: Run step5_voice_generation.py")


if __name__ == "__main__":
    main()
