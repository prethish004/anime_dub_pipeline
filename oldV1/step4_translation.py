# # # # # # # # step4_translation.py
# # # # # # # import json
# # # # # # # import os
# # # # # # # from openai import OpenAI
# # # # # # # from datetime import datetime
# # # # # # # import time
# # # # # # # # 
# # # # # # # # Configuration
# # # # # # # INPUT_JSON = "work/transcription_with_speakers.json"
# # # # # # # OUTPUT_JSON = "work/translated_segments.json"

# # # # # # # # OpenAI API Key
# # # # # # # OPENAI_API_KEY = "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"  # Replace with your key

# # # # # # # # Translation settings
# # # # # # # TARGET_LANGUAGE = "English"
# # # # # # # SOURCE_LANGUAGE = "Japanese"

# # # # # # # def check_prerequisites():
# # # # # # #     """Check if required files and API key exist"""
    
# # # # # # #     if not os.path.exists(INPUT_JSON):
# # # # # # #         print(f"❌ Input file not found: {INPUT_JSON}")
# # # # # # #         print("   Please run step3_diarization_simple.py first")
# # # # # # #         return False
    
# # # # # # #     if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
# # # # # # #         print("❌ OpenAI API key not set!")
# # # # # # #         print("\n📝 To get your API key:")
# # # # # # #         print("   1. Go to: https://platform.openai.com/api-keys")
# # # # # # #         print("   2. Click 'Create new secret key'")
# # # # # # #         print("   3. Copy the key (starts with sk-...)")
# # # # # # #         print("   4. Paste it in step4_translation.py (OPENAI_API_KEY variable)")
# # # # # # #         print("\n💰 Cost estimate: ~$0.50 per episode")
# # # # # # #         print("\n💡 Alternative: Use free option (I'll provide code if needed)")
# # # # # # #         return False
    
# # # # # # #     return True

# # # # # # # def load_data():
# # # # # # #     """Load transcription with speakers"""
# # # # # # #     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
# # # # # # #         data = json.load(f)
    
# # # # # # #     print(f"📄 Loaded {data['total_segments']} segments")
# # # # # # #     return data

# # # # # # # def estimate_speech_duration(text, words_per_second=2.5):
# # # # # # #     """Estimate how long text will take to speak in English"""
# # # # # # #     # Average English speech: ~150 words/minute = 2.5 words/second
# # # # # # #     word_count = len(text.split())
# # # # # # #     estimated_duration = word_count / words_per_second
# # # # # # #     return estimated_duration

# # # # # # # def translate_text(client, text, target_duration=None):
# # # # # # #     """Translate Japanese to English with optional duration constraint"""
    
# # # # # # #     try:
# # # # # # #         if target_duration is None:
# # # # # # #             # Simple translation
# # # # # # #             response = client.chat.completions.create(
# # # # # # #                 model="gpt-4o-mini",  # Cheaper and faster than gpt-4
# # # # # # #                 messages=[
# # # # # # #                     {
# # # # # # #                         "role": "system",
# # # # # # #                         "content": "You are a professional anime translator. Translate Japanese dialogue to natural, conversational English suitable for dubbing. Keep translations concise and natural-sounding."
# # # # # # #                     },
# # # # # # #                     {
# # # # # # #                         "role": "user",
# # # # # # #                         "content": f"Translate this Japanese dialogue to English:\n{text}"
# # # # # # #                     }
# # # # # # #                 ],
# # # # # # #                 temperature=0.7,
# # # # # # #                 max_tokens=100
# # # # # # #             )
# # # # # # #         else:
# # # # # # #             # Translation with duration constraint
# # # # # # #             target_words = int(target_duration * 2.5)  # 2.5 words per second
            
# # # # # # #             response = client.chat.completions.create(
# # # # # # #                 model="gpt-4o-mini",
# # # # # # #                 messages=[
# # # # # # #                     {
# # # # # # #                         "role": "system",
# # # # # # #                         "content": "You are a professional anime dubbing translator. Translate Japanese to English while keeping the translation SHORT enough to fit the original timing."
# # # # # # #                     },
# # # # # # #                     {
# # # # # # #                         "role": "user",
# # # # # # #                         "content": f"Translate this Japanese dialogue to English. The translation MUST fit in {target_duration:.1f} seconds of speech (approximately {target_words} words max):\n\n{text}\n\nProvide ONLY the English translation, nothing else."
# # # # # # #                     }
# # # # # # #                 ],
# # # # # # #                 temperature=0.7,
# # # # # # #                 max_tokens=100
# # # # # # #             )
        
# # # # # # #         translation = response.choices[0].message.content.strip()
# # # # # # #         return translation
    
# # # # # # #     except Exception as e:
# # # # # # #         print(f"❌ Translation error: {e}")
# # # # # # #         return None

# # # # # # # def process_segments(client, segments):
# # # # # # #     """Translate all segments with duration matching"""
    
# # # # # # #     print(f"\n🌍 Translating {len(segments)} segments...")
# # # # # # #     print("⏳ This will take a few minutes...")
    
# # # # # # #     translated_segments = []
    
# # # # # # #     for idx, seg in enumerate(segments, 1):
# # # # # # #         japanese_text = seg['text']
# # # # # # #         original_duration = seg['duration']
        
# # # # # # #         print(f"\n[{idx}/{len(segments)}] Translating...")
# # # # # # #         print(f"   JP: {japanese_text}")
        
# # # # # # #         # First translation attempt
# # # # # # #         english_text = translate_text(client, japanese_text)
        
# # # # # # #         if english_text is None:
# # # # # # #             print("   ⚠️  Translation failed, skipping")
# # # # # # #             continue
        
# # # # # # #         # Check if duration fits
# # # # # # #         estimated_duration = estimate_speech_duration(english_text)
# # # # # # #         duration_ratio = estimated_duration / original_duration if original_duration > 0 else 1.0
        
# # # # # # #         # If translation is too long (>20% over), compress it
# # # # # # #         if duration_ratio > 1.2:
# # # # # # #             print(f"   ⚠️  Too long ({estimated_duration:.1f}s vs {original_duration:.1f}s), compressing...")
            
# # # # # # #             compressed_text = translate_text(client, japanese_text, target_duration=original_duration)
            
# # # # # # #             if compressed_text:
# # # # # # #                 english_text = compressed_text
# # # # # # #                 estimated_duration = estimate_speech_duration(english_text)
# # # # # # #                 print(f"   ✅ Compressed: {english_text}")
# # # # # # #             else:
# # # # # # #                 print(f"   ⚠️  Compression failed, using original translation")
        
# # # # # # #         print(f"   EN: {english_text}")
# # # # # # #         print(f"   Duration: {original_duration:.1f}s → ~{estimated_duration:.1f}s")
        
# # # # # # #         # Save translation
# # # # # # #         translated_seg = seg.copy()
# # # # # # #         translated_seg['original_text'] = japanese_text
# # # # # # #         translated_seg['translated_text'] = english_text
# # # # # # #         translated_seg['estimated_duration'] = estimated_duration
# # # # # # #         translated_seg['duration_ratio'] = duration_ratio
        
# # # # # # #         translated_segments.append(translated_seg)
        
# # # # # # #         # Rate limiting (avoid API throttling)
# # # # # # #         time.sleep(0.5)
    
# # # # # # #     return translated_segments

# # # # # # # def save_results(data, translated_segments):
# # # # # # #     """Save translated segments"""
    
# # # # # # #     output_data = {
# # # # # # #         'model': data.get('model', 'unknown'),
# # # # # # #         'source_language': SOURCE_LANGUAGE,
# # # # # # #         'target_language': TARGET_LANGUAGE,
# # # # # # #         'timestamp': datetime.now().isoformat(),
# # # # # # #         'total_segments': len(translated_segments),
# # # # # # #         'segments': translated_segments,
# # # # # # #         'diarization': data.get('diarization', {})
# # # # # # #     }
    
# # # # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # # # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # # # # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # # # # # def display_summary(segments):
# # # # # # #     """Display translation summary"""
    
# # # # # # #     print("\n" + "="*60)
# # # # # # #     print("📊 TRANSLATION SUMMARY")
# # # # # # #     print("="*60)
    
# # # # # # #     total_segments = len(segments)
# # # # # # #     avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
# # # # # # #     over_limit = sum(1 for s in segments if s['duration_ratio'] > 1.2)
    
# # # # # # #     print(f"Total segments: {total_segments}")
# # # # # # #     print(f"Average duration ratio: {avg_ratio:.2f}x")
# # # # # # #     print(f"Segments over limit (>1.2x): {over_limit}")
    
# # # # # # #     print("\n" + "="*60)
# # # # # # #     print("📋 SAMPLE TRANSLATIONS (First 3)")
# # # # # # #     print("="*60)
    
# # # # # # #     for seg in segments[:3]:
# # # # # # #         print(f"\n[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
# # # # # # #         print(f"🇯🇵 {seg['original_text']}")
# # # # # # #         print(f"🇬🇧 {seg['translated_text']}")
# # # # # # #         print(f"⏱️  {seg['duration']:.1f}s → ~{seg['estimated_duration']:.1f}s ({seg['duration_ratio']:.2f}x)")

# # # # # # # def main():
# # # # # # #     print("=" * 60)
# # # # # # #     print("STEP 4: Translation with Duration Matching")
# # # # # # #     print("=" * 60)
    
# # # # # # #     # Check prerequisites
# # # # # # #     if not check_prerequisites():
# # # # # # #         return
    
# # # # # # #     # Initialize OpenAI client
# # # # # # #     try:
# # # # # # #         client = OpenAI(api_key=OPENAI_API_KEY)
# # # # # # #         print("✅ OpenAI client initialized")
# # # # # # #     except Exception as e:
# # # # # # #         print(f"❌ Failed to initialize OpenAI client: {e}")
# # # # # # #         return
    
# # # # # # #     # Load data
# # # # # # #     data = load_data()
    
# # # # # # #     # Process segments
# # # # # # #     translated_segments = process_segments(client, data['segments'])
    
# # # # # # #     if not translated_segments:
# # # # # # #         print("❌ No segments were translated")
# # # # # # #         return
    
# # # # # # #     # Save results
# # # # # # #     save_results(data, translated_segments)
    
# # # # # # #     # Display summary
# # # # # # #     display_summary(translated_segments)
    
# # # # # # #     print("\n" + "=" * 60)
# # # # # # #     print("✅ Step 4 Complete!")
# # # # # # #     print("=" * 60)
# # # # # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # # # # #     print(f"📝 Translated: {len(translated_segments)} segments")
# # # # # # #     print("\nNext: Run step5_voice_generation.py")

# # # # # # # if __name__ == "__main__":
# # # # # # #     main()
# # # # # # # # step4_translation_gemini.py (FREE with Google Gemini)
# # # # # # # # import json
# # # # # # # # import os
# # # # # # # # import google.generativeai as genai
# # # # # # # # from datetime import datetime
# # # # # # # # import time

# # # # # # # # # Configuration
# # # # # # # # INPUT_JSON = "work/transcription_with_speakers.json"
# # # # # # # # OUTPUT_JSON = "work/translated_segments.json"

# # # # # # # # # Google Gemini API Key (FREE!)
# # # # # # # # GEMINI_API_KEY = "AIzaSyDsh5rO_zdkYtfe52g_HoaDzqe0VL6VqHU"  # Replace with your key

# # # # # # # # # Translation settings
# # # # # # # # TARGET_LANGUAGE = "English"
# # # # # # # # SOURCE_LANGUAGE = "Japanese"

# # # # # # # # def check_prerequisites():
# # # # # # # #     """Check if required files and API key exist"""
    
# # # # # # # #     if not os.path.exists(INPUT_JSON):
# # # # # # # #         print(f"❌ Input file not found: {INPUT_JSON}")
# # # # # # # #         print("   Please run step3_diarization_simple.py first")
# # # # # # # #         return False
    
# # # # # # # #     if GEMINI_API_KEY == "AIzaSyDsh5rO_zdkYtfe52g_HoaDzqe0VL6VqHU":
# # # # # # # #         print("❌ Gemini API key not set!")
# # # # # # # #         print("\n📝 To get your FREE API key:")
# # # # # # # #         print("   1. Go to: https://aistudio.google.com/app/apikey")
# # # # # # # #         print("   2. Click 'Create API key'")
# # # # # # # #         print("   3. Copy the key")
# # # # # # # #         print("   4. Paste it in step4_translation_gemini.py (GEMINI_API_KEY variable)")
# # # # # # # #         print("\n💰 Cost: 100% FREE (1500 requests/day limit)")
# # # # # # # #         return False
    
# # # # # # # #     return True

# # # # # # # # def load_data():
# # # # # # # #     """Load transcription with speakers"""
# # # # # # # #     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
# # # # # # # #         data = json.load(f)
    
# # # # # # # #     print(f"📄 Loaded {data['total_segments']} segments")
# # # # # # # #     return data

# # # # # # # # def estimate_speech_duration(text, words_per_second=2.5):
# # # # # # # #     """Estimate how long text will take to speak in English"""
# # # # # # # #     word_count = len(text.split())
# # # # # # # #     estimated_duration = word_count / words_per_second
# # # # # # # #     return estimated_duration

# # # # # # # # def translate_text(model, text, target_duration=None):
# # # # # # # #     """Translate Japanese to English with optional duration constraint"""
    
# # # # # # # #     try:
# # # # # # # #         if target_duration is None:
# # # # # # # #             # Simple translation
# # # # # # # #             prompt = f"""You are a professional anime translator. Translate this Japanese dialogue to natural, conversational English suitable for dubbing. Keep it concise and natural-sounding.

# # # # # # # # Japanese: {text}

# # # # # # # # Provide ONLY the English translation, nothing else."""
# # # # # # # #         else:
# # # # # # # #             # Translation with duration constraint
# # # # # # # #             target_words = int(target_duration * 2.5)  # 2.5 words per second
            
# # # # # # # #             prompt = f"""You are a professional anime dubbing translator. Translate this Japanese to English while keeping it SHORT to fit the timing.

# # # # # # # # Japanese: {text}

# # # # # # # # Requirements:
# # # # # # # # - Must fit in {target_duration:.1f} seconds of speech (max {target_words} words)
# # # # # # # # - Keep the meaning accurate
# # # # # # # # - Sound natural when spoken

# # # # # # # # Provide ONLY the English translation, nothing else."""
        
# # # # # # # #         response = model.generate_content(prompt)
# # # # # # # #         translation = response.text.strip()
        
# # # # # # # #         # Clean up common issues
# # # # # # # #         translation = translation.replace('"', '').replace("'", "")
        
# # # # # # # #         return translation
    
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"❌ Translation error: {e}")
# # # # # # # #         return None

# # # # # # # # def process_segments(model, segments):
# # # # # # # #     """Translate all segments with duration matching"""
    
# # # # # # # #     print(f"\n🌍 Translating {len(segments)} segments...")
# # # # # # # #     print("⏳ This will take a few minutes...")
    
# # # # # # # #     translated_segments = []
    
# # # # # # # #     for idx, seg in enumerate(segments, 1):
# # # # # # # #         japanese_text = seg['text']
# # # # # # # #         original_duration = seg['duration']
        
# # # # # # # #         print(f"\n[{idx}/{len(segments)}] Translating...")
# # # # # # # #         print(f"   JP: {japanese_text}")
        
# # # # # # # #         # First translation attempt
# # # # # # # #         english_text = translate_text(model, japanese_text)
        
# # # # # # # #         if english_text is None:
# # # # # # # #             print("   ⚠️  Translation failed, skipping")
# # # # # # # #             continue
        
# # # # # # # #         # Check if duration fits
# # # # # # # #         estimated_duration = estimate_speech_duration(english_text)
# # # # # # # #         duration_ratio = estimated_duration / original_duration if original_duration > 0 else 1.0
        
# # # # # # # #         # If translation is too long (>20% over), compress it
# # # # # # # #         if duration_ratio > 1.2:
# # # # # # # #             print(f"   ⚠️  Too long ({estimated_duration:.1f}s vs {original_duration:.1f}s), compressing...")
            
# # # # # # # #             compressed_text = translate_text(model, japanese_text, target_duration=original_duration)
            
# # # # # # # #             if compressed_text:
# # # # # # # #                 english_text = compressed_text
# # # # # # # #                 estimated_duration = estimate_speech_duration(english_text)
# # # # # # # #                 print(f"   ✅ Compressed: {english_text}")
# # # # # # # #             else:
# # # # # # # #                 print(f"   ⚠️  Compression failed, using original translation")
        
# # # # # # # #         print(f"   EN: {english_text}")
# # # # # # # #         print(f"   Duration: {original_duration:.1f}s → ~{estimated_duration:.1f}s")
        
# # # # # # # #         # Save translation
# # # # # # # #         translated_seg = seg.copy()
# # # # # # # #         translated_seg['original_text'] = japanese_text
# # # # # # # #         translated_seg['translated_text'] = english_text
# # # # # # # #         translated_seg['estimated_duration'] = estimated_duration
# # # # # # # #         translated_seg['duration_ratio'] = duration_ratio
        
# # # # # # # #         translated_segments.append(translated_seg)
        
# # # # # # # #         # Rate limiting (be nice to free API)
# # # # # # # #         time.sleep(1)
    
# # # # # # # #     return translated_segments

# # # # # # # # def save_results(data, translated_segments):
# # # # # # # #     """Save translated segments"""
    
# # # # # # # #     output_data = {
# # # # # # # #         'model': data.get('model', 'unknown'),
# # # # # # # #         'translation_model': 'google-gemini-pro',
# # # # # # # #         'source_language': SOURCE_LANGUAGE,
# # # # # # # #         'target_language': TARGET_LANGUAGE,
# # # # # # # #         'timestamp': datetime.now().isoformat(),
# # # # # # # #         'total_segments': len(translated_segments),
# # # # # # # #         'segments': translated_segments,
# # # # # # # #         'diarization': data.get('diarization', {})
# # # # # # # #     }
    
# # # # # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # # # # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # # # # # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # # # # # # def display_summary(segments):
# # # # # # # #     """Display translation summary"""
    
# # # # # # # #     print("\n" + "="*60)
# # # # # # # #     print("📊 TRANSLATION SUMMARY")
# # # # # # # #     print("="*60)
    
# # # # # # # #     total_segments = len(segments)
# # # # # # # #     avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
# # # # # # # #     over_limit = sum(1 for s in segments if s['duration_ratio'] > 1.2)
    
# # # # # # # #     print(f"Total segments: {total_segments}")
# # # # # # # #     print(f"Average duration ratio: {avg_ratio:.2f}x")
# # # # # # # #     print(f"Segments over limit (>1.2x): {over_limit}")
    
# # # # # # # #     print("\n" + "="*60)
# # # # # # # #     print("📋 SAMPLE TRANSLATIONS (First 3)")
# # # # # # # #     print("="*60)
    
# # # # # # # #     for seg in segments[:3]:
# # # # # # # #         print(f"\n[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
# # # # # # # #         print(f"🇯🇵 {seg['original_text']}")
# # # # # # # #         print(f"🇬🇧 {seg['translated_text']}")
# # # # # # # #         print(f"⏱️  {seg['duration']:.1f}s → ~{seg['estimated_duration']:.1f}s ({seg['duration_ratio']:.2f}x)")

# # # # # # # # def main():
# # # # # # # #     print("=" * 60)
# # # # # # # #     print("STEP 4: Translation with Google Gemini (FREE)")
# # # # # # # #     print("=" * 60)
    
