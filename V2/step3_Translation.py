# import os
# import json
# from datetime import datetime
# import numpy as np
# import torch
# import torchaudio
# from transformers import pipeline
# from openai import OpenAI
# from dotenv import load_dotenv
# import re

# load_dotenv()

# print("="*60)
# print("STEP 3: Emotion Detection + Translation")
# print("="*60)

# # ========= CONFIG =========
# WORK_DIR = "work"
# VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio/vocals.wav"
# TRANSCRIPT_JSON = os.path.join(WORK_DIR, "transcription_with_speakers.json")
# EMOTION_JSON = os.path.join(WORK_DIR, "emotion_detection.json")
# TRANSLATED_JSON = os.path.join(WORK_DIR, "translated_segments_step3.json")

# # ✅ WORKING MODELS (no preprocessor issues)
# EMOTION_PRIMARY = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"  # 8-class
# EMOTION_FALLBACK = "superb/wav2vec2-base-superb-er"  # 4-class

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     raise ValueError("Set OPENAI_API_KEY environment variable")
# client = OpenAI(api_key=OPENAI_API_KEY)

# device = 0 if torch.cuda.is_available() else -1

# # ========= LOAD MODELS =========
# print("🔄 Loading emotion models...")

# # Primary: 8 emotions (angry, disgust, fear, happy, neutral, sad, surprise)
# emotion_primary = pipeline(
#     "audio-classification",
#     model=EMOTION_PRIMARY,
#     device=device
# )

# # Fallback: 4 emotions (angry, happy, neutral, sad)
# emotion_fallback = pipeline(
#     "audio-classification", 
#     model=EMOTION_FALLBACK,
#     device=device
# )

# print("✅ Emotion models loaded")

# # Emotion → syllables/second (tune these!)
# EMOTION_RATE = {
#     "angry": 5.0,
#     "disgust": 4.2,
#     "fear": 4.8,
#     "happy": 4.5,
#     "neutral": 4.0,
#     "sad": 3.5,
#     "surprise": 4.8
# }

# def load_audio_segment(path, start_sec, end_sec, target_sr=16000):
#     """Load cropped segment from full audio."""
#     wav, sr = torchaudio.load(path)
#     if sr != target_sr:
#         wav = torchaudio.functional.resample(wav, sr, target_sr)
#         sr = target_sr
#     if wav.size(0) > 1:
#         wav = wav.mean(dim=0, keepdim=True)
    
#     s_idx = int(start_sec * sr)
#     e_idx = int(end_sec * sr)
#     return wav.squeeze(0)[s_idx:e_idx].numpy()

# def classify_emotion(audio_np, duration):
#     """Classify emotion with fallback logic."""
#     if duration >= 0.5:  # Use 8-class model
#         result = emotion_primary(audio_np)
#     else:  # Use 4-class for short clips
#         result = emotion_fallback(audio_np)
    
#     label = result[0]['label'].lower()
#     conf = result[0]['score']
    
#     return label, conf

# def estimate_syllable_budget(duration, emotion):
#     rate = EMOTION_RATE.get(emotion, 4.0)
#     target = int(duration * rate)
#     return max(3, target)

# def translate_segment(seg, emotion_label, syllable_target, prev_english=""):
#     """GPT translation with emotion + context."""
#     jp_text = seg["text"]
#     duration = seg["duration"]
#     gender = seg.get("gender", "neutral")
#     speaker = seg["speaker"]
    
#     context = ""
#     if prev_english:
#         context = f"\nPrevious English line: \"{prev_english}\""
    
#     prompt = f"""You are an anime ADR script adapter.

# Translate/adapt Japanese → natural English dub line.

# CONTEXT:
# - Speaker: {speaker} ({gender})
# - Emotion: {emotion_label}  
# - Duration: {duration:.2f}s
# - Target syllables: ~{syllable_target}

# INSTRUCTIONS:
# 1. Preserve emotional tone and character personality
# 2. Match speaking rhythm for lip-sync (syllable count)
# 3. Sound like spoken dialogue, not subtitles
# 4. You can rephrase freely for natural flow/timing

# {context}

# Japanese: "{jp_text}"

# JSON response only:
# {{
#   "english": "dub line here",
#   "syllables": 0,
#   "notes": "brief timing/emotion note"
# }}"""

#     try:
#         resp = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             response_format={"type": "json_object"}
#         )
#         content = resp.choices[0].message.content.strip()
#         obj = json.loads(content)
#         english = obj.get("english", jp_text).strip()
#         notes = obj.get("notes", "")
#         syl_est = estimate_syllable_budget(duration, emotion_label)  # placeholder
#     except Exception as e:
#         english = jp_text  # fallback
#         notes = f"GPT error: {e}"
#         syl_est = 0
    
#     return english, notes, syl_est
# def translate_segment(seg, emotion_label, syllable_target, prev_english=""):
#     """GPT translation with explicit accuracy and ADR constraints."""
#     jp_text = seg["text"]
#     duration = seg["duration"]
#     gender = seg.get("gender", "neutral")
#     speaker = seg["speaker"]
    
#     context = ""
#     if prev_english:
#         context = f"\nPrevious English line: \"{prev_english}\""
    
#     # Updated prompt with instructions for explicit/literal accuracy
#     prompt = f"""You are an adult-oriented anime ADR script adapter.

# Translate/adapt Japanese → English dub line.

# CONTEXT:
# - Speaker: {speaker} ({gender})
# - Emotion: {emotion_label}  
# - Duration: {duration:.2f}s
# - Target syllables: ~{syllable_target}

