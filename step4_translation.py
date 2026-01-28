# step4_translation.py
import json
import os
from openai import OpenAI
from datetime import datetime
import time

# Configuration
INPUT_JSON = "work/transcription_with_speakers.json"
OUTPUT_JSON = "work/translated_segments.json"

# OpenAI API Key
OPENAI_API_KEY = "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"  # Replace with your key

# Translation settings
TARGET_LANGUAGE = "English"
SOURCE_LANGUAGE = "Japanese"

def check_prerequisites():
    """Check if required files and API key exist"""
    
    if not os.path.exists(INPUT_JSON):
        print(f"❌ Input file not found: {INPUT_JSON}")
        print("   Please run step3_diarization_simple.py first")
        return False
    
    if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
        print("❌ OpenAI API key not set!")
        print("\n📝 To get your API key:")
        print("   1. Go to: https://platform.openai.com/api-keys")
        print("   2. Click 'Create new secret key'")
        print("   3. Copy the key (starts with sk-...)")
        print("   4. Paste it in step4_translation.py (OPENAI_API_KEY variable)")
        print("\n💰 Cost estimate: ~$0.50 per episode")
        print("\n💡 Alternative: Use free option (I'll provide code if needed)")
        return False
    
    return True

def load_data():
    """Load transcription with speakers"""
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {data['total_segments']} segments")
    return data

def estimate_speech_duration(text, words_per_second=2.5):
    """Estimate how long text will take to speak in English"""
    # Average English speech: ~150 words/minute = 2.5 words/second
    word_count = len(text.split())
    estimated_duration = word_count / words_per_second
    return estimated_duration

def translate_text(client, text, target_duration=None):
    """Translate Japanese to English with optional duration constraint"""
    
    try:
        if target_duration is None:
            # Simple translation
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper and faster than gpt-4
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional anime translator. Translate Japanese dialogue to natural, conversational English suitable for dubbing. Keep translations concise and natural-sounding."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this Japanese dialogue to English:\n{text}"
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )
        else:
            # Translation with duration constraint
            target_words = int(target_duration * 2.5)  # 2.5 words per second
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional anime dubbing translator. Translate Japanese to English while keeping the translation SHORT enough to fit the original timing."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this Japanese dialogue to English. The translation MUST fit in {target_duration:.1f} seconds of speech (approximately {target_words} words max):\n\n{text}\n\nProvide ONLY the English translation, nothing else."
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )
        
        translation = response.choices[0].message.content.strip()
        return translation
    
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return None

def process_segments(client, segments):
    """Translate all segments with duration matching"""
    
    print(f"\n🌍 Translating {len(segments)} segments...")
    print("⏳ This will take a few minutes...")
    
    translated_segments = []
    
    for idx, seg in enumerate(segments, 1):
        japanese_text = seg['text']
        original_duration = seg['duration']
        
        print(f"\n[{idx}/{len(segments)}] Translating...")
        print(f"   JP: {japanese_text}")
        
        # First translation attempt
        english_text = translate_text(client, japanese_text)
        
        if english_text is None:
            print("   ⚠️  Translation failed, skipping")
            continue
        
        # Check if duration fits
        estimated_duration = estimate_speech_duration(english_text)
        duration_ratio = estimated_duration / original_duration if original_duration > 0 else 1.0
        
        # If translation is too long (>20% over), compress it
        if duration_ratio > 1.2:
            print(f"   ⚠️  Too long ({estimated_duration:.1f}s vs {original_duration:.1f}s), compressing...")
            
            compressed_text = translate_text(client, japanese_text, target_duration=original_duration)
            
            if compressed_text:
                english_text = compressed_text
                estimated_duration = estimate_speech_duration(english_text)
                print(f"   ✅ Compressed: {english_text}")
            else:
                print(f"   ⚠️  Compression failed, using original translation")
        
        print(f"   EN: {english_text}")
        print(f"   Duration: {original_duration:.1f}s → ~{estimated_duration:.1f}s")
        
        # Save translation
        translated_seg = seg.copy()
        translated_seg['original_text'] = japanese_text
        translated_seg['translated_text'] = english_text
        translated_seg['estimated_duration'] = estimated_duration
        translated_seg['duration_ratio'] = duration_ratio
        
        translated_segments.append(translated_seg)
        
        # Rate limiting (avoid API throttling)
        time.sleep(0.5)
    
    return translated_segments

def save_results(data, translated_segments):
    """Save translated segments"""
    
    output_data = {
        'model': data.get('model', 'unknown'),
        'source_language': SOURCE_LANGUAGE,
        'target_language': TARGET_LANGUAGE,
        'timestamp': datetime.now().isoformat(),
        'total_segments': len(translated_segments),
        'segments': translated_segments,
        'diarization': data.get('diarization', {})
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to: {OUTPUT_JSON}")

def display_summary(segments):
    """Display translation summary"""
    
    print("\n" + "="*60)
    print("📊 TRANSLATION SUMMARY")
    print("="*60)
    
    total_segments = len(segments)
    avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
    over_limit = sum(1 for s in segments if s['duration_ratio'] > 1.2)
    
    print(f"Total segments: {total_segments}")
    print(f"Average duration ratio: {avg_ratio:.2f}x")
    print(f"Segments over limit (>1.2x): {over_limit}")
    
    print("\n" + "="*60)
    print("📋 SAMPLE TRANSLATIONS (First 3)")
    print("="*60)
    
    for seg in segments[:3]:
        print(f"\n[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
        print(f"🇯🇵 {seg['original_text']}")
        print(f"🇬🇧 {seg['translated_text']}")
        print(f"⏱️  {seg['duration']:.1f}s → ~{seg['estimated_duration']:.1f}s ({seg['duration_ratio']:.2f}x)")

def main():
    print("=" * 60)
    print("STEP 4: Translation with Duration Matching")
    print("=" * 60)
    
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
    
    # Process segments
    translated_segments = process_segments(client, data['segments'])
    
    if not translated_segments:
        print("❌ No segments were translated")
        return
    
    # Save results
    save_results(data, translated_segments)
    
    # Display summary
    display_summary(translated_segments)
    
    print("\n" + "=" * 60)
    print("✅ Step 4 Complete!")
    print("=" * 60)
    print(f"📁 Output: {OUTPUT_JSON}")
    print(f"📝 Translated: {len(translated_segments)} segments")
    print("\nNext: Run step5_voice_generation.py")

if __name__ == "__main__":
    main()
# step4_translation_gemini.py (FREE with Google Gemini)
# import json
# import os
# import google.generativeai as genai
# from datetime import datetime
# import time

# # Configuration
# INPUT_JSON = "work/transcription_with_speakers.json"
# OUTPUT_JSON = "work/translated_segments.json"

# # Google Gemini API Key (FREE!)
# GEMINI_API_KEY = "AIzaSyDsh5rO_zdkYtfe52g_HoaDzqe0VL6VqHU"  # Replace with your key

# # Translation settings
# TARGET_LANGUAGE = "English"
# SOURCE_LANGUAGE = "Japanese"

# def check_prerequisites():
#     """Check if required files and API key exist"""
    
#     if not os.path.exists(INPUT_JSON):
#         print(f"❌ Input file not found: {INPUT_JSON}")
#         print("   Please run step3_diarization_simple.py first")
#         return False
    
#     if GEMINI_API_KEY == "AIzaSyDsh5rO_zdkYtfe52g_HoaDzqe0VL6VqHU":
#         print("❌ Gemini API key not set!")
#         print("\n📝 To get your FREE API key:")
#         print("   1. Go to: https://aistudio.google.com/app/apikey")
#         print("   2. Click 'Create API key'")
#         print("   3. Copy the key")
#         print("   4. Paste it in step4_translation_gemini.py (GEMINI_API_KEY variable)")
#         print("\n💰 Cost: 100% FREE (1500 requests/day limit)")
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
#     word_count = len(text.split())
#     estimated_duration = word_count / words_per_second
#     return estimated_duration

# def translate_text(model, text, target_duration=None):
#     """Translate Japanese to English with optional duration constraint"""
    
#     try:
#         if target_duration is None:
#             # Simple translation
#             prompt = f"""You are a professional anime translator. Translate this Japanese dialogue to natural, conversational English suitable for dubbing. Keep it concise and natural-sounding.

# Japanese: {text}

# Provide ONLY the English translation, nothing else."""
#         else:
#             # Translation with duration constraint
#             target_words = int(target_duration * 2.5)  # 2.5 words per second
            
#             prompt = f"""You are a professional anime dubbing translator. Translate this Japanese to English while keeping it SHORT to fit the timing.

# Japanese: {text}

# Requirements:
# - Must fit in {target_duration:.1f} seconds of speech (max {target_words} words)
# - Keep the meaning accurate
# - Sound natural when spoken

# Provide ONLY the English translation, nothing else."""
        
#         response = model.generate_content(prompt)
#         translation = response.text.strip()
        
#         # Clean up common issues
#         translation = translation.replace('"', '').replace("'", "")
        
#         return translation
    
#     except Exception as e:
#         print(f"❌ Translation error: {e}")
#         return None

# def process_segments(model, segments):
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
#         english_text = translate_text(model, japanese_text)
        
#         if english_text is None:
#             print("   ⚠️  Translation failed, skipping")
#             continue
        
#         # Check if duration fits
#         estimated_duration = estimate_speech_duration(english_text)
#         duration_ratio = estimated_duration / original_duration if original_duration > 0 else 1.0
        
#         # If translation is too long (>20% over), compress it
#         if duration_ratio > 1.2:
#             print(f"   ⚠️  Too long ({estimated_duration:.1f}s vs {original_duration:.1f}s), compressing...")
            
#             compressed_text = translate_text(model, japanese_text, target_duration=original_duration)
            
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
        
#         # Rate limiting (be nice to free API)
#         time.sleep(1)
    
#     return translated_segments

# def save_results(data, translated_segments):
#     """Save translated segments"""
    
#     output_data = {
#         'model': data.get('model', 'unknown'),
#         'translation_model': 'google-gemini-pro',
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
#     print("STEP 4: Translation with Google Gemini (FREE)")
#     print("=" * 60)
    
#     # Check prerequisites
#     if not check_prerequisites():
#         return
    
#     # Initialize Gemini
#     try:
#         genai.configure(api_key=GEMINI_API_KEY)
#         model = genai.GenerativeModel('gemini-1.5-flash')
#         print("✅ Google Gemini initialized (FREE)")
#     except Exception as e:
#         print(f"❌ Failed to initialize Gemini: {e}")
#         return
    
#     # Load data
#     data = load_data()
    
#     # Process segments
#     translated_segments = process_segments(model, data['segments'])
    
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
#     print(f"💰 Cost: $0.00 (FREE!)")
#     print("\nNext: Run step5_voice_generation.py")

# if __name__ == "__main__":
#     main()