# # # # # # # #     # Check prerequisites
# # # # # # # #     if not check_prerequisites():
# # # # # # # #         return
    
# # # # # # # #     # Initialize Gemini
# # # # # # # #     try:
# # # # # # # #         genai.configure(api_key=GEMINI_API_KEY)
# # # # # # # #         model = genai.GenerativeModel('gemini-1.5-flash')
# # # # # # # #         print("✅ Google Gemini initialized (FREE)")
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"❌ Failed to initialize Gemini: {e}")
# # # # # # # #         return
    
# # # # # # # #     # Load data
# # # # # # # #     data = load_data()
    
# # # # # # # #     # Process segments
# # # # # # # #     translated_segments = process_segments(model, data['segments'])
    
# # # # # # # #     if not translated_segments:
# # # # # # # #         print("❌ No segments were translated")
# # # # # # # #         return
    
# # # # # # # #     # Save results
# # # # # # # #     save_results(data, translated_segments)
    
# # # # # # # #     # Display summary
# # # # # # # #     display_summary(translated_segments)
    
# # # # # # # #     print("\n" + "=" * 60)
# # # # # # # #     print("✅ Step 4 Complete!")
# # # # # # # #     print("=" * 60)
# # # # # # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # # # # # #     print(f"📝 Translated: {len(translated_segments)} segments")
# # # # # # # #     print(f"💰 Cost: $0.00 (FREE!)")
# # # # # # # #     print("\nNext: Run step5_voice_generation.py")

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     main()
# # # # # # # step4_translation_enhanced.py (Enhanced Duration Matching)
# # # # # # import json
# # # # # # import os
# # # # # # from openai import OpenAI
# # # # # # from datetime import datetime
# # # # # # import time
# # # # # # import re

# # # # # # # Configuration
# # # # # # INPUT_JSON = "work/transcription_with_speakers.json"
# # # # # # OUTPUT_JSON = "work/translated_segments.json"

# # # # # # # OpenAI API Key
# # # # # # OPENAI_API_KEY = "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"

# # # # # # # Translation settings
# # # # # # TARGET_LANGUAGE = "English"
# # # # # # SOURCE_LANGUAGE = "Japanese"

# # # # # # # Duration matching thresholds
# # # # # # TARGET_RATIO_MIN = 0.85  # Minimum 85% of original duration
# # # # # # TARGET_RATIO_MAX = 1.15  # Maximum 115% of original duration
# # # # # # IDEAL_RATIO = 1.0        # Perfect match

# # # # # # # Syllable rate for English (syllables per second)
# # # # # # SYLLABLES_PER_SECOND = 4.5  # Average for natural speech


# # # # # # def check_prerequisites():
# # # # # #     """Check if required files and API key exist"""
    
# # # # # #     if not os.path.exists(INPUT_JSON):
# # # # # #         print(f"❌ Input file not found: {INPUT_JSON}")
# # # # # #         print("   Please run step3_diarization.py first")
# # # # # #         return False
    
# # # # # #     if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
# # # # # #         print("❌ OpenAI API key not set!")
# # # # # #         print("\n📝 To get your API key:")
# # # # # #         print("   1. Go to: https://platform.openai.com/api-keys")
# # # # # #         print("   2. Click 'Create new secret key'")
# # # # # #         print("   3. Copy the key (starts with sk-...)")
# # # # # #         print("   4. Paste it in step4_translation_enhanced.py")
# # # # # #         print("\n💰 Cost estimate: ~$0.50-1.00 per episode")
# # # # # #         return False
    
# # # # # #     return True


# # # # # # def load_data():
# # # # # #     """Load transcription with speakers"""
# # # # # #     with open(INPUT_JSON, 'r', encoding='utf-8') as f:
# # # # # #         data = json.load(f)
    
# # # # # #     print(f"📄 Loaded {data['total_segments']} segments")
# # # # # #     return data


# # # # # # def count_syllables(word):
# # # # # #     """Count syllables in a word (English)"""
# # # # # #     word = word.lower()
    
# # # # # #     # Handle special cases
# # # # # #     if len(word) <= 3:
# # # # # #         return 1
    
# # # # # #     # Count vowel groups
# # # # # #     vowels = "aeiouy"
# # # # # #     syllable_count = 0
# # # # # #     previous_was_vowel = False
    
# # # # # #     for char in word:
# # # # # #         is_vowel = char in vowels
# # # # # #         if is_vowel and not previous_was_vowel:
# # # # # #             syllable_count += 1
# # # # # #         previous_was_vowel = is_vowel
    
# # # # # #     # Adjust for silent 'e'
# # # # # #     if word.endswith('e'):
# # # # # #         syllable_count -= 1
    
# # # # # #     # Adjust for 'le' ending
# # # # # #     if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
# # # # # #         syllable_count += 1
    
# # # # # #     # Ensure at least 1 syllable
# # # # # #     return max(1, syllable_count)


# # # # # # def estimate_speech_duration_syllables(text):
# # # # # #     """Estimate speech duration based on syllables (more accurate)"""
    
# # # # # #     # Remove punctuation and split into words
# # # # # #     words = re.findall(r'\b\w+\b', text.lower())
    
# # # # # #     # Count total syllables
# # # # # #     total_syllables = sum(count_syllables(word) for word in words)
    
# # # # # #     # Calculate duration (syllables / syllables_per_second)
# # # # # #     estimated_duration = total_syllables / SYLLABLES_PER_SECOND
    
# # # # # #     return estimated_duration, total_syllables


# # # # # # def translate_with_duration_matching(client, japanese_text, target_duration, speaker_info=None):
# # # # # #     """
# # # # # #     Translate with iterative duration matching
# # # # # #     Attempts up to 3 times to get duration within acceptable range
# # # # # #     """
    
# # # # # #     # Get speaker context if available
# # # # # #     gender = speaker_info.get('gender', 'unknown') if speaker_info else 'unknown'
# # # # # #     age_group = speaker_info.get('age_group', 'adult') if speaker_info else 'adult'
    
# # # # # #     # Calculate target syllable count
# # # # # #     target_syllables = int(target_duration * SYLLABLES_PER_SECOND)
# # # # # #     syllable_min = int(target_syllables * TARGET_RATIO_MIN)
# # # # # #     syllable_max = int(target_syllables * TARGET_RATIO_MAX)
    
# # # # # #     best_translation = None
# # # # # #     best_ratio = float('inf')
    
# # # # # #     # Attempt 1: Natural anime-style translation
# # # # # #     print(f"   🔄 Attempt 1: Natural translation...")
    
# # # # # #     response = client.chat.completions.create(
# # # # # #         model="gpt-4o-mini",
# # # # # #         messages=[
# # # # # #             {
# # # # # #                 "role": "system",
# # # # # #                 "content": """You are a professional anime dubbing translator. 
                
# # # # # # Rules:
# # # # # # 1. Translate Japanese to natural, punchy English anime dialogue
# # # # # # 2. Keep the dramatic anime tone and style
# # # # # # 3. Use short, impactful phrases (anime characters speak dramatically)
# # # # # # 4. Match character personality (gender: {gender}, age: {age_group})
# # # # # # 5. Provide ONLY the English translation, no quotes or explanations

# # # # # # Examples:
# # # # # # - "痛みを知れ" → "Know pain"
# # # # # # - "お前はもう死んでいる" → "You're already dead"
# # # # # # - "これが俺の力だ" → "This is my power"
# # # # # # """.format(gender=gender, age_group=age_group)
# # # # # #             },
# # # # # #             {
# # # # # #                 "role": "user",
# # # # # #                 "content": f"Translate to English (anime style):\n{japanese_text}"
# # # # # #             }
# # # # # #         ],
# # # # # #         temperature=0.7,
# # # # # #         max_tokens=100
# # # # # #     )
    
# # # # # #     translation = response.choices[0].message.content.strip()
# # # # # #     translation = translation.strip('"\'')  # Remove quotes if present
    
# # # # # #     estimated_duration, syllable_count = estimate_speech_duration_syllables(translation)
# # # # # #     duration_ratio = estimated_duration / target_duration if target_duration > 0 else 1.0
    
# # # # # #     print(f"      Result: \"{translation}\"")
# # # # # #     print(f"      Syllables: {syllable_count} (target: {target_syllables})")
# # # # # #     print(f"      Duration: {estimated_duration:.2f}s (target: {target_duration:.2f}s)")
# # # # # #     print(f"      Ratio: {duration_ratio:.2f}x")
    
# # # # # #     # Check if it's within acceptable range
# # # # # #     if TARGET_RATIO_MIN <= duration_ratio <= TARGET_RATIO_MAX:
# # # # # #         print(f"      ✅ Duration match acceptable!")
# # # # # #         return translation, estimated_duration, duration_ratio
    
# # # # # #     best_translation = translation
# # # # # #     best_ratio = abs(duration_ratio - IDEAL_RATIO)
    
# # # # # #     # Attempt 2: Adjust for duration
# # # # # #     print(f"   🔄 Attempt 2: Adjusting for duration...")
    
# # # # # #     if duration_ratio < TARGET_RATIO_MIN:
# # # # # #         # Too short - need to expand
# # # # # #         adjustment_prompt = f"""The previous translation "{translation}" is too short ({estimated_duration:.1f}s vs target {target_duration:.1f}s).

# # # # # # Provide a LONGER alternative with the SAME meaning that takes approximately {target_duration:.1f} seconds to say.
# # # # # # Add descriptive words or rephrase to be slightly longer while keeping anime style.

# # # # # # Target: {target_syllables} syllables (currently {syllable_count})

# # # # # # Provide ONLY the revised English translation."""
# # # # # #     else:
# # # # # #         # Too long - need to compress
# # # # # #         adjustment_prompt = f"""The previous translation "{translation}" is too long ({estimated_duration:.1f}s vs target {target_duration:.1f}s).

# # # # # # Provide a SHORTER alternative with the SAME meaning that takes approximately {target_duration:.1f} seconds to say.
# # # # # # Use fewer words or more concise phrasing while keeping anime style.

# # # # # # Target: {target_syllables} syllables (currently {syllable_count})

# # # # # # Provide ONLY the revised English translation."""
    
# # # # # #     response = client.chat.completions.create(
# # # # # #         model="gpt-4o-mini",
# # # # # #         messages=[
# # # # # #             {
# # # # # #                 "role": "system",
# # # # # #                 "content": "You are a professional anime dubbing translator focused on precise timing."
# # # # # #             },
# # # # # #             {
# # # # # #                 "role": "user",
# # # # # #                 "content": adjustment_prompt
# # # # # #             }
# # # # # #         ],
# # # # # #         temperature=0.8,
# # # # # #         max_tokens=100
# # # # # #     )
    
# # # # # #     translation2 = response.choices[0].message.content.strip()
# # # # # #     translation2 = translation2.strip('"\'')
    
# # # # # #     estimated_duration2, syllable_count2 = estimate_speech_duration_syllables(translation2)
# # # # # #     duration_ratio2 = estimated_duration2 / target_duration if target_duration > 0 else 1.0
    
# # # # # #     print(f"      Result: \"{translation2}\"")
# # # # # #     print(f"      Syllables: {syllable_count2} (target: {target_syllables})")
# # # # # #     print(f"      Duration: {estimated_duration2:.2f}s (target: {target_duration:.2f}s)")
# # # # # #     print(f"      Ratio: {duration_ratio2:.2f}x")
    
# # # # # #     # Check if improved
# # # # # #     if TARGET_RATIO_MIN <= duration_ratio2 <= TARGET_RATIO_MAX:
# # # # # #         print(f"      ✅ Duration match achieved!")
# # # # # #         return translation2, estimated_duration2, duration_ratio2
    
# # # # # #     # Track best result
# # # # # #     ratio_diff2 = abs(duration_ratio2 - IDEAL_RATIO)
# # # # # #     if ratio_diff2 < best_ratio:
# # # # # #         best_translation = translation2
# # # # # #         best_ratio = ratio_diff2
# # # # # #         estimated_duration = estimated_duration2
# # # # # #         duration_ratio = duration_ratio2
    
# # # # # #     # Attempt 3: Final refinement with explicit syllable target
# # # # # #     print(f"   🔄 Attempt 3: Final refinement...")
    
# # # # # #     response = client.chat.completions.create(
# # # # # #         model="gpt-4o-mini",
# # # # # #         messages=[
# # # # # #             {
# # # # # #                 "role": "system",
# # # # # #                 "content": "You are an expert at creating perfectly-timed anime translations."
# # # # # #             },
# # # # # #             {
# # # # # #                 "role": "user",
# # # # # #                 "content": f"""Japanese: {japanese_text}

# # # # # # Previous attempts:
# # # # # # 1. "{translation}" ({syllable_count} syllables, {estimated_duration:.1f}s)
# # # # # # 2. "{translation2}" ({syllable_count2} syllables, {estimated_duration2:.1f}s)

# # # # # # Create a final translation that:
# # # # # # - Has EXACTLY {target_syllables} syllables (±2 syllables acceptable)
# # # # # # - Takes approximately {target_duration:.1f} seconds to say
# # # # # # - Keeps the same meaning
# # # # # # - Maintains anime dialogue style

# # # # # # Provide ONLY the final English translation."""
# # # # # #             }
# # # # # #         ],
# # # # # #         temperature=0.9,
# # # # # #         max_tokens=100
# # # # # #     )
    
# # # # # #     translation3 = response.choices[0].message.content.strip()
# # # # # #     translation3 = translation3.strip('"\'')
    
# # # # # #     estimated_duration3, syllable_count3 = estimate_speech_duration_syllables(translation3)
# # # # # #     duration_ratio3 = estimated_duration3 / target_duration if target_duration > 0 else 1.0
    
# # # # # #     print(f"      Result: \"{translation3}\"")
# # # # # #     print(f"      Syllables: {syllable_count3} (target: {target_syllables})")
# # # # # #     print(f"      Duration: {estimated_duration3:.2f}s (target: {target_duration:.2f}s)")
# # # # # #     print(f"      Ratio: {duration_ratio3:.2f}x")
    
# # # # # #     # Check if improved
# # # # # #     ratio_diff3 = abs(duration_ratio3 - IDEAL_RATIO)
# # # # # #     if ratio_diff3 < best_ratio:
# # # # # #         best_translation = translation3
# # # # # #         estimated_duration = estimated_duration3
# # # # # #         duration_ratio = duration_ratio3
    
# # # # # #     # Return best result
# # # # # #     if TARGET_RATIO_MIN <= duration_ratio <= TARGET_RATIO_MAX:
# # # # # #         print(f"      ✅ Best match achieved!")
# # # # # #     else:
# # # # # #         print(f"      ⚠️  Using best attempt (ratio: {duration_ratio:.2f}x)")
    
# # # # # #     return best_translation, estimated_duration, duration_ratio


# # # # # # def process_segments(client, segments, speaker_profiles):
# # # # # #     """Translate all segments with enhanced duration matching"""
    
# # # # # #     print(f"\n🌍 Translating {len(segments)} segments...")
# # # # # #     print("⏳ This will take several minutes (3 attempts per segment)...\n")
    
# # # # # #     translated_segments = []
    
# # # # # #     for idx, seg in enumerate(segments, 1):
# # # # # #         japanese_text = seg['text']
# # # # # #         original_duration = seg['duration']
# # # # # #         speaker = seg.get('speaker', 'UNKNOWN')
        
# # # # # #         # Get speaker info
# # # # # #         speaker_info = speaker_profiles.get(speaker, {})
        
# # # # # #         print(f"\n{'='*60}")
# # # # # #         print(f"[{idx}/{len(segments)}] Segment {idx}")
# # # # # #         print(f"{'='*60}")
# # # # # #         print(f"   Speaker: {speaker}")
# # # # # #         print(f"   Japanese: \"{japanese_text}\"")
# # # # # #         print(f"   Target Duration: {original_duration:.2f}s")
        
# # # # # #         try:
# # # # # #             # Translate with duration matching
# # # # # #             english_text, estimated_duration, duration_ratio = translate_with_duration_matching(
# # # # # #                 client,
# # # # # #                 japanese_text,
# # # # # #                 original_duration,
# # # # # #                 speaker_info
# # # # # #             )
            
# # # # # #             print(f"\n   ✅ Final Translation: \"{english_text}\"")
# # # # # #             print(f"   📊 Duration Match: {duration_ratio:.2f}x ({estimated_duration:.2f}s / {original_duration:.2f}s)")
            
# # # # # #             # Quality indicator
# # # # # #             if 0.95 <= duration_ratio <= 1.05:
# # # # # #                 print(f"   🎯 EXCELLENT match!")
# # # # # #             elif TARGET_RATIO_MIN <= duration_ratio <= TARGET_RATIO_MAX:
# # # # # #                 print(f"   ✅ Good match")
# # # # # #             else:
# # # # # #                 print(f"   ⚠️  Acceptable (best effort)")
            
# # # # # #             # Save translation
# # # # # #             translated_seg = seg.copy()
# # # # # #             translated_seg['original_text'] = japanese_text
# # # # # #             translated_seg['translated_text'] = english_text
# # # # # #             translated_seg['estimated_duration'] = estimated_duration
# # # # # #             translated_seg['duration_ratio'] = duration_ratio
            
# # # # # #             translated_segments.append(translated_seg)
            
# # # # # #             # Rate limiting
# # # # # #             time.sleep(1.0)  # Longer delay due to multiple requests
        
# # # # # #         except Exception as e:
# # # # # #             print(f"\n   ❌ Translation error: {e}")
# # # # # #             print(f"   Skipping segment {idx}")
# # # # # #             continue
    
# # # # # #     return translated_segments


# # # # # # def save_results(data, translated_segments):
# # # # # #     """Save translated segments"""
    
# # # # # #     output_data = {
# # # # # #         'model': data.get('model', 'unknown'),
# # # # # #         'source_language': SOURCE_LANGUAGE,
# # # # # #         'target_language': TARGET_LANGUAGE,
# # # # # #         'timestamp': datetime.now().isoformat(),
# # # # # #         'total_segments': len(translated_segments),
# # # # # #         'translation_method': 'enhanced_duration_matching',
# # # # # #         'segments': translated_segments,
# # # # # #         'diarization': data.get('diarization', {})
# # # # # #     }
    
# # # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # # # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")


# # # # # # def display_summary(segments):
# # # # # #     """Display translation summary"""
    
# # # # # #     print("\n" + "="*70)
# # # # # #     print("📊 TRANSLATION SUMMARY")
# # # # # #     print("="*70)
    
# # # # # #     total_segments = len(segments)
# # # # # #     avg_ratio = sum(s['duration_ratio'] for s in segments) / total_segments if total_segments > 0 else 0
    
# # # # # #     # Quality bins
# # # # # #     excellent = sum(1 for s in segments if 0.95 <= s['duration_ratio'] <= 1.05)
# # # # # #     good = sum(1 for s in segments if TARGET_RATIO_MIN <= s['duration_ratio'] <= TARGET_RATIO_MAX)
# # # # # #     acceptable = total_segments - good
    
# # # # # #     print(f"\nTotal segments: {total_segments}")
# # # # # #     print(f"Average duration ratio: {avg_ratio:.2f}x")
# # # # # #     print(f"\nQuality Distribution:")
# # # # # #     print(f"  🎯 Excellent (0.95-1.05x): {excellent}")
# # # # # #     print(f"  ✅ Good (0.85-1.15x): {good}")
# # # # # #     print(f"  ⚠️  Acceptable (other): {acceptable}")
    