# INSTRUCTIONS:
# 1. MANDATORY: Translate all anatomical terms and vulgarities LITERALLY (e.g., "shiri no ana" must be "asshole" or "anus"). Do not sanitize or soften the language.
# 2. Preserve the specific relationship terms (e.g., "Neesan" as "Sister" or "Big Sister").
# 3. Match speaking rhythm for lip-sync (syllable count: {syllable_target}).
# 4. Sound like natural, spoken adult dialogue.

# {context}

# Japanese: "{jp_text}"

# JSON response only:
# {{
#   "english": "dub line here",
#   "syllables": 0,
#   "notes": "brief timing/emotion note"
# }}"""

#     try:
#         # Lowering temperature to 0.4 for more consistent/literal translations
#         resp = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.4, 
#             response_format={"type": "json_object"}
#         )
#         import json
#         content = resp.choices[0].message.content.strip()
#         obj = json.loads(content)
#         english = obj.get("english", jp_text).strip()
#         notes = obj.get("notes", "")
#         # Use the actual syllable count returned by the AI or your estimation function
#         syl_est = obj.get("syllables", 0) 
#     except Exception as e:
#         english = jp_text  # fallback
#         notes = f"GPT error: {e}"
#         syl_est = 0
    
#     return english, notes, syl_est
# # def translate_segment(seg, emotion_label, syllable_target, prev_text=""):
# #     jp_text = seg["text"]
# #     duration = seg["duration"]
# #     gender = seg.get("gender", "neutral")
# #     speaker = seg["speaker"]
    
# #     prompt = f"""You are an adult-oriented anime Tanglish ADR adapter.
# # Translate Japanese → Natural Tanglish (Tamil + English mix).

# # CRITICAL: USE ONLY ENGLISH LETTERS (Romanized). No Tamil script (தமிழ் வேண்டாம்).

# # CONTEXT:
# # - Speaker: {speaker} ({gender})
# # - Emotion: {emotion_label}
# # - Duration: {duration:.2f}s
# # - Target syllables: ~{syllable_target}

# # INSTRUCTIONS:
# # 1. Write Tamil words in English letters (e.g., "Appa", "Enna da", "Sari").
# # 2. Mix in English naturally (e.g., "Ready", "Gun", "Wait").
# # 3. Literal adult language: "shiri no ana" -> "asshole". No sanitizing.
# # 4. ADR: Keep syllable count near {syllable_target}.

# # Japanese: "{jp_text}"

# # JSON response only:
# # {{
# #   "translated_text": "Tanglish line here in English letters",
# #   "syllables": 0,
# #   "notes": "brief note"
# # }}"""

# #     try:
# #         resp = client.chat.completions.create(
# #             model="gpt-4o-mini",
# #             messages=[{"role": "user", "content": prompt}],
# #             temperature=0.4, 
# #             response_format={"type": "json_object"}
# #         )
# #         import json
# #         obj = json.loads(resp.choices[0].message.content.strip())
# #         return obj.get("translated_text", jp_text).strip(), obj.get("notes", ""), obj.get("syllables", 0)
# #     except Exception as e:
# #         return jp_text, f"Error: {e}", 0
# # ========= MAIN =========
# print(f"\n📂 Loading {TRANSCRIPT_JSON}...")

# with open(TRANSCRIPT_JSON, "r", encoding="utf-8") as f:
#     data = json.load(f)

# segments = data["segments"]
# print(f"✅ Loaded {len(segments)} segments")

# # Load full vocals
# full_audio, sr = torchaudio.load(VOCALS_PATH)
# if sr != 16000:
#     full_audio = torchaudio.functional.resample(full_audio, sr, 16000)
# full_audio = full_audio.mean(dim=0).squeeze()  # mono

# # ========= EMOTION DETECTION =========
# print("\n🎭 1. Emotion detection...")
# emotion_results = []

# for i, seg in enumerate(segments):
#     s, e = seg["start"], seg["end"]
#     duration = e - s
    
#     # Extract audio chunk
#     s_idx = int(s * sr)
#     e_idx = int(e * sr)
#     chunk = full_audio[s_idx:e_idx].numpy()
    
#     if len(chunk) < sr * 0.1:  # <100ms
#         emo_label, emo_conf = "unknown", 0.0
#     else:
#         emo_label, emo_conf = classify_emotion(chunk, duration)
    
#     emotion_results.append({
#         "segment_id": seg["id"],
#         "speaker": seg["speaker"],
#         "start": s,
#         "end": e,
#         "duration": duration,
#         "emotion": emo_label,
#         "confidence": emo_conf
#     })
    
#     print(f"  Seg {i+1:02d}: {seg['speaker']} → {emo_label} ({emo_conf:.2f})")

# # Save emotions
# with open(EMOTION_JSON, "w", encoding="utf-8") as f:
#     json.dump({
#         "timestamp": datetime.now().isoformat(),
#         "emotions": emotion_results
#     }, f, ensure_ascii=False, indent=2)

# print(f"✅ Emotions saved: {EMOTION_JSON}")

# # ========= TRANSLATION =========
# print("\n🌐 2. Emotion-aware translation...")
# translated = []
# prev_english = ""

# for i, seg in enumerate(segments):
#     emo = next((e for e in emotion_results if e["segment_id"] == seg["id"]), {})
#     emo_label = emo.get("emotion", "neutral")
    
#     syl_budget = estimate_syllable_budget(seg["duration"], emo_label)
    
#     english, notes, syl_est = translate_segment(
#         seg, emo_label, syl_budget, prev_english
#     )
    
#     translated.append({
#         "segment_id": seg["id"],
#         "speaker": seg["speaker"],
#         "start": seg["start"],
#         "end": seg["end"],
#         "duration": seg["duration"],
#         "japanese": seg["text"],
#         "english": english,
#         "emotion": emo_label,
#         "emotion_confidence": emo.get("confidence", 0.0),
#         "syllable_budget": syl_budget,
#         "notes": notes
#     })
    
