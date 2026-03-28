# # # # import os
# # # # import json
# # # # import time
# # # # from datetime import datetime

# # # # import torch
# # # # from TTS.api import TTS
# # # # from pydub import AudioSegment


# # # # # ==============================
# # # # # CONFIG
# # # # # ==============================
# # # # TRANSLATED_JSON = "work/translated_segments_interactive.json"
# # # # OUTPUT_DIR = "work/voice_clips"
# # # # METADATA_OUT = "work/voice_clips_metadata.json"
# # # # SAMPLE_ROOT = "sample_voices"

# # # # LANGUAGE_CODE = "en"

# # # # # Duration control limits (prevent robotic distortion)
# # # # MAX_STRETCH = 1.25
# # # # MIN_STRETCH = 0.85

# # # # # Emotion mapping from your JSON format
# # # # EMOTION_MAP = {
# # # #     "hap": "happy",
# # # #     "sad": "sad",
# # # #     "ang": "angry",
# # # #     "fea": "fearful",
# # # #     "sur": "surprised",
# # # #     "neu": "neutral"
# # # # }

# # # # # Better anime-style emotional conditioning
# # # # STYLE_PROMPTS = {
# # # #     "happy": "In a bright, cheerful anime voice, say:",
# # # #     "sad": "In a soft emotional voice, say:",
# # # #     "angry": "In an intense angry anime voice, say:",
# # # #     "fearful": "In a trembling fearful voice, say:",
# # # #     "surprised": "In a shocked surprised voice, say:",
# # # #     "neutral": ""
# # # # }


# # # # # ==============================
# # # # # UTILITIES
# # # # # ==============================
# # # # def check_files():
# # # #     if not os.path.exists(TRANSLATED_JSON):
# # # #         print(f"❌ Missing {TRANSLATED_JSON}")
# # # #         return False
# # # #     os.makedirs(OUTPUT_DIR, exist_ok=True)
# # # #     return True


# # # # def load_segments():
# # # #     with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
# # # #         data = json.load(f)
# # # #     segments = data.get("segments", [])
# # # #     print(f"📄 Loaded {len(segments)} segments")
# # # #     return segments


# # # # def list_samples():
# # # #     samples = {"male": [], "female": []}
# # # #     for gender in samples.keys():
# # # #         folder = os.path.join(SAMPLE_ROOT, gender)
# # # #         if os.path.isdir(folder):
# # # #             for f in sorted(os.listdir(folder)):
# # # #                 if f.lower().endswith((".wav", ".mp3")):
# # # #                     samples[gender].append(os.path.join(folder, f))
# # # #     return samples


# # # # def select_voice(samples):
# # # #     print("\n🎭 Select voice sample")
# # # #     all_samples = samples["male"] + samples["female"]

# # # #     if not all_samples:
# # # #         raise Exception("❌ No voice samples found in sample_voices folder!")

# # # #     for i, path in enumerate(all_samples, 1):
# # # #         print(f"[{i}] {os.path.basename(path)}")

# # # #     choice = input("Choose sample number (default=1): ").strip()
# # # #     idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(all_samples) else 0

# # # #     selected = all_samples[idx]
# # # #     print(f"✅ Selected: {os.path.basename(selected)}")
# # # #     return selected


# # # # def build_emotional_text(seg):
# # # #     base_text = seg.get("translated_text", "")
# # # #     emotion_short = seg.get("emotion", "neu").lower()
# # # #     emotion = EMOTION_MAP.get(emotion_short, "neutral")

# # # #     confidence = seg.get("emotion_confidence", 0.0)

# # # #     if confidence < 0.6:
# # # #         emotion = "neutral"

# # # #     style_prefix = STYLE_PROMPTS.get(emotion, "")
# # # #     if style_prefix:
# # # #         final_text = f"{style_prefix} {base_text}"
# # # #     else:
# # # #         final_text = base_text

# # # #     return final_text, emotion


# # # # def match_duration(audio_path, target_duration):
# # # #     audio = AudioSegment.from_file(audio_path)
# # # #     current_duration = len(audio) / 1000.0

# # # #     if target_duration <= 0:
# # # #         return

# # # #     ratio = target_duration / current_duration

# # # #     # Keep safe range
# # # #     if ratio > MAX_STRETCH:
# # # #         ratio = MAX_STRETCH
# # # #     elif ratio < MIN_STRETCH:
# # # #         ratio = MIN_STRETCH

# # # #     # Only adjust if outside 10% tolerance
# # # #     if abs(current_duration - target_duration) / target_duration > 0.1:
# # # #         new_frame_rate = int(audio.frame_rate * ratio)
# # # #         stretched = audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
# # # #         stretched = stretched.set_frame_rate(audio.frame_rate)
# # # #         stretched.export(audio_path, format="wav")


# # # # # ==============================
# # # # # LOAD XTTS
# # # # # ==============================
# # # # def load_model():
# # # #     device = "cuda" if torch.cuda.is_available() else "cpu"
# # # #     print(f"🧠 Loading XTTS on {device} ...")
# # # #     tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
# # # #     print("✅ Model loaded")
# # # #     return tts


# # # # # ==============================
# # # # # MAIN
# # # # # ==============================
# # # # def generate():
# # # #     if not check_files():
# # # #         return

# # # #     segments = load_segments()
# # # #     samples = list_samples()
# # # #     selected_voice = select_voice(samples)

# # # #     tts = load_model()

# # # #     clips_meta = []

# # # #     print("\n🎙 Generating voices...\n")

# # # #     for idx, seg in enumerate(segments, 1):

# # # #         text, emotion = build_emotional_text(seg)
# # # #         duration_target = seg.get("duration", 0.0)

# # # #         if not text.strip():
# # # #             print(f"[{idx}] Empty text — skipping")
# # # #             continue

# # # #         print(f"[{idx}/{len(segments)}] Emotion: {emotion}")
# # # #         print(f"Text: {text[:70]}...\n")

# # # #         output_path = os.path.join(
# # # #             OUTPUT_DIR,
# # # #             f"segment_{idx:03d}.wav"
# # # #         )

# # # #         try:
# # # #             tts.tts_to_file(
# # # #                 text=text,
# # # #                 file_path=output_path,
# # # #                 speaker_wav=[selected_voice],
# # # #                 language=LANGUAGE_CODE,
# # # #             )
# # # #         except Exception as e:
# # # #             print(f"❌ TTS error: {e}")
# # # #             continue

# # # #         # Duration sync
# # # #         try:
# # # #             match_duration(output_path, duration_target)
# # # #         except Exception as e:
# # # #             print(f"⚠ Duration match error: {e}")

# # # #         seg_meta = seg.copy()
# # # #         seg_meta["audio_file"] = output_path
# # # #         seg_meta["emotion_used"] = emotion

# # # #         clips_meta.append(seg_meta)

# # # #         time.sleep(0.1)

# # # #     metadata = {
# # # #         "timestamp": datetime.now().isoformat(),
# # # #         "backend": "xtts_v2",
# # # #         "voice_sample": selected_voice,
# # # #         "total_clips": len(clips_meta),
# # # #         "clips": clips_meta
# # # #     }

# # # #     with open(METADATA_OUT, "w", encoding="utf-8") as f:
# # # #         json.dump(metadata, f, ensure_ascii=False, indent=2)

# # # #     print("\n✅ Voice generation complete!")
# # # #     print(f"📁 Audio clips: {OUTPUT_DIR}")
# # # #     print(f"💾 Metadata saved: {METADATA_OUT}")
# # # #     print("\nNext: python step6_final_assembly.py")


# # # # if __name__ == "__main__":
# # # #     generate()
# # # import os
# # # import json
# # # import time
# # # from datetime import datetime

# # # import torch
# # # from TTS.api import TTS
# # # from pydub import AudioSegment


# # # # CONFIG
# # # TRANSLATED_JSON = "work/translated_segments_interactive.json"
# # # OUTPUT_DIR = "work/voice_clips"
# # # METADATA_OUT = "work/voice_clips_metadata.json"
# # # SAMPLE_ROOT = "sample_voices"
# # # LANGUAGE_CODE = "en"

# # # MAX_STRETCH = 1.25
# # # MIN_STRETCH = 0.85


# # # EMOTION_MAP = {
# # #     "hap": "happy",
# # #     "sad": "sad",
# # #     "ang": "angry",
# # #     "fea": "fearful",
# # #     "sur": "surprised",
# # #     "neu": "neutral"
# # # }

# # # STYLE_PROMPTS = {
# # #     "happy": "In a bright cheerful anime voice, say:",
# # #     "sad": "In a soft emotional voice, say:",
# # #     "angry": "In an intense angry anime voice, say:",
# # #     "fearful": "In a trembling fearful voice, say:",
# # #     "surprised": "In a shocked surprised voice, say:",
# # #     "neutral": ""
# # # }


# # # def load_segments():
# # #     with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
# # #         data = json.load(f)
# # #     return data.get("segments", [])


# # # def list_voice_samples():
# # #     samples = []
# # #     for root, _, files in os.walk(SAMPLE_ROOT):
# # #         for f in files:
# # #             if f.lower().endswith((".wav", ".mp3")):
# # #                 samples.append(os.path.join(root, f))
# # #     return sorted(samples)


# # # def get_unique_speakers(segments):
# # #     return sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))


# # # def manual_speaker_mapping(unique_speakers, samples):
# # #     mapping = {}

# # #     print("\n🎭 MANUAL VOICE ASSIGNMENT\n")

# # #     for speaker in unique_speakers:
# # #         print(f"\nAssign voice for speaker: {speaker}")

# # #         for i, sample in enumerate(samples, 1):
# # #             print(f"[{i}] {os.path.basename(sample)}")

# # #         choice = input("Choose sample number: ").strip()
# # #         while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
# # #             choice = input("Invalid. Choose again: ").strip()

# # #         mapping[speaker] = samples[int(choice) - 1]
# # #         print(f"✅ {speaker} → {os.path.basename(mapping[speaker])}")

# # #     return mapping
# # # def choose_voice(samples, message="Choose voice sample"):
# # #     print(f"\n{message}")
# # #     for i, sample in enumerate(samples, 1):
# # #         print(f"[{i}] {os.path.basename(sample)}")

# # #     choice = input("Choose sample number: ").strip()
# # #     while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
# # #         choice = input("Invalid. Choose again: ").strip()

# # #     return samples[int(choice) - 1]

# # # # def build_emotional_text(seg):
# # # #     base_text = seg.get("translated_text", "")
# # # #     emotion_code = seg.get("emotion", "neu").lower()
# # # #     emotion = EMOTION_MAP.get(emotion_code, "neutral")

# # # #     confidence = seg.get("emotion_confidence", 0.0)
# # # #     if confidence < 0.6:
# # # #         emotion = "neutral"

# # # #     prefix = STYLE_PROMPTS.get(emotion, "")
# # # #     return f"{prefix} {base_text}" if prefix else base_text, emotion

# # # def build_emotional_text(seg):
# # #     text = seg.get("translated_text", "")
# # #     emotion_code = seg.get("emotion", "neu").lower()
# # #     confidence = seg.get("emotion_confidence", 0.0)

# # #     if confidence < 0.6:
# # #         return text, "neutral"

# # #     if emotion_code == "ang":
# # #         text = text.rstrip(".") + "!"
# # #     elif emotion_code == "sad":
# # #         text = text.rstrip(".") + "..."
# # #     elif emotion_code == "hap":
# # #         text = text.rstrip(".") + "!"
# # #     elif emotion_code == "fea":
# # #         text = "W-" + text

# # #     return text, emotion_code

# # # def match_duration(audio_path, target_duration):
# # #     audio = AudioSegment.from_file(audio_path)
# # #     current_duration = len(audio) / 1000.0

# # #     if target_duration <= 0:
# # #         return

# # #     ratio = target_duration / current_duration

# # #     if ratio > MAX_STRETCH:
# # #         ratio = MAX_STRETCH
# # #     elif ratio < MIN_STRETCH:
# # #         ratio = MIN_STRETCH

# # #     if abs(current_duration - target_duration) / target_duration > 0.1:
# # #         new_rate = int(audio.frame_rate * ratio)
# # #         stretched = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
# # #         stretched = stretched.set_frame_rate(audio.frame_rate)
# # #         stretched.export(audio_path, format="wav")


# # # def load_model():
# # #     device = "cuda" if torch.cuda.is_available() else "cpu"
# # #     print(f"\n🧠 Loading XTTS on {device}...")
# # #     model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
# # #     print("✅ Model loaded\n")
# # #     return model


# # # # def generate():
# # # #     os.makedirs(OUTPUT_DIR, exist_ok=True)

# # # #     segments = load_segments()
# # # #     samples = list_voice_samples()

# # # #     if not samples:
# # # #         raise Exception("❌ No voice samples found in sample_voices folder")

# # # #     unique_speakers = get_unique_speakers(segments)
# # # #     speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)

# # # #     tts = load_model()

# # # #     metadata = []

# # # #     print("\n🎙 Generating Voice Clips...\n")

# # # #     for idx, seg in enumerate(segments, 1):

# # # #         speaker = seg.get("speaker", "UNKNOWN")
# # # #         sample_voice = speaker_voice_map[speaker]

# # # #         text, emotion = build_emotional_text(seg)
# # # #         target_duration = seg.get("duration", 0)

# # # #         output_path = os.path.join(
# # # #             OUTPUT_DIR,
# # # #             f"segment_{idx:03d}_{speaker}.wav"
# # # #         )

# # # #         print(f"[{idx}] Speaker: {speaker} | Emotion: {emotion}")

# # # #         tts.tts_to_file(
# # # #             text=text,
# # # #             file_path=output_path,
# # # #             speaker_wav=[sample_voice],
# # # #             language=LANGUAGE_CODE
# # # #         )

# # # #         match_duration(output_path, target_duration)

# # # #         seg_meta = seg.copy()
# # # #         seg_meta["audio_file"] = output_path
# # # #         seg_meta["voice_sample"] = sample_voice
# # # #         seg_meta["emotion_used"] = emotion

# # # #         metadata.append(seg_meta)
# # # #         time.sleep(0.1)

# # # #     final_meta = {
# # # #         "timestamp": datetime.now().isoformat(),
# # # #         "speakers": speaker_voice_map,
# # # #         "total_clips": len(metadata),
# # # #         "clips": metadata
# # # #     }

# # # #     with open(METADATA_OUT, "w", encoding="utf-8") as f:
# # # #         json.dump(final_meta, f, indent=2, ensure_ascii=False)

# # # #     print("\n✅ Multi-speaker voice generation finished.")
# # # def generate():
# # #     os.makedirs(OUTPUT_DIR, exist_ok=True)

# # #     segments = load_segments()
# # #     samples = list_voice_samples()

# # #     if not samples:
# # #         raise Exception("❌ No voice samples found in sample_voices folder")

# # #     print("\nVoice Assignment Mode")
# # #     print("1 - Speaker based")
# # #     print("2 - Segment based")
# # #     print("3 - Speaker + override")

# # #     mode = input("Choose mode: ").strip()

# # #     speaker_voice_map = {}

# # #     if mode in ["1", "3"]:
# # #         unique_speakers = get_unique_speakers(segments)
# # #         speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)

# # #     tts = load_model()

# # #     metadata = []

# # #     print("\n🎙 Generating Voice Clips...\n")

# # #     for idx, seg in enumerate(segments, 1):

# # #         speaker = seg.get("speaker", "UNKNOWN")

# # #         # -------- Voice Selection Logic --------

# # #         if mode == "1":
# # #             sample_voice = speaker_voice_map[speaker]

# # #         elif mode == "2":
# # #             sample_voice = choose_voice(
# # #                 samples,
# # #                 f"Segment {idx} | Speaker: {speaker}\nText: {seg.get('translated_text','')}"
# # #             )

# # #         elif mode == "3":
# # #             default_voice = speaker_voice_map[speaker]

# # #             print(f"\nSegment {idx} | Speaker: {speaker}")
# # #             print(f"Default voice: {os.path.basename(default_voice)}")
# # #             override = input("Override voice? (y/n): ").strip().lower()

# # #             if override == "y":
# # #                 sample_voice = choose_voice(samples, "Choose override voice")
# # #             else:
# # #                 sample_voice = default_voice

# # #         else:
# # #             raise Exception("Invalid mode selected")

# # #         # -------- Emotion Processing --------

# # #         text, emotion = build_emotional_text(seg)
# # #         target_duration = seg.get("duration", 0)

# # #         output_path = os.path.join(
# # #             OUTPUT_DIR,
# # #             f"segment_{idx:03d}_{speaker}.wav"
# # #         )

# # #         print(f"[{idx}] Speaker: {speaker} | Emotion: {emotion}")
# # #         print(f"Voice: {os.path.basename(sample_voice)}")

# # #         tts.tts_to_file(
# # #             text=text,
# # #             file_path=output_path,
# # #             speaker_wav=[sample_voice],
# # #             language=LANGUAGE_CODE
# # #         )

# # #         match_duration(output_path, target_duration)

# # #         seg_meta = seg.copy()
# # #         seg_meta["audio_file"] = output_path
# # #         seg_meta["voice_sample"] = sample_voice
# # #         seg_meta["emotion_used"] = emotion

# # #         metadata.append(seg_meta)
# # #         time.sleep(0.1)

# # #     final_meta = {
# # #         "timestamp": datetime.now().isoformat(),
# # #         "speakers": speaker_voice_map,
# # #         "total_clips": len(metadata),
# # #         "clips": metadata
# # #     }

# # #     with open(METADATA_OUT, "w", encoding="utf-8") as f:
# # #         json.dump(final_meta, f, indent=2, ensure_ascii=False)

# # #     print("\n✅ Multi-speaker voice generation finished.")

# # # if __name__ == "__main__":
# # #     generate()
# # # import os
# # # import json
# # # import time
# # # from datetime import datetime
# # # import torch
# # # from TTS.api import TTS
# # # from pydub import AudioSegment

# # # # CONFIG (unchanged)
# # # TRANSLATED_JSON = "work/translated_segments_interactive.json"
# # # OUTPUT_DIR = "work/voice_clips"
# # # METADATA_OUT = "work/voice_clips_metadata.json"
# # # SAMPLE_ROOT = "sample_voices"
# # # LANGUAGE_CODE = "en"

# # # MAX_STRETCH = 1.25
# # # MIN_STRETCH = 0.85

# # # # IMPROVED: Emotion → Prosody mapping (XTTS-native control)
# # # EMOTION_PROSODY = {
# # #     "happy":    {"speed": 1.15, "pitch_shift": 1.1,  "temp": 0.4, "desc": "cheerfully"},
# # #     "sad":      {"speed": 0.85, "pitch_shift": 0.9,  "temp": 0.3, "desc": "sadly"},
# # #     "angry":    {"speed": 1.25, "pitch_shift": 1.05, "temp": 0.5, "desc": "angrily"},
# # #     "fearful":  {"speed": 0.95, "pitch_shift": 1.15, "temp": 0.45, "desc": "trembling"},
# # #     "surprised": {"speed": 1.2,  "pitch_shift": 1.2,  "temp": 0.5, "desc": "shocked"},
# # #     "neutral":  {"speed": 1.0,  "pitch_shift": 1.0,   "temp": 0.35, "desc": ""}
# # # }

# # # def load_segments():
# # #     with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
# # #         data = json.load(f)
# # #     return data.get("segments", [])

# # # # ... (keep your list_voice_samples, get_unique_speakers, manual_speaker_mapping, choose_voice unchanged)
# # # def list_voice_samples():
# # #     samples = []
# # #     for root, _, files in os.walk(SAMPLE_ROOT):
# # #         for f in files:
# # #             if f.lower().endswith((".wav", ".mp3")):
# # #                 samples.append(os.path.join(root, f))
# # #     return sorted(samples)


# # # def get_unique_speakers(segments):
# # #     return sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))


# # # def manual_speaker_mapping(unique_speakers, samples):
# # #     mapping = {}

# # #     print("\n🎭 MANUAL VOICE ASSIGNMENT\n")

# # #     for speaker in unique_speakers:
# # #         print(f"\nAssign voice for speaker: {speaker}")

# # #         for i, sample in enumerate(samples, 1):
# # #             print(f"[{i}] {os.path.basename(sample)}")

# # #         choice = input("Choose sample number: ").strip()
# # #         while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
# # #             choice = input("Invalid. Choose again: ").strip()

# # #         mapping[speaker] = samples[int(choice) - 1]
# # #         print(f"✅ {speaker} → {os.path.basename(mapping[speaker])}")

# # #     return mapping
# # # def choose_voice(samples, message="Choose voice sample"):
# # #     print(f"\n{message}")
# # #     for i, sample in enumerate(samples, 1):
# # #         print(f"[{i}] {os.path.basename(sample)}")

# # #     choice = input("Choose sample number: ").strip()
# # #     while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
# # #         choice = input("Invalid. Choose again: ").strip()

# # #     return samples[int(choice) - 1]

# # # def build_emotional_text(seg):
# # #     """Enhanced: Text engineering + prosody hints for XTTS"""
# # #     text = seg.get("translated_text", "").strip()
# # #     emotion_code = seg.get("emotion", "neu").lower()
# # #     confidence = seg.get("emotion_confidence", 0.0)
    
# # #     if confidence < 0.6:
# # #         return text, "neutral"
    
# # #     emotion = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
    
# # #     # Punctuation for natural prosody
# # #     if emotion_code == "angry":
# # #         text = text.rstrip(".?!") + "!!"
# # #     elif emotion_code == "sad":
# # #         text = text.rstrip(".?!") + "..."
# # #     elif emotion_code == "happy":
# # #         text = text.rstrip(".?!") + "!"
# # #     elif emotion_code == "fearful":
# # #         text = "(stammering) " + text
# # #     elif emotion_code == "surprised":
# # #         text = "!? " + text
    
# # #     # Style descriptor (XTTS picks up context)
# # #     styled = f"[{emotion['desc']}] {text}" if emotion["desc"] else text
    
# # #     return styled, emotion_code

# # # def preview_emotion(tts, sample_voice, text_sample, emotion_code):
# # #     """Quick preview of emotion tuning for first segment"""
# # #     emotion = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
# # #     preview_path = "work/preview_emotion.wav"
    
# # #     tts.tts_to_file(
# # #         text=text_sample,
# # #         file_path=preview_path,
# # #         speaker_wav=[sample_voice],
# # #         language=LANGUAGE_CODE,
# # #         speed=emotion["speed"],      # Core emotion control
# # #         temperature=emotion["temp"]
# # #     )
# # #     print(f"🔊 Preview saved: {preview_path}")

# # # def post_process_prosody(audio_path, emotion_code, target_duration):
# # #     """Apply pitch shift + fine-tune speed (pydub post-processing)"""
# # #     audio = AudioSegment.from_file(audio_path)
# # #     emotion = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
    
# # #     # Pitch shift (semitones)
# # #     octaves = (emotion["pitch_shift"] - 1.0) * 0.12  # ~12 semitones per octave
# # #     audio = audio._spawn(audio.raw_data, overrides={
# # #         'frame_rate': int(audio.frame_rate * (2.0 ** octaves))
# # #     }).set_frame_rate(audio.frame_rate)
    
# # #     # Duration matching (existing logic, now emotion-aware)
# # #     current_duration = len(audio) / 1000.0
# # #     if target_duration > 0 and abs(current_duration - target_duration) / target_duration > 0.1:
# # #         ratio = target_duration / current_duration
# # #         ratio = max(MIN_STRETCH, min(MAX_STRETCH, ratio))
# # #         new_rate = int(audio.frame_rate * ratio)
# # #         audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
# # #         audio = audio.set_frame_rate(audio.frame_rate)
    
# # #     audio.export(audio_path, format="wav")

# # # def load_model():
# # #     device = "cuda" if torch.cuda.is_available() else "cpu"
# # #     print(f"\n🧠 Loading XTTS v2 on {device}...")
# # #     model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
# # #     print("✅ Model loaded\n")
# # #     return model

# # # def generate():
# # #     os.makedirs(OUTPUT_DIR, exist_ok=True)
    
# # #     segments = load_segments()
# # #     samples = list_voice_samples()
    
# # #     if not samples:
# # #         raise Exception("❌ No voice samples found in sample_voices folder")
    
# # #     # Voice assignment modes (your existing logic)
# # #     print("\nVoice Assignment Mode")
# # #     print("1 - Speaker based")
# # #     print("2 - Segment based") 
# # #     print("3 - Speaker + override")
# # #     mode = input("Choose mode: ").strip()
    
# # #     speaker_voice_map = {}
# # #     if mode in ["1", "3"]:
# # #         unique_speakers = get_unique_speakers(segments)
# # #         speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)
    
# # #     tts = load_model()
# # #     metadata = []
    
# # #     # NEW: Emotion preview (optional, for first segment)
# # #     first_seg = segments[0] if segments else None
# # #     if first_seg:
# # #         print("\n🎭 Emotion Preview? (y/n): ", end="")
# # #         if input().lower() == 'y':
# # #             sample_voice = list(samples)[0]  # Default sample
# # #             text_sample, emotion_sample = build_emotional_text(first_seg)
# # #             preview_emotion(tts, sample_voice, text_sample, first_seg.get("emotion", "neu"))
    
# # #     print("\n🎙 Generating Emotion-Tuned Voice Clips...\n")
    
# # #     for idx, seg in enumerate(segments, 1):
# # #         speaker = seg.get("speaker", "UNKNOWN")
        
# # #         # Voice selection (your existing modes)
# # #         if mode == "1":
# # #             sample_voice = speaker_voice_map[speaker]
# # #         # elif mode == "2":
# # #         #     sample_voice = choose_voice(samples, f"Segment {idx} | Speaker: {speaker}")
# # #         elif mode == "2":
# # #             sentence = seg.get("translated_text", "").strip()
# # #             emotion = seg.get("emotion", "neutral")
# # #             duration = seg.get("duration", 0)

# # #             print("\n--------------------------------")
# # #             print(f"Segment {idx}")
# # #             print(f"Speaker   : {speaker}")
# # #             print(f"Emotion   : {emotion}")
# # #             print(f"Duration  : {duration:.2f}s")
# # #             print(f"Dialogue  : {sentence}")
# # #             print("--------------------------------")

# # #             sample_voice = choose_voice(samples, "Choose voice sample")
# # #         elif mode == "3":
# # #             default_voice = speaker_voice_map[speaker]
# # #             print(f"\nSegment {idx} | Speaker: {speaker}")
# # #             print(f"Default: {os.path.basename(default_voice)}")
# # #             override = input("Override voice? (y/n): ").strip().lower()
# # #             sample_voice = choose_voice(samples, "Choose override") if override == "y" else default_voice
# # #         else:
# # #             raise Exception("Invalid mode")
        
# # #         # Emotion processing
# # #         text, emotion_code = build_emotional_text(seg)
# # #         emotion_config = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
# # #         target_duration = seg.get("duration", 0)
        
# # #         output_path = os.path.join(OUTPUT_DIR, f"segment_{idx:03d}_{speaker}.wav")
        
# # #         print(f"[{idx:2d}] {speaker:10} | {emotion_code:8} | {os.path.basename(sample_voice)}")
# # #         print(f"     Speed:{emotion_config['speed']:.2f} Temp:{emotion_config['temp']:.2f}")
        
# # #         # XTTS generation with emotion prosody
# # #         tts.tts_to_file(
# # #             text=text,
# # #             file_path=output_path,
# # #             speaker_wav=[sample_voice],
# # #             language=LANGUAGE_CODE,
# # #             speed=emotion_config["speed"],           # Faster=excited, slower=sad
# # #             temperature=emotion_config["temp"]       # More varied=emotional
# # #         )
        
# # #         # Post-process pitch + duration
# # #         post_process_prosody(output_path, emotion_code, target_duration)
        
# # #         # Metadata
# # #         seg_meta = seg.copy()
# # #         seg_meta["audio_file"] = output_path
# # #         seg_meta["voice_sample"] = sample_voice
# # #         seg_meta["emotion_used"] = emotion_code
# # #         seg_meta["prosody"] = emotion_config  # Save settings
# # #         metadata.append(seg_meta)
        
# # #         time.sleep(0.1)  # Rate limit
    
# # #     # Save enhanced metadata
# # #     final_meta = {
# # #         "timestamp": datetime.now().isoformat(),
# # #         "tts_model": "xtts_v2",
# # #         "speakers": speaker_voice_map,
# # #         "emotions_used": list(set(m["emotion_used"] for m in metadata)),
# # #         "total_clips": len(metadata),
# # #         "clips": metadata
# # #     }
    
# # #     with open(METADATA_OUT, "w", encoding="utf-8") as f:
# # #         json.dump(final_meta, f, indent=2, ensure_ascii=False)
    
# # #     print(f"\n✅ Emotion-tuned generation complete! {len(metadata)} clips")
# # #     print(f"📊 Emotions: {final_meta['emotions_used']}")

# # # if __name__ == "__main__":
# # #     generate()
# # import os
# # import json
# # import time
# # from datetime import datetime
# # import torch
# # from TTS.api import TTS
# # from pydub import AudioSegment

# # # =========================
# # # CONFIG
# # # =========================

# # TRANSLATED_JSON = "work/translated_segments_interactive.json"
# # OUTPUT_DIR = "work/voice_clips"
# # METADATA_OUT = "work/voice_clips_metadata.json"
# # SAMPLE_ROOT = "sample_voices"
# # LANGUAGE_CODE = "en"

# # MAX_STRETCH = 1.25
# # MIN_STRETCH = 0.85


# # # =========================
# # # LOAD SEGMENTS
# # # =========================

# # def load_segments():
# #     with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
# #         data = json.load(f)
# #     return data.get("segments", [])


# # # =========================
# # # LIST VOICE SAMPLES
# # # =========================

# # def list_voice_samples():
# #     samples = []

# #     for root, _, files in os.walk(SAMPLE_ROOT):
# #         for f in files:
# #             if f.lower().endswith((".wav", ".mp3")):
# #                 samples.append(os.path.join(root, f))

# #     return sorted(samples)


# # # =========================
# # # SPEAKER UTILS
# # # =========================

# # def get_unique_speakers(segments):
# #     return sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))


# # def manual_speaker_mapping(unique_speakers, samples):

# #     mapping = {}

# #     print("\n🎭 MANUAL VOICE ASSIGNMENT\n")

# #     for speaker in unique_speakers:

# #         print(f"\nAssign voice for speaker: {speaker}")

# #         for i, sample in enumerate(samples, 1):
# #             print(f"[{i}] {os.path.basename(sample)}")

# #         choice = input("Choose sample number: ").strip()

# #         while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
# #             choice = input("Invalid. Choose again: ").strip()

# #         mapping[speaker] = samples[int(choice) - 1]

# #         print(f"✅ {speaker} → {os.path.basename(mapping[speaker])}")

# #     return mapping


# # # =========================
# # # VOICE SELECTOR
# # # =========================

# # def choose_voice(samples, message="Choose voice sample"):

# #     print(f"\n{message}")

# #     for i, sample in enumerate(samples, 1):
# #         print(f"[{i}] {os.path.basename(sample)}")

# #     print("[0] Skip this segment")

# #     choice = input("Choose sample number: ").strip()

# #     if choice == "0":
# #         return None

# #     while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
# #         choice = input("Invalid. Choose again: ").strip()

# #     return samples[int(choice) - 1]


# # # =========================
# # # POST PROCESS (DURATION MATCH)
# # # =========================

# # def post_process_prosody(audio_path, target_duration):

# #     audio = AudioSegment.from_file(audio_path)

# #     current_duration = len(audio) / 1000.0

# #     if target_duration > 0:

# #         ratio = target_duration / current_duration

# #         ratio = max(MIN_STRETCH, min(MAX_STRETCH, ratio))

# #         new_rate = int(audio.frame_rate * ratio)

# #         audio = audio._spawn(audio.raw_data, overrides={
# #             "frame_rate": new_rate
# #         }).set_frame_rate(audio.frame_rate)

# #     audio.export(audio_path, format="wav")


# # # =========================
# # # LOAD MODEL
# # # =========================

# # def load_model():

# #     device = "cuda" if torch.cuda.is_available() else "cpu"

# #     print(f"\n🧠 Loading XTTS v2 on {device}...")

# #     model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# #     print("✅ Model loaded\n")

# #     return model


# # # =========================
# # # MAIN GENERATION
# # # =========================

# # def generate():

# #     os.makedirs(OUTPUT_DIR, exist_ok=True)

# #     segments = load_segments()
# #     samples = list_voice_samples()

# #     if not samples:
# #         raise Exception("❌ No voice samples found in sample_voices folder")

# #     # =========================
# #     # VOICE ASSIGNMENT MODE
# #     # =========================

# #     print("\nVoice Assignment Mode")
# #     print("1 - Speaker based")
# #     print("2 - Segment based")
# #     print("3 - Speaker + override")

# #     mode = input("Choose mode: ").strip()

# #     speaker_voice_map = {}

# #     if mode in ["1", "3"]:
# #         unique_speakers = get_unique_speakers(segments)
# #         speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)

# #     # =========================
# #     # LOAD MODEL
# #     # =========================

# #     tts = load_model()

# #     metadata = []

# #     print("\n🎙 Generating Voice Clips (Lip Sync Mode)...\n")

# #     for idx, seg in enumerate(segments, 1):

# #         speaker = seg.get("speaker", "UNKNOWN")

# #         sentence = seg.get("translated_text", "").strip()

# #         duration = seg.get("duration", 0)

# #         print("\n--------------------------------")
# #         print(f"Segment {idx}")
# #         print(f"Speaker   : {speaker}")
# #         print(f"Duration  : {duration:.2f}s")
# #         print(f"Dialogue  : {sentence}")
# #         print("--------------------------------")

# #         # =========================
# #         # VOICE SELECTION
# #         # =========================

# #         if mode == "1":

# #             sample_voice = speaker_voice_map[speaker]

# #         elif mode == "2":

# #             sample_voice = choose_voice(samples)

# #             if sample_voice is None:
# #                 print("⏭ Segment skipped")
# #                 continue

# #         elif mode == "3":

# #             default_voice = speaker_voice_map[speaker]

# #             print(f"Default Voice: {os.path.basename(default_voice)}")

# #             override = input("Override voice? (y/n): ").strip().lower()

# #             if override == "y":

# #                 sample_voice = choose_voice(samples)

# #                 if sample_voice is None:
# #                     print("⏭ Segment skipped")
# #                     continue

# #             else:
# #                 sample_voice = default_voice

# #         else:
# #             raise Exception("Invalid mode")

# #         # =========================
# #         # OUTPUT PATH
# #         # =========================

# #         output_path = os.path.join(
# #             OUTPUT_DIR,
# #             f"segment_{idx:03d}_{speaker}.wav"
# #         )

# #         print(f"🎤 Using voice: {os.path.basename(sample_voice)}")

# #         # =========================
# #         # TTS GENERATION
# #         # =========================

# #         tts.tts_to_file(
# #             text=sentence,
# #             file_path=output_path,
# #             speaker_wav=[sample_voice],
# #             language=LANGUAGE_CODE,
# #             speed=1.0,
# #             temperature=0.35
# #         )

# #         # =========================
# #         # DURATION MATCH
# #         # =========================

# #         post_process_prosody(output_path, duration)

# #         # =========================
# #         # METADATA
# #         # =========================

# #         seg_meta = seg.copy()

# #         seg_meta["audio_file"] = output_path
# #         seg_meta["voice_sample"] = sample_voice

# #         metadata.append(seg_meta)

# #         time.sleep(0.1)

# #     # =========================
# #     # SAVE METADATA
# #     # =========================

# #     final_meta = {

# #         "timestamp": datetime.now().isoformat(),
# #         "tts_model": "xtts_v2",
# #         "speakers": speaker_voice_map,
# #         "total_clips": len(metadata),
# #         "clips": metadata
# #     }

# #     with open(METADATA_OUT, "w", encoding="utf-8") as f:

# #         json.dump(final_meta, f, indent=2, ensure_ascii=False)

# #     print(f"\n✅ Generation complete! {len(metadata)} clips created")


# # # =========================
# # # RUN
# # # =========================

# # if __name__ == "__main__":
# #     generate()
# import os
# import json
# import time
# from datetime import datetime
# import torch
# from TTS.api import TTS
# from pydub import AudioSegment
# import librosa
# import librosa.display
# import matplotlib.pyplot as plt
# import numpy as np

# # =========================
# # CONFIG
# # =========================

# TRANSLATED_JSON = "work/translated_segments_interactive.json"
# OUTPUT_DIR = "work/voice_clips"
# METADATA_OUT = "work/voice_clips_metadata.json"
# SAMPLE_ROOT = "sample_voices"
# CROPPED_AUDIO_DIR = "work/cropped_segments"
# WAVEFORM_PLOT_DIR = "work/waveform_comparisons"
# LANGUAGE_CODE = "en"

# MAX_STRETCH = 1.25
# MIN_STRETCH = 0.85

# # =========================
# # SETUP & UTILS
# # =========================

# def setup_directories():
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     os.makedirs(WAVEFORM_PLOT_DIR, exist_ok=True)

# def load_segments():
#     with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     return data.get("segments", [])

# def list_voice_samples():
#     samples = []
#     for root, _, files in os.walk(SAMPLE_ROOT):
#         for f in files:
#             if f.lower().endswith((".wav", ".mp3")):
#                 samples.append(os.path.join(root, f))
#     return sorted(samples)

# def get_unique_speakers(segments):
#     return sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))

# # =========================
# # VOICE SELECTOR & UI
# # =========================

# def choose_voice(samples, message="Choose voice sample"):
#     print(f"\n{message}")
#     for i, sample in enumerate(samples, 1):
#         print(f"[{i}] {os.path.basename(sample)}")
#     print("[0] Skip this segment")

#     choice = input("Choose sample number: ").strip()
#     if choice == "0":
#         return None
#     while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
#         choice = input("Invalid. Choose again: ").strip()
#     return samples[int(choice) - 1]

# def display_segment_info(idx, seg):
#     speaker = seg.get("speaker", "UNKNOWN")
#     duration = seg.get("total_duration", 0)
#     sentence = seg.get("translated_text", "").strip()
    
#     # Emotion data from Step 3
#     emotion = seg.get("emotion_used", "neutral")
    
#     print("\n" + "-"*50)
#     print(f"Segment {idx} | Speaker: {speaker}")
#     print(f"Emotion Predicted: {emotion.upper()}")
#     print(f"Duration: {duration:.2f}s")
#     print(f"Full Text: {sentence}")
#     print("-" * 50)
#     return speaker, duration

# # =========================
# # AUDIO PROCESSING
# # =========================

# def match_duration(audio_segment, target_duration_sec):
#     """Stretch or compress a pydub AudioSegment to match target duration"""
#     current_duration_sec = len(audio_segment) / 1000.0
#     if target_duration_sec <= 0 or current_duration_sec <= 0:
#         return audio_segment

#     ratio = target_duration_sec / current_duration_sec
#     ratio = max(MIN_STRETCH, min(MAX_STRETCH, ratio))
    
#     # Avoid unnecessary stretching if it's already very close
#     if abs(1.0 - ratio) < 0.02:
#         return audio_segment

#     new_rate = int(audio_segment.frame_rate * ratio)
#     stretched = audio_segment._spawn(audio_segment.raw_data, overrides={"frame_rate": new_rate})
#     return stretched.set_frame_rate(audio_segment.frame_rate)

# # def generate_blueprint_audio(tts, segment, sample_voice, output_path):
# #     """Loops through rhythm blueprint, generates speech, adds silence, and combines them"""
# #     blueprint = segment.get("rhythm_blueprint", [])
    
# #     if not blueprint:
# #         print("⚠️ No blueprint found. Falling back to single generation.")
# #         # Fallback to old method if blueprint missing
# #         tts.tts_to_file(
# #             text=segment.get("translated_text", ""),
# #             file_path=output_path,
# #             speaker_wav=[sample_voice],
# #             language=LANGUAGE_CODE
# #         )
# #         audio = AudioSegment.from_file(output_path)
# #         audio = match_duration(audio, segment.get("total_duration", 0))
# #         audio.export(output_path, format="wav")
# #         return
        
# #     combined_audio = AudioSegment.empty()
    
# #     for i, block in enumerate(blueprint):
# #         target_dur = block['duration']
        
# #         if block['type'] == 'speech':
# #             text = block.get('text_chunk', '').strip()
# #             if not text: continue
            
# #             # 1. Generate this specific chunk
# #             temp_path = f"work/temp_chunk_{i}.wav"
# #             tts.tts_to_file(
# #                 text=text,
# #                 file_path=temp_path,
# #                 speaker_wav=[sample_voice],
# #                 language=LANGUAGE_CODE,
# #                 speed=1.0,
# #                 temperature=0.35
# #             )
            
# #             # 2. Load and stretch chunk to EXACT blueprint duration
# #             chunk_audio = AudioSegment.from_file(temp_path)
# #             chunk_audio = match_duration(chunk_audio, target_dur)
# #             combined_audio += chunk_audio
# #             os.remove(temp_path)
            
# #         elif block['type'] == 'pause':
# #             # Generate pure silence using pydub
# #             silence_ms = int(target_dur * 1000)
# #             combined_audio += AudioSegment.silent(duration=silence_ms)

# #     # Export final stitched audio
# #     combined_audio.export(output_path, format="wav")
# def generate_blueprint_audio(tts, segment, sample_voice, output_path):
#     """Fixed: Proper word splitting + master duration control"""
#     blueprint = segment.get("rhythm_blueprint", [])
    
#     if not blueprint:
#         # Fallback: single generation
#         tts.tts_to_file(
#             text=segment.get("translated_text", ""),
#             file_path=output_path,
#             speaker_wav=[sample_voice],
#             language=LANGUAGE_CODE,
#             speed=1.0
#         )
#         audio = AudioSegment.from_file(output_path)
#         target_duration = segment.get("total_duration", 0)
#         audio = match_duration(audio, target_duration)
#         audio.export(output_path, format="wav")
#         return
        
#     combined_audio = AudioSegment.empty()
#     speech_chunks = []
    
#     # Step 1: Generate ALL speech chunks first
#     for i, block in enumerate(blueprint):
#         if block['type'] == 'speech' and block.get('text_chunk', '').strip():
#             text = block['text_chunk'].strip()
#             temp_path = f"work/temp_speech_{i}.wav"
            
#             tts.tts_to_file(
#                 text=text,
#                 file_path=temp_path,
#                 speaker_wav=[sample_voice],
#                 language=LANGUAGE_CODE,
#                 speed=1.0,  # Natural speed first
#                 temperature=0.35
#             )
            
#             chunk_audio = AudioSegment.from_file(temp_path)
#             # DON'T stretch individual chunks yet - measure natural duration
#             speech_chunks.append(chunk_audio)
#             os.remove(temp_path)
#         else:
#             speech_chunks.append(None)  # Placeholder for empty/silence
    
#     # Step 2: MASTER DURATION CALCULATION
#     target_total_duration = segment.get("total_duration", 0)
    
#     # Build timeline with natural durations first
#     timeline = []
#     current_time = 0.0
    
#     speech_idx = 0
#     for block in blueprint:
#         if block['type'] == 'pause':
#             # Pure silence
#             silence_ms = int(block['duration'] * 1000)
#             timeline.append(('silence', silence_ms))
#             current_time += block['duration']
#         else:  # speech
#             if speech_chunks[speech_idx] is not None:
#                 natural_dur = len(speech_chunks[speech_idx]) / 1000.0
#                 timeline.append(('speech', natural_dur, speech_idx))
#                 current_time += natural_dur
#                 speech_idx += 1
#             else:
#                 # Empty speech block = tiny silence
#                 timeline.append(('silence', 20))  # 20ms minimum
#                 current_time += 0.02
    
#     # Step 3: Global Speed Adjustment
#     if current_time > 0 and target_total_duration > 0:
#         global_speed_ratio = target_total_duration / current_time
#         global_speed_ratio = max(0.7, min(1.4, global_speed_ratio))  # Safe range
        
#         print(f"🎚️  Global speed adjustment: {global_speed_ratio:.2f}x (natural={current_time:.2f}s → target={target_total_duration:.2f}s)")
        
#         # Apply global speed to ALL speech chunks
#         for i in range(len(speech_chunks)):
#             if speech_chunks[i] is not None:
#                 chunk = speech_chunks[i]
#                 new_rate = int(chunk.frame_rate * global_speed_ratio)
#                 speech_chunks[i] = chunk._spawn(chunk.raw_data, overrides={
#                     "frame_rate": new_rate
#                 }).set_frame_rate(chunk.frame_rate)
    
#     # Step 4: Final Assembly (NOW stretch to exact blueprint timing)
#     speech_idx = 0
#     for block in blueprint:
#         if block['type'] == 'pause':
#             silence_ms = int(block['duration'] * 1000)
#             combined_audio += AudioSegment.silent(duration=silence_ms)
#         else:  # speech
#             if speech_chunks[speech_idx] is not None:
#                 # FINAL precise timing match for this exact block
#                 chunk_audio = speech_chunks[speech_idx]
#                 chunk_audio = match_duration(chunk_audio, block['duration'])
#                 combined_audio += chunk_audio
#             else:
#                 # Empty speech = silence
#                 silence_ms = int(block['duration'] * 1000)
#                 combined_audio += AudioSegment.silent(duration=silence_ms)
#             speech_idx += 1
    
#     # Export
#     combined_audio.export(output_path, format="wav")
#     print(f"✅ Total generated: {len(combined_audio)/1000:.2f}s vs target {target_total_duration:.2f}s")
# # def generate_blueprint_audio(tts, segment, sample_voice, output_path):
# #     """🔧 FIXED: Proper XTTS speaker handling + timing alignment"""
# #     blueprint = segment.get("rhythm_blueprint", [])
# #     target_total_duration = segment.get("total_duration", 0)
    
# #     print(f"📋 Blueprint has {len([b for b in blueprint if b['type']=='speech'])} speech blocks")
    
# #     if not blueprint:
# #         # Fallback: Generate full sentence at once
# #         print(f"🎤 Fallback: Single generation '{segment.get('translated_text', '')}'")
# #         tts.tts_to_file(
# #             text=segment.get("translated_text", ""),
# #             file_path=output_path,
# #             speaker_wav=sample_voice,  # Single file path, NOT list
# #             language=LANGUAGE_CODE,
# #             speed=1.0
# #         )
# #         audio = AudioSegment.from_file(output_path)
# #         audio = match_duration(audio, target_total_duration)
# #         audio.export(output_path, format="wav")
# #         return
    
# #     # Step 1: Generate ALL speech chunks using the SAME speaker reference
# #     speech_audio_chunks = []
# #     speech_texts = []
    
# #     speech_count = 0
# #     for block in blueprint:
# #         if block['type'] == 'speech' and block.get('text_chunk', '').strip():
# #             text = block['text_chunk'].strip()
# #             speech_texts.append(text)
# #             speech_count += 1
    
# #     print(f"🗣️  Found {speech_count} non-empty speech chunks")
    
# #     if speech_count == 0:
# #         # No speech at all, just silence
# #         silence_audio = AudioSegment.silent(duration=int(target_total_duration * 1000))
# #         silence_audio.export(output_path, format="wav")
# #         return
    
# #     # Step 2: Generate speech chunks (BATCHED to avoid speaker cache issues)
# #     temp_base_path = "work/temp_speech_chunk"
    
# #     for i, text in enumerate(speech_texts):
# #         temp_path = f"{temp_base_path}_{i}.wav"
# #         print(f"  Generating chunk {i+1}: '{text}'")
        
# #         try:
# #             tts.tts_to_file(
# #                 text=text,
# #                 file_path=temp_path,
# #                 speaker_wav=sample_voice,  # Single file path (str), NOT list!
# #                 language=LANGUAGE_CODE,
# #                 speed=1.0,
# #                 temperature=0.35
# #             )
            
# #             chunk_audio = AudioSegment.from_file(temp_path)
# #             speech_audio_chunks.append(chunk_audio)
# #             os.remove(temp_path)
            
# #         except Exception as e:
# #             print(f"❌ TTS failed for '{text}': {e}")
# #             # Fallback: silence for this chunk
# #             speech_audio_chunks.append(AudioSegment.silent(duration=100))  # 100ms silence
    
# #     # Step 3: Rebuild timeline matching blueprint exactly
# #     combined_audio = AudioSegment.empty()
# #     speech_idx = 0
    
# #     for block in blueprint:
# #         if block['type'] == 'pause':
# #             # Pure silence
# #             silence_ms = int(block['duration'] * 1000)
# #             combined_audio += AudioSegment.silent(duration=silence_ms)
# #             print(f"  ⏸️  Pause: {block['duration']:.3f}s")
            
# #         else:  # speech block
# #             if speech_idx < len(speech_audio_chunks):
# #                 chunk_audio = speech_audio_chunks[speech_idx]
# #                 # Stretch to EXACT blueprint duration
# #                 target_chunk_dur = block['duration']
# #                 chunk_audio = match_duration(chunk_audio, target_chunk_dur)
# #                 combined_audio += chunk_audio
# #                 print(f"  🗣️  Speech[{speech_idx}]: {target_chunk_dur:.3f}s (was {len(chunk_audio)/1000:.3f}s)")
# #                 speech_idx += 1
# #             else:
# #                 # No more speech chunks, fill with silence
# #                 silence_ms = int(block['duration'] * 1000)
# #                 combined_audio += AudioSegment.silent(duration=silence_ms)
# #                 print(f"  ⏸️  Empty speech slot: {block['duration']:.3f}s")
    
# #     # Step 4: FINAL total duration verification
# #     final_duration = len(combined_audio) / 1000.0
# #     print(f"🎯 FINAL: {final_duration:.3f}s vs target {target_total_duration:.3f}s "
# #           f"(diff: {abs(final_duration-target_total_duration):.3f}s)")
    
# #     # Export
# #     combined_audio.export(output_path, format="wav")
# # def generate_blueprint_audio(tts, segment, sample_voice, output_path):
# #     """🔥 ULTIMATE FIX: Perfect timing + no chipmunk effect"""
# #     blueprint = segment.get("rhythm_blueprint", [])
# #     target_total_duration = segment.get("total_duration", 0)
    
# #     print(f"📋 Blueprint: {len(blueprint)} blocks, target: {target_total_duration:.2f}s")
    
# #     if not blueprint:
# #         # Fallback single generation
# #         tts.tts_to_file(segment.get("translated_text", ""), output_path, 
# #                        speaker_wav=sample_voice, language=LANGUAGE_CODE)
# #         audio = AudioSegment.from_file(output_path)
# #         audio = match_duration(audio, target_total_duration)
# #         audio.export(output_path, format="wav")
# #         return
    
# #     # ===== STEP 1: Extract ALL speech text first =====
# #     speech_texts = []
# #     total_speech_duration = 0
    
# #     for block in blueprint:
# #         if block['type'] == 'speech' and block.get('text_chunk', '').strip():
# #             text = block['text_chunk'].strip()
# #             speech_texts.append(text)
# #             total_speech_duration += block['duration']
    
# #     print(f"🗣️  Speech texts: {speech_texts} (total speech dur: {total_speech_duration:.2f}s)")
    
# #     if not speech_texts:
# #         # Pure silence segment
# #         silence = AudioSegment.silent(duration=int(target_total_duration * 1000))
# #         silence.export(output_path, format="wav")
# #         return
    
# #     # ===== STEP 2: Generate FULL SENTENCE at natural speed FIRST =====
# #     full_text = " ".join(speech_texts)
# #     temp_full_path = "work/temp_full_sentence.wav"
    
# #     print(f"🎤 Generating full sentence: '{full_text}'")
# #     tts.tts_to_file(
# #         text=full_text,
# #         file_path=temp_full_path,
# #         speaker_wav=sample_voice,
# #         language=LANGUAGE_CODE,
# #         speed=1.0  # NATURAL speed
# #     )
    
# #     full_audio = AudioSegment.from_file(temp_full_path)
# #     natural_full_duration = len(full_audio) / 1000.0
# #     os.remove(temp_full_path)
    
# #     print(f"⏱️  Natural duration: {natural_full_duration:.2f}s")
    
# #     # ===== STEP 3: Calculate IDEAL global speed =====
# #     if total_speech_duration > 0:
# #         ideal_speed = natural_full_duration / total_speech_duration
# #         ideal_speed = max(0.7, min(1.5, ideal_speed))  # Safe range
# #         print(f"⚡ Ideal speed: {ideal_speed:.2f}x")
# #     else:
# #         ideal_speed = 1.0
    
# #     # ===== STEP 4: Re-generate speech at ideal speed =====
# #     temp_full_speed_path = "work/temp_full_speed.wav"
# #     tts.tts_to_file(
# #         text=full_text,
# #         file_path=temp_full_speed_path,
# #         speaker_wav=sample_voice,
# #         language=LANGUAGE_CODE,
# #         speed=ideal_speed
# #     )
    
# #     speech_audio = AudioSegment.from_file(temp_full_speed_path)
# #     speech_duration = len(speech_audio) / 1000.0
# #     os.remove(temp_full_speed_path)
    
# #     # ===== STEP 5: Build timeline EXACTLY matching blueprint =====
# #     combined_audio = AudioSegment.empty()
    
# #     # Distribute speech across blueprint speech blocks proportionally
# #     speech_idx = 0
# #     speech_block_count = len([b for b in blueprint if b['type'] == 'speech'])
    
# #     for block in blueprint:
# #         if block['type'] == 'pause':
# #             # Pure silence - EXACT duration
# #             silence_ms = int(block['duration'] * 1000)
# #             combined_audio += AudioSegment.silent(duration=silence_ms)
# #             print(f"  ⏸️  Pause: {block['duration']:.3f}s")
            
# #         else:  # speech block
# #             if speech_block_count > 0:
# #                 # Distribute speech proportionally across ALL speech blocks
# #                 block_ratio = block['duration'] / total_speech_duration
# #                 chunk_duration = speech_duration * block_ratio
                
# #                 # Cut exact chunk from full speech
# #                 chunk_start_ms = sum(b['duration'] * 1000 for b in blueprint[:speech_idx] if b['type'] == 'speech')
# #                 chunk_end_ms = chunk_start_ms + (chunk_duration * 1000)
                
# #                 chunk_audio = speech_audio[chunk_start_ms:chunk_end_ms]
# #                 combined_audio += chunk_audio
# #                 print(f"  🗣️  Speech block {speech_idx}: {block['duration']:.3f}s (ratio {block_ratio:.2f})")
# #             else:
# #                 silence_ms = int(block['duration'] * 1000)
# #                 combined_audio += AudioSegment.silent(duration=silence_ms)
            
# #             speech_idx += 1
    
# #     # ===== STEP 6: FINAL VERIFICATION =====
# #     final_duration = len(combined_audio) / 1000.0
# #     print(f"🎯 FINAL: {final_duration:.3f}s vs target {target_total_duration:.3f}s "
# #           f"(error: {abs(final_duration-target_total_duration):.3f}s)")
    
# #     combined_audio.export(output_path, format="wav")

# # =========================
# # WAVEFORM PLOTTING
# # =========================

# def plot_waveform_comparison(original_wav_path, generated_wav_path, segment_id, speaker):
#     """Creates a visual PNG comparing Japanese and English audio rhythms"""
#     if not os.path.exists(original_wav_path) or not os.path.exists(generated_wav_path):
#         return

#     # Load audio files
#     y_orig, sr_orig = librosa.load(original_wav_path, sr=16000)
#     y_gen, sr_gen = librosa.load(generated_wav_path, sr=16000)

#     # Create Plot
#     plt.figure(figsize=(12, 6))
    
#     # Plot Original (Japanese)
#     plt.subplot(2, 1, 1)
#     librosa.display.waveshow(y_orig, sr=sr_orig, color='blue', alpha=0.7)
#     plt.title(f"Original Japanese (Segment {segment_id})")
#     plt.xlabel("Time (s)")
#     plt.ylabel("Amplitude")
    
#     # Plot Generated (English)
#     plt.subplot(2, 1, 2)
#     librosa.display.waveshow(y_gen, sr=sr_gen, color='green', alpha=0.7)
#     plt.title(f"Generated English (Speaker: {speaker})")
#     plt.xlabel("Time (s)")
#     plt.ylabel("Amplitude")
    
#     plt.tight_layout()
    
#     # Save Image
#     plot_path = os.path.join(WAVEFORM_PLOT_DIR, f"comparison_{segment_id:03d}.png")
#     plt.savefig(plot_path)
#     plt.close()
#     print(f"📊 Rhythm Comparison saved: {os.path.basename(plot_path)}")

# # =========================
# # MAIN
# # =========================

# def main():
#     setup_directories()
#     segments = load_segments()
#     samples = list_voice_samples()

#     if not samples:
#         raise Exception("❌ No voice samples found in sample_voices folder")

#     print("\nVoice Assignment Mode")
#     print("1 - Segment based (Interactive)")
#     mode = input("Choose mode [1]: ").strip() or "1"

#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     print(f"\n🧠 Loading XTTS v2 on {device}...")
#     tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

#     metadata = []
#     print("\n🎙 Generating Blueprint-Synced Voice Clips...\n")

#     for idx, seg in enumerate(segments, 1):
#         seg_id = seg.get("segment_id", idx)
#         speaker, duration = display_segment_info(idx, seg)

#         # Voice Selection
#         sample_voice = choose_voice(samples)
#         if sample_voice is None:
#             print("⏭ Segment skipped")
#             continue

#         output_path = os.path.join(OUTPUT_DIR, f"segment_{seg_id:03d}_{speaker}.wav")
#         print(f"🎤 Generating with blueprint using: {os.path.basename(sample_voice)}")

#         # 1. Generate audio precisely matching the rhythm blueprint
#         generate_blueprint_audio(tts, seg, sample_voice, output_path)

#         # 2. Compare Waveforms (Original JP vs Generated EN)
#         original_audio_path = os.path.join(CROPPED_AUDIO_DIR, f"segment_{seg_id:03d}.wav")
#         plot_waveform_comparison(original_audio_path, output_path, seg_id, speaker)

#         # 3. Save Metadata
#         seg_meta = seg.copy()
#         seg_meta["audio_file"] = output_path
#         seg_meta["voice_sample"] = sample_voice
#         metadata.append(seg_meta)

#     # Save final JSON
#     final_meta = {
#         "timestamp": datetime.now().isoformat(),
#         "tts_model": "xtts_v2",
#         "total_clips": len(metadata),
#         "clips": metadata
#     }
#     with open(METADATA_OUT, "w", encoding="utf-8") as f:
#         json.dump(final_meta, f, indent=2, ensure_ascii=False)

#     print(f"\n✅ Generation complete! {len(metadata)} clips created.")
#     print(f"📁 Check {WAVEFORM_PLOT_DIR} for lip-sync comparison graphs!")

# if __name__ == "__main__":
#     main()
import os
import json
import time
from datetime import datetime
import torch
from TTS.api import TTS
from pydub import AudioSegment
import matplotlib.pyplot as plt
import numpy as np
import librosa

# =========================
# CONFIG
# =========================

TRANSLATED_JSON = "work/translated_segments_interactive.json"
ORIGINAL_JSON = "work/transcription_with_speakers.json"  # To get gender/age info
OUTPUT_DIR = "work/voice_clips"
METADATA_OUT = "work/voice_clips_metadata.json"
SAMPLE_ROOT = "sample_voices"
CROPPED_DIR = "work/cropped_segments"
COMPARISON_DIR = "work/waveform_comparisons"
LANGUAGE_CODE = "en"

# XTTS needs a little more flexibility when stretching tiny chunks
MAX_STRETCH = 1.35 
MIN_STRETCH = 0.75

# =========================
# LOAD SEGMENTS
# =========================

def load_segments():
    with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments", [])
    
    # Also load the Step 3 JSON to merge Gender, Age, and Emotion data
    if os.path.exists(ORIGINAL_JSON):
        with open(ORIGINAL_JSON, "r", encoding="utf-8") as f:
            orig_data = json.load(f)
            orig_segs = {seg["id"]: seg for seg in orig_data.get("segments", [])}
            
            for seg in segments:
                orig_seg = orig_segs.get(seg.get("segment_id"), {})
                analysis = orig_seg.get("analysis", {})
                
                # Attach to segment
                seg["gender"] = analysis.get("gender", "unknown")
                seg["age"] = analysis.get("age", "unknown")
                seg["emotion"] = analysis.get("emotion", seg.get("emotion_used", "neutral"))
                
    return segments

# =========================
# LIST VOICE SAMPLES
# =========================

def list_voice_samples():
    samples = []
    for root, _, files in os.walk(SAMPLE_ROOT):
        for f in files:
            if f.lower().endswith((".wav", ".mp3")):
                samples.append(os.path.join(root, f))
    return sorted(samples)

# =========================
# SPEAKER UTILS
# =========================

def get_unique_speakers(segments):
    return sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))

def manual_speaker_mapping(unique_speakers, samples, segments):
    mapping = {}
    print("\n🎭 MANUAL VOICE ASSIGNMENT\n")
    
    for speaker in unique_speakers:
        # Get majority gender for this speaker to help user
        spk_segs = [s for s in segments if s.get("speaker") == speaker]
        genders = [s.get("gender", "unknown") for s in spk_segs]
        dom_gender = max(set(genders), key=genders.count) if genders else "unknown"

        print(f"\nAssign voice for speaker: {speaker} (Detected Gender: {dom_gender})")
        for i, sample in enumerate(samples, 1):
            print(f"[{i}] {os.path.basename(sample)}")

        choice = input("Choose sample number: ").strip()
        while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
            choice = input("Invalid. Choose again: ").strip()

        mapping[speaker] = samples[int(choice) - 1]
        print(f"✅ {speaker} → {os.path.basename(mapping[speaker])}")

    return mapping

# =========================
# VOICE SELECTOR
# =========================

def choose_voice(samples, message="Choose voice sample"):
    print(f"\n{message}")
    for i, sample in enumerate(samples, 1):
        print(f"[{i}] {os.path.basename(sample)}")
    print("[0] Skip this segment")

    choice = input("Choose sample number: ").strip()
    if choice == "0":
        return None
    while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
        choice = input("Invalid. Choose again: ").strip()

    return samples[int(choice) - 1]

# =========================
# STRETCH CHUNK
# =========================

def stretch_audiosegment(audio, target_duration_sec):
    current_duration = len(audio) / 1000.0
    if current_duration == 0 or target_duration_sec <= 0:
        return audio
        
    ratio = target_duration_sec / current_duration
    ratio = max(MIN_STRETCH, min(MAX_STRETCH, ratio))
    
    new_rate = int(audio.frame_rate * ratio)
    stretched = audio._spawn(audio.raw_data, overrides={
        "frame_rate": new_rate
    }).set_frame_rate(audio.frame_rate)
    
    return stretched

# =========================
# WAVEFORM COMPARISON PLOT
# =========================

def plot_waveform_comparison(orig_path, gen_path, out_path, segment_id):
    """Generates an overlay plot of Japanese vs English audio waveforms"""
    if not os.path.exists(orig_path) or not os.path.exists(gen_path):
        return

    y_orig, sr_orig = librosa.load(orig_path, sr=None)
    y_gen, sr_gen = librosa.load(gen_path, sr=None)
    
    time_orig = np.linspace(0, len(y_orig)/sr_orig, num=len(y_orig))
    time_gen = np.linspace(0, len(y_gen)/sr_gen, num=len(y_gen))
    
    plt.figure(figsize=(12, 4))
    
    # Plot Original (Japanese)
    plt.plot(time_orig, y_orig, label='Original (Japanese)', color='dodgerblue', alpha=0.7)
    # Plot Generated (English)
    plt.plot(time_gen, y_gen, label='Generated (English)', color='darkorange', alpha=0.75)
    
    plt.title(f"Lip-Sync Waveform Comparison: Segment {segment_id}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.legend(loc="upper right")
    plt.tight_layout()
    
    plt.savefig(out_path)
    plt.close()

# =========================
# LOAD MODEL
# =========================

def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🧠 Loading XTTS v2 on {device}...")
    model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    print("✅ Model loaded\n")
    return model

# =========================
# MAIN GENERATION
# =========================

def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(COMPARISON_DIR, exist_ok=True)

    segments = load_segments()
    samples = list_voice_samples()

    if not samples:
        raise Exception("❌ No voice samples found in sample_voices folder")

    # =========================
    # VOICE ASSIGNMENT MODE
    # =========================
    print("\nVoice Assignment Mode")
    print("1 - Speaker based")
    print("2 - Segment based")
    print("3 - Speaker + override")

    mode = input("Choose mode: ").strip()

    speaker_voice_map = {}
    if mode in ["1", "3"]:
        unique_speakers = get_unique_speakers(segments)
        speaker_voice_map = manual_speaker_mapping(unique_speakers, samples, segments)

    tts = load_model()
    metadata = []

    print("\n🎙 Generating Rhythm-Matched Voice Clips...\n")

    for idx, seg in enumerate(segments, 1):
        seg_id = seg.get("segment_id", idx-1)
        speaker = seg.get("speaker", "UNKNOWN")
        sentence = seg.get("translated_text", "").strip()
        duration = seg.get("total_duration", 0)
        blueprint = seg.get("rhythm_blueprint", [])
        
        gender = seg.get("gender", "unknown")
        age = seg.get("age", "unknown")
        emotion = seg.get("emotion", "neutral").upper()

        # 🔥 NEW: Display step 3 data to the user!
        print(f"\n--------------------------------")
        print(f"Segment {idx} (ID: {seg_id})")
        print(f"Speaker   : {speaker}")
        print(f"Profile   : Gender: {gender} | Age: ~{age} | Emotion: {emotion}")
        print(f"Duration  : {duration:.2f}s")
        print(f"Dialogue  : {sentence}")
        print("--------------------------------")

        # =========================
        # VOICE SELECTION
        # =========================
        if mode == "1":
            sample_voice = speaker_voice_map[speaker]
        elif mode == "2":
            sample_voice = choose_voice(samples)
            if sample_voice is None:
                print("⏭ Segment skipped")
                continue
        elif mode == "3":
            default_voice = speaker_voice_map[speaker]
            print(f"Default Voice: {os.path.basename(default_voice)}")
            override = input("Override voice? (y/n): ").strip().lower()
            if override == "y":
                sample_voice = choose_voice(samples)
                if sample_voice is None:
                    continue
            else:
                sample_voice = default_voice
        else:
            raise Exception("Invalid mode")

        print(f"🎤 Using voice: {os.path.basename(sample_voice)}")

        # =========================
        # TTS GENERATION (CHUNK BY CHUNK)
        # =========================
        output_path = os.path.join(OUTPUT_DIR, f"segment_{seg_id:03d}_{speaker}.wav")
        final_audio = AudioSegment.empty()

        for b_idx, block in enumerate(blueprint):
            if block["type"] == "pause":
                # Inject pure silence
                silence_dur = int(block["duration"] * 1000)
                final_audio += AudioSegment.silent(duration=silence_dur)
                
            elif block["type"] == "speech":
                chunk_text = block.get("text_chunk", "").strip()
                chunk_dur = block["duration"]
                
                # If chunk is empty or weirdly small, add silence
                if not chunk_text or chunk_dur < 0.1:
                    final_audio += AudioSegment.silent(duration=int(chunk_dur * 1000))
                    continue

                temp_wav = os.path.join(OUTPUT_DIR, f"temp_chunk_{seg_id}_{b_idx}.wav")
                
                try:
                    # Generate this specific chunk
                    tts.tts_to_file(
                        text=chunk_text,
                        file_path=temp_wav,
                        speaker_wav=[sample_voice],
                        language=LANGUAGE_CODE,
                        speed=1.0,
                        temperature=0.35
                    )
                    
                    # Stretch chunk to match blueprint exactly
                    chunk_audio = AudioSegment.from_file(temp_wav)
                    chunk_audio = stretch_audiosegment(chunk_audio, chunk_dur)
                    
                    final_audio += chunk_audio
                    os.remove(temp_wav) # Clean up
                    
                except Exception as e:
                    print(f"  ⚠️ Failed chunk '{chunk_text}': {e}")
                    final_audio += AudioSegment.silent(duration=int(chunk_dur * 1000))

        # Save fully stitched audio
        final_audio.export(output_path, format="wav")
        
        # =========================
        # CREATE WAVEFORM COMPARISON
        # =========================
        # Fetch the cropped original from Step 2.5
        orig_crop_path = os.path.join(CROPPED_DIR, f"segment_{seg_id:03d}.wav")
        comp_image_path = os.path.join(COMPARISON_DIR, f"comparison_{seg_id:03d}.png")
        
        plot_waveform_comparison(orig_crop_path, output_path, comp_image_path, seg_id)

        # =========================
        # METADATA
        # =========================
        seg_meta = seg.copy()
        seg_meta["audio_file"] = output_path
        seg_meta["voice_sample"] = sample_voice
        seg_meta["comparison_image"] = comp_image_path
        metadata.append(seg_meta)

        time.sleep(0.1)

    # =========================
    # SAVE METADATA
    # =========================
    final_meta = {
        "timestamp": datetime.now().isoformat(),
        "tts_model": "xtts_v2",
        "speakers": speaker_voice_map,
        "total_clips": len(metadata),
        "clips": metadata
    }

    with open(METADATA_OUT, "w", encoding="utf-8") as f:
        json.dump(final_meta, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Generation complete! {len(metadata)} clips created")
    print(f"📊 Waveform comparisons saved to: {COMPARISON_DIR}/")

if __name__ == "__main__":
    generate()
