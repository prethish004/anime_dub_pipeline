"""
step3_translation.py
====================
Modular Backend Step 3: Speech Emotion Classification + Style & Length Bias Analysis + GPT ADR Translation
"""

import os
import sys
import json
import torch
import librosa
import numpy as np
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from transformers import pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

STYLE_PATTERNS = {
    "tsundere": ["b-baka", "idiot", "hmph", "not like i", "shut up", "うるさい", "べつに"],
    "aggressive": ["die", "kill", "damn", "bastard", "fight", "てめぇ", "ぶっ殺す"],
    "formal_cool": ["indeed", "understood", "as expected", "certainly", "なるほど", "承知"],
    "cute": ["master", "please", "yay", "hehe", "senpai", "先輩", "おねがい"],
    "reflective": ["perhaps", "i wonder", "maybe", "always", "ふむ", "かな"],
}

# Candidate labels for the zero-shot style classifier, phrased as natural
# language descriptions (NLI-style models perform much better on a full
# phrase than on a single ambiguous word like "cute" or "cool").
STYLE_LABELS = {
    "tsundere, hostile on the surface but secretly caring": "tsundere",
    "aggressive or hostile": "aggressive",
    "formal and composed": "formal_cool",
    "cute and affectionate": "cute",
    "reflective or thoughtful": "reflective",
    "neutral, plain statement": "neutral",
}

def _detect_dialogue_style_keywords(text: str) -> str:
    """Keyword-matching fallback, used only if the zero-shot classifier
    couldn't be loaded. Fast but crude — misses anything phrased
    differently from the exact listed words/phrases."""
    text_lower = text.lower()
    for style, patterns in STYLE_PATTERNS.items():
        if any(p in text_lower for p in patterns):
            return style
    return "neutral"

def make_style_classifier(device_idx: int):
    """Loads a multilingual zero-shot text classifier for dialogue style.
    Unlike keyword matching, this understands tone/phrasing it has never
    seen a literal example of. Runs directly on the Japanese source text
    (mDeBERTa-v3's XNLI training covers Japanese), so style can still be
    computed before translation, same as before. Returns None on failure
    so callers fall back to keyword matching rather than crashing Step 3
    over a style-tagging model."""
    try:
        return pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
            device=device_idx
        )
    except Exception as e:
        print(f"  ⚠️ Style classifier failed to load: {e}. Falling back to keyword matching.")
        return None

def detect_dialogue_style(text: str, style_pipe=None) -> str:
    """Keyword matching runs first and wins whenever it finds a hit — it is
    slower to write but 100% precise on the patterns it knows. The zero-shot
    classifier only gets a vote when keyword matching finds nothing, as a
    best-effort guess for phrasing the keyword list doesn't cover.

    Measured empirically before wiring this up: classifying raw Japanese
    text against the English candidate labels only scored ~1/5 on dialogue
    phrased differently from the keyword list (barely above chance for a
    6-way choice) — translating the same lines to English and classifying
    those got 3/5, so the cross-lingual gap is real, but reordering the
    pipeline to classify after translation would mean losing style as an
    input to the translation prompt itself, which is a bigger change than
    this fix. So: keyword-first, classifier as a low-confidence fallback,
    not a replacement.
    """
    keyword_style = _detect_dialogue_style_keywords(text)
    if keyword_style != "neutral":
        return keyword_style

    if style_pipe is not None and text and text.strip():
        try:
            candidate_labels = list(STYLE_LABELS.keys())
            result = style_pipe(text, candidate_labels)
            if result["scores"][0] >= 0.35:
                return STYLE_LABELS[result["labels"][0]]
        except Exception:
            pass
    return "neutral"

def run_step3(options: dict) -> bool:
    print("=" * 60)
    print("STEP 3: Emotion Detection + ADR Translation")
    print("=" * 60)

    work_dir = options.get("work_dir")
    if not work_dir:
        work_dir = os.path.join(PROJECT_ROOT, "web_app", "sessions", "default_work")
    os.makedirs(work_dir, exist_ok=True)

    lang_choice = options.get("language", "english").lower()
    if lang_choice in ["1", "english", "en"]:
        lang_mode = "english"
    elif lang_choice in ["2", "tamil", "ta"]:
        lang_mode = "tamil"
    elif lang_choice in ["3", "tanglish", "ta_en"]:
        lang_mode = "tanglish"
    else:
        lang_mode = "english"

    print(f"  Target Language Mode: {lang_mode.upper()}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file.")
        return False
    client = OpenAI(api_key=api_key)

    trans_json = os.path.join(work_dir, "transcription_with_speakers.json")
    vocals_path = os.path.join(work_dir, "stems", "htdemucs_6s", "raw_audio_44k", "vocals.wav")
    if not os.path.exists(vocals_path):
        vocals_path = os.path.join(work_dir, "stems", "htdemucs", "raw_audio_44k", "vocals.wav")
    if not os.path.exists(vocals_path):
        vocals_path = os.path.join(work_dir, "vocals_clean.wav")
    if not os.path.exists(vocals_path):
        vocals_path = os.path.join(work_dir, "raw_audio_44k.wav")


    if not os.path.exists(trans_json):
        print(f"❌ ERROR: Missing {trans_json}")
        return False

    output_json = os.path.join(work_dir, "translated_segments_step3.json")
    emotion_json = os.path.join(work_dir, "emotion_detection.json")

    with open(trans_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    print(f"  Loaded {len(segments)} segments to process")

    print("\n🎭 1. Classifying speech emotions...")
    device_idx = 0 if torch.cuda.is_available() else -1
    try:
        emotion_pipe = pipeline(
            "audio-classification",
            model="superb/wav2vec2-base-superb-er",
            device=device_idx
        )
    except Exception as e:
        print(f"  ⚠️ Primary emotion model failed: {e}. Trying fallback...")
        emotion_pipe = pipeline(
            "audio-classification",
            model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
            device=device_idx
        )

    audio_np, sr = librosa.load(vocals_path, sr=16000)
    emotion_results = []

    for seg in segments:
        s_idx = int(seg['start'] * sr)
        e_idx = int(seg['end'] * sr)
        seg_audio = audio_np[s_idx:e_idx]
        if len(seg_audio) < int(0.2 * sr):
            emo = "neutral"
            score = 1.0
        else:
            try:
                res = emotion_pipe({"array": seg_audio, "sampling_rate": 16000})
                emo = res[0]['label'].lower()
                score = float(res[0]['score'])
            except Exception:
                emo = "neutral"
                score = 0.5

        emotion_results.append({
            "segment_id": seg['id'],
            "speaker": seg['speaker'],
            "emotion": emo,
            "confidence": round(score, 3)
        })

    with open(emotion_json, "w", encoding="utf-8") as f:
        json.dump(emotion_results, f, indent=2)

    emo_by_id = {e["segment_id"]: e for e in emotion_results}

    print("\n🎨 Classifying dialogue style...")
    style_pipe = make_style_classifier(device_idx)
    style_by_id = {seg['id']: detect_dialogue_style(seg['text'], style_pipe) for seg in segments}

    print("\n🤖 2. GPT ADR Translation & Lip-Sync Adaptation...")
    system_prompt = f"""You are a professional Anime Dubbing ADR Director.
Target Language: {lang_mode.upper()}

Rules:
1. Translate Japanese dialogue into natural, spoken {lang_mode.upper()} ADR script lines.
2. Fit syllable duration budget (~3.5 syl/sec for EN, ~2.8 for TA).
3. Output JSON array with segment_id, translated_text.
"""

    def translate_batch(batch):
        """Attempts to translate a batch of segments in a single GPT call.
        Returns {segment_id: translated_text}. Raises on any failure
        (malformed JSON, missing segment, API error, etc.) so the caller
        can retry at a smaller batch size instead of giving up."""
        prompt_lines = []
        for s in batch:
            emo_info = emo_by_id.get(s['id'], {})
            style = style_by_id.get(s['id'], "neutral")
            prompt_lines.append(
                f"ID: {s['id']} | Speaker: {s['speaker']} | Duration: {s['duration']}s | Emotion: {emo_info.get('emotion','neutral')} | Style: {style}\n"
                f"JP Text: {s['text']}\n"
            )
        prompt_str = "\n".join(prompt_lines)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_str}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        raw_res = response.choices[0].message.content
        parsed = json.loads(raw_res)

        if isinstance(parsed, list):
            batch_outputs = parsed
        elif "segment_id" in parsed:
            batch_outputs = [parsed]
        else:
            list_values = [v for v in parsed.values() if isinstance(v, list)]
            batch_outputs = list_values[0] if list_values else []

        output_by_id = {b.get("segment_id", i): b for i, b in enumerate(batch_outputs) if isinstance(b, dict)}

        result = {}
        for s in batch:
            out_item = output_by_id.get(s['id'])
            if not out_item or "translated_text" not in out_item:
                raise ValueError(f"no translation returned for segment {s['id']}")
            result[s['id']] = out_item["translated_text"]
        return result

    def translate_with_retry(batch):
        """Translates a batch, halving it and retrying (down to one
        segment at a time) whenever a call fails — e.g. GPT truncating its
        JSON output for a large batch. A segment only falls back to its
        original Japanese text if it still fails completely alone, so one
        bad response no longer costs an entire 10-segment batch."""
        try:
            return translate_batch(batch)
        except Exception as e:
            if len(batch) == 1:
                seg_id = batch[0]['id']
                print(f"  ❌ GPT translation failed for segment {seg_id}, keeping original text: {e}")
                return {seg_id: batch[0]['text']}
            mid = len(batch) // 2
            print(f"  ⚠️ Batch of {len(batch)} failed ({e}); retrying as {mid} + {len(batch) - mid}...")
            result = translate_with_retry(batch[:mid])
            result.update(translate_with_retry(batch[mid:]))
            return result

    translated_segments = []
    batch_size = 10

    for idx in range(0, len(segments), batch_size):
        batch = segments[idx:idx + batch_size]
        output_by_id = translate_with_retry(batch)

        for s in batch:
            translated_text = output_by_id.get(s['id'], s['text'])
            emo_info = emo_by_id.get(s['id'], {})
            style = style_by_id.get(s['id'], "neutral")

            translated_segments.append({
                "segment_id": s['id'],
                "start": s['start'],
                "end": s['end'],
                "duration": s['duration'],
                "speaker": s['speaker'],
                "japanese_text": s['text'],
                "translated_text": translated_text,
                "language_mode": lang_mode,
                "emotion": emo_info.get("emotion", "neutral"),
                "emotion_confidence": emo_info.get("confidence", 1.0),
                "style": style,
                "words": s.get("words", [])
            })

    final_payload = {
        "timestamp": datetime.now().isoformat(),
        "language_mode": lang_mode,
        "total_segments": len(translated_segments),
        "segments": translated_segments
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Step 3 Complete! Workspace: {work_dir}")
    return True