#     prev_english = english
#     print(f"  → '{seg['text'][:30]}...' → '{english[:30]}...' [{emo_label}]")

# # Save final translated segments
# with open(TRANSLATED_JSON, "w", encoding="utf-8") as f:
#     json.dump({
#         "timestamp": datetime.now().isoformat(),
#         "total_segments": len(translated),
#         "segments": translated
#     }, f, ensure_ascii=False, indent=2)

# print(f"\n✅ Step 3 complete!")
# print(f"📄 Emotions: {EMOTION_JSON}")
# print(f"📄 Translations: {TRANSLATED_JSON}")
# print("="*60)
"""
STEP 3: Emotion Detection + Translation
========================================
Language mode selection:
  1 — English only
  2 — Tamil only
  3 — Tanglish (Tamil + English mix, modern urban speech)

Output JSON field changes per mode:
  English   → "english" key
  Tamil     → "tamil" key
  Tanglish  → "tamil" key (but mixed content)

Step 4 reads the target field automatically based on
the language_mode stored in the output JSON.
"""

import os
import sys
import json
from datetime import datetime

import numpy as np
import torch
import torchaudio
from transformers import pipeline
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("STEP 3: Emotion Detection + Translation")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# LANGUAGE SELECTION — terminal prompt
# ─────────────────────────────────────────────────────────────
# def choose_language() -> dict:
#     """
#     Ask the user which target language to generate.
#     Returns a config dict consumed by the translation function.
#     """
#     print("\n── Target Language Selection ──\n")
#     print("  [1] English          — standard anime ADR dub")
#     print("  [2] Tamil            — full Tamil (தமிழ்) translation")
#     print("  [3] Tanglish         — Tamil + English mix (modern urban)")
#     print()

#     while True:
#         choice = input("  Enter 1, 2, or 3 › ").strip()
#         if choice in ("1", "2", "3"):
#             break
#         print("  Please enter 1, 2, or 3.")

# #     configs = {
# #         "1": {
# #             "mode":        "english",
# #             "label":       "English",
# #             "output_key":  "english",
# #             "tts_lang":    "en",
# #             "system_prompt": (
# #                 "You are an adult-oriented anime ADR script adapter. "
# #                 "Translate Japanese → natural spoken English dub dialogue."
# #             ),
# #             "instruction": (
# #                 "1. Translate all terms LITERALLY — do not sanitize.\n"
# #                 "2. Match syllable count for lip-sync.\n"
# #                 "3. Sound like natural spoken English.\n"
# #                 "4. Preserve relationship terms (Neesan → Big Sister, etc).\n"
# #                 'Return JSON: {"english": "...", "syllables": 0, "notes": "..."}'
# #             ),
# #             "json_field":  "english",
# #         },
# #         "2": {
# #             "mode":        "tamil",
# #             "label":       "Tamil",
# #             "output_key":  "tamil",
# #             "tts_lang":    "ta",
# #             "system_prompt": (
# #                 "நீங்கள் ஒரு அனிமே டப்பிங் திரைக்கதை மாற்றியமைப்பாளர். "
# #                 "Japanese → இயற்கையான பேச்சு தமிழ் வசனமாக மாற்றுங்கள்."
# #             ),
# #             "instruction": (
# #                 "1. Japanese-ஐ இயற்கையான பேச்சு தமிழாக மொழிபெயர்க்கவும்.\n"
# #                 "2. உணர்ச்சி மற்றும் உதட்டு-ஒத்திசைவுக்கு பொருத்தமான syllable எண்ணிக்கை.\n"
# #                 "3. உறவுச் சொற்களை பாதுகாக்கவும் (அக்கா, தம்பி போன்றவை).\n"
# #                 "4. அனைத்து சொற்களையும் நேரடியாக மொழிபெயர்க்கவும் — மென்மைப்படுத்த வேண்டாம்.\n"
# #                 'Return JSON: {"tamil": "...", "syllables": 0, "notes": "..."}'
# #             ),
# #             "json_field":  "tamil",
# #         },
# #         "3": {
# #             "mode":        "tanglish",
# #             "label":       "Tanglish",
# #             "output_key":  "tamil",
# #             "tts_lang":    "ta",
# #             "system_prompt": (
# #                 "You are an anime dubbing adapter for modern Tamil urban speech. "
# #                 "Generate natural Tanglish — Tamil mixed with common English words."
# #             ),
# #             "instruction": (
# #                 "1. Use natural spoken Tamil mixed with common English terms.\n"
# #                 "   Examples: Gun, Boots, Ready, Start, Fight, Boss, Game, Team.\n"
# #                 "   Character names always stay in English.\n"
# #                 "2. Sound like modern Chennai/urban Tamil street speech.\n"
# #                 "3. Match syllable count for lip-sync.\n"
# #                 "4. Translate all terms literally — do not sanitize.\n"
# #                 "5. Preserve relationship terms (அக்கா, தம்பி, Anna, etc).\n"
# #                 'Return JSON: {"tamil": "tanglish line here", "syllables": 0, "notes": "..."}'
# #             ),
# #             "json_field":  "tamil",
# #         },
# #     }
#     configs = {
#         "1": {
#             "mode":        "english",
#             "label":       "English",
#             "output_key":  "english",
#             "tts_lang":    "en",
#             "system_prompt": (
#                 "You are an elite Anime ADR Script Adapter. "
#                 "Your goal is to transform Japanese meaning into cinematic, punchy English dub dialogue. "
#                 "Prioritize character attitude, 'cool factor,' and mouth-sync over literal translation."
#             ),
#             "instruction": (
#                 "1. ADAPT, DON'T JUST TRANSLATE: Use anime-style idioms and 'cool' speech patterns.\n"
#                 "2. LIP-SYNC FOCUS: Match the energy and syllable count of the original Japanese breath patterns.\n"
#                 "3. CHARACTER FLAVOR: If the character is a 'tsundere,' 'villain,' or 'hero,' reflect that in the slang and tone used.\n"
#                 "4. NO SANITIZATION: Keep the raw, adult edge of the original source.\n"
#                 "5. FORMAT: Return JSON: {'english': 'punchy dub line here', 'syllables': 0, 'notes': 'vibe/intent'}"
#             ),
#             "json_field":  "english",
#         },
#         "2": {
#             "mode":        "tamil",
#             "label":       "Tamil",
#             "output_key":  "tamil",
#             "tts_lang":    "ta",
#             "system_prompt": (
#                 "நீங்கள் ஒரு அனுபவம் வாய்ந்த அனிமே டப்பிங் வசனகர்த்தா (Script Writer). "
#                 "வெறும் மொழிபெயர்ப்பு செய்யாமல், அனிமே கதாபாத்திரத்தின் உணர்ச்சிக்கும் 'Gethu' (attitude) க்கும் ஏற்ப வசனங்களை மாற்றியமைக்கவும்."
#             ),
#             "instruction": (
#                 "1. CINEMATIC TAMIL: புத்தகத் தமிழ் தவிர்க்கவும். அனிமே பாணிக்கு ஏற்ற அதிரடியான பேச்சுத் தமிழைப் பயன்படுத்தவும்.\n"
#                 "2. EMOTION SYNC: அழுகை, கோபம், நக்கல் போன்ற உணர்ச்சிகள் வசனத்தில் வெளிப்பட வேண்டும்.\n"
#                 "3. LIP-SYNC: ஜப்பானிய உதட்டசைவிற்கு ஏற்ப சொற்களைச் சுருக்கவும் அல்லது நீட்டிக்கவும்.\n"
#                 "4. RELATIONSHIPS: அக்கா, தம்பி போன்ற உறவுமுறைகளை சூழலுக்கு ஏற்ப 'Respectful' அல்லது 'Rowdy' ஆக மாற்றவும்.\n"
#                 "5. FORMAT: Return JSON: {'tamil': 'வசனம் இங்கே', 'syllables': 0, 'notes': 'character vibe'}"
#             ),
#             "json_field":  "tamil",
#         },
#         "3": {
#             "mode":        "tanglish",
#             "label":       "Tanglish",
#             "output_key":  "tamil",
#             "tts_lang":    "ta",
#             "system_prompt": (
#                 "You are an Anime Dub Adapter specializing in 'Local' and 'Trendy' Chennai-style dubbing. "
#                 "Think of how a stylish urban anime protagonist would talk—sharp, witty, and mixed with English."
#             ),
#             "instruction": (
#                 "1. URBAN SLANG: Use 'Tanglish' that hits like a modern blockbuster movie (e.g., 'Scene ah?', 'Vibe', 'Mass').\n"
#                 "2. PUNCH DIALOGUE: Every line should have an 'impact.' Avoid flat or robotic sentences.\n"
#                 "3. ENGLISH WEAVING: Use English words for emphasis (e.g., 'Target locked', 'Chance-ay illa', 'Game over').\n"
#                 "4. LIP-MATCH: Ensure the flow fits the fast-paced Japanese speech patterns.\n"
#                 "5. FORMAT: Return JSON: {'tamil': 'Tanglish punch line here', 'syllables': 0, 'notes': 'vibe check'}"
#             ),
#             "json_field":  "tamil",
#         },
#     }
# def choose_language() -> dict:
#     print("\n── Professional ADR Dub-Adaptation Selection ──\n")
#     print("  [1] English ADR (Professional Dub)")
#     print("  [2] Tamil ADR (Professional Dub)")
#     print("  [3] Tanglish ADR (Professional Dub)")

#     while True:
#         choice = input("\n  Enter 1, 2, or 3 › ").strip()
#         if choice in ("1", "2", "3"): break
#         print("  Invalid choice.")

#     # These rules are based on professional ADR standards
#     # focusing on Isochrony (timing) and Labial sync (mouth closure).
#     configs = {
#         "1": {
#             "mode": "english",
#             "output_key": "english",
#             "label": "English",
#             "tts_lang": "en",
#             "system_prompt": (
#                 "You are an Elite Anime ADR Script Adapter. Your task is DUB-ADAPTATION, "
#                 "not just translation. You must rewrite Japanese lines into English that "
#                 "PERFECTLY matches the character's lip flaps."
#             ),
#             "instruction": (
#                 "PROFESSIONAL ADR RULES:\n"
#                 "1. ISOCHRONY: The English line MUST be spoken in the exact duration provided.\n"
#                 "2. SYLLABLE BUDGET: You MUST hit the target syllable count (+/- 1). This is non-negotiable for sync.\n"
#                 "3. LABIAL SYNC: If the Japanese word ends in a lip-closure (sounds like 'u' or 'm'), "
#                 "the English word must end in a labial consonant (P, B, M) or a closed vowel.\n"
#                 "4. PUNCH DIALOGUE: Use concise, punchy slang to save space if the Japanese is fast. "
#                 "Prioritize mouth-sync over word-for-word accuracy.\n"
#                 "5. RELATIONSHIPS: Keep Honorifics (Kun/Chan/Sama) if they fit the beat, otherwise adapt to attitude.\n"
#                 'Return JSON: {"english": "...", "syllables": 0, "sync_accuracy": "high/med", "notes": "..."}'
#             ),
#             "json_field": "english",
#         },
#         "2": {
#             "mode": "tamil",
#             "output_key": "tamil",
#              "label":"Tamil",
#             "tts_lang": "ta",
#             "system_prompt": (
#                 "நீங்கள் ஒரு தொழில்முறை அனிமே டப்பிங் வசனகர்த்தா. "
#                 "ஜப்பானிய வசனங்களை தமிழ் உதட்டசைவுக்கு (Lip flaps) ஏற்ப மாற்றியமைப்பதே உங்கள் பணி."
#             ),
#             "instruction": (
#                 "PROFESSIONAL ADR RULES (TAMIL):\n"
#                 "1. SYLLABLE SYNC: தமிழ்சொற்கள் நீளமாக இருப்பதால், 'Syllable Budget'-ஐ சரியாக பின்பற்றவும். "
#                 "வசனம் நீண்டால் உதட்டசைவு மிஸ் ஆகும்.\n"
#                 "2. COLLOQUIAL TAMIL: புத்தகத் தமிழைத் தவிர்க்கவும். அனிமே பாணிக்கு ஏற்ற 'Local Punch' வசனங்களைப் பயன்படுத்தவும்.\n"
#                 "3. LABIALS (P/B/M): உதடு மூடும் இடங்களில் (ம, ப, வ) போன்ற எழுத்துக்கள் வருமாறு வசனத்தை அமையுங்கள்.\n"
#                 "4. ISOCHRONY: கால அளவை (Duration) ஒருபோதும் தாண்டக்கூடாது.\n"
#                 'Return JSON: {"tamil": "...", "syllables": 0, "sync_accuracy": "high", "notes": "..."}'
#             ),
#             "json_field": "tamil",
#         },
#         "3": {
#             "mode": "tanglish",
#             "output_key": "tamil",
#             "label": "Tanglish",
#             "tts_lang": "ta",
#             "system_prompt": "You are a Trendy Chennai Anime Dub Adapter specializing in Tanglish Punch Dialogues.",
#             "instruction": (
#                 "ADR RULES (TANGLISH):\n"
#                 "1. WEAVE ENGLISH: Use English words (e.g., 'Target Locked', 'Game Over') to control the syllable budget. "
#                 "English words are often shorter than Tamil and help in lip-sync.\n"
#                 "2. ATTITUDE: Use modern urban slang (Vibe, Scene-ah, Mass) to match the 'Gethu' of the character.\n"
#                 "3. HARD LIMIT: Match the syllable budget exactly to fit the Japanese mouth-flaps.\n"
#                 'Return JSON: {"tamil": "Tanglish line here", "syllables": 0, "notes": "..."}'
#             ),
#             "json_field": "tamil",
#         }
#     }
#     cfg = configs[choice]
#     print(f"\n  Selected: {cfg['label']}")
#     print(f"  TTS language code: {cfg['tts_lang']}")
#     print(f"  Output JSON field: {cfg['output_key']}\n")

#     return cfg
def choose_language() -> dict:
    print("\n── Professional ADR Dub-Adaptation Selection ──\n")
    print("  [1] English ADR  (Professional Dub)")
    print("  [2] Tamil ADR    (Professional Dub)")
    print("  [3] Tanglish ADR (Professional Dub)")

    while True:
        choice = input("\n  Enter 1, 2, or 3 › ").strip()
        if choice in ("1", "2", "3"):
            break
        print("  Invalid choice. Enter 1, 2, or 3.")

    # ── SYLLABLE BUDGET FORMULA ───────────────────────────────────────────────
    # English  : ~3.5 syllables/sec  (casual anime speech)
    # Tamil    : ~2.8 syllables/sec  (Tamil is syllabically heavier)
    # Tanglish : ~3.2 syllables/sec  (English words compress the count)
    #
    # The LLM receives a DURATION field per segment and must compute:
    #   target_syllables = round(duration × rate)
    # These rates are embedded in the system prompts below.
    #
    # LABIAL SYNC reference:
    #   Japanese lip-closure sounds: ま(ma) む(mu) ぶ(bu) ぷ(pu) ぼ(bo) ふ(fu)
    #   English equivalents        : M, B, P at word endings
    #   Tamil equivalents          : ம(ma) ப(pa) வ(va) at syllable endings
    # ─────────────────────────────────────────────────────────────────────────

    configs = {
        # ── ENGLISH ──────────────────────────────────────────────────────────
        "1": {
            "mode":       "english",
            "output_key": "english",
            "label":      "English",
            "tts_lang":   "en",
            "text_field": "english",

            "system_prompt": (
                "You are an Elite Anime ADR Script Adapter working at a professional dubbing studio. "
                "Your ONLY job is DUB-ADAPTATION — rewriting Japanese lines into English that fits "
                "the character's exact lip movement, emotional beat, and on-screen duration.\n\n"

                "CORE PHILOSOPHY:\n"
                "- Mouth-sync beats word-for-word accuracy. Always.\n"
                "- A natural-sounding line that fits the flaps is ALWAYS better than a literal "
                "translation that doesn't.\n"
                "- Think in SYLLABLES and BREATH GROUPS, not sentences.\n\n"

                "SYLLABLE RATE: English anime dub runs at ~3.5 syllables/second.\n"
                "Given a segment duration D seconds, your target syllable count = round(D × 3.5).\n"
                "Tolerance: ±1 syllable. Exceeding this breaks lip sync."
            ),

            "instruction": (
                "ADR RULES — apply ALL of these:\n\n"

                "1. ISOCHRONY (timing):\n"
                "   The line MUST fit the duration field exactly when spoken at natural pace.\n"
                "   Use contractions (I'm, don't, can't), dropped syllables, or split pauses '...' "
                "to control timing. A '...' pause = ~0.4s of breath — use it deliberately.\n\n"

                "2. SYLLABLE BUDGET:\n"
                "   Compute target = round(duration × 3.5). Hit it within ±1 syllable.\n"
                "   Count every syllable: 'maybe' = 2, 'kept' = 1, 'together' = 3.\n"
                "   If the JP line is short and fast, use punchy slang. If it's long, "
                "expand with natural English filler ('of all things', 'all along', 'after everything').\n\n"

                "3. LABIAL SYNC:\n"
                "   Inspect the Japanese text for lip-closure sounds: ま む ぶ ぷ ぼ ふ\n"
                "   If the JP line ENDS in a lip closure → the EN line must end with M, B, or P.\n"
                "   Example: ends in 'む' → end with 'them', 'up', 'come', 'keep'.\n\n"

                "4. EXPANSION FOR SHORT LINES:\n"
                "   If the EN translation is naturally shorter than the JP (fewer syllables), "
                "DO NOT pad with silence. Instead:\n"
                "   - Add a hesitation: 'Maybe I just... didn't want anyone to see.'\n"
                "   - Expand the thought: 'Maybe I just kept my mask up — so no one would know.'\n"
                "   - Use an internal monologue tone for reflective lines.\n\n"

                "5. CHARACTER VOICE:\n"
                "   Match the register. A tough character uses clipped sentences. "
                "A soft character uses longer, breathier phrasing. Never make a tsundere sound polite.\n\n"

                "6. PUNCH LINES:\n"
                "   Action/battle lines must hit hard on the stressed syllable. "
                "Avoid soft-sounding words ('perhaps', 'possibly') for aggressive characters.\n\n"

                "Return ONLY valid JSON — no markdown, no extra text:\n"
                '{"english": "...", "syllables": 0, "sync_accuracy": "high/med/low", '
                '"labial_end": true/false, "notes": "one line explaining adaptation choices"}'
            ),

            "json_field": "english",
        },

        # ── TAMIL ─────────────────────────────────────────────────────────────
        "2": {
            "mode":       "tamil",
            "output_key": "tamil",
            "label":      "Tamil",
            "tts_lang":   "ta",
            "text_field": "tamil",

            "system_prompt": (
                "நீங்கள் ஒரு தொழில்முறை அனிமே ADR வசனகர்த்தா. "
                "ஜப்பானிய வசனங்களை தமிழ் உதட்டசைவுக்கு (Lip flaps) மற்றும் "
                "கால அளவுக்கு (Duration) ஏற்ப மாற்றியமைப்பதே உங்கள் பணி.\n\n"

                "CORE PHILOSOPHY:\n"
                "- உதட்டசைவு (Mouth-sync) எப்போதும் நேரடி மொழிபெயர்ப்பை விட முக்கியம்.\n"
                "- இயற்கையான வசனம் = சரியான timing. இரண்டும் ஒன்றாக வர வேண்டும்.\n\n"

                "SYLLABLE RATE: தமிழ் அனிமே டப்பிங் ~2.8 syllables/second.\n"
                "Target syllables = round(duration × 2.8). இதை ±1 tolerance-ல் பின்பற்றவும்."
            ),

            "instruction": (
                "ADR RULES (TAMIL) — அனைத்தையும் பின்பற்றவும்:\n\n"

                "1. ISOCHRONY (கால அளவு):\n"
                "   வசனம் கொடுக்கப்பட்ட duration-ஐ தாண்டவோ குறைக்கவோ கூடாது.\n"
                "   '...' pause = ~0.4 வினாடி — தேவைப்பட்டால் இதை பயன்படுத்தவும்.\n\n"

                "2. SYLLABLE BUDGET:\n"
                "   Target = round(duration × 2.8). ±1 syllable மட்டுமே tolerance.\n"
                "   தமிழ் syllable count: 'வந்தேன்' = 3, 'தெரியும்' = 3, 'நம்பிக்கை' = 4.\n"
                "   வசனம் குறைவாக இருந்தால் — நீட்டிக்கவும், அதிகமாக இருந்தால் — சுருக்கவும்.\n\n"

                "3. LABIAL SYNC (உதடு மூடல்):\n"
                "   ஜப்பானிய வசனம் உதடு மூடும் எழுத்தில் (ま む ぶ ぷ) முடிந்தால்,\n"
                "   தமிழ் வசனமும் ம, ப, வ எழுத்தில் முடிய வேண்டும்.\n"
                "   எடுத்துக்காட்டு: 'む' → 'நாம்', 'தாவிடாம்', 'வேணும்'\n\n"

                "4. COLLOQUIAL TAMIL மட்டுமே:\n"
                "   புத்தகத் தமிழை தவிர்க்கவும். Chennai/Madurai informal speech style.\n"
                "   'அவர்' → 'அவன்/அவ', 'நான் செல்கிறேன்' → 'நான் போறேன்'\n\n"

                "5. CHARACTER REGISTER:\n"
                "   Tough character → கட்டிங் வசனம், குறுகிய sentences.\n"
                "   Soft character → இழுத்த பேச்சு, breath groups.\n"
                "   Tsundere → கோபமான tone, ஆனால் உள்ளே care.\n\n"

                "6. குறுகிய வசனங்களை நீட்டிக்கும் போது:\n"
                "   தயக்கம்: 'ஆமா... நான் மறைச்சிட்டே இருந்தேன்'\n"
                "   உணர்வு விரிவாக்கம்: 'யாருக்கும் தெரியாம மட்டும் போதும்னு நினைச்சேன்'\n\n"

                "Valid JSON மட்டும் return செய்யவும் — markdown இல்லை:\n"
                '{"tamil": "...", "syllables": 0, "sync_accuracy": "high/med/low", '
                '"labial_end": true/false, "notes": "adaptation choice explanation"}'
            ),

            "json_field": "tamil",
        },

        # ── TANGLISH ──────────────────────────────────────────────────────────
        "3": {
            "mode":       "tanglish",
            "output_key": "tamil",
            "label":      "Tanglish",
            "tts_lang":   "ta",
            "text_field": "tamil",

            "system_prompt": (
                "You are a Trendy Chennai Anime Dub Adapter specializing in Tanglish — "
                "the natural code-switching between Tamil and English used by urban Tamil youth.\n\n"

                "CORE PHILOSOPHY:\n"
                "- Tanglish is NOT broken Tamil or broken English. It's a fluid, confident mix.\n"
                "- English words are TOOLS for syllable control — they're shorter and punchier.\n"
                "- The line must sound like something a Chennai college student would actually say.\n\n"

                "SYLLABLE RATE: Tanglish dub runs at ~3.2 syllables/second.\n"
                "Target syllables = round(duration × 3.2). Tolerance: ±1 syllable."
            ),

            "instruction": (
                "ADR RULES (TANGLISH) — apply all:\n\n"

                "1. SYLLABLE BUDGET:\n"
                "   Target = round(duration × 3.2). Hit it within ±1.\n"
                "   Use English keywords to compress: 'Target lock ஆச்சு' < 'இலக்கு நிர்ணயிக்கப்பட்டது'\n"
                "   Use Tamil suffixes on English roots: 'Finish-ஆ', 'Level-அப்', 'Game-over-ஆச்சு'\n\n"

                "2. ISOCHRONY:\n"
                "   The line must fit the duration field exactly at natural speech pace.\n"
                "   '...' = ~0.4s pause. Use it for dramatic beats or short lines.\n\n"

                "3. LABIAL SYNC:\n"
                "   If JP line ends in a lip closure (ま む ぶ ぷ) → end with 'up', 'map', 'bomb', "
                "'வேணும்', 'நாம்', 'தாம்'.\n\n"

                "4. ATTITUDE VOCABULARY:\n"
                "   Use current Chennai slang naturally:\n"
                "   Mass / Scene-ah / Vibe / Gethu / Semma / Poda / Da / Di\n"
                "   'Target locked, da!' / 'Scene-ah இல்ல?' / 'Full vibe-ல இருக்கேன்'\n\n"

                "5. CHARACTER VOICE:\n"
                "   Protagonist: confident, punchy, short bursts.\n"
                "   Villain: slow, deliberate, English-heavy for menace.\n"
                "   Comic relief: fast Tanglish, lots of suffixes on English words.\n\n"

                "6. EXPANSION RULE (for short lines):\n"
                "   Never leave silence. Expand with attitude:\n"
                "   'Maybe I kept it up' → 'Mask-ஐ கழட்டவே இல்ல, da... யாருக்கும் தெரியாம போச்சு'\n\n"

                "Return ONLY valid JSON — no markdown:\n"
                '{"tamil": "Tanglish line here", "syllables": 0, "sync_accuracy": "high/med/low", '
                '"labial_end": true/false, "notes": "one line on adaptation choices"}'
            ),

            "json_field": "tamil",
        },
    }

    cfg = configs[choice]

    print(f"\n  Selected  : {cfg['label']}")
    print(f"  TTS code  : {cfg['tts_lang']}")
    print(f"  JSON field: {cfg['output_key']}")
    print(f"  Syllable rate: "
          f"{'3.5' if choice=='1' else '2.8' if choice=='2' else '3.2'} syl/sec\n")

    return cfg

LANG_CFG = choose_language()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
WORK_DIR        = "work"
VOCALS_PATH     = "work/stems/htdemucs_6s/raw_audio/vocals.wav"
TRANSCRIPT_JSON = os.path.join(WORK_DIR, "transcription_with_speakers.json")
EMOTION_JSON    = os.path.join(WORK_DIR, "emotion_detection.json")
TRANSLATED_JSON = os.path.join(WORK_DIR, "translated_segments_step3.json")

EMOTION_PRIMARY  = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
EMOTION_FALLBACK = "superb/wav2vec2-base-superb-er"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Set OPENAI_API_KEY in your .env file")
client = OpenAI(api_key=OPENAI_API_KEY)

device = 0 if torch.cuda.is_available() else -1

# ─────────────────────────────────────────────────────────────
# LOAD EMOTION MODELS
# ─────────────────────────────────────────────────────────────
print("Loading emotion models...")

emotion_primary = pipeline(
    "audio-classification",
    model=EMOTION_PRIMARY,
    device=device
)
emotion_fallback = pipeline(
    "audio-classification",
    model=EMOTION_FALLBACK,
    device=device
)
print("Emotion models loaded")

# ─────────────────────────────────────────────────────────────
# EMOTION → SYLLABLE RATE
# ─────────────────────────────────────────────────────────────
# Tamil syllables/second — Tamil is a mora-timed language,
# slightly slower than English on average
EMOTION_RATE_ENGLISH = {
    "angry": 5.0, "disgust": 4.2, "fear": 4.8,
    "happy": 4.5, "neutral": 4.0, "sad": 3.5, "surprise": 4.8
}
EMOTION_RATE_TAMIL = {
    "angry": 4.5, "disgust": 3.8, "fear": 4.2,
    "happy": 4.0, "neutral": 3.6, "sad": 3.0, "surprise": 4.2
}

EMOTION_RATE = (
    EMOTION_RATE_TAMIL
    if LANG_CFG["tts_lang"] == "ta"
    else EMOTION_RATE_ENGLISH
)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def classify_emotion(audio_np, duration):
    model = emotion_primary if duration >= 0.5 else emotion_fallback
    result = model(audio_np)
    return result[0]["label"].lower(), result[0]["score"]


def estimate_syllable_budget(duration, emotion):
    rate = EMOTION_RATE.get(emotion, 3.8)
    return max(2, int(duration * rate))


def translate_segment(seg, emotion_label, syllable_target, prev_line=""):
    """
    Translate one segment using the selected language config.
    Works for English, Tamil, and Tanglish — driven by LANG_CFG.
    """
    jp_text  = seg["text"]
    duration = seg["duration"]
    gender   = seg.get("gender", "neutral")
    speaker  = seg["speaker"]

    context = f'\nPrevious line: "{prev_line}"' if prev_line else ""

    prompt = f"""{LANG_CFG["system_prompt"]}

CONTEXT:
- Speaker: {speaker} ({gender})
- Emotion: {emotion_label}
- Duration: {duration:.2f}s
- Target syllables: ~{syllable_target}
{context}

INSTRUCTIONS:
{LANG_CFG["instruction"]}

Japanese source: "{jp_text}"
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        obj       = json.loads(resp.choices[0].message.content.strip())
        out_text  = obj.get(LANG_CFG["json_field"], jp_text).strip()
        notes     = obj.get("notes", "")
        syl_est   = obj.get("syllables", 0)
    except Exception as e:
        out_text = jp_text
        notes    = f"GPT error: {e}"
        syl_est  = 0

    return out_text, notes, syl_est


# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
print(f"\nLoading {TRANSCRIPT_JSON}...")
with open(TRANSCRIPT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)
segments = data["segments"]
print(f"Loaded {len(segments)} segments")

# Load full vocals audio
print(f"Loading vocals: {VOCALS_PATH}")
full_audio, sr = torchaudio.load(VOCALS_PATH)
if sr != 16000:
    full_audio = torchaudio.functional.resample(full_audio, sr, 16000)
    sr = 16000
full_audio = full_audio.mean(dim=0).squeeze()

# ─────────────────────────────────────────────────────────────
# EMOTION DETECTION
# ─────────────────────────────────────────────────────────────
print("\n1. Emotion detection...")
emotion_results = []

for i, seg in enumerate(segments):
    s, e     = seg["start"], seg["end"]
    duration = e - s
    s_idx    = int(s * sr)
    e_idx    = int(e * sr)
    chunk    = full_audio[s_idx:e_idx].numpy()

    if len(chunk) < sr * 0.1:
        emo_label, emo_conf = "unknown", 0.0
    else:
        emo_label, emo_conf = classify_emotion(chunk, duration)

    emotion_results.append({
        "segment_id": seg["id"],
        "speaker":    seg["speaker"],
        "start":      s,
        "end":        e,
        "duration":   duration,
        "emotion":    emo_label,
        "confidence": emo_conf,
    })
    print(f"  Seg {i+1:02d}: {seg['speaker']} → {emo_label} ({emo_conf:.2f})")

with open(EMOTION_JSON, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "emotions":  emotion_results,
    }, f, ensure_ascii=False, indent=2)
print(f"Emotions saved: {EMOTION_JSON}")

# ─────────────────────────────────────────────────────────────
# TRANSLATION
# ─────────────────────────────────────────────────────────────
print(f"\n2. Translation ({LANG_CFG['label']})...")
translated = []
prev_line  = ""

for i, seg in enumerate(segments):
    emo = next(
        (e for e in emotion_results if e["segment_id"] == seg["id"]), {}
    )
    emo_label  = emo.get("emotion", "neutral")
    syl_budget = estimate_syllable_budget(seg["duration"], emo_label)

    out_text, notes, syl_est = translate_segment(
        seg, emo_label, syl_budget, prev_line
    )

    # Build output segment — always include both "english" and "tamil" keys
    # so Step 4 can read either without crashing regardless of mode
    out_seg = {
        "segment_id":         seg["id"],
        "speaker":            seg["speaker"],
        "start":              seg["start"],
        "end":                seg["end"],
        "duration":           seg["duration"],
        "japanese":           seg["text"],
        "english":            out_text if LANG_CFG["mode"] == "english" else "",
        "tamil":              out_text if LANG_CFG["mode"] in ("tamil", "tanglish") else "",
        "emotion":            emo_label,
        "emotion_confidence": emo.get("confidence", 0.0),
        "syllable_budget":    syl_budget,
        "notes":              notes,
    }
    translated.append(out_seg)
    prev_line = out_text

    # Print preview (handles Tamil unicode)
    src_preview = seg["text"][:25]
    tgt_preview = out_text[:30]
    print(f"  [{i+1:02d}] \"{src_preview}\" → \"{tgt_preview}\" [{emo_label}]")

# ─────────────────────────────────────────────────────────────
# SAVE OUTPUT
# ─────────────────────────────────────────────────────────────
output = {
    "timestamp":      datetime.now().isoformat(),
    "total_segments": len(translated),
    "language_mode":  LANG_CFG["mode"],        # "english" | "tamil" | "tanglish"
    "tts_language":   LANG_CFG["tts_lang"],    # "en" | "ta"
    "output_field":   LANG_CFG["output_key"],  # which JSON key has the dub text
    "segments":       translated,
}
with open(TRANSLATED_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nStep 3 complete!")
print(f"  Emotions     : {EMOTION_JSON}")
print(f"  Translations : {TRANSLATED_JSON}")
print(f"  Language     : {LANG_CFG['label']}")
print(f"  TTS code     : {LANG_CFG['tts_lang']}")
print("=" * 60)
print("Next → step4_setup.py  then  step4_genvoice_complete.py")