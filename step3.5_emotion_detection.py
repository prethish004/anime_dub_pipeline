# # # step3.5_emotion_detection.py
# # # 🎯 Detects emotions PER SPEAKER SEGMENT for OpenVoice
# # # Input: work/audio_16k.wav + work/transcription_with_speakers.json
# # # Output: work/emotion_detection.json (used by step5)

# # import json
# # import os
# # import librosa
# # import numpy as np
# # import torch
# # from pathlib import Path
# # import soundfile as sf

# # # Wav2Vec2 emotion model (HuggingFace)
# # from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification
# # import torch.nn.functional as F

# # AUDIO_FILE = "work/audio_16k.wav"
# # DIARIZATION_FILE = "work/transcription_with_speakers.json"
# # OUTPUT_JSON = "work/emotion_detection.json"

# # # Emotion model (pre-trained)
# # EMOTION_MODEL = "superb/wav2vec2-base-superb-er"  # angry, happy, sad, neutral

# # def check_prerequisites():
# #     if not os.path.exists(AUDIO_FILE):
# #         print(f"❌ {AUDIO_FILE} not found!")
# #         return False
# #     if not os.path.exists(DIARIZATION_FILE):
# #         print(f"❌ {DIARIZATION_FILE} not found! Run step3_diarization.py first")
# #         return False
# #     os.makedirs("work", exist_ok=True)
# #     return True

# # def load_data():
# #     # Load full audio
# #     audio, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
# #     # Load diarization + transcription
# #     with open(DIARIZATION_FILE, 'r') as f:
# #         data = json.load(f)
    
# #     print(f"✅ Audio: {len(audio)/sr:.1f}s")
# #     print(f"✅ Segments: {len(data['segments'])}")
# #     return audio, sr, data['segments']

# # def init_emotion_model():
# #     """Load pre-trained emotion detection model"""
# #     print("🔄 Loading emotion model...")
# #     processor = Wav2Vec2Processor.from_pretrained(EMOTION_MODEL)
# #     model = Wav2Vec2ForSequenceClassification.from_pretrained(EMOTION_MODEL)
# #     device = "cuda" if torch.cuda.is_available() else "cpu"
# #     model.to(device)
# #     model.eval()
# #     print(f"✅ Model loaded on {device}")
# #     return processor, model, device

# # def predict_emotion(audio_segment, sr, processor, model, device):
# #     """Predict emotion for audio segment"""
# #     try:
# #         # Process audio
# #         inputs = processor(
# #             audio_segment, 
# #             sampling_rate=sr, 
# #             return_tensors="pt", 
# #             padding=True
# #         )
# #         inputs = {k: v.to(device) for k, v in inputs.items()}
        
# #         # Predict
# #         with torch.no_grad():
# #             logits = model(**inputs).logits
        
# #         predicted_id = torch.argmax(logits, dim=-1).item()
# #         probabilities = F.softmax(logits, dim=-1)
        
# #         # Map to emotion labels
# #         emotions = ['neutral', 'angry', 'disgust', 'fear', 'happy', 'sad']
# #         emotion = emotions[predicted_id]
# #         confidence = probabilities[0][predicted_id].item()
        
# #         return emotion, confidence
        
# #     except Exception as e:
# #         print(f"⚠️  Emotion prediction failed: {e}")
# #         return 'neutral', 0.0

# # def analyze_speaker_emotions(audio, sr, segments, processor, model, device):
# #     """Analyze emotions for all segments"""
# #     print("\n🎭 Emotion detection per segment...")
    
# #     results = {}
# #     for speaker in set(s.get('speaker') for s in segments):
# #         speaker_segments = [s for s in segments if s.get('speaker') == speaker]
# #         results[speaker] = {}
        
# #         print(f"\n{speaker}: {len(speaker_segments)} segments")
        
# #         for seg in speaker_segments:
# #             start_sample = int(seg['start'] * sr)
# #             end_sample = int(seg['end'] * sr)
# #             audio_seg = audio[start_sample:end_sample]
            
# #             # Skip too short segments
# #             if len(audio_seg) < sr * 0.5:  # 0.5s minimum
# #                 results[speaker][f"seg_{seg['start']:.1f}"] = {
# #                     'emotion': 'neutral',
# #                     'confidence': 0.0,
# #                     'duration': seg['duration']
# #                 }
# #                 continue
            
# #             emotion, confidence = predict_emotion(
# #                 audio_seg, sr, processor, model, device
# #             )
            
# #             seg_id = f"seg_{seg['start']:.1f}"
# #             results[speaker][seg_id] = {
# #                 'emotion': emotion,
# #                 'confidence': float(confidence),
# #                 'duration': seg['duration'],
# #                 'text': seg['text'][:50] + "..." if len(seg['text']) > 50 else seg['text']
# #             }
            
# #             print(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] {emotion} ({confidence:.1%})")
    
# #     return results

# # def save_results(emotions):
# #     """Save emotion detection results"""
# #     output = {
# #         'timestamp': datetime.now().isoformat(),
# #         'model': EMOTION_MODEL,
# #         'speakers': emotions,
# #         'total_segments': sum(len(s) for s in emotions.values())
# #     }
    
# #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# #         json.dump(output, f, ensure_ascii=False, indent=2)
    
# #     print(f"\n💾 Saved: {OUTPUT_JSON}")

# # def show_summary(emotions):
# #     """Show emotion summary per speaker"""
# #     print("\n" + "="*60)
# #     print("🎭 EMOTION SUMMARY")
# #     print("="*60)
    
# #     for speaker, segments in emotions.items():
# #         counts = {}
# #         total_conf = 0
# #         for seg_data in segments.values():
# #             emotion = seg_data['emotion']
# #             counts[emotion] = counts.get(emotion, 0) + 1
# #             total_conf += seg_data['confidence']
        
# #         print(f"\n{speaker}:")
# #         for emotion, count in counts.items():
# #             avg_conf = total_conf / len(segments)
# #             print(f"  {emotion}: {count}/{len(segments)} ({count/len(segments)*100:.0f}%) "
# #                   f"avg_conf: {avg_conf:.1%}")

# # def main():
# #     print("="*60)
# #     print("STEP 3.5: Emotion Detection for OpenVoice")
# #     print("="*60)
    
# #     if not check_prerequisites():
# #         return
    
# #     # Load data
# #     audio, sr, segments = load_data()
    
# #     # Initialize model
# #     processor, model, device = init_emotion_model()
    
# #     # Analyze emotions
# #     emotions = analyze_speaker_emotions(audio, sr, segments, processor, model, device)
    
# #     # Save results
# #     save_results(emotions)
# #     show_summary(emotions)
    
# #     print(f"\n✅ Emotion detection complete!")
# #     print(f"📁 Output: {OUTPUT_JSON}")
# #     print("🎯 Ready for step5_openvoice_interactive.py!")

# # if __name__ == "__main__":
# #     main()
# # ============================================================
# # STEP 3.5: Emotion Detection for OpenVoice
# # ============================================================
# # 🎯 Detects emotions PER SPEAKER SEGMENT
# # Input:
# #   - work/audio_16k.wav
# #   - work/transcription_with_speakers.json
# # Output:
# #   - work/emotion_detection.json (used by step5)
# # ============================================================

# import json
# import os
# from datetime import datetime

# import librosa
# import torch
# import torch.nn.functional as F

# # ✅ CORRECT HuggingFace imports for emotion recognition
# from transformers import AutoProcessor, AutoModelForAudioClassification

# # ------------------------------------------------------------
# # Paths
# # ------------------------------------------------------------
# AUDIO_FILE = "work/audio_16k.wav"
# DIARIZATION_FILE = "work/transcription_with_speakers.json"
# OUTPUT_JSON = "work/emotion_detection.json"

# # ✅ Emotion model (audio-only, NO tokenizer)
# EMOTION_MODEL = "superb/wav2vec2-base-superb-er"  # angry, happy, sad, neutral


# # ------------------------------------------------------------
# # Checks
# # ------------------------------------------------------------
# def check_prerequisites():
#     if not os.path.exists(AUDIO_FILE):
#         print(f"❌ Missing audio: {AUDIO_FILE}")
#         return False

#     if not os.path.exists(DIARIZATION_FILE):
#         print(f"❌ Missing diarization file: {DIARIZATION_FILE}")
#         print("➡️ Run step3_diarization.py first")
#         return False

#     os.makedirs("work", exist_ok=True)
#     return True


# # ------------------------------------------------------------
# # Load Audio + Segments
# # ------------------------------------------------------------
# def load_data():
#     audio, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)

#     with open(DIARIZATION_FILE, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     print(f"✅ Audio: {len(audio) / sr:.1f}s")
#     print(f"✅ Segments: {len(data['segments'])}")

#     return audio, sr, data["segments"]


# # ------------------------------------------------------------
# # Initialize Emotion Model (FIXED)
# # ------------------------------------------------------------
# def init_emotion_model():
#     print("🔄 Loading emotion model...")

#     processor = AutoProcessor.from_pretrained(EMOTION_MODEL)
#     model = AutoModelForAudioClassification.from_pretrained(EMOTION_MODEL)

#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     model.to(device)
#     model.eval()

#     print(f"✅ Emotion model loaded on {device}")
#     return processor, model, device


# # ------------------------------------------------------------
# # Emotion Prediction
# # ------------------------------------------------------------
# def predict_emotion(audio_segment, sr, processor, model, device):
#     try:
#         inputs = processor(
#             audio_segment,
#             sampling_rate=sr,
#             return_tensors="pt",
#             padding=True
#         )

#         inputs = {k: v.to(device) for k, v in inputs.items()}

#         with torch.no_grad():
#             outputs = model(**inputs)
#             logits = outputs.logits

#         probs = F.softmax(logits, dim=-1)
#         predicted_id = torch.argmax(probs, dim=-1).item()
#         confidence = probs[0, predicted_id].item()

#         # ✅ SAFE label mapping
#         emotion = model.config.id2label[predicted_id].lower()

#         return emotion, confidence

#     except Exception as e:
#         print(f"⚠️ Emotion prediction failed: {e}")
#         return "neutral", 0.0


# # ------------------------------------------------------------
# # Analyze Emotions Per Speaker
# # ------------------------------------------------------------
# def analyze_speaker_emotions(audio, sr, segments, processor, model, device):
#     print("\n🎭 Emotion detection per segment...")
#     results = {}

#     speakers = sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))

#     for speaker in speakers:
#         speaker_segments = [s for s in segments if s.get("speaker") == speaker]
#         results[speaker] = {}

#         print(f"\n{speaker}: {len(speaker_segments)} segments")

#         for seg in speaker_segments:
#             start = int(seg["start"] * sr)
#             end = int(seg["end"] * sr)
#             audio_seg = audio[start:end]

#             seg_id = f"seg_{seg['start']:.2f}"

#             # ⏱️ Skip tiny segments
#             if len(audio_seg) < sr * 0.5:
#                 results[speaker][seg_id] = {
#                     "emotion": "neutral",
#                     "confidence": 0.0,
#                     "duration": seg["duration"],
#                     "text": seg["text"]
#                 }
#                 continue

#             emotion, confidence = predict_emotion(
#                 audio_seg, sr, processor, model, device
#             )

#             results[speaker][seg_id] = {
#                 "emotion": emotion,
#                 "confidence": round(confidence, 4),
#                 "duration": seg["duration"],
#                 "text": seg["text"]
#             }

#             print(
#                 f"  [{seg['start']:.1f}s–{seg['end']:.1f}s] "
#                 f"{emotion.upper()} ({confidence:.0%})"
#             )

#     return results


# # ------------------------------------------------------------
# # Save Output
# # ------------------------------------------------------------
# def save_results(emotions):
#     output = {
#         "timestamp": datetime.now().isoformat(),
#         "model": EMOTION_MODEL,
#         "speakers": emotions,
#         "total_segments": sum(len(s) for s in emotions.values())
#     }

#     with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
#         json.dump(output, f, ensure_ascii=False, indent=2)

#     print(f"\n💾 Saved emotion file → {OUTPUT_JSON}")


# # ------------------------------------------------------------
# # Summary
# # ------------------------------------------------------------
# def show_summary(emotions):
#     print("\n" + "=" * 60)
#     print("🎭 EMOTION SUMMARY")
#     print("=" * 60)

#     for speaker, segs in emotions.items():
#         counts = {}
#         for s in segs.values():
#             counts[s["emotion"]] = counts.get(s["emotion"], 0) + 1

#         print(f"\n{speaker}:")
#         for emo, count in counts.items():
#             print(f"  {emo}: {count}")


# # ------------------------------------------------------------
# # MAIN
# # ------------------------------------------------------------
# def main():
#     print("=" * 60)
#     print("STEP 3.5: Emotion Detection for OpenVoice")
#     print("=" * 60)

#     if not check_prerequisites():
#         return

#     audio, sr, segments = load_data()
#     processor, model, device = init_emotion_model()

#     emotions = analyze_speaker_emotions(
#         audio, sr, segments, processor, model, device
#     )

#     save_results(emotions)
#     show_summary(emotions)

#     print("\n✅ Emotion detection complete!")
#     print("🎯 Ready for step5_openvoice_interactive.py")


# if __name__ == "__main__":
#     main()
import json
import os
from datetime import datetime

import librosa
import torch
import torch.nn.functional as F

# ✅ Correct imports (NO AutoProcessor)
from transformers import (
    Wav2Vec2FeatureExtractor,
    AutoModelForAudioClassification
)

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
AUDIO_FILE = "separated/htdemucs/audio_16k/vocals.wav"
DIARIZATION_FILE = "work/transcription_with_speakers.json"
OUTPUT_JSON = "work/emotion_detection.json"

# ✅ Emotion model (Audio Classification only)
EMOTION_MODEL = "superb/wav2vec2-base-superb-er"


# ------------------------------------------------------------
# Checks
# ------------------------------------------------------------
def check_prerequisites():
    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Missing audio: {AUDIO_FILE}")
        return False

    if not os.path.exists(DIARIZATION_FILE):
        print(f"❌ Missing diarization file: {DIARIZATION_FILE}")
        print("➡️ Run step3_diarization.py first")
        return False

    os.makedirs("work", exist_ok=True)
    return True


# ------------------------------------------------------------
# Load Audio + Segments
# ------------------------------------------------------------
def load_data():
    audio, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)

    with open(DIARIZATION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✅ Audio: {len(audio) / sr:.1f}s")
    print(f"✅ Segments: {len(data['segments'])}")

    return audio, sr, data["segments"]


# ------------------------------------------------------------
# Initialize Emotion Model (FIXED)
# ------------------------------------------------------------
def init_emotion_model():
    print("🔄 Loading emotion model...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ✅ Correct way (FeatureExtractor only)
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(EMOTION_MODEL)
    model = AutoModelForAudioClassification.from_pretrained(EMOTION_MODEL)

    model.to(device)
    model.eval()

    print(f"✅ Emotion model loaded on {device}")
    return feature_extractor, model, device


# ------------------------------------------------------------
# Emotion Prediction
# ------------------------------------------------------------
def predict_emotion(audio_segment, sr, feature_extractor, model, device):
    try:
        inputs = feature_extractor(
            audio_segment,
            sampling_rate=sr,
            return_tensors="pt"
        )

        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits

        probs = F.softmax(logits, dim=-1)
        predicted_id = torch.argmax(probs, dim=-1).item()
        confidence = probs[0, predicted_id].item()

        emotion = model.config.id2label[predicted_id].lower()

        return emotion, confidence

    except Exception as e:
        print(f"⚠️ Emotion prediction failed: {e}")
        return "neutral", 0.0


# ------------------------------------------------------------
# Analyze Emotions Per Speaker
# ------------------------------------------------------------
def analyze_speaker_emotions(audio, sr, segments, feature_extractor, model, device):
    print("\n🎭 Emotion detection per segment...")
    results = {}

    speakers = sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))

    for speaker in speakers:
        speaker_segments = [s for s in segments if s.get("speaker") == speaker]
        results[speaker] = {}

        print(f"\n{speaker}: {len(speaker_segments)} segments")

        for seg in speaker_segments:
            start = int(seg["start"] * sr)
            end = int(seg["end"] * sr)
            audio_seg = audio[start:end]

            seg_id = f"seg_{seg['start']:.2f}"

            # ⏱️ Skip very short clips (<0.5 sec)
            if len(audio_seg) < sr * 0.5:
                results[speaker][seg_id] = {
                    "emotion": "neutral",
                    "confidence": 0.0,
                    "duration": seg["duration"],
                    "text": seg["text"]
                }
                continue

            emotion, confidence = predict_emotion(
                audio_seg, sr, feature_extractor, model, device
            )

            results[speaker][seg_id] = {
                "emotion": emotion,
                "confidence": round(confidence, 4),
                "duration": seg["duration"],
                "text": seg["text"]
            }

            print(
                f"  [{seg['start']:.1f}s–{seg['end']:.1f}s] "
                f"{emotion.upper()} ({confidence:.0%})"
            )

    return results


# ------------------------------------------------------------
# Save Output
# ------------------------------------------------------------
def save_results(emotions):
    output = {
        "timestamp": datetime.now().isoformat(),
        "model": EMOTION_MODEL,
        "speakers": emotions,
        "total_segments": sum(len(s) for s in emotions.values())
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved emotion file → {OUTPUT_JSON}")


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
def show_summary(emotions):
    print("\n" + "=" * 60)
    print("🎭 EMOTION SUMMARY")
    print("=" * 60)

    for speaker, segs in emotions.items():
        counts = {}
        for s in segs.values():
            counts[s["emotion"]] = counts.get(s["emotion"], 0) + 1

        print(f"\n{speaker}:")
        for emo, count in counts.items():
            print(f"  {emo}: {count}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    print("=" * 60)
    print("STEP 3.5: Emotion Detection for OpenVoice")
    print("=" * 60)

    if not check_prerequisites():
        return

    audio, sr, segments = load_data()
    feature_extractor, model, device = init_emotion_model()

    emotions = analyze_speaker_emotions(
        audio, sr, segments, feature_extractor, model, device
    )

    save_results(emotions)
    show_summary(emotions)

    print("\n✅ Emotion detection complete!")
    print("🎯 Ready for step5_openvoice_interactive.py")


if __name__ == "__main__":
    main()