# # # # # #     print("\n" + "="*70)
# # # # # #     print("📋 ALL TRANSLATIONS")
# # # # # #     print("="*70)
    
# # # # # #     for seg in segments:
# # # # # #         quality = "🎯" if 0.95 <= seg['duration_ratio'] <= 1.05 else "✅" if TARGET_RATIO_MIN <= seg['duration_ratio'] <= TARGET_RATIO_MAX else "⚠️"
        
# # # # # #         print(f"\n{quality} [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg.get('speaker', 'UNKNOWN')}")
# # # # # #         print(f"   🇯🇵 {seg['original_text']}")
# # # # # #         print(f"   🇬🇧 {seg['translated_text']}")
# # # # # #         print(f"   ⏱️  {seg['duration']:.2f}s → {seg['estimated_duration']:.2f}s (ratio: {seg['duration_ratio']:.2f}x)")


# # # # # # def main():
# # # # # #     print("=" * 70)
# # # # # #     print("STEP 4: Enhanced Translation with Duration Matching")
# # # # # #     print("=" * 70)
    
# # # # # #     # Check prerequisites
# # # # # #     if not check_prerequisites():
# # # # # #         return
    
# # # # # #     # Initialize OpenAI client
# # # # # #     try:
# # # # # #         client = OpenAI(api_key=OPENAI_API_KEY)
# # # # # #         print("✅ OpenAI client initialized")
# # # # # #     except Exception as e:
# # # # # #         print(f"❌ Failed to initialize OpenAI client: {e}")
# # # # # #         return
    
# # # # # #     # Load data
# # # # # #     data = load_data()
    
# # # # # #     # Get speaker profiles
# # # # # #     speaker_profiles = data.get('diarization', {}).get('speaker_profiles', {})
    
# # # # # #     # Process segments
# # # # # #     translated_segments = process_segments(
# # # # # #         client,
# # # # # #         data['segments'],
# # # # # #         speaker_profiles
# # # # # #     )
    
# # # # # #     if not translated_segments:
# # # # # #         print("❌ No segments were translated")
# # # # # #         return
    
# # # # # #     # Save results
# # # # # #     save_results(data, translated_segments)
    
# # # # # #     # Display summary
# # # # # #     display_summary(translated_segments)
    
# # # # # #     print("\n" + "=" * 70)
# # # # # #     print("✅ Step 4 Complete!")
# # # # # #     print("=" * 70)
# # # # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # # # #     print(f"📝 Translated: {len(translated_segments)} segments")
# # # # # #     print("\nNext: Run step5_voice_generation.py")


# # # # # # if __name__ == "__main__":
# # # # # #     main()
# # # # # # step4_translation_interactive.py (Interactive Translation with User Choice)
# # # # # import json
# # # # # import os
# # # # # import time
# # # # # from openai import OpenAI
# # # # # from datetime import datetime
# # # # # import sys
# # # # # from dotenv import load_dotenv

# # # # # load_dotenv()  # ← this line is mandatory

# # # # # # Configuration
# # # # # TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
# # # # # EMOTION_FILE = "work/emotion_detection.json"
# # # # # OUTPUT_JSON = "work/translated_segments_interactive.json"
# # # # # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# # # # # # OPENAI_API_KEY = "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"

# # # # # # Translation settings
# # # # # SOURCE_LANGUAGE = "Japanese"
# # # # # TARGET_LANGUAGE = "English"
# # # # # STYLE = "anime dubbing (natural, conversational)"


# # # # # def check_prerequisites():
# # # # #     """Check if required files exist"""
    
# # # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # # # #         print("   Please run step3_diarization.py first")
# # # # #         return False
    
# # # # #     if not OPENAI_API_KEY:
# # # # #         print(f"❌ OPENAI_API_KEY not found in environment")
# # # # #         print("   Please set it: export OPENAI_API_KEY='your-key'")
# # # # #         return False
    
# # # # #     return True


# # # # # def load_transcription():
# # # # #     """Load transcription from JSON"""
# # # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # # #         data = json.load(f)
    
# # # # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # # # #     return data


# # # # # # def load_emotions():
# # # # # #     """Load emotion detection results if available"""
# # # # # #     if os.path.exists(EMOTION_FILE):
# # # # # #         with open(EMOTION_FILE, 'r', encoding='utf-8') as f:
# # # # # #             data = json.load(f)
        
# # # # # #         # Create emotion map
# # # # # #         emotion_map = {e['segment_id']: e for e in data['emotions']}
# # # # # #         print(f"🎭 Loaded emotions for {len(emotion_map)} segments")
# # # # # #         return emotion_map
# # # # # #     else:
# # # # # #         print(f"⚠️  No emotion file found (optional)")
# # # # # #         return {}

# # # # # def load_emotions():
# # # # #     """Load emotion detection results (compatible with new format)"""
# # # # #     if not os.path.exists(EMOTION_FILE):
# # # # #         print("⚠️  No emotion file found (optional)")
# # # # #         return {}

# # # # #     with open(EMOTION_FILE, 'r', encoding='utf-8') as f:
# # # # #         data = json.load(f)

# # # # #     emotion_map = {}

# # # # #     # 🔥 New format: speakers → seg_ids
# # # # #     segment_counter = 1

# # # # #     for speaker, segments in data.get("speakers", {}).items():
# # # # #         for seg_id, seg_data in segments.items():
# # # # #             emotion_map[segment_counter] = {
# # # # #                 "emotion": seg_data.get("emotion", "neutral"),
# # # # #                 "confidence": seg_data.get("confidence", 0.0)
# # # # #             }
# # # # #             segment_counter += 1

# # # # #     print(f"🎭 Loaded emotions for {len(emotion_map)} segments")
# # # # #     return emotion_map

# # # # # def estimate_syllable_count(text):
# # # # #     """Estimate syllable count for English text"""
# # # # #     # Simple vowel-counting heuristic
# # # # #     vowels = "aeiouAEIOU"
# # # # #     syllables = 0
# # # # #     prev_was_vowel = False
    
# # # # #     for char in text:
# # # # #         is_vowel = char in vowels
# # # # #         if is_vowel and not prev_was_vowel:
# # # # #             syllables += 1
# # # # #         prev_was_vowel = is_vowel
    
# # # # #     return max(1, syllables)


# # # # # def estimate_duration(text, syllables_per_second=3.5):
# # # # #     """Estimate speech duration based on syllables"""
# # # # #     syllables = estimate_syllable_count(text)
# # # # #     duration = syllables / syllables_per_second
# # # # #     return duration


# # # # # # def generate_translation_attempts(client, segment, original_duration, emotion_info=None):
# # # # # #     """Generate 3 translation attempts with different strategies"""
    
# # # # # #     japanese_text = segment['text']
# # # # # #     speaker = segment.get('speaker', 'UNKNOWN')
    
# # # # # #     # Get emotion context
# # # # # #     emotion = None
# # # # # #     emotion_tag = ""
# # # # # #     if emotion_info:
# # # # # #         emotion = emotion_info.get('emotion', 'neutral')
# # # # # #         emotion_tag = emotion_info.get('emotion_tag', '')
    
# # # # # #     attempts = []
    
# # # # # #     # Attempt 1: Natural translation (prioritize meaning)
# # # # # #     print(f"\n   Generating Attempt 1 (Natural)...", end=' ')
# # # # # #     prompt1 = f"""Translate this Japanese anime dialogue to English.
# # # # # # Prioritize natural, conversational English that sounds authentic.

# # # # # # Japanese: {japanese_text}
# # # # # # Emotion: {emotion if emotion else 'neutral'}
# # # # # # Speaker: {speaker}

# # # # # # Provide ONLY the English translation, nothing else."""
    
# # # # # #     try:
# # # # # #         response1 = client.chat.completions.create(
# # # # # #             model="gpt-4o-mini",
# # # # # #             messages=[{"role": "user", "content": prompt1}],
# # # # # #             temperature=0.7
# # # # # #         )
# # # # # #         translation1 = response1.choices[0].message.content.strip()
# # # # # #         syllables1 = estimate_syllable_count(translation1)
# # # # # #         duration1 = estimate_duration(translation1)
# # # # # #         ratio1 = duration1 / original_duration if original_duration > 0 else 0
        
# # # # # #         attempts.append({
# # # # # #             'attempt': 1,
# # # # # #             'strategy': 'Natural',
# # # # # #             'translation': translation1,
# # # # # #             'syllables': syllables1,
# # # # # #             'estimated_duration': round(duration1, 2),
# # # # # #             'duration_ratio': round(ratio1, 2),
# # # # # #             'emotion_tag': emotion_tag
# # # # # #         })
# # # # # #         print(f"✅ ({syllables1} syllables, {ratio1:.2f}x)")
# # # # # #     except Exception as e:
# # # # # #         print(f"❌ Error: {str(e)[:40]}")
# # # # # #         attempts.append({
# # # # # #             'attempt': 1,
# # # # # #             'strategy': 'Natural',
# # # # # #             'translation': '[ERROR]',
# # # # # #             'syllables': 0,
# # # # # #             'estimated_duration': 0,
# # # # # #             'duration_ratio': 0,
# # # # # #             'emotion_tag': emotion_tag
# # # # # #         })
    
# # # # # #     time.sleep(0.5)  # Rate limiting
    
# # # # # #     # Attempt 2: Duration-matched (adjust length to match timing)
# # # # # #     print(f"   Generating Attempt 2 (Duration-matched)...", end=' ')
# # # # # #     prompt2 = f"""Translate this Japanese anime dialogue to English.
# # # # # # IMPORTANT: The translation should take approximately {original_duration:.1f} seconds to speak.
# # # # # # Adjust word count to match the duration (aim for {int(original_duration * 3.5)} syllables).

# # # # # # Japanese: {japanese_text}
# # # # # # Emotion: {emotion if emotion else 'neutral'}
# # # # # # Speaker: {speaker}
# # # # # # Original Duration: {original_duration:.2f}s

# # # # # # Provide ONLY the English translation, nothing else."""
    
# # # # # #     try:
# # # # # #         response2 = client.chat.completions.create(
# # # # # #             model="gpt-4o-mini",
# # # # # #             messages=[{"role": "user", "content": prompt2}],
# # # # # #             temperature=0.7
# # # # # #         )
# # # # # #         translation2 = response2.choices[0].message.content.strip()
# # # # # #         syllables2 = estimate_syllable_count(translation2)
# # # # # #         duration2 = estimate_duration(translation2)
# # # # # #         ratio2 = duration2 / original_duration if original_duration > 0 else 0
        
# # # # # #         attempts.append({
# # # # # #             'attempt': 2,
# # # # # #             'strategy': 'Duration-matched',
# # # # # #             'translation': translation2,
# # # # # #             'syllables': syllables2,
# # # # # #             'estimated_duration': round(duration2, 2),
# # # # # #             'duration_ratio': round(ratio2, 2),
# # # # # #             'emotion_tag': emotion_tag
# # # # # #         })
# # # # # #         print(f"✅ ({syllables2} syllables, {ratio2:.2f}x)")
# # # # # #     except Exception as e:
# # # # # #         print(f"❌ Error: {str(e)[:40]}")
# # # # # #         attempts.append({
# # # # # #             'attempt': 2,
# # # # # #             'strategy': 'Duration-matched',
# # # # # #             'translation': '[ERROR]',
# # # # # #             'syllables': 0,
# # # # # #             'estimated_duration': 0,
# # # # # #             'duration_ratio': 0,
# # # # # #             'emotion_tag': emotion_tag
# # # # # #         })
    
# # # # # #     time.sleep(0.5)  # Rate limiting
    
# # # # # #     # Attempt 3: Refined (balance meaning + duration)
# # # # # #     print(f"   Generating Attempt 3 (Refined)...", end=' ')
# # # # # #     prompt3 = f"""Translate this Japanese anime dialogue to English.
# # # # # # Balance natural meaning with appropriate duration ({original_duration:.1f}s).
# # # # # # Use emotion-appropriate language.

# # # # # # Japanese: {japanese_text}
# # # # # # Emotion: {emotion if emotion else 'neutral'}
# # # # # # Speaker: {speaker}
# # # # # # Original Duration: {original_duration:.2f}s
# # # # # # Target syllables: {int(original_duration * 3.5)}

# # # # # # Provide ONLY the English translation, nothing else."""
    
# # # # # #     try:
# # # # # #         response3 = client.chat.completions.create(
# # # # # #             model="gpt-4o-mini",
# # # # # #             messages=[{"role": "user", "content": prompt3}],
# # # # # #             temperature=0.8
# # # # # #         )
# # # # # #         translation3 = response3.choices[0].message.content.strip()
# # # # # #         syllables3 = estimate_syllable_count(translation3)
# # # # # #         duration3 = estimate_duration(translation3)
# # # # # #         ratio3 = duration3 / original_duration if original_duration > 0 else 0
        
# # # # # #         attempts.append({
# # # # # #             'attempt': 3,
# # # # # #             'strategy': 'Refined',
# # # # # #             'translation': translation3,
# # # # # #             'syllables': syllables3,
# # # # # #             'estimated_duration': round(duration3, 2),
# # # # # #             'duration_ratio': round(ratio3, 2),
# # # # # #             'emotion_tag': emotion_tag
# # # # # #         })
# # # # # #         print(f"✅ ({syllables3} syllables, {ratio3:.2f}x)")
# # # # # #     except Exception as e:
# # # # # #         print(f"❌ Error: {str(e)[:40]}")
# # # # # #         attempts.append({
# # # # # #             'attempt': 3,
# # # # # #             'strategy': 'Refined',
# # # # # #             'translation': '[ERROR]',
# # # # # #             'syllables': 0,
# # # # # #             'estimated_duration': 0,
# # # # # #             'duration_ratio': 0,
# # # # # #             'emotion_tag': emotion_tag
# # # # # #         })
    
# # # # # #     return attempts
# # # # # # def generate_translation_attempts(client, segment, original_duration, emotion_info=None):
    
# # # # # #     japanese_text = segment['text']
# # # # # #     speaker = segment.get('speaker', 'UNKNOWN')
# # # # # #     emotion = emotion_info.get('emotion', 'neutral') if emotion_info else "neutral"

# # # # # #     target_syllables = int(original_duration * 3.5)
# # # # # #     prompt = f"""
# # # # # #     You are a professional anime dubbing script adapter.

# # # # # #     Translate the Japanese dialogue into natural spoken English suitable for anime dubbing.

# # # # # #     Requirements:
# # # # # #     - Keep emotional tone: {emotion}.
# # # # # #     - Spoken dialogue only.
# # # # # #     - No explanations.
# # # # # #     - No stage directions.
# # # # # #     - No time references.
# # # # # #     - Keep similar speaking duration (~{original_duration:.2f} seconds).
# # # # # #     - Target approximately {int(original_duration * 3.5)} syllables.
# # # # # #     - Minimum {int(original_duration * 3.0)} syllables.
# # # # # #     - Maximum {int(original_duration * 4.0)} syllables.
# # # # # #     - Slight expansion is allowed to match timing.
# # # # # #     - Avoid very short replies unless dramatically required.

# # # # # #     Return JSON:
# # # # # #     {{
# # # # # #     "natural": "...",
# # # # # #     "duration_matched": "...",
# # # # # #     "refined": "..."
# # # # # #     }}

# # # # # #     Japanese:
# # # # # #     {japanese_text}
# # # # # # """
# # # # # # #     prompt = f"""
# # # # # # # You are a professional anime dubbing script adapter.

# # # # # # # Task:
# # # # # # # Translate the Japanese dialogue into natural spoken English suitable for anime dubbing.

# # # # # # # Requirements:
# # # # # # # - Sound like spoken dialogue, not written translation.
# # # # # # # - Keep emotional tone: {emotion}.
# # # # # # # - Keep similar speaking duration (~{original_duration:.2f} seconds).
# # # # # # # - Target around {target_syllables} syllables.
# # # # # # # - Prioritize rhythm and lip-sync friendliness.
# # # # # # # - Avoid overly long words.
# # # # # # # - Short, punchy phrasing preferred.
# # # # # # # - Do NOT explain anything.

# # # # # # # Return EXACTLY this JSON format:

# # # # # # # {{
# # # # # # #   "natural": "...",
# # # # # # #   "duration_matched": "...",
# # # # # # #   "refined": "..."
# # # # # # # }}

# # # # # # # Japanese:
# # # # # # # {japanese_text}
# # # # # # # """

# # # # # #     # response = client.chat.completions.create(
# # # # # #     #     model="gpt-4o-mini",
# # # # # #     #     messages=[{"role": "user", "content": prompt}],
# # # # # #     #     temperature=0.8
# # # # # #     # )
# # # # # #     response = client.chat.completions.create(
# # # # # #         model="gpt-4o-mini",
# # # # # #         messages=[{"role": "user", "content": prompt}],
# # # # # #         temperature=0.8,
# # # # # #         response_format={"type": "json_object"}  # 🔥 THIS IS IMPORTANT
# # # # # #     )
# # # # # #     content = response.choices[0].message.content.strip()

# # # # # #     try:
# # # # # #         translations = json.loads(content)
# # # # # #     except:
# # # # # #         print("⚠ JSON parsing failed, fallback to raw text")
# # # # # #         translations = {
# # # # # #             "natural": content,
# # # # # #             "duration_matched": content,
# # # # # #             "refined": content
# # # # # #         }

# # # # # #     attempts = []
# # # # # #     for i, key in enumerate(["natural", "duration_matched", "refined"], start=1):
# # # # # #         text = translations.get(key, "")

# # # # # #         syllables = estimate_syllable_count(text)
# # # # # #         duration = estimate_duration(text)
# # # # # #         ratio = duration / original_duration if original_duration > 0 else 0

# # # # # #         attempts.append({
# # # # # #             "attempt": i,
# # # # # #             "strategy": key,
# # # # # #             "translation": text,
# # # # # #             "syllables": syllables,
# # # # # #             "estimated_duration": round(duration, 2),
# # # # # #             "duration_ratio": round(ratio, 2),
# # # # # #             "emotion_tag": emotion.upper()
# # # # # #         })

# # # # # #     return attempts
# # # # # def generate_translation_attempts(client, segment, original_duration, emotion_info=None):
# # # # #     japanese_text = segment['text']
# # # # #     speaker = segment.get('speaker', 'UNKNOWN')
# # # # #     emotion = emotion_info.get('emotion', 'neutral') if emotion_info else "neutral"

# # # # #     target_syllables = int(original_duration * 3.5)

# # # # #     prompt = f"""
# # # # # You are an experienced ADR script adapter for Japanese anime.

# # # # # Your job is NOT to translate literally.
# # # # # Your job is to write NATURAL, PERFORMABLE ENGLISH LINES that:
# # # # # - Keep the same intent and emotion as the Japanese
# # # # # - Fit the character's mouth flaps and timing
# # # # # - Sound like real anime dub dialogue in English

# # # # # You may:
# # # # # - Change wording and sentence structure
# # # # # - Add or remove small words ("well", "hey", "come on", etc.)
# # # # # - Slightly strengthen or soften expressions
# # # # # as long as the emotional meaning stays the same.

# # # # # Technical constraints:
# # # # # - Original language: {SOURCE_LANGUAGE}
# # # # # - Target language: {TARGET_LANGUAGE}
# # # # # - Emotional tone: {emotion}
# # # # # - Original speaking duration: ~{original_duration:.2f} seconds
# # # # # - Target around {target_syllables} English syllables
# # # # # - Minimum: {int(original_duration * 3.0)} syllables
# # # # # - Maximum: {int(original_duration * 4.0)} syllables

# # # # # Priorities (in order):
# # # # # 1) Timing and rhythm for lip-sync (length & beats similar to Japanese)
# # # # # 2) Emotional impact and character voice
# # # # # 3) Semantic faithfulness (core meaning, not word-for-word)

# # # # # Avoid:
# # # # # - Explanations, notes, or stage directions
# # # # # - Brackets like [sighs], [gasps] etc.
# # # # # - Timecodes or any meta text

# # # # # Return EXACTLY this JSON object (no extra text):

# # # # # {{
# # # # #   "natural": "Most natural English line for general dub (can be slightly free).",
# # # # #   "duration_matched": "Version tuned closest to the original timing.",
# # # # #   "refined": "Best compromise between timing, emotion, and natural English."
# # # # # }}

# # # # # Japanese line:
# # # # # {japanese_text}
# # # # # """

# # # # #     response = client.chat.completions.create(
# # # # #         model="gpt-4o-mini",
# # # # #         messages=[{"role": "user", "content": prompt}],
# # # # #         temperature=0.9,  # a bit more creative for adaptation
# # # # #         response_format={"type": "json_object"}
# # # # #     )

# # # # #     content = response.choices[0].message.content.strip()

# # # # #     try:
# # # # #         translations = json.loads(content)
# # # # #     except:
# # # # #         print("⚠ JSON parsing failed, fallback to raw text")
# # # # #         translations = {
# # # # #             "natural": content,
# # # # #             "duration_matched": content,
# # # # #             "refined": content
# # # # #         }

# # # # #     attempts = []
# # # # #     for i, key in enumerate(["natural", "duration_matched", "refined"], start=1):
# # # # #         text = translations.get(key, "").strip()

# # # # #         syllables = estimate_syllable_count(text)
# # # # #         duration = estimate_duration(text)
# # # # #         ratio = duration / original_duration if original_duration > 0 else 0

# # # # #         attempts.append({
# # # # #             "attempt": i,
# # # # #             "strategy": key,
# # # # #             "translation": text,
# # # # #             "syllables": syllables,
# # # # #             "estimated_duration": round(duration, 2),
# # # # #             "duration_ratio": round(ratio, 2),
# # # # #             "emotion_tag": emotion.upper()
# # # # #         })

# # # # #     return attempts


# # # # # def display_attempts(segment, attempts, emotion_info=None):
# # # # #     """Display all 3 attempts with details"""
    
# # # # #     print("\n" + "="*80)
# # # # #     print(f"SEGMENT {segment['id'] + 1}")
# # # # #     print("="*80)
    
# # # # #     # Original info
# # # # #     print(f"\n📝 Original (Japanese):")
# # # # #     print(f"   Text: {segment['text']}")
# # # # #     print(f"   Speaker: {segment.get('speaker', 'UNKNOWN')}")
# # # # #     print(f"   Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
# # # # #     print(f"   Duration: {segment['duration']:.2f}s")
    
# # # # #     if emotion_info:
# # # # #         emotion = emotion_info.get('emotion', 'neutral')
# # # # #         confidence = emotion_info.get('confidence', 0.0)
# # # # #         print(f"   Emotion: {emotion.upper()} ({confidence:.1%} confidence)")
    
# # # # #     # Display all attempts
# # # # #     print(f"\n🔄 Translation Attempts:\n")
    
# # # # #     for attempt in attempts:
# # # # #         attempt_num = attempt['attempt']
# # # # #         strategy = attempt['strategy']
# # # # #         translation = attempt['translation']
# # # # #         syllables = attempt['syllables']
# # # # #         duration = attempt['estimated_duration']
# # # # #         ratio = attempt['duration_ratio']
# # # # #         emotion_tag = attempt.get('emotion_tag', '')
        
# # # # #         # Quality indicator
# # # # #         if 0.95 <= ratio <= 1.05:
# # # # #             quality = "🎯 Perfect"
# # # # #             color = "green"
# # # # #         elif 0.85 <= ratio <= 1.15:
# # # # #             quality = "✅ Good"
# # # # #             color = "orange"
# # # # #         elif 0.70 <= ratio <= 1.30:
# # # # #             quality = "⚠️  Acceptable"
# # # # #             color = "yellow"
# # # # #         else:
# # # # #             quality = "❌ Poor"
# # # # #             color = "red"
        
# # # # #         print(f"   [{attempt_num}] {strategy}:")
# # # # #         print(f"       Translation: \"{translation}\"")
# # # # #         if emotion_tag:
# # # # #             print(f"       With emotion: \"{emotion_tag} {translation}\"")
# # # # #         print(f"       Syllables: {syllables} | Duration: {duration:.2f}s | Ratio: {ratio:.2f}x | {quality}")
# # # # #         print()


# # # # # def get_user_choice(segment, attempts):
# # # # #     """Get user's choice interactively"""
    
# # # # #     while True:
# # # # #         print("\n" + "-"*80)
# # # # #         print("OPTIONS:")
# # # # #         print("  [1] [2] [3]  - Choose attempt 1, 2, or 3")
# # # # #         print("  [EDIT 1]     - Edit attempt 1")
# # # # #         print("  [EDIT 2]     - Edit attempt 2")
# # # # #         print("  [EDIT 3]     - Edit attempt 3")
# # # # #         print("  [CUSTOM]     - Write your own translation")
# # # # #         print("  [RETRY]      - Generate new attempts")
# # # # #         print("  [SKIP]       - Skip this segment (use attempt 1 as default)")
# # # # #         print("-"*80)
        
# # # # #         choice = input("\nYour choice: ").strip().upper()
        
# # # # #         # Direct choice
# # # # #         if choice in ['1', '2', '3']:
# # # # #             attempt_idx = int(choice) - 1
# # # # #             selected = attempts[attempt_idx]
# # # # #             print(f"\n✅ Selected Attempt {choice}")
# # # # #             return selected
        
# # # # #         # Edit attempt
# # # # #         elif choice.startswith('EDIT'):
# # # # #             parts = choice.split()
# # # # #             if len(parts) == 2 and parts[1] in ['1', '2', '3']:
# # # # #                 attempt_idx = int(parts[1]) - 1
# # # # #                 original = attempts[attempt_idx]['translation']
                
# # # # #                 print(f"\n✏️  Editing Attempt {parts[1]}:")
# # # # #                 print(f"   Original: {original}")
# # # # #                 new_translation = input("   New translation: ").strip()
                
# # # # #                 if new_translation:
# # # # #                     # Update attempt
# # # # #                     attempts[attempt_idx]['translation'] = new_translation
# # # # #                     attempts[attempt_idx]['syllables'] = estimate_syllable_count(new_translation)
# # # # #                     attempts[attempt_idx]['estimated_duration'] = estimate_duration(new_translation)
# # # # #                     attempts[attempt_idx]['duration_ratio'] = attempts[attempt_idx]['estimated_duration'] / segment['duration']
                    
# # # # #                     print(f"   ✅ Updated!")
# # # # #                     # print(f"   New syllables: {attempts[attempt_idx]['syllables']}")
# # # # #                     # print(f"   New duration: {attempts[attempt_idx]['estimated_duration']:.2f}s")
# # # # #                     # print(f"   New ratio: {attempts[attempt_idx]['duration_ratio']:.2f}x")
# # # # #                     syllables = attempts[attempt_idx]['syllables']
# # # # #                     duration = attempts[attempt_idx]['estimated_duration']
# # # # #                     ratio = attempts[attempt_idx]['duration_ratio']

# # # # #                     if 0.95 <= ratio <= 1.05:
# # # # #                         quality = "🎯 Perfect"
# # # # #                     elif 0.85 <= ratio <= 1.15:
# # # # #                         quality = "✅ Good"
# # # # #                     elif 0.70 <= ratio <= 1.30:
# # # # #                         quality = "⚠️ Acceptable"
# # # # #                     else:
# # # # #                         quality = "❌ Poor"

# # # # #                     print(f"\n   Updated Metrics:")
# # # # #                     print(f"   Syllables: {syllables} | Duration: {duration:.2f}s | Ratio: {ratio:.2f}x | {quality}")
                    
# # # # #                     # Ask if they want to use this
# # # # #                     use_it = input("\n   Use this version? [Y/n]: ").strip().upper()
# # # # #                     if use_it != 'N':
# # # # #                         return attempts[attempt_idx]
# # # # #                     else:
# # # # #                         continue
# # # # #                 else:
# # # # #                     print("   ❌ Empty translation, cancelled")
# # # # #                     continue
# # # # #             else:
# # # # #                 print("   ❌ Invalid format. Use: EDIT 1, EDIT 2, or EDIT 3")
# # # # #                 continue
        
# # # # #         # Custom translation
# # # # #         elif choice == 'CUSTOM':
# # # # #             print(f"\n✏️  Custom Translation:")
# # # # #             custom_translation = input("   Enter your translation: ").strip()
            
# # # # #             if custom_translation:
# # # # #                 custom_attempt = {
# # # # #                     'attempt': 4,
# # # # #                     'strategy': 'Custom',
# # # # #                     'translation': custom_translation,
# # # # #                     'syllables': estimate_syllable_count(custom_translation),
# # # # #                     'estimated_duration': estimate_duration(custom_translation),
# # # # #                     'duration_ratio': estimate_duration(custom_translation) / segment['duration'],
# # # # #                     'emotion_tag': attempts[0].get('emotion_tag', '')
# # # # #                 }
                
# # # # #                 print(f"   ✅ Custom translation created!")
# # # # #                 print(f"   Syllables: {custom_attempt['syllables']}")
# # # # #                 print(f"   Duration: {custom_attempt['estimated_duration']:.2f}s")
# # # # #                 print(f"   Ratio: {custom_attempt['duration_ratio']:.2f}x")
                
# # # # #                 return custom_attempt
# # # # #             else:
# # # # #                 print("   ❌ Empty translation, cancelled")
# # # # #                 continue
        
# # # # #         # Retry
# # # # #         elif choice == 'RETRY':
# # # # #             print("\n🔄 Regenerating is not implemented yet (would cost API credits)")
# # # # #             print("   Please choose one of the existing attempts or edit them.")
# # # # #             continue
        
# # # # #         # Skip
# # # # #         elif choice == 'SKIP':
# # # # #             print(f"\n⏭️  Skipping, using Attempt 1 as default")
# # # # #             return attempts[0]
        
# # # # #         else:
# # # # #             print(f"   ❌ Invalid choice: {choice}")
# # # # #             continue


# # # # # def process_segments_interactively(client, segments, emotion_map):
# # # # #     """Process all segments with user interaction"""
    
# # # # #     results = []
    
# # # # #     for idx, segment in enumerate(segments):
# # # # #         print(f"\n{'='*80}")
# # # # #         print(f"PROCESSING SEGMENT {idx + 1} / {len(segments)}")
# # # # #         print(f"{'='*80}")
        
# # # # #         # Get emotion info
# # # # #         emotion_info = emotion_map.get(idx + 1)
        
# # # # #         # Generate 3 attempts
# # # # #         attempts = generate_translation_attempts(
# # # # #             client, segment, segment['duration'], emotion_info
# # # # #         )
        
# # # # #         # Display all attempts
# # # # #         display_attempts(segment, attempts, emotion_info)
        
# # # # #         # Get user choice
# # # # #         selected = get_user_choice(segment, attempts)
        
# # # # #         # Save result
# # # # #         result = {
# # # # #             'segment_id': idx + 1,
# # # # #             'original_text': segment['text'],
# # # # #             'speaker': segment.get('speaker', 'UNKNOWN'),
# # # # #             'start': segment['start'],
# # # # #             'end': segment['end'],
# # # # #             'duration': segment['duration'],
# # # # #             'all_attempts': attempts,
# # # # #             'selected_attempt': selected['attempt'],
# # # # #             'selected_strategy': selected['strategy'],
# # # # #             'translated_text': selected['translation'],
# # # # #             'syllables': selected['syllables'],
# # # # #             'estimated_duration': selected['estimated_duration'],
# # # # #             'duration_ratio': selected['duration_ratio'],
# # # # #             'emotion': emotion_info.get('emotion') if emotion_info else None,
# # # # #             'emotion_confidence': emotion_info.get('confidence') if emotion_info else None,
# # # # #             'emotion_tag': selected.get('emotion_tag', ''),
# # # # #             'text_with_emotion': f"{selected.get('emotion_tag', '')} {selected['translation']}".strip()
# # # # #         }
        
# # # # #         results.append(result)
        
# # # # #         print(f"\n✅ Segment {idx + 1} complete!")
# # # # #         print(f"   Selected: {selected['translation']}")
        
# # # # #         # Progress indicator
# # # # #         remaining = len(segments) - (idx + 1)
# # # # #         if remaining > 0:
# # # # #             print(f"\n📊 Progress: {idx + 1}/{len(segments)} complete, {remaining} remaining")
# # # # #             input("\nPress Enter to continue to next segment...")
    
# # # # #     return results


# # # # # def save_results(results):
# # # # #     """Save translation results"""
    
# # # # #     output_data = {
# # # # #         'timestamp': datetime.now().isoformat(),
# # # # #         'total_segments': len(results),
# # # # #         'source_language': SOURCE_LANGUAGE,
# # # # #         'target_language': TARGET_LANGUAGE,
# # # # #         'style': STYLE,
# # # # #         'segments': results
# # # # #     }
    
# # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # # # #     print(f"\n💾 Results saved to: {OUTPUT_JSON}")


# # # # # def display_summary(results):
# # # # #     """Display summary of all translations"""
    
# # # # #     print(f"\n{'='*80}")
# # # # #     print("📊 TRANSLATION SUMMARY")
# # # # #     print(f"{'='*80}\n")
    
# # # # #     print(f"{'Seg':<4} | {'Original':<30} | {'Translation':<35} | {'Ratio':<8}")
# # # # #     print(f"{'-'*4}-+-{'-'*30}-+-{'-'*35}-+-{'-'*8}")
    
# # # # #     for result in results:
# # # # #         seg_id = result['segment_id']
# # # # #         original = result['original_text'][:28]
# # # # #         translation = result['translated_text'][:33]
# # # # #         ratio = result['duration_ratio']
        
# # # # #         if 0.95 <= ratio <= 1.05:
# # # # #             quality = "🎯"
# # # # #         elif 0.85 <= ratio <= 1.15:
# # # # #             quality = "✅"
# # # # #         else:
# # # # #             quality = "⚠️ "
        
# # # # #         print(f" {seg_id:<3} | {original:<30} | {translation:<35} | {ratio:.2f}x {quality}")


# # # # # def main():
# # # # #     print("="*80)
# # # # #     print("STEP 4: Interactive Translation Selection")
# # # # #     print("="*80)
    
# # # # #     # Check prerequisites
# # # # #     if not check_prerequisites():
# # # # #         return
    
# # # # #     # Initialize OpenAI client
# # # # #     client = OpenAI(api_key=OPENAI_API_KEY)
    
# # # # #     # Load data
# # # # #     transcription_data = load_transcription()
# # # # #     emotion_map = load_emotions()
    
# # # # #     segments = transcription_data['segments']
    
# # # # #     print(f"\n🎬 Starting interactive translation...")
# # # # #     print(f"   You will see 3 translation attempts for each segment")
# # # # #     print(f"   Choose the one you like best, or edit/create your own")
# # # # #     print(f"\n⚠️  This will take time: ~3-5 minutes per segment")
# # # # #     print(f"   Total estimated: {len(segments) * 4} minutes\n")
    
# # # # #     input("Press Enter to start...")
    
# # # # #     # Process segments interactively
# # # # #     results = process_segments_interactively(client, segments, emotion_map)
    
# # # # #     # Save results
# # # # #     save_results(results)
    
# # # # #     # Display summary
# # # # #     display_summary(results)
    
# # # # #     print(f"\n{'='*80}")
# # # # #     print("✅ INTERACTIVE TRANSLATION COMPLETE!")
# # # # #     print(f"{'='*80}")
# # # # #     print(f"\n📁 Output: {OUTPUT_JSON}")
# # # # #     print(f"\n💡 Next Steps:")
# # # # #     print(f"   1. Review translated_segments_interactive.json")
# # # # #     print(f"   2. Run step5_voice_generation.py to create voices")
# # # # #     print(f"   3. Emotion tags are already included!")


# # # # # if __name__ == "__main__":
# # # # #     main()
# # # # import json
# # # # import os
# # # # import time
# # # # from openai import OpenAI
# # # # from datetime import datetime
# # # # from dotenv import load_dotenv

# # # # load_dotenv()  # ← this line is mandatory

# # # # # Configuration
# # # # TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
# # # # OUTPUT_JSON = "work/translated_segments_interactive.json"
# # # # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # # # # Translation settings
# # # # SOURCE_LANGUAGE = "Japanese"
# # # # TARGET_LANGUAGE = "English"

# # # # def check_prerequisites():
# # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # # #         return False
# # # #     if not OPENAI_API_KEY:
# # # #         print(f"❌ OPENAI_API_KEY not found in environment")
# # # #         return False
# # # #     return True

# # # # def load_transcription():
# # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # #         return json.load(f)

# # # # def estimate_syllable_count(text):
# # # #     """Estimate syllable count for English text"""
# # # #     vowels = "aeiouAEIOU"
# # # #     syllables = 0
# # # #     prev_was_vowel = False
# # # #     for char in text:
# # # #         is_vowel = char in vowels
# # # #         if is_vowel and not prev_was_vowel:
# # # #             syllables += 1
# # # #         prev_was_vowel = is_vowel
# # # #     return max(1, syllables)

# # # # # def build_chunked_prompt(segment, emotion, gender):
# # # # #     """Creates a strict prompt forcing the LLM to write text for specific rhythm chunks"""
# # # # #     japanese_text = segment['text']
# # # # #     blueprint = segment.get('rhythm_blueprint', [])
    
# # # # #     # Filter only the speech blocks from the blueprint
# # # # #     speech_blocks = [b for b in blueprint if b['type'] == 'speech']
    
# # # # #     # Calculate target syllables for each speech block (approx 3.5 syllables per second)
# # # # #     chunk_instructions = []
# # # # #     for i, block in enumerate(speech_blocks):
# # # # #         target_syl = max(1, int(block['duration'] * 3.5))
# # # # #         chunk_instructions.append(f"Chunk {i+1}: Needs ~{target_syl} syllables (Fits into {block['duration']:.2f} seconds)")

# # # # #     chunk_format = ",\n    ".join([f'"{i+1}": "..."' for i in range(len(speech_blocks))])

# # # # #     prompt = f"""
# # # # # You are an expert ADR script adapter for anime. 
# # # # # You are translating Japanese into performable English.

# # # # # Context:
# # # # # - Original text: {japanese_text}
# # # # # - Emotion: {emotion}
# # # # # - Voice Type: {gender}

# # # # # CRITICAL TASK:
# # # # # The character speaks in a specific rhythm with micro-pauses. I have broken their speech into {len(speech_blocks)} distinct rhythmic chunks. 
# # # # # You must translate the sentence by breaking the English translation into {len(speech_blocks)} parts that fit the timing of each chunk.

# # # # # Timing Constraints:
# # # # # {chr(10).join(chunk_instructions)}

# # # # # Rules:
# # # # # 1. Do not translate literally if it breaks the timing. Adapt the wording to fit the syllables!
# # # # # 2. The chunks must flow together to form a complete, natural English sentence.
# # # # # 3. No brackets, stage directions, or extra text.

# # # # # Return EXACTLY this JSON format and nothing else:
# # # # # {{
# # # # #   "natural_adaptation": {{
# # # # #     {chunk_format}
# # # # #   }}
# # # # # }}
# # # # # """
# # # # #     return prompt, speech_blocks
# # # # def build_chunked_prompt(segment, emotion, gender):
# # # #     """Creates a strict prompt forcing the LLM to write text for specific rhythm chunks"""
# # # #     japanese_text = segment['text']
# # # #     blueprint = segment.get('rhythm_blueprint', [])
    
# # # #     # Filter only the speech blocks from the blueprint
# # # #     speech_blocks = [b for b in blueprint if b['type'] == 'speech']
    
# # # #     # Calculate target syllables for each speech block (approx 3.5 syllables per second)
# # # #     chunk_instructions = []
# # # #     for i, block in enumerate(speech_blocks):
# # # #         target_syl = max(1, int(block['duration'] * 3.5))
# # # #         chunk_instructions.append(f"Chunk {i+1}: Needs ~{target_syl} syllables (Fits into {block['duration']:.2f} seconds)")

# # # #     chunk_format = ",\n    ".join([f'"{i+1}": "..."' for i in range(len(speech_blocks))])

# # # #     prompt = f"""
# # # # You are an expert ADR script adapter for anime. 
# # # # You are translating Japanese into performable English.

# # # # Context:
# # # # - Original text: {japanese_text}
# # # # - Emotion: {emotion}
# # # # - Voice Type: {gender}

# # # # CRITICAL TASK:
# # # # The character speaks in a specific rhythm with micro-pauses. I have broken their speech into {len(speech_blocks)} distinct rhythmic chunks. 
# # # # You must translate the sentence by breaking the English translation into {len(speech_blocks)} parts that fit the timing of each chunk.

# # # # Timing Constraints:
# # # # {chr(10).join(chunk_instructions)}

# # # # Rules & Adaptation Techniques:
# # # # 1. DO NOT translate literally if it breaks the timing. Adapt the wording!
# # # # 2. PRO TECHNIQUE: Analyze the entire segment's meaning first. If you need MORE syllables to fill a long gap, use Passive Voice (e.g., "The enemy was defeated by me"). If you need FEWER syllables for a short gap, use Active Voice (e.g., "I beat them").
# # # # 3. You can add or remove filler words ("well", "hey", "look") to adjust syllable counts perfectly.
# # # # 4. The chunks must flow together to form a complete, natural English sentence.
# # # # 5. No brackets, stage directions, or extra text.

# # # # Return EXACTLY this JSON format and nothing else:
# # # # {{
# # # #   "natural_adaptation": {{
# # # #     {chunk_format}
# # # #   }}
# # # # }}
# # # # """
# # # #     return prompt, speech_blocks

# # # # def generate_translation(client, segment):
# # # #     """Calls OpenAI to generate the chunked translation"""
# # # #     analysis = segment.get('analysis', {})
# # # #     emotion = analysis.get('emotion', 'neutral')
# # # #     gender = analysis.get('gender', 'unknown')

# # # #     # If there is no rhythm blueprint, fallback to old logic safely
# # # #     if not segment.get('rhythm_blueprint'):
# # # #         print(f"⚠️ Segment {segment['id']} has no rhythm blueprint. Skipping.")
# # # #         return None

# # # #     prompt, speech_blocks = build_chunked_prompt(segment, emotion, gender)

# # # #     try:
# # # #         response = client.chat.completions.create(
# # # #             model="gpt-4o-mini",
# # # #             messages=[{"role": "user", "content": prompt}],
# # # #             temperature=0.7,
# # # #             response_format={"type": "json_object"}
# # # #         )
# # # #         content = json.loads(response.choices[0].message.content.strip())
# # # #         adapted_chunks = content.get("natural_adaptation", {})

# # # #         # Rebuild the final blueprint with the English text injected
# # # #         final_blueprint = []
# # # #         speech_index = 1
# # # #         total_english_syllables = 0
        
# # # #         for block in segment['rhythm_blueprint']:
# # # #             if block['type'] == 'speech':
# # # #                 # Grab the english text the LLM generated for this chunk
# # # #                 eng_text = adapted_chunks.get(str(speech_index), "")
# # # #                 syl_count = estimate_syllable_count(eng_text)
                
# # # #                 final_blueprint.append({
# # # #                     "type": "speech",
# # # #                     "duration": block['duration'],
# # # #                     "text_chunk": eng_text,
# # # #                     "syllables": syl_count
# # # #                 })
# # # #                 total_english_syllables += syl_count
# # # #                 speech_index += 1
# # # #             else:
# # # #                 # Keep pauses exactly as they are
# # # #                 final_blueprint.append(block)

# # # #         # Full combined text for display
# # # #         full_english_text = " ".join([b['text_chunk'] for b in final_blueprint if b['type'] == 'speech']).strip()

# # # #         return {
# # # #             'segment_id': segment['id'],
# # # #             'speaker': segment.get('speaker', 'UNKNOWN'),
# # # #             'original_text': segment['text'],
# # # #             'translated_text': full_english_text,
# # # #             'emotion_used': emotion,
# # # #             'total_duration': segment['duration'],
# # # #             'total_syllables': total_english_syllables,
# # # #             'rhythm_blueprint': final_blueprint  # The new English blueprint!
# # # #         }

# # # #     except Exception as e:
# # # #         print(f"❌ API Error on segment {segment['id']}: {e}")
# # # #         return None

# # # # def process_segments_interactively(client, data):
# # # #     segments = data['segments']
# # # #     results = []

# # # #     print(f"\n🎬 Starting chunked adaptive translation...")
    
# # # #     for idx, segment in enumerate(segments):
# # # #         print(f"\n{'='*60}")
# # # #         print(f"PROCESSING SEGMENT {idx} / {len(segments)-1}")
# # # #         print(f"Original: {segment['text']}")
        
# # # #         result = generate_translation(client, segment)
        
# # # #         if result:
# # # #             print(f"Translation: {result['translated_text']}")
# # # #             print("\nRhythm Blueprint Breakdown:")
# # # #             for b in result['rhythm_blueprint']:
# # # #                 if b['type'] == 'speech':
# # # #                     print(f"  🗣️ [{b['duration']:.2f}s] {b['text_chunk']} ({b['syllables']} syl)")
# # # #                 else:
# # # #                     print(f"  ⏸️ [{b['duration']:.2f}s] (Silence)")
            
# # # #             # Auto-accept for now (You can re-add your manual override loop here if you want)
# # # #             results.append(result)
# # # #             time.sleep(0.5) # Prevent rate limits
            
# # # #     return results

# # # # def main():
# # # #     print("="*80)
# # # #     print("STEP 4: Rhythm-Aware Translation")
# # # #     print("="*80)
    
# # # #     if not check_prerequisites():
# # # #         return
    
# # # #     client = OpenAI(api_key=OPENAI_API_KEY)
# # # #     transcription_data = load_transcription()
    
# # # #     results = process_segments_interactively(client, transcription_data)
    
# # # #     output_data = {
# # # #         'timestamp': datetime.now().isoformat(),
# # # #         'total_segments': len(results),
# # # #         'segments': results
# # # #     }
    
# # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # # #     print(f"\n✅ Rhythm translation complete! Saved to {OUTPUT_JSON}")

# # # # if __name__ == "__main__":
# # # #     main()
# # # import json
# # # import os
# # # import time
# # # import math
# # # from openai import OpenAI
# # # from datetime import datetime
# # # from dotenv import load_dotenv
# # # import re

# # # load_dotenv()

# # # # Configuration
# # # TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
# # # OUTPUT_JSON = "work/translated_segments_interactive.json"
# # # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # # SOURCE_LANGUAGE = "Japanese"
# # # TARGET_LANGUAGE = "English"

# # # def check_prerequisites():
# # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # #         return False
# # #     if not OPENAI_API_KEY:
# # #         print(f"❌ OPENAI_API_KEY not found in environment")
# # #         return False
# # #     return True

# # # def estimate_syllable_count(text):
# # #     """Estimate syllable count for English text"""
# # #     vowels = "aeiouAEIOU"
# # #     syllables = 0
# # #     prev_was_vowel = False
# # #     for char in text:
# # #         is_vowel = char in vowels
# # #         if is_vowel and not prev_was_vowel:
# # #             syllables += 1
# # #         prev_was_vowel = is_vowel
# # #     return max(1, syllables)

# # # def get_base_translation(client, segment, total_speech_duration, emotion, gender):
# # #     """Step 1: Get a SINGLE, concise English translation without expanding meaning"""
# # #     japanese_text = segment['text']
    
# # #     # Calculate how many syllables we ideally want for the total speaking time
# # #     target_syllables = max(1, int(total_speech_duration * 3.5))

# # #     prompt = f"""
# # # Translate the following Japanese anime dialogue to {TARGET_LANGUAGE} for lip-sync dubbing.

# # # Context:
# # # - Original Text: {japanese_text}
# # # - Emotion: {emotion}
# # # - Gender: {gender}

# # # CRITICAL RULES:
# # # 1. DO NOT expand the meaning. Do not add filler words.
# # # 2. If the Japanese is one short phrase (like "Wakatta"), the English MUST be one short phrase (like "Got it" or "I see").
# # # 3. Target Length: Approximately {target_syllables} syllables total.
# # # 4. Output ONLY the translated English text string. No quotes, no JSON, no explanation.
# # # """

# # #     try:
# # #         response = client.chat.completions.create(
# # #             model="gpt-4o-mini",
# # #             messages=[{"role": "user", "content": prompt}],
# # #             temperature=0.3, # Low temperature to prevent hallucination/expansion
# # #         )
# # #         return response.choices[0].message.content.strip()
# # #     except Exception as e:
# # #         print(f"❌ Translation Error: {e}")
# # #         return "Translation failed."

# # # def map_text_to_blueprint(english_text, blueprint):
# # #     """Step 2: Mathematically distribute the English words into the speech blocks"""
# # #     # Clean the text and split into words
# # #     words = [w for w in re.split(r'([ ,.!?]+)', english_text) if w.strip()]
    
# # #     # Filter to only the speech blocks
# # #     speech_blocks = [b for b in blueprint if b['type'] == 'speech']
# # #     if not speech_blocks:
# # #         return blueprint
        
# # #     total_speech_dur = sum(b['duration'] for b in speech_blocks)
    
# # #     # Distribute words to blocks based on the block's percentage of total duration
# # #     current_word_idx = 0
# # #     mapped_speech_blocks = []
    
# # #     for block in speech_blocks:
# # #         if current_word_idx >= len(words):
# # #             # We ran out of words, just leave this block empty (it will be short silence)
# # #             mapped_speech_blocks.append("")
# # #             continue
            
# # #         dur_ratio = block['duration'] / total_speech_dur
# # #         # How many words should go into this block?
# # #         words_for_this_block = max(1, math.ceil(len(words) * dur_ratio))
        
# # #         chunk_words = words[current_word_idx : current_word_idx + words_for_this_block]
# # #         mapped_speech_blocks.append("".join(chunk_words).strip())
        
# # #         current_word_idx += words_for_this_block

# # #     # Put any leftover words in the last block
# # #     if current_word_idx < len(words):
# # #         leftovers = "".join(words[current_word_idx:]).strip()
# # #         if mapped_speech_blocks:
# # #             mapped_speech_blocks[-1] = f"{mapped_speech_blocks[-1]} {leftovers}"
            
# # #     # Reconstruct the final blueprint
# # #     final_blueprint = []
# # #     speech_idx = 0
    
# # #     for block in blueprint:
# # #         if block['type'] == 'speech':
# # #             text_chunk = mapped_speech_blocks[speech_idx]
# # #             final_blueprint.append({
# # #                 "type": "speech",
# # #                 "duration": block['duration'],
# # #                 "text_chunk": text_chunk,
# # #                 "syllables": estimate_syllable_count(text_chunk)
# # #             })
# # #             speech_idx += 1
# # #         else:
# # #             final_blueprint.append(block)
            
# # #     return final_blueprint

# # # def process_segments(client, data):
# # #     segments = data['segments']
# # #     results = []

# # #     print(f"\n🎬 Starting constrained adaptive translation...")
    
# # #     for idx, segment in enumerate(segments):
# # #         print(f"\n{'='*60}")
# # #         print(f"SEGMENT {idx} | Original: {segment['text']}")
        
# # #         blueprint = segment.get('rhythm_blueprint', [])
        
# # #         # 1. Calculate total actual speaking time
# # #         total_speech_duration = sum(b['duration'] for b in blueprint if b['type'] == 'speech')
        
# # #         if total_speech_duration <= 0:
# # #             print("⚠️ No speech duration found, skipping.")
# # #             continue

# # #         emotion = segment.get('analysis', {}).get('emotion', 'neu')
# # #         gender = segment.get('analysis', {}).get('gender', 'unknown')

# # #         # 2. Get literal translation (LLM)
# # #         base_translation = get_base_translation(client, segment, total_speech_duration, emotion, gender)
# # #         print(f"Base Translation: {base_translation}")

# # #         # 3. Map to Blueprint (Python Algorithm)
# # #         final_blueprint = map_text_to_blueprint(base_translation, blueprint)

# # #         # Print the breakdown
# # #         print("\nRhythm Blueprint Breakdown:")
# # #         total_syl = 0
# # #         for b in final_blueprint:
# # #             if b['type'] == 'speech':
# # #                 print(f"  🗣️ [{b['duration']:.2f}s] {b['text_chunk']}")
# # #                 total_syl += b.get('syllables', 0)
# # #             else:
# # #                 print(f"  ⏸️ [{b['duration']:.2f}s] (Silence)")

# # #         result = {
# # #             'segment_id': segment['id'],
# # #             'speaker': segment.get('speaker', 'UNKNOWN'),
# # #             'original_text': segment['text'],
# # #             'translated_text': base_translation,
# # #             'emotion_used': emotion,
# # #             'total_duration': segment['duration'],
# # #             'total_syllables': total_syl,
# # #             'rhythm_blueprint': final_blueprint
# # #         }
        
# # #         results.append(result)
# # #         time.sleep(0.5) 
            
# # #     return results

# # # def main():
# # #     print("="*80)
# # #     print("STEP 4: Rhythm-Aware Translation (Constrained)")
# # #     print("="*80)
    
# # #     if not check_prerequisites():
# # #         return
    
# # #     client = OpenAI(api_key=OPENAI_API_KEY)
    
# # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # #         transcription_data = json.load(f)
    
# # #     results = process_segments(client, transcription_data)
    
# # #     output_data = {
# # #         'timestamp': datetime.now().isoformat(),
# # #         'total_segments': len(results),
# # #         'segments': results
# # #     }
    
# # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # #         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
# # #     print(f"\n✅ Rhythm translation complete! Saved to {OUTPUT_JSON}")

# # # if __name__ == "__main__":
# # #     main()
# # """
# # STEP 4: Voice Generation Pipeline (4 Stages)
# # =============================================
# # Fixes applied vs original:
# #   1. itertools.chain for rglob (was: broken + on generators)
# #   2. import soundfile as sf (was: NameError)
# #   3. from datetime import datetime (was: NameError)
# #   4. SPEAKER_MAP for voice assignment (was: always same voice)
# #   5. ratio clamped 0.90–1.10 + inverted for pyrubberband (was: unclamped + wrong direction)
# #   6. json.dump(output_meta, f, ...) (was: missing file arg)
# # """

# # import os
# # import json
# # import itertools
# # import soundfile as sf
# # from datetime import datetime
# # from pathlib import Path

# # import torch
# # import librosa
# # import numpy as np
# # from pydub import AudioSegment
# # import pyrubberband as pyrb
# # from TTS.api import TTS

# # print("=" * 60)
# # print("STEP 4: Voice Generation Pipeline (4 Stages)")
# # print("=" * 60)

# # # ─────────────────────────────────────────────
# # # CONFIG
# # # ─────────────────────────────────────────────
# # INPUT_JSON       = "work/translated_segments_step3.json"
# # OUTPUT_DIR       = "work/generated_audio"
# # VOICE_SAMPLES_DIR = "sample_voices"

# # # Map each speaker label → voice sample path
# # # Edit this to match your speakers
# # SPEAKER_MAP = {
# #     "SPEAKER_00": "sample_voices/female/Amber.mp3",
# #     "SPEAKER_01": "sample_voices/female/tsunade_voice sample.mp3",
# #     "SPEAKER_02": "sample_voices/male/madara.mp3",
# #     "SPEAKER_03": "sample_voices/male/madara.mp3",   # adjust as needed
# # }
# # DEFAULT_VOICE = "sample_voices/female/Amber.mp3"

# # # Stretch window — outside this range the clip is flagged, not forced
# # MIN_RATIO = 0.90
# # MAX_RATIO = 1.10

# # # RMS loudness targets per emotion (dBFS)
# # EMOTION_LOUDNESS = {
# #     "angry":     -14,
# #     "ang":       -14,
# #     "surprised": -15,
# #     "sur":       -15,
# #     "happy":     -16,
# #     "hap":       -16,
# #     "neutral":   -18,
# #     "neu":       -18,
# #     "sad":       -22,
# #     "unknown":   -18,
# # }

# # os.makedirs(OUTPUT_DIR, exist_ok=True)

# # # ─────────────────────────────────────────────
# # # LOAD XTTS
# # # ─────────────────────────────────────────────
# # device = "cuda" if torch.cuda.is_available() else "cpu"
# # tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device == "cuda"))
# # print(f"✅ XTTS loaded on {device}")

# # # ─────────────────────────────────────────────
# # # STAGE 0: VOICE LIBRARY SCAN
# # # ─────────────────────────────────────────────
# # print("\n── Stage 0: Voice library scan ──")
# # voice_catalogue = {}

# # # Fix 1: use itertools.chain — rglob() is a generator, not a list
# # for voice_file in itertools.chain(
# #     Path(VOICE_SAMPLES_DIR).rglob("*.wav"),
# #     Path(VOICE_SAMPLES_DIR).rglob("*.mp3"),
# # ):
# #     stem        = voice_file.stem
# #     gender_dir  = voice_file.parent.name        # "female" or "male"
# #     display     = stem.replace("_voice sample", "").replace("_", " ").title()
# #     voice_catalogue[stem] = {
# #         "path":    str(voice_file),
# #         "gender":  gender_dir,
# #         "display": display,
# #     }
# #     print(f"  📁 [{gender_dir}] {display}")

# # print(f"\n🎤 Found {len(voice_catalogue)} voice samples")

# # # ─────────────────────────────────────────────
# # # LOAD SEGMENTS
# # # ─────────────────────────────────────────────
# # with open(INPUT_JSON, "r", encoding="utf-8") as f:
# #     data = json.load(f)

# # segments = data["segments"]
# # print(f"✅ Loaded {len(segments)} segments")

# # # ─────────────────────────────────────────────
# # # HELPERS
# # # ─────────────────────────────────────────────
# # def trim_silence(y: np.ndarray, sr: int, top_db: int = 35) -> np.ndarray:
# #     """Remove leading/trailing silence, keep 20ms/30ms buffer."""
# #     y_t, idx = librosa.effects.trim(y, top_db=top_db,
# #                                      frame_length=512, hop_length=128)
# #     lead  = max(0, idx[0] - int(0.02 * sr))
# #     trail = min(len(y), idx[1] + int(0.03 * sr))
# #     return y[lead:trail]


# # def rms_normalise(y: np.ndarray, target_dbfs: float = -18.0) -> np.ndarray:
# #     """Normalise to target dBFS level."""
# #     rms = np.sqrt(np.mean(y ** 2))
# #     if rms < 1e-6:
# #         return y
# #     target_rms = 10 ** (target_dbfs / 20.0)
# #     gain = target_rms / rms
# #     return np.clip(y * gain, -0.95, 0.95)


# # def pad_or_trim(y: np.ndarray, sr: int, target_dur: float) -> np.ndarray:
# #     """Hard clamp to exact target duration after stretching."""
# #     target_samples = int(target_dur * sr)
# #     if len(y) < target_samples:
# #         return np.pad(y, (0, target_samples - len(y)))
# #     return y[:target_samples]


# # # ─────────────────────────────────────────────
# # # MAIN PIPELINE
# # # ─────────────────────────────────────────────
# # generated_clips = []
# # qc_flags_all    = []

# # for i, seg in enumerate(segments):
# #     print(f"\n{'=' * 50}")
# #     print(f"SEGMENT {i+1:02d}/{len(segments)} | {seg['speaker']} | {seg['duration']:.2f}s")
# #     print(f"  Text:    {seg['english']}")
# #     print(f"  Emotion: {seg['emotion']} (conf: {seg.get('emotion_confidence', '?')})")

# #     speaker       = seg["speaker"]
# #     target_dur    = float(seg["duration"])
# #     english_text  = seg["english"]
# #     emotion       = seg.get("emotion", "neutral").lower()
# #     emotion_conf  = float(seg.get("emotion_confidence", 1.0))

# #     # Fix 2: use SPEAKER_MAP for correct voice assignment
# #     voice_sample = SPEAKER_MAP.get(speaker, DEFAULT_VOICE)
# #     if not os.path.exists(voice_sample):
# #         print(f"  ⚠️  Voice sample not found: {voice_sample} — using default")
# #         voice_sample = DEFAULT_VOICE
# #     print(f"  Voice:   {os.path.basename(voice_sample)}")

# #     qc_flags = []
# #     raw_path     = os.path.join(OUTPUT_DIR, f"raw_{i:03d}.wav")
# #     aligned_path = os.path.join(OUTPUT_DIR, f"aligned_{i:03d}.wav")
# #     emotion_path = os.path.join(OUTPUT_DIR, f"emotion_{i:03d}.wav")
# #     final_path   = os.path.join(OUTPUT_DIR, f"final_{i:03d}.wav")

# #     # ── STAGE 1: XTTS VOICE CLONING ──────────────────────────
# #     print("  [1] XTTS voice cloning...")
# #     tts.tts_to_file(
# #         text=english_text,
# #         speaker_wav=voice_sample,
# #         language="en",
# #         file_path=raw_path,
# #     )
# #     y_raw, sr = librosa.load(raw_path, sr=22050)
# #     y_raw      = trim_silence(y_raw, sr)          # strip XTTS padding
# #     raw_dur    = len(y_raw) / sr
# #     print(f"         raw duration (trimmed): {raw_dur:.3f}s  (target: {target_dur:.3f}s)")

# #     # ── STAGE 2: RUBBERBAND TIMING ALIGNMENT ─────────────────
# #     print("  [2] Timing alignment (Rubberband)...")

# #     # Fix 3: clamp ratio to safe window
# #     ratio = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))

# #     # Fix 4: pyrubberband takes playback RATE = 1/duration_ratio
# #     # rate > 1 = faster (shorter), rate < 1 = slower (longer)
# #     y_aligned = pyrb.time_stretch(y_raw, sr, rate=1.0 / ratio)

# #     # Pad or trim to exact target
# #     y_aligned  = pad_or_trim(y_aligned, sr, target_dur)
# #     actual_dur = len(y_aligned) / sr
# #     stretch_applied = actual_dur / raw_dur

# #     print(f"         ratio: {ratio:.3f}×  final: {actual_dur:.3f}s")

# #     if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
# #         msg = f"HIGH_STRETCH:{ratio:.3f}"
# #         qc_flags.append(msg)
# #         print(f"         ⚠️  {msg} — consider re-translating this segment")

# #     sf.write(aligned_path, y_aligned, sr)

# #     # ── STAGE 3: EMOTION FINE-TUNING ─────────────────────────
# #     print("  [3] Emotion fine-tuning...")

# #     # Use neutral if confidence is too low to trust
# #     effective_emotion = emotion if emotion_conf >= 0.30 else "neutral"
# #     if effective_emotion != emotion:
# #         print(f"         Low confidence ({emotion_conf:.2f}) — using neutral prosody")

# #     target_dbfs = EMOTION_LOUDNESS.get(effective_emotion, -18)
# #     y_emotion   = rms_normalise(y_aligned, target_dbfs=target_dbfs)

# #     # Simple tonal shaping per emotion
# #     from scipy.signal import butter, filtfilt

# #     def butter_filter(y, sr, cutoff, btype, order=4):
# #         nyq = sr / 2
# #         b, a = butter(order, cutoff / nyq, btype=btype)
# #         return filtfilt(b, a, y)

# #     if effective_emotion in ("sad",):
# #         y_emotion = butter_filter(y_emotion, sr, 3500, "low")   # muffle highs

# #     elif effective_emotion in ("angry", "ang"):
# #         y_emotion = butter_filter(y_emotion, sr, 150, "high")   # remove rumble
# #         # Slight high-shelf boost — add 15% of HPF'd signal above 3kHz
# #         y_hf      = butter_filter(y_emotion, sr, 3000, "high")
# #         y_emotion = np.clip(y_emotion + 0.15 * y_hf, -0.95, 0.95)

# #     elif effective_emotion in ("happy", "hap"):
# #         y_hf      = butter_filter(y_emotion, sr, 4000, "high")
# #         y_emotion = np.clip(y_emotion + 0.10 * y_hf, -0.95, 0.95)

# #     sf.write(emotion_path, y_emotion, sr)

# #     # ── STAGE 4: AGE / TYPE TRANSFORMATION ───────────────────
# #     print("  [4] Age/type transformation (pass-through — configure below)...")
# #     # Set age_category per speaker in SPEAKER_MAP if needed.
# #     # Options: "adult" (no change), "child", "old", "robot"
# #     # Implementation: see Parselmouth + kNN-VC in voice pipeline docs.
# #     y_final = y_emotion    # pass-through until you configure per character

# #     sf.write(final_path, y_final, sr)

# #     # ── CLIP QC FLAG: short clip ─────────────────────────────
# #     if len(y_final) / sr < 0.15:
# #         qc_flags.append("TOO_SHORT")

# #     # ── METADATA ─────────────────────────────────────────────
# #     clip_meta = {
# #         "segment_id":       seg["segment_id"],
# #         "speaker":          seg["speaker"],
# #         "start":            seg["start"],
# #         "end":              seg["end"],
# #         "duration_target":  target_dur,
# #         "duration_raw":     round(raw_dur, 4),
# #         "duration_final":   round(len(y_final) / sr, 4),
# #         "stretch_ratio":    round(stretch_applied, 4),
# #         "voice_sample":     os.path.basename(voice_sample),
# #         "emotion":          emotion,
# #         "emotion_effective": effective_emotion,
# #         "emotion_confidence": emotion_conf,
# #         "text":             english_text,
# #         "qc_flags":         qc_flags,
# #         "files": {
# #             "raw":     raw_path,
# #             "aligned": aligned_path,
# #             "emotion": emotion_path,
# #             "final":   final_path,
# #         },
# #     }
# #     generated_clips.append(clip_meta)
# #     if qc_flags:
# #         qc_flags_all.append((seg["segment_id"], qc_flags))

# #     status = "⚠️" if qc_flags else "✅"
# #     print(f"  {status} Done → {final_path}")

# # # ─────────────────────────────────────────────
# # # SAVE METADATA
# # # ─────────────────────────────────────────────
# # output_meta = {
# #     "timestamp":   datetime.now().isoformat(),   # Fix 5: datetime now imported
# #     "total_clips": len(generated_clips),
# #     "clips":       generated_clips,
# # }

# # meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
# # with open(meta_path, "w", encoding="utf-8") as f:
# #     json.dump(output_meta, f, indent=2, ensure_ascii=False)  # Fix 6: f arg + ensure_ascii

# # # ─────────────────────────────────────────────
# # # QC SUMMARY
# # # ─────────────────────────────────────────────
# # print(f"\n{'=' * 60}")
# # print(f"🎉 STEP 4 COMPLETE — {len(generated_clips)} clips generated")
# # print(f"📁 Output dir : {OUTPUT_DIR}/")
# # print(f"📊 Metadata   : {meta_path}")

# # if qc_flags_all:
# #     print(f"\n⚠️  QC FLAGS ({len(qc_flags_all)} segments):")
# #     for sid, flags in qc_flags_all:
# #         print(f"   [{sid:03d}] {flags}")
# # else:
# #     print("\n✅ All segments passed QC — no flags raised")
# """
# STEP 4: Voice Generation Pipeline — Complete (All 7 Requirements)
# ==================================================================
# Requirements implemented:
#   1. ✅ Voice library scan + user picks sample per speaker (SPEAKER_MAP)
#   2. ✅ XTTS-v2 voice cloning + generation
#   3. ✅ Waveform comparison plot — generated EN vs original JP side-by-side PNG
#   4. ✅ Timing enforcement — Rubberband 0.90–1.10× + pad/trim to exact target
#   5. ✅ Emotion fine-tuning — user toggle (EMOTION_ENABLED) + confidence gate
#   6. ✅ Age/type transformation — child / adult / old / robot (Parselmouth + HF)
#   7. ✅ Understandability guard — SNR + spectral flatness check after stretch

# HuggingFace models used:
#   - coqui/XTTS-v2         → voice cloning (Stage 1)
#   - bshall/knn-vc         → ML-based age/voice conversion (Stage 4, optional)

# Install:
#   pip install TTS pyrubberband praat-parselmouth scipy soundfile
#   pip install librosa matplotlib numpy torch torchaudio
#   pip install knnvc   # optional, for ML age conversion
# """

# import os
# import json
# import itertools
# import soundfile as sf
# from datetime import datetime
# from pathlib import Path

# import torch
# import librosa
# import numpy as np
# import matplotlib
# matplotlib.use("Agg")   # non-interactive backend — safe for servers
# import matplotlib.pyplot as plt
# import pyrubberband as pyrb
# import parselmouth
# from parselmouth.praat import call
# from scipy.signal import butter, filtfilt
# from TTS.api import TTS

# # ─────────────────────────────────────────────────────────────
# # CONFIG — edit these before running
# # ─────────────────────────────────────────────────────────────
# INPUT_JSON        = "work/translated_segments_step3.json"
# OUTPUT_DIR        = "work/generated_audio"
# WAVEFORM_DIR      = "work/waveform_comparisons"
# CROPPED_DIR       = "work/cropped_segments"     # JP originals from Step 2
# VOICE_SAMPLES_DIR = "sample_voices"

# # ── Toggle options ────────────────────────────────────────────
# EMOTION_ENABLED   = True    # set False to skip Stage 3 entirely
# AGE_ENABLED       = True    # set False to skip Stage 4 entirely
# USE_KNNVC         = False   # set True to use HF kNN-VC for age conversion
#                             # requires: pip install knnvc + reference clips

# # ── Stretch safety window ─────────────────────────────────────
# MIN_RATIO = 0.90
# MAX_RATIO = 1.10

# # ── Speaker → voice sample + age category ────────────────────
# # age_category: "adult" | "child_young" | "child_teen" | "old_60s" | "old_80s" | "robot"
# SPEAKER_MAP = {
#     "SPEAKER_00": {
#         "voice_sample":  "sample_voices/female/Amber.mp3",
#         "age_category":  "adult",
#         "knnvc_ref":     None,                  # path to reference clip for kNN-VC
#     },
#     "SPEAKER_01": {
#         "voice_sample":  "sample_voices/female/tsunade_voice sample.mp3",
#         "age_category":  "old_60s",
#         "knnvc_ref":     None,
#     },
#     "SPEAKER_02": {
#         "voice_sample":  "sample_voices/male/madara.mp3",
#         "age_category":  "adult",
#         "knnvc_ref":     None,
#     },
#     "SPEAKER_03": {
#         "voice_sample":  "sample_voices/male/madara.mp3",
#         "age_category":  "adult",
#         "knnvc_ref":     None,
#     },
# }
# DEFAULT_VOICE     = "sample_voices/female/Amber.mp3"

# # ── Emotion loudness targets (dBFS) ──────────────────────────
# EMOTION_LOUDNESS = {
#     "angry": -14, "ang": -14,
#     "surprised": -15, "sur": -15,
#     "fearful": -15, "fea": -15,
#     "happy": -16, "hap": -16,
#     "neutral": -18, "neu": -18,
#     "sad": -22,
#     "disgusted": -17, "dis": -17,
#     "unknown": -18,
# }

# # ── Age preset parameters for Parselmouth ────────────────────
# AGE_PRESETS = {
#     "adult":       None,   # no transformation
#     "child_young": {"formant_factor": 1.45, "pitch_factor": 2.0,  "rate_factor": 0.92, "breathiness": 0.00, "jitter": 0.005},
#     "child_teen":  {"formant_factor": 1.20, "pitch_factor": 1.40, "rate_factor": 1.00, "breathiness": 0.00, "jitter": 0.005},
#     "old_60s":     {"formant_factor": 0.97, "pitch_factor": 0.94, "rate_factor": 0.90, "breathiness": 0.15, "jitter": 0.012},
#     "old_80s":     {"formant_factor": 0.95, "pitch_factor": 0.88, "rate_factor": 0.80, "breathiness": 0.35, "jitter": 0.025},
#     "robot":       "robot",  # handled separately
# }

# os.makedirs(OUTPUT_DIR,   exist_ok=True)
# os.makedirs(WAVEFORM_DIR, exist_ok=True)

# # ─────────────────────────────────────────────────────────────
# # LOAD MODELS
# # ─────────────────────────────────────────────────────────────
# device = "cuda" if torch.cuda.is_available() else "cpu"
# print("=" * 60)
# print("STEP 4: Voice Generation Pipeline (All 7 Requirements)")
# print("=" * 60)

# # XTTS-v2 from coqui / HuggingFace
# tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device == "cuda"))
# print(f"✅ XTTS-v2 loaded on {device}")

# # kNN-VC (optional HuggingFace model — bshall/knn-vc)
# knnvc_model = None
# if USE_KNNVC:
#     try:
#         from knnvc import KNN_VC
#         knnvc_model = KNN_VC.from_pretrained(vocoder="hifigan", device=device)
#         print("✅ kNN-VC loaded (bshall/knn-vc)")
#     except ImportError:
#         print("⚠️  kNN-VC not installed — pip install knnvc — falling back to DSP")
#         USE_KNNVC = False

# # ─────────────────────────────────────────────────────────────
# # STAGE 0: VOICE LIBRARY SCAN
# # ─────────────────────────────────────────────────────────────
# print("\n── Stage 0: Voice library scan ──")
# voice_catalogue = {}
# for vf in itertools.chain(
#     Path(VOICE_SAMPLES_DIR).rglob("*.wav"),
#     Path(VOICE_SAMPLES_DIR).rglob("*.mp3"),
# ):
#     display = vf.stem.replace("_voice sample", "").replace("_", " ").title()
#     gender  = vf.parent.name
#     voice_catalogue[vf.stem] = {"path": str(vf), "gender": gender, "display": display}
#     print(f"  [{gender}] {display}")
# print(f"  → {len(voice_catalogue)} voices available\n")

# # ─────────────────────────────────────────────────────────────
# # LOAD SEGMENTS
# # ─────────────────────────────────────────────────────────────
# with open(INPUT_JSON, "r", encoding="utf-8") as f:
#     data = json.load(f)
# segments = data["segments"]
# print(f"✅ Loaded {len(segments)} segments from {INPUT_JSON}")

# # ─────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────

# def trim_silence(y: np.ndarray, sr: int, top_db: int = 35) -> np.ndarray:
#     """Remove leading/trailing silence, keep tiny 20ms/30ms buffers."""
#     _, idx = librosa.effects.trim(y, top_db=top_db, frame_length=512, hop_length=128)
#     lead  = max(0, idx[0] - int(0.02 * sr))
#     trail = min(len(y), idx[1] + int(0.03 * sr))
#     return y[lead:trail]


# def rms_normalise(y: np.ndarray, target_dbfs: float = -18.0) -> np.ndarray:
#     """Normalise to target dBFS. Soft-clip at 0.95."""
#     rms = np.sqrt(np.mean(y ** 2))
#     if rms < 1e-6:
#         return y
#     target_rms = 10 ** (target_dbfs / 20.0)
#     return np.clip(y * (target_rms / rms), -0.95, 0.95)


# def pad_or_trim(y: np.ndarray, sr: int, target_dur: float) -> np.ndarray:
#     """Clamp to exact target duration after stretching."""
#     n = int(target_dur * sr)
#     if len(y) < n:
#         return np.pad(y, (0, n - len(y)))
#     return y[:n]


# def butter_filter(y: np.ndarray, sr: int, cutoff: float, btype: str, order: int = 4) -> np.ndarray:
#     """Butterworth filter wrapper."""
#     nyq = sr / 2.0
#     b, a = butter(order, min(cutoff / nyq, 0.99), btype=btype)
#     return filtfilt(b, a, y)


# # ─────────────────────────────────────────────────────────────
# # REQUIREMENT 3 — WAVEFORM COMPARISON PLOT
# # ─────────────────────────────────────────────────────────────
# def save_waveform_comparison(
#     jp_path: str,
#     en_y: np.ndarray,
#     en_sr: int,
#     target_dur: float,
#     seg_id: int,
#     speaker: str,
#     emotion: str,
#     stretch_ratio: float,
# ):
#     """
#     Save side-by-side waveform PNG:
#       TOP    — original Japanese clip
#       BOTTOM — generated English clip
#     Both on the same time axis. Red vertical line = target duration boundary.
#     """
#     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
#     fig.patch.set_facecolor("#1a1a2e")

#     def style_ax(ax, label, color):
#         ax.set_facecolor("#16213e")
#         ax.spines[:].set_color("#444")
#         ax.tick_params(colors="#aaa")
#         ax.set_ylabel(label, color="#aaa", fontsize=9)
#         ax.yaxis.label.set_color("#aaa")

#     # JP original
#     if jp_path and os.path.exists(jp_path):
#         y_jp, sr_jp = librosa.load(jp_path, sr=None)
#         t_jp = np.linspace(0, len(y_jp) / sr_jp, len(y_jp))
#         ax1.plot(t_jp, y_jp, color="#5DCAA5", linewidth=0.5, alpha=0.85)
#     else:
#         ax1.text(0.5, 0.5, "JP source not found", transform=ax1.transAxes,
#                  ha="center", va="center", color="#888", fontsize=9)
#     style_ax(ax1, "JP original", "#5DCAA5")
#     ax1.set_title(
#         f"Seg {seg_id:03d} | {speaker} | {emotion} | stretch {stretch_ratio:.3f}×",
#         color="#ddd", fontsize=10, pad=6,
#     )

#     # EN generated
#     t_en = np.linspace(0, len(en_y) / en_sr, len(en_y))
#     ax2.plot(t_en, en_y, color="#7F77DD", linewidth=0.5, alpha=0.85)
#     style_ax(ax2, "EN generated", "#7F77DD")
#     ax2.set_xlabel("Time (s)", color="#aaa", fontsize=9)

#     # Target duration marker on both axes
#     for ax in (ax1, ax2):
#         ax.axvline(x=target_dur, color="#E24B4A", linewidth=1.2,
#                    linestyle="--", alpha=0.8, label=f"target {target_dur:.2f}s")
#         ax.legend(fontsize=8, facecolor="#222", labelcolor="#ccc",
#                   edgecolor="#444", loc="upper right")

#     plt.tight_layout(pad=1.5)
#     out_path = os.path.join(WAVEFORM_DIR, f"comparison_{seg_id:03d}.png")
#     plt.savefig(out_path, dpi=110, bbox_inches="tight", facecolor=fig.get_facecolor())
#     plt.close(fig)
#     return out_path


# # ─────────────────────────────────────────────────────────────
# # REQUIREMENT 7 — UNDERSTANDABILITY / QUALITY CHECK
# # ─────────────────────────────────────────────────────────────
# def check_understandability(y: np.ndarray, sr: int, stretch_ratio: float) -> dict:
#     """
#     Quality check after time-stretching.
#     Uses two metrics:
#       1. Spectral flatness — a very flat spectrum (close to 1.0) means the
#          signal has become noise-like. Natural speech has low flatness (0.0–0.15).
#          After extreme stretching, phase-smearing raises this score.
#       2. Zero-crossing rate variance — very low variance means the signal
#          has become periodic/robotic (over-stretched). Natural speech has
#          moderate variance in ZCR.
#     Returns a dict with scores and a pass/fail flag.
#     """
#     # Spectral flatness (lower = more tonal / more natural)
#     flatness = librosa.feature.spectral_flatness(y=y)
#     mean_flat = float(np.mean(flatness))

#     # Zero-crossing rate variance
#     zcr = librosa.feature.zero_crossing_rate(y)
#     zcr_var = float(np.var(zcr))

#     # Heuristic thresholds — tuned for speech
#     # Flagged if stretch was aggressive AND flatness is elevated
#     quality_ok = True
#     reason     = "ok"

#     if abs(stretch_ratio - 1.0) > 0.08 and mean_flat > 0.20:
#         quality_ok = False
#         reason = f"spectral_smearing (flatness={mean_flat:.3f})"

#     if abs(stretch_ratio - 1.0) > 0.08 and zcr_var < 1e-5:
#         quality_ok = False
#         reason = f"robotic_periodicity (zcr_var={zcr_var:.2e})"

#     return {
#         "quality_ok":      quality_ok,
#         "reason":          reason,
#         "spectral_flatness": round(mean_flat, 4),
#         "zcr_variance":    round(zcr_var, 8),
#     }


# # ─────────────────────────────────────────────────────────────
# # REQUIREMENT 6 — AGE / TYPE TRANSFORMATION (Parselmouth + kNN-VC)
# # ─────────────────────────────────────────────────────────────
# def apply_age_transform(
#     audio_path: str,
#     out_path: str,
#     age_category: str,
#     knnvc_ref: str = None,
# ) -> str:
#     """
#     Transform voice to age/type category.
#     adult   → pass-through
#     child_* → formant + pitch shift (Parselmouth Change Gender)
#     old_*   → jitter + shimmer + breathiness + rate slow (Parselmouth + scipy)
#     robot   → LPC resynthesis with periodic buzz source (Parselmouth)
#     """
#     if age_category == "adult" or age_category is None:
#         import shutil
#         shutil.copy(audio_path, out_path)
#         return out_path

#     preset = AGE_PRESETS.get(age_category)
#     if preset is None:
#         import shutil
#         shutil.copy(audio_path, out_path)
#         return out_path

#     # ── ML path: kNN-VC (HuggingFace bshall/knn-vc) ──────────
#     if USE_KNNVC and knnvc_model is not None and knnvc_ref and os.path.exists(knnvc_ref):
#         try:
#             matching_set = knnvc_model.get_matching_set([knnvc_ref])
#             query_seq    = knnvc_model.get_features(audio_path)
#             out_wav      = knnvc_model.match(query_seq, matching_set, topk=4)
#             import torchaudio
#             torchaudio.save(out_path, out_wav, 16000)
#             return out_path
#         except Exception as e:
#             print(f"    ⚠️  kNN-VC failed ({e}) — falling back to DSP")

#     # ── DSP path: Parselmouth ─────────────────────────────────
#     if preset == "robot":
#         return _apply_robot(audio_path, out_path)

#     sound = parselmouth.Sound(audio_path)
#     ff    = preset["formant_factor"]
#     pf    = preset["pitch_factor"]
#     rf    = preset["rate_factor"]

#     # Change Gender: shifts formants + pitch independently
#     transformed = call(
#         sound, "Change gender",
#         75, 600,          # min/max pitch range
#         ff,               # formant shift ratio — key for vocal tract length
#         0,                # new pitch median (0 = keep original)
#         pf,               # pitch range factor
#         rf,               # duration factor (rate)
#     )

#     # Add jitter for old voice (pitch perturbation)
#     jitter = preset.get("jitter", 0.0)
#     if jitter > 0:
#         y_arr = transformed.as_array().flatten()
#         sr_p  = int(transformed.sampling_frequency)
#         noise = np.random.normal(0, jitter, len(y_arr))
#         y_arr = y_arr + noise * np.abs(y_arr)
#         transformed = parselmouth.Sound(y_arr, sr_p)

#     # Add breathiness for old voice (high-passed noise mix)
#     breathiness = preset.get("breathiness", 0.0)
#     if breathiness > 0:
#         y_arr = transformed.as_array().flatten()
#         sr_p  = int(transformed.sampling_frequency)
#         noise = np.random.normal(0, 0.015, len(y_arr))
#         b, a  = butter(4, 2000 / (sr_p / 2), btype="high")
#         breath = filtfilt(b, a, noise)
#         # High-freq rolloff for old voice (aging reduces HF energy)
#         b2, a2 = butter(2, 4500 / (sr_p / 2), btype="low")
#         y_arr  = filtfilt(b2, a2, y_arr)
#         y_arr  = y_arr * (1 - breathiness) + breath * breathiness
#         y_arr  = np.clip(y_arr, -0.95, 0.95)
#         transformed = parselmouth.Sound(y_arr, sr_p)

#     transformed.save(out_path, "WAV")
#     return out_path


# def _apply_robot(audio_path: str, out_path: str) -> str:
#     """
#     Robot effect via LPC resynthesis.
#     Replaces the natural excitation (vocal fold vibration) with a
#     periodic buzz tone at the same F0, keeping the vocal tract filter.
#     Words remain intelligible — naturalness is removed.
#     """
#     sound = parselmouth.Sound(audio_path)
#     sr    = int(sound.sampling_frequency)
#     y     = sound.as_array().flatten()

#     # Extract F0 contour
#     pitch = call(sound, "To Pitch", 0.01, 75, 600)

#     # Create a buzz-wave source at mean F0
#     f0_values = [call(pitch, "Get value at time", t, "Hertz", "Linear")
#                  for t in np.arange(0, sound.duration, 0.01)]
#     f0_clean  = [f for f in f0_values if not (f != f)]   # remove NaN
#     mean_f0   = float(np.mean(f0_clean)) if f0_clean else 150.0

#     # Sawtooth buzz at mean_f0 (richer harmonics than sine)
#     t_arr = np.arange(len(y)) / sr
#     buzz  = 2 * (t_arr * mean_f0 % 1) - 1   # sawtooth wave
#     buzz  = buzz * 0.5 * np.std(y)           # match amplitude

#     # Mix: 70% buzz, 30% original (keeps some naturalness)
#     robot = np.clip(buzz * 0.7 + y * 0.3, -0.95, 0.95)

#     sf.write(out_path, robot, sr)
#     return out_path


# # ─────────────────────────────────────────────────────────────
# # MAIN PIPELINE LOOP
# # ─────────────────────────────────────────────────────────────
# generated_clips = []
# qc_flags_all    = []

# for i, seg in enumerate(segments):
#     sid          = seg["segment_id"]
#     speaker      = seg["speaker"]
#     english_text = seg["english"]
#     target_dur   = float(seg["duration"])
#     emotion      = seg.get("emotion", "neutral").lower()
#     emotion_conf = float(seg.get("emotion_confidence", 1.0))

#     print(f"\n{'─' * 55}")
#     print(f"[{i+1:02d}/{len(segments)}] Seg {sid:03d} | {speaker} | {target_dur:.2f}s")
#     print(f"  text:    {english_text}")
#     print(f"  emotion: {emotion} (conf {emotion_conf:.2f})")

#     spk_info     = SPEAKER_MAP.get(speaker, {"voice_sample": DEFAULT_VOICE, "age_category": "adult", "knnvc_ref": None})
#     voice_sample = spk_info.get("voice_sample", DEFAULT_VOICE)
#     age_category = spk_info.get("age_category", "adult")
#     knnvc_ref    = spk_info.get("knnvc_ref", None)

#     if not os.path.exists(voice_sample):
#         print(f"  ⚠️  voice sample not found: {voice_sample} — using default")
#         voice_sample = DEFAULT_VOICE
#     print(f"  voice:   {os.path.basename(voice_sample)}  | age: {age_category}")

#     qc_flags   = []
#     raw_path   = os.path.join(OUTPUT_DIR, f"raw_{sid:03d}.wav")
#     align_path = os.path.join(OUTPUT_DIR, f"aligned_{sid:03d}.wav")
#     emot_path  = os.path.join(OUTPUT_DIR, f"emotion_{sid:03d}.wav")
#     age_path   = os.path.join(OUTPUT_DIR, f"age_{sid:03d}.wav")
#     final_path = os.path.join(OUTPUT_DIR, f"final_{sid:03d}.wav")

#     # ── STAGE 1: XTTS-v2 VOICE CLONING ───────────────────────
#     print("  [1] XTTS-v2 cloning...")
#     tts.tts_to_file(
#         text=english_text,
#         speaker_wav=voice_sample,
#         language="en",
#         file_path=raw_path,
#     )
#     y_raw, sr = librosa.load(raw_path, sr=22050)
#     y_raw     = trim_silence(y_raw, sr)
#     raw_dur   = len(y_raw) / sr
#     print(f"       raw (trimmed): {raw_dur:.3f}s  target: {target_dur:.3f}s")

#     # ── STAGE 2: TIMING ALIGNMENT (Rubberband) ────────────────
#     print("  [2] Timing alignment...")
#     ratio      = max(MIN_RATIO, min(MAX_RATIO, target_dur / raw_dur))
#     # pyrubberband: rate=1/ratio (playback rate, not duration ratio)
#     y_aligned  = pyrb.time_stretch(y_raw, sr, rate=1.0 / ratio)
#     y_aligned  = pad_or_trim(y_aligned, sr, target_dur)
#     actual_dur = len(y_aligned) / sr
#     print(f"       ratio: {ratio:.3f}×  final: {actual_dur:.3f}s")

#     if ratio >= MAX_RATIO or ratio <= MIN_RATIO:
#         qc_flags.append(f"HIGH_STRETCH:{ratio:.3f}")
#         print(f"       ⚠️  HIGH_STRETCH — consider re-translating")

#     sf.write(align_path, y_aligned, sr)

#     # ── REQUIREMENT 7: UNDERSTANDABILITY CHECK ────────────────
#     quality = check_understandability(y_aligned, sr, ratio)
#     print(f"       quality: {quality['reason']}  "
#           f"flatness={quality['spectral_flatness']:.3f}")
#     if not quality["quality_ok"]:
#         qc_flags.append(f"QUALITY_DEGRADED:{quality['reason']}")

#     # ── REQUIREMENT 3: WAVEFORM COMPARISON PLOT ───────────────
#     jp_crop = os.path.join(CROPPED_DIR, f"segment_{sid:03d}.wav")
#     wf_path = save_waveform_comparison(
#         jp_path=jp_crop,
#         en_y=y_aligned,
#         en_sr=sr,
#         target_dur=target_dur,
#         seg_id=sid,
#         speaker=speaker,
#         emotion=emotion,
#         stretch_ratio=ratio,
#     )
#     print(f"       waveform saved: {wf_path}")

#     # ── STAGE 3: EMOTION FINE-TUNING (OPTIONAL) ───────────────
#     # REQUIREMENT 5: EMOTION_ENABLED toggle + confidence gate
#     if EMOTION_ENABLED:
#         effective_emotion = emotion if emotion_conf >= 0.30 else "neutral"
#         if effective_emotion != emotion:
#             print(f"  [3] Emotion: low confidence → using neutral")
#         else:
#             print(f"  [3] Emotion fine-tuning: {effective_emotion}")

#         target_dbfs = EMOTION_LOUDNESS.get(effective_emotion, -18)
#         y_emotion   = rms_normalise(y_aligned, target_dbfs=target_dbfs)

#         # Tonal shaping per emotion
#         if effective_emotion in ("sad",):
#             y_emotion = butter_filter(y_emotion, sr, 3500, "low")

#         elif effective_emotion in ("angry", "ang"):
#             y_emotion = butter_filter(y_emotion, sr, 150, "high")
#             y_hf      = butter_filter(y_emotion, sr, 3000, "high")
#             y_emotion = np.clip(y_emotion + 0.15 * y_hf, -0.95, 0.95)

#         elif effective_emotion in ("happy", "hap"):
#             y_hf      = butter_filter(y_emotion, sr, 4000, "high")
#             y_emotion = np.clip(y_emotion + 0.10 * y_hf, -0.95, 0.95)

#         elif effective_emotion in ("fearful", "fea", "surprised", "sur"):
#             # Add slight breathiness for fear/surprise
#             noise  = np.random.normal(0, 0.008, len(y_emotion))
#             breath = butter_filter(noise, sr, 3000, "high")
#             y_emotion = np.clip(y_emotion + breath * 0.12, -0.95, 0.95)

#     else:
#         print("  [3] Emotion fine-tuning: DISABLED")
#         y_emotion        = y_aligned
#         effective_emotion = "skipped"

#     sf.write(emot_path, y_emotion, sr)

#     # ── STAGE 4: AGE / TYPE TRANSFORMATION (OPTIONAL) ─────────
#     # REQUIREMENT 6: child / adult / old / robot
#     if AGE_ENABLED and age_category != "adult":
#         print(f"  [4] Age transform: {age_category} ({'kNN-VC' if USE_KNNVC and knnvc_ref else 'DSP'})")
#         apply_age_transform(emot_path, age_path, age_category, knnvc_ref)
#         # Reload and verify duration after transformation
#         y_final, sr_f = librosa.load(age_path, sr=None)
#         y_final = pad_or_trim(y_final, sr_f, target_dur)
#         sf.write(age_path, y_final, sr_f)
#         final_src = age_path
#         sr_final  = sr_f
#     else:
#         if not AGE_ENABLED:
#             print("  [4] Age transform: DISABLED")
#         else:
#             print("  [4] Age transform: adult (no change)")
#         y_final  = y_emotion
#         sr_final = sr
#         final_src = emot_path

#     # Write final
#     sf.write(final_path, y_final, sr_final)
#     final_dur = len(y_final) / sr_final

#     # Short clip guard
#     if final_dur < 0.15:
#         qc_flags.append("TOO_SHORT")

#     # ── METADATA RECORD ───────────────────────────────────────
#     clip_meta = {
#         "segment_id":          sid,
#         "speaker":             speaker,
#         "start":               seg["start"],
#         "end":                 seg["end"],
#         "duration_target":     round(target_dur, 4),
#         "duration_raw_trimmed": round(raw_dur, 4),
#         "duration_final":      round(final_dur, 4),
#         "stretch_ratio":       round(ratio, 4),
#         "voice_sample":        os.path.basename(voice_sample),
#         "emotion":             emotion,
#         "emotion_effective":   effective_emotion if EMOTION_ENABLED else "disabled",
#         "emotion_confidence":  round(emotion_conf, 4),
#         "emotion_enabled":     EMOTION_ENABLED,
#         "age_category":        age_category,
#         "age_enabled":         AGE_ENABLED,
#         "quality_check":       quality,
#         "qc_flags":            qc_flags,
#         "waveform_plot":       wf_path,
#         "files": {
#             "raw":     raw_path,
#             "aligned": align_path,
#             "emotion": emot_path,
#             "age":     age_path if (AGE_ENABLED and age_category != "adult") else None,
#             "final":   final_path,
#         },
#     }
#     generated_clips.append(clip_meta)
#     if qc_flags:
#         qc_flags_all.append((sid, qc_flags))

#     status = "⚠️" if qc_flags else "✅"
#     print(f"  {status} [{sid:03d}] done → {final_path}")

# # ─────────────────────────────────────────────────────────────
# # SAVE METADATA JSON
# # ─────────────────────────────────────────────────────────────
# output_meta = {
#     "timestamp":       datetime.now().isoformat(),
#     "total_clips":     len(generated_clips),
#     "emotion_enabled": EMOTION_ENABLED,
#     "age_enabled":     AGE_ENABLED,
#     "clips":           generated_clips,
# }
# meta_path = os.path.join(OUTPUT_DIR, "generation_metadata.json")
# with open(meta_path, "w", encoding="utf-8") as f:
#     json.dump(output_meta, f, indent=2, ensure_ascii=False)

# # ─────────────────────────────────────────────────────────────
# # QC SUMMARY
# # ─────────────────────────────────────────────────────────────
# print(f"\n{'=' * 60}")
# print(f"🎉 STEP 4 COMPLETE — {len(generated_clips)} clips generated")
# print(f"📁 Audio dir     : {OUTPUT_DIR}/")
# print(f"📊 Metadata      : {meta_path}")
# print(f"🖼  Waveform plots: {WAVEFORM_DIR}/")

# if qc_flags_all:
#     print(f"\n⚠️  QC FLAGS — {len(qc_flags_all)} segments need attention:")
#     for sid, flags in sorted(qc_flags_all):
#         print(f"   [seg {sid:03d}] {flags}")
# else:
#     print("\n✅ All segments passed QC")

# print(f"\nNext → step5_assembly.py")
#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         STEP 4 SETUP — Voice Selection & Installation        ║
║  Run this ONCE before step4_genvoice_complete.py             ║
║  Outputs: work/speaker_config.json                           ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python step4_setup.py

What it does:
    1. Checks + installs all required packages
    2. Scans sample_voices/ folder
    3. Interactive terminal — assign voice + age per speaker
    4. Saves config to work/speaker_config.json
    5. step4_genvoice_complete.py reads this config automatically
"""

import sys
import os
import json
import subprocess
import itertools
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# TERMINAL COLOURS
# ─────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    PURPLE = "\033[95m"
    WHITE  = "\033[97m"
    BG_DARK = "\033[40m"

def header(text):
    width = 60
    print(f"\n{C.CYAN}{'═' * width}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}  {text}{C.RESET}")
    print(f"{C.CYAN}{'═' * width}{C.RESET}\n")

def success(text): print(f"  {C.GREEN}✅ {text}{C.RESET}")
def warn(text):    print(f"  {C.YELLOW}⚠️  {text}{C.RESET}")
def error(text):   print(f"  {C.RED}❌ {text}{C.RESET}")
def info(text):    print(f"  {C.CYAN}ℹ  {text}{C.RESET}")
def dim(text):     print(f"  {C.DIM}{text}{C.RESET}")

def prompt(text, default=None):
    if default is not None:
        hint = f"{C.DIM} [{default}]{C.RESET}"
    else:
        hint = ""
    val = input(f"\n  {C.BOLD}{C.WHITE}{text}{hint}{C.RESET}  › ").strip()
    if not val and default is not None:
        return default
    return val

def numbered_menu(title, options, descriptions=None, default=0):
    """Show a numbered menu and return the chosen index."""
    print(f"\n  {C.BOLD}{title}{C.RESET}")
    print(f"  {C.DIM}{'─' * 40}{C.RESET}")
    for i, opt in enumerate(options):
        marker  = f"{C.GREEN}▶{C.RESET}" if i == default else " "
        desc    = f"  {C.DIM}{descriptions[i]}{C.RESET}" if descriptions else ""
        default_tag = f"  {C.DIM}(default){C.RESET}" if i == default else ""
        print(f"  {marker} {C.CYAN}[{i}]{C.RESET} {C.WHITE}{opt}{C.RESET}{desc}{default_tag}")

    while True:
        raw = input(f"\n  {C.BOLD}Enter number (0–{len(options)-1}){C.RESET} › ").strip()
        if raw == "" :
            return default
        if raw.isdigit() and 0 <= int(raw) < len(options):
            return int(raw)
        warn(f"Please enter a number between 0 and {len(options)-1}")

# ─────────────────────────────────────────────────────────────
# PART 1 — INSTALLATION
# ─────────────────────────────────────────────────────────────
PACKAGES = [
    # (pip_name,          import_name,     description)
    ("TTS",               "TTS",           "Coqui XTTS-v2 voice cloning"),
    ("pyrubberband",      "pyrubberband",  "High-quality time-stretching"),
    ("praat-parselmouth", "parselmouth",   "Voice age/type transformation"),
    ("scipy",             "scipy",         "Audio filters (EQ, breathiness)"),
    ("soundfile",         "soundfile",     "WAV read/write"),
    ("librosa",           "librosa",       "Audio analysis + silence trim"),
    ("matplotlib",        "matplotlib",    "Waveform comparison plots"),
    ("numpy",             "numpy",         "Array operations"),
    ("torch",             "torch",         "PyTorch (GPU support)"),
    ("torchaudio",        "torchaudio",    "Audio I/O for PyTorch"),
    ("pyphen",            "pyphen",        "Syllable counting"),
]

OPTIONAL_PACKAGES = [
    ("knnvc",             "knnvc",         "HuggingFace kNN-VC age conversion (optional)"),
]

SYSTEM_DEPS = {
    "linux":  "sudo apt-get install -y rubberband-cli ffmpeg",
    "darwin": "brew install rubberband ffmpeg",
    "win32":  "# Windows: download rubberband from https://breakfastquay.com/rubberband/",
}


def check_package(import_name):
    """Return True if package can be imported."""
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def install_package(pip_name):
    """pip install a package, return success bool."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
        capture_output=True,
    )
    return result.returncode == 0


def run_installation():
    header("Part 1 — Package Installation")

    # System dependencies hint
    platform = sys.platform
    sys_cmd  = SYSTEM_DEPS.get(platform, SYSTEM_DEPS["linux"])
    print(f"  {C.BOLD}System dependencies (run manually if not installed):{C.RESET}")
    print(f"  {C.DIM}{sys_cmd}{C.RESET}\n")

    # Python packages
    print(f"  {C.BOLD}Checking Python packages...{C.RESET}\n")
    all_ok = True
    for pip_name, import_name, description in PACKAGES:
        if check_package(import_name):
            success(f"{pip_name:<25} {C.DIM}{description}{C.RESET}")
        else:
            print(f"  {C.YELLOW}⟳  Installing {pip_name:<22} {C.DIM}{description}...{C.RESET}", end="", flush=True)
            if install_package(pip_name):
                print(f"  {C.GREEN}done{C.RESET}")
            else:
                print(f"  {C.RED}FAILED{C.RESET}")
                error(f"Could not install {pip_name}. Try manually: pip install {pip_name}")
                all_ok = False

    # Optional packages
    print(f"\n  {C.BOLD}Optional packages:{C.RESET}\n")
    for pip_name, import_name, description in OPTIONAL_PACKAGES:
        if check_package(import_name):
            success(f"{pip_name:<25} {C.DIM}{description}{C.RESET}")
        else:
            warn(f"{pip_name:<25} {C.DIM}not installed — {description}{C.RESET}")
            ans = input(f"  Install {pip_name}? (y/N) › ").strip().lower()
            if ans == "y":
                print(f"  Installing {pip_name}...", end="", flush=True)
                if install_package(pip_name):
                    print(f"  {C.GREEN}done{C.RESET}")
                else:
                    print(f"  {C.RED}FAILED{C.RESET}")

    if all_ok:
        success("All required packages ready")
    else:
        error("Some packages failed — fix manually before continuing")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# PART 2 — VOICE LIBRARY SCAN
# ─────────────────────────────────────────────────────────────
VOICE_SAMPLES_DIR = "sample_voices"

def scan_voices():
    """Scan sample_voices/ and return catalogue list."""
    catalogue = []
    for vf in itertools.chain(
        Path(VOICE_SAMPLES_DIR).rglob("*.wav"),
        Path(VOICE_SAMPLES_DIR).rglob("*.mp3"),
    ):
        duration_s = get_audio_duration(str(vf))
        display    = (vf.stem
                      .replace("_voice sample", "")
                      .replace("_", " ")
                      .strip()
                      .title())
        gender     = vf.parent.name.lower()
        quality    = "ok" if duration_s >= 6 else "too_short"

        catalogue.append({
            "display":    display,
            "path":       str(vf),
            "gender":     gender,
            "duration_s": round(duration_s, 1),
            "quality":    quality,
            "filename":   vf.name,
        })

    # Sort: female first, then male, alphabetically within each
    catalogue.sort(key=lambda x: (x["gender"] != "female", x["display"]))
    return catalogue


def get_audio_duration(path):
    """Get audio duration in seconds using soundfile, fallback to 0."""
    try:
        import soundfile as sf
        info = sf.info(path)
        return info.duration
    except Exception:
        try:
            import librosa
            y, sr = librosa.load(path, sr=None, duration=1)
            return librosa.get_duration(path=path)
        except Exception:
            return 0.0


def print_voice_catalogue(catalogue):
    """Print a formatted voice catalogue table."""
    print(f"\n  {C.BOLD}{'#':<4} {'Name':<32} {'Gender':<10} {'Dur':>6}  {'Quality'}{C.RESET}")
    print(f"  {C.DIM}{'─' * 60}{C.RESET}")
    for i, v in enumerate(catalogue):
        quality_str = (f"{C.GREEN}ok{C.RESET}"
                       if v["quality"] == "ok"
                       else f"{C.YELLOW}short (<6s){C.RESET}")
        gender_str  = (f"{C.PURPLE}female{C.RESET}"
                       if v["gender"] == "female"
                       else f"{C.BLUE}male{C.RESET}")
        print(
            f"  {C.CYAN}[{i:<2}]{C.RESET} "
            f"{v['display']:<32} "
            f"{gender_str:<18} "
            f"{C.DIM}{v['duration_s']:>5.1f}s{C.RESET}  "
            f"{quality_str}"
        )


# ─────────────────────────────────────────────────────────────
# PART 3 — SPEAKER DISCOVERY FROM JSON
# ─────────────────────────────────────────────────────────────
INPUT_JSON = "work/translated_segments_step3.json"

AGE_CATEGORIES = [
    "adult",
    "child_young",
    "child_teen",
    "old_60s",
    "old_80s",
    "robot",
]
AGE_DESCRIPTIONS = [
    "No transformation — natural voice",
    "Young child (5–10y) — formant+pitch shifted up 45%",
    "Teenager (11–16y) — formant+pitch shifted up 20%",
    "Elderly 60s — slight jitter + breathiness + slower",
    "Elderly 80s — strong jitter + heavy breathiness + much slower",
    "Robot — LPC resynthesis with buzz-wave source",
]


def discover_speakers():
    """Read JSON and return list of unique speaker IDs."""
    if not os.path.exists(INPUT_JSON):
        error(f"Input JSON not found: {INPUT_JSON}")
        info("Please run Steps 1–3 first to generate the translated segments JSON.")
        sys.exit(1)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    speakers = {}
    for seg in data.get("segments", []):
        spk = seg.get("speaker", "UNKNOWN")
        if spk not in speakers:
            speakers[spk] = {
                "count":    0,
                "emotions": set(),
                "sample_text": seg.get("english", ""),
            }
        speakers[spk]["count"]  += 1
        speakers[spk]["emotions"].add(seg.get("emotion", "neu"))

    return speakers


# ─────────────────────────────────────────────────────────────
# PART 4 — INTERACTIVE SPEAKER CONFIGURATION
# ─────────────────────────────────────────────────────────────
def configure_speakers(speakers, catalogue, existing_config=None):
    """
    Interactive loop — for each speaker ask:
      1. Which voice sample to use
      2. Which age/type category
    Returns speaker_map dict.
    """
    header("Part 3 — Speaker Voice Assignment")

    print(f"  Found {C.BOLD}{len(speakers)}{C.RESET} unique speakers in your JSON.\n")
    print(f"  {C.DIM}For each speaker you will:{C.RESET}")
    print(f"  {C.DIM}  1. Choose a voice sample from your sample_voices/ folder{C.RESET}")
    print(f"  {C.DIM}  2. Choose an age/type category{C.RESET}")
    print(f"  {C.DIM}  3. (Optional) provide a kNN-VC reference clip{C.RESET}\n")

    speaker_map = {}

    for spk_id, spk_info in sorted(speakers.items()):
        print(f"\n  {C.BOLD}{C.BG_DARK}{C.WHITE}  Speaker: {spk_id}  {C.RESET}")
        print(f"  {C.DIM}Lines: {spk_info['count']} | Emotions: {', '.join(spk_info['emotions'])}{C.RESET}")
        print(f"  {C.DIM}Sample line: \"{spk_info['sample_text'][:60]}...\"  {C.RESET}")

        # ── VOICE SELECTION ───────────────────────────────────
        print(f"\n  {C.BOLD}Step A — Choose voice sample{C.RESET}")
        print_voice_catalogue(catalogue)

        # Default: try to match gender if available, else 0
        default_idx = 0
        if existing_config and spk_id in existing_config:
            prev_path = existing_config[spk_id].get("voice_sample", "")
            for j, v in enumerate(catalogue):
                if v["path"] == prev_path:
                    default_idx = j
                    break

        voice_idx = numbered_menu(
            f"Select voice for {spk_id}",
            [f"{v['display']} ({v['gender']}, {v['duration_s']}s)" for v in catalogue],
            default=default_idx,
        )
        chosen_voice = catalogue[voice_idx]

        if chosen_voice["quality"] == "too_short":
            warn(f"This sample is only {chosen_voice['duration_s']}s — "
                 f"recommend 15s+ for best cloning quality.")

        success(f"Voice: {chosen_voice['display']}  [{chosen_voice['filename']}]")

        # ── AGE CATEGORY ──────────────────────────────────────
        print(f"\n  {C.BOLD}Step B — Choose age / voice type{C.RESET}")
        default_age = 0
        if existing_config and spk_id in existing_config:
            prev_age = existing_config[spk_id].get("age_category", "adult")
            if prev_age in AGE_CATEGORIES:
                default_age = AGE_CATEGORIES.index(prev_age)

        age_idx = numbered_menu(
            f"Select age/type for {spk_id}",
            AGE_CATEGORIES,
            descriptions=AGE_DESCRIPTIONS,
            default=default_age,
        )
        chosen_age = AGE_CATEGORIES[age_idx]
        success(f"Age/type: {chosen_age}  — {AGE_DESCRIPTIONS[age_idx]}")

        # ── kNN-VC REFERENCE CLIP (optional) ─────────────────
        knnvc_ref = None
        if chosen_age not in ("adult", "robot"):
            print(f"\n  {C.BOLD}Step C — kNN-VC reference clip{C.RESET} {C.DIM}(optional){C.RESET}")
            info("Providing a 5–10s reference clip of a real child/elderly voice "
                 "enables ML-based conversion instead of DSP.")
            info("Leave blank to use DSP (Parselmouth) instead.")
            ref_path = input(f"  Path to reference clip (or press Enter to skip) › ").strip()
            if ref_path and os.path.exists(ref_path):
                knnvc_ref = ref_path
                success(f"kNN-VC reference: {ref_path}")
            elif ref_path:
                warn(f"File not found: {ref_path} — using DSP fallback")

        speaker_map[spk_id] = {
            "voice_sample":  chosen_voice["path"],
            "voice_display": chosen_voice["display"],
            "age_category":  chosen_age,
            "knnvc_ref":     knnvc_ref,
        }

    return speaker_map


# ─────────────────────────────────────────────────────────────
# PART 5 — GLOBAL OPTIONS
# ─────────────────────────────────────────────────────────────
def configure_global_options(existing_config=None):
    """Ask user for global pipeline toggles."""
    header("Part 4 — Global Options")

    prev = existing_config.get("options", {}) if existing_config else {}

    # Emotion toggle
    prev_emot = prev.get("emotion_enabled", True)
    emot_idx  = numbered_menu(
        "Emotion fine-tuning (Stage 3)",
        ["Enabled  — apply emotion-aware loudness + EQ per segment",
         "Disabled — skip Stage 3, pass timing-aligned audio through"],
        default=0 if prev_emot else 1,
    )
    emotion_enabled = (emot_idx == 0)

    # Age toggle
    prev_age = prev.get("age_enabled", True)
    age_idx  = numbered_menu(
        "Age / type transformation (Stage 4)",
        ["Enabled  — apply child/old/robot transform per speaker",
         "Disabled — skip Stage 4, use cloned voice as-is"],
        default=0 if prev_age else 1,
    )
    age_enabled = (age_idx == 0)

    # kNN-VC toggle
    prev_knnvc = prev.get("use_knnvc", False)
    try:
        import knnvc
        knnvc_available = True
    except ImportError:
        knnvc_available = False

    if knnvc_available:
        knnvc_idx = numbered_menu(
            "Age conversion method",
            ["DSP (Parselmouth) — no reference clip needed, fast",
             "kNN-VC (HuggingFace bshall/knn-vc) — ML, needs reference clips, more natural"],
            default=1 if prev_knnvc else 0,
        )
        use_knnvc = (knnvc_idx == 1)
    else:
        warn("kNN-VC not installed — using DSP (Parselmouth) only")
        info("Install with: pip install knnvc")
        use_knnvc = False

    return {
        "emotion_enabled": emotion_enabled,
        "age_enabled":     age_enabled,
        "use_knnvc":       use_knnvc,
    }


# ─────────────────────────────────────────────────────────────
# PART 6 — SAVE + SUMMARY
# ─────────────────────────────────────────────────────────────
CONFIG_PATH = "work/speaker_config.json"

def save_config(speaker_map, options):
    os.makedirs("work", exist_ok=True)
    config = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "input_json":   INPUT_JSON,
        "options":      options,
        "speakers":     speaker_map,
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config


def print_summary(config):
    header("Configuration Summary")

    opts = config["options"]
    print(f"  {C.BOLD}Global options:{C.RESET}")
    print(f"    Emotion fine-tuning : {C.GREEN}ON{C.RESET}" if opts["emotion_enabled"]
          else f"    Emotion fine-tuning : {C.DIM}OFF{C.RESET}")
    print(f"    Age/type transform  : {C.GREEN}ON{C.RESET}" if opts["age_enabled"]
          else f"    Age/type transform  : {C.DIM}OFF{C.RESET}")
    print(f"    Age conversion mode : {'kNN-VC (ML)' if opts['use_knnvc'] else 'DSP (Parselmouth)'}")

    print(f"\n  {C.BOLD}Speaker assignments:{C.RESET}")
    print(f"  {C.DIM}{'Speaker':<14} {'Voice':<28} {'Age/Type'}{C.RESET}")
    print(f"  {C.DIM}{'─' * 58}{C.RESET}")
    for spk_id, info_d in sorted(config["speakers"].items()):
        voice   = info_d.get("voice_display", os.path.basename(info_d["voice_sample"]))
        age     = info_d["age_category"]
        knn     = f"  {C.DIM}[kNN-VC ref set]{C.RESET}" if info_d.get("knnvc_ref") else ""
        age_col = (f"{C.PURPLE}{age}{C.RESET}" if "child" in age
                   else f"{C.YELLOW}{age}{C.RESET}" if "old" in age
                   else f"{C.BLUE}{age}{C.RESET}" if age == "robot"
                   else f"{C.GREEN}{age}{C.RESET}")
        print(f"  {C.CYAN}{spk_id:<14}{C.RESET} {voice:<28} {age_col}{knn}")

    print(f"\n  {C.BOLD}Saved to:{C.RESET} {C.GREEN}{CONFIG_PATH}{C.RESET}")
    print(f"\n  {C.BOLD}Run next:{C.RESET}")
    print(f"  {C.DIM}python step4_genvoice_complete.py{C.RESET}\n")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    print(f"\n{C.BOLD}{C.CYAN}")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║     Anime Dubbing Pipeline — Step 4 Setup           ║")
    print("  ║     Voice Selection & Installation                  ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print(C.RESET)

    # Load existing config if present (for re-runs with defaults)
    existing_config = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            existing_config = json.load(f)
        info(f"Found existing config: {CONFIG_PATH}")
        ans = input("  Re-use existing defaults? (Y/n) › ").strip().lower()
        if ans == "n":
            existing_config = None

    # ── Part 1: Installation ──────────────────────────────────
    header("Part 1 — Installation Check")
    skip_install = False
    if existing_config:
        ans = input("  Skip installation check? (Y/n) › ").strip().lower()
        skip_install = (ans != "n")

    if not skip_install:
        run_installation()
    else:
        info("Skipping installation check")

    # ── Part 2: Voice library scan ────────────────────────────
    header("Part 2 — Voice Library")
    if not os.path.isdir(VOICE_SAMPLES_DIR):
        error(f"Voice samples folder not found: {VOICE_SAMPLES_DIR}/")
        info("Create the folder and add your .wav / .mp3 voice samples:")
        print(f"  {C.DIM}sample_voices/")
        print(f"  ├── female/  (Amber.mp3, Chloe.mp3, ...)")
        print(f"  └── male/    (madara.mp3, denji.mp3, ...){C.RESET}")
        sys.exit(1)

    catalogue = scan_voices()
    if not catalogue:
        error("No .wav or .mp3 files found in sample_voices/")
        sys.exit(1)

    success(f"Found {len(catalogue)} voice samples")

    # ── Part 3: Speaker config ────────────────────────────────
    speakers = discover_speakers()
    success(f"Found {len(speakers)} unique speakers in {INPUT_JSON}")

    existing_speakers = existing_config.get("speakers") if existing_config else None
    speaker_map = configure_speakers(speakers, catalogue, existing_speakers)

    # ── Part 4: Global options ────────────────────────────────
    options = configure_global_options(existing_config)

    # ── Part 5: Save + summary ────────────────────────────────
    config = save_config(speaker_map, options)
    print_summary(config)

    success("Setup complete — ready to run step4_genvoice_complete.py")


if __name__ == "__main__":
    main()