import os
import json
from datetime import datetime
import numpy as np
import torch
import torchaudio
from transformers import pipeline
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

print("="*60)
print("STEP 3: Emotion Detection + Translation")
print("="*60)

# ========= CONFIG =========
WORK_DIR = "work"
VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio/vocals.wav"
TRANSCRIPT_JSON = os.path.join(WORK_DIR, "transcription_with_speakers.json")
EMOTION_JSON = os.path.join(WORK_DIR, "emotion_detection.json")
TRANSLATED_JSON = os.path.join(WORK_DIR, "translated_segments_step3.json")

# ✅ WORKING MODELS (no preprocessor issues)
EMOTION_PRIMARY = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"  # 8-class
EMOTION_FALLBACK = "superb/wav2vec2-base-superb-er"  # 4-class

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Set OPENAI_API_KEY environment variable")
client = OpenAI(api_key=OPENAI_API_KEY)

device = 0 if torch.cuda.is_available() else -1

# ========= LOAD MODELS =========
print("🔄 Loading emotion models...")

# Primary: 8 emotions (angry, disgust, fear, happy, neutral, sad, surprise)
emotion_primary = pipeline(
    "audio-classification",
    model=EMOTION_PRIMARY,
    device=device
)

# Fallback: 4 emotions (angry, happy, neutral, sad)
emotion_fallback = pipeline(
    "audio-classification", 
    model=EMOTION_FALLBACK,
    device=device
)

print("✅ Emotion models loaded")

# Emotion → syllables/second (tune these!)
EMOTION_RATE = {
    "angry": 5.0,
    "disgust": 4.2,
    "fear": 4.8,
    "happy": 4.5,
    "neutral": 4.0,
    "sad": 3.5,
    "surprise": 4.8
}

def load_audio_segment(path, start_sec, end_sec, target_sr=16000):
    """Load cropped segment from full audio."""
    wav, sr = torchaudio.load(path)
    if sr != target_sr:
        wav = torchaudio.functional.resample(wav, sr, target_sr)
        sr = target_sr
    if wav.size(0) > 1:
        wav = wav.mean(dim=0, keepdim=True)
    
    s_idx = int(start_sec * sr)
    e_idx = int(end_sec * sr)
    return wav.squeeze(0)[s_idx:e_idx].numpy()

def classify_emotion(audio_np, duration):
    """Classify emotion with fallback logic."""
    if duration >= 0.5:  # Use 8-class model
        result = emotion_primary(audio_np)
    else:  # Use 4-class for short clips
        result = emotion_fallback(audio_np)
    
    label = result[0]['label'].lower()
    conf = result[0]['score']
    
    return label, conf

def estimate_syllable_budget(duration, emotion):
    rate = EMOTION_RATE.get(emotion, 4.0)
    target = int(duration * rate)
    return max(3, target)

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
def translate_segment(seg, emotion_label, syllable_target, prev_english=""):
    """GPT translation with explicit accuracy and ADR constraints."""
    jp_text = seg["text"]
    duration = seg["duration"]
    gender = seg.get("gender", "neutral")
    speaker = seg["speaker"]
    
    context = ""
    if prev_english:
        context = f"\nPrevious English line: \"{prev_english}\""
    
    # Updated prompt with instructions for explicit/literal accuracy
    prompt = f"""You are an adult-oriented anime ADR script adapter.

Translate/adapt Japanese → English dub line.

CONTEXT:
- Speaker: {speaker} ({gender})
- Emotion: {emotion_label}  
- Duration: {duration:.2f}s
- Target syllables: ~{syllable_target}

INSTRUCTIONS:
1. MANDATORY: Translate all anatomical terms and vulgarities LITERALLY (e.g., "shiri no ana" must be "asshole" or "anus"). Do not sanitize or soften the language.
2. Preserve the specific relationship terms (e.g., "Neesan" as "Sister" or "Big Sister").
3. Match speaking rhythm for lip-sync (syllable count: {syllable_target}).
4. Sound like natural, spoken adult dialogue.

{context}

Japanese: "{jp_text}"

JSON response only:
{{
  "english": "dub line here",
  "syllables": 0,
  "notes": "brief timing/emotion note"
}}"""

    try:
        # Lowering temperature to 0.4 for more consistent/literal translations
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4, 
            response_format={"type": "json_object"}
        )
        import json
        content = resp.choices[0].message.content.strip()
        obj = json.loads(content)
        english = obj.get("english", jp_text).strip()
        notes = obj.get("notes", "")
        # Use the actual syllable count returned by the AI or your estimation function
        syl_est = obj.get("syllables", 0) 
    except Exception as e:
        english = jp_text  # fallback
        notes = f"GPT error: {e}"
        syl_est = 0
    
    return english, notes, syl_est
# ========= MAIN =========
print(f"\n📂 Loading {TRANSCRIPT_JSON}...")

with open(TRANSCRIPT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

segments = data["segments"]
print(f"✅ Loaded {len(segments)} segments")

# Load full vocals
full_audio, sr = torchaudio.load(VOCALS_PATH)
if sr != 16000:
    full_audio = torchaudio.functional.resample(full_audio, sr, 16000)
full_audio = full_audio.mean(dim=0).squeeze()  # mono

# ========= EMOTION DETECTION =========
print("\n🎭 1. Emotion detection...")
emotion_results = []

for i, seg in enumerate(segments):
    s, e = seg["start"], seg["end"]
    duration = e - s
    
    # Extract audio chunk
    s_idx = int(s * sr)
    e_idx = int(e * sr)
    chunk = full_audio[s_idx:e_idx].numpy()
    
    if len(chunk) < sr * 0.1:  # <100ms
        emo_label, emo_conf = "unknown", 0.0
    else:
        emo_label, emo_conf = classify_emotion(chunk, duration)
    
    emotion_results.append({
        "segment_id": seg["id"],
        "speaker": seg["speaker"],
        "start": s,
        "end": e,
        "duration": duration,
        "emotion": emo_label,
        "confidence": emo_conf
    })
    
    print(f"  Seg {i+1:02d}: {seg['speaker']} → {emo_label} ({emo_conf:.2f})")

# Save emotions
with open(EMOTION_JSON, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "emotions": emotion_results
    }, f, ensure_ascii=False, indent=2)

print(f"✅ Emotions saved: {EMOTION_JSON}")

# ========= TRANSLATION =========
print("\n🌐 2. Emotion-aware translation...")
translated = []
prev_english = ""

for i, seg in enumerate(segments):
    emo = next((e for e in emotion_results if e["segment_id"] == seg["id"]), {})
    emo_label = emo.get("emotion", "neutral")
    
    syl_budget = estimate_syllable_budget(seg["duration"], emo_label)
    
    english, notes, syl_est = translate_segment(
        seg, emo_label, syl_budget, prev_english
    )
    
    translated.append({
        "segment_id": seg["id"],
        "speaker": seg["speaker"],
        "start": seg["start"],
        "end": seg["end"],
        "duration": seg["duration"],
        "japanese": seg["text"],
        "english": english,
        "emotion": emo_label,
        "emotion_confidence": emo.get("confidence", 0.0),
        "syllable_budget": syl_budget,
        "notes": notes
    })
    
    prev_english = english
    print(f"  → '{seg['text'][:30]}...' → '{english[:30]}...' [{emo_label}]")

# Save final translated segments
with open(TRANSLATED_JSON, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "total_segments": len(translated),
        "segments": translated
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ Step 3 complete!")
print(f"📄 Emotions: {EMOTION_JSON}")
print(f"📄 Translations: {TRANSLATED_JSON}")
print("="*60)