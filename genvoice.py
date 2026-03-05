# # import os
# # import json
# # import time
# # from datetime import datetime

# # import torch
# # from TTS.api import TTS
# # from pydub import AudioSegment


# # # ==============================
# # # CONFIG
# # # ==============================
# # TRANSLATED_JSON = "work/translated_segments_interactive.json"
# # OUTPUT_DIR = "work/voice_clips"
# # METADATA_OUT = "work/voice_clips_metadata.json"
# # SAMPLE_ROOT = "sample_voices"

# # LANGUAGE_CODE = "en"

# # # Duration control limits (prevent robotic distortion)
# # MAX_STRETCH = 1.25
# # MIN_STRETCH = 0.85

# # # Emotion mapping from your JSON format
# # EMOTION_MAP = {
# #     "hap": "happy",
# #     "sad": "sad",
# #     "ang": "angry",
# #     "fea": "fearful",
# #     "sur": "surprised",
# #     "neu": "neutral"
# # }

# # # Better anime-style emotional conditioning
# # STYLE_PROMPTS = {
# #     "happy": "In a bright, cheerful anime voice, say:",
# #     "sad": "In a soft emotional voice, say:",
# #     "angry": "In an intense angry anime voice, say:",
# #     "fearful": "In a trembling fearful voice, say:",
# #     "surprised": "In a shocked surprised voice, say:",
# #     "neutral": ""
# # }


# # # ==============================
# # # UTILITIES
# # # ==============================
# # def check_files():
# #     if not os.path.exists(TRANSLATED_JSON):
# #         print(f"❌ Missing {TRANSLATED_JSON}")
# #         return False
# #     os.makedirs(OUTPUT_DIR, exist_ok=True)
# #     return True


# # def load_segments():
# #     with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
# #         data = json.load(f)
# #     segments = data.get("segments", [])
# #     print(f"📄 Loaded {len(segments)} segments")
# #     return segments


# # def list_samples():
# #     samples = {"male": [], "female": []}
# #     for gender in samples.keys():
# #         folder = os.path.join(SAMPLE_ROOT, gender)
# #         if os.path.isdir(folder):
# #             for f in sorted(os.listdir(folder)):
# #                 if f.lower().endswith((".wav", ".mp3")):
# #                     samples[gender].append(os.path.join(folder, f))
# #     return samples


# # def select_voice(samples):
# #     print("\n🎭 Select voice sample")
# #     all_samples = samples["male"] + samples["female"]

# #     if not all_samples:
# #         raise Exception("❌ No voice samples found in sample_voices folder!")

# #     for i, path in enumerate(all_samples, 1):
# #         print(f"[{i}] {os.path.basename(path)}")

# #     choice = input("Choose sample number (default=1): ").strip()
# #     idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(all_samples) else 0

# #     selected = all_samples[idx]
# #     print(f"✅ Selected: {os.path.basename(selected)}")
# #     return selected


# # def build_emotional_text(seg):
# #     base_text = seg.get("translated_text", "")
# #     emotion_short = seg.get("emotion", "neu").lower()
# #     emotion = EMOTION_MAP.get(emotion_short, "neutral")

# #     confidence = seg.get("emotion_confidence", 0.0)

# #     if confidence < 0.6:
# #         emotion = "neutral"

# #     style_prefix = STYLE_PROMPTS.get(emotion, "")
# #     if style_prefix:
# #         final_text = f"{style_prefix} {base_text}"
# #     else:
# #         final_text = base_text

# #     return final_text, emotion


# # def match_duration(audio_path, target_duration):
# #     audio = AudioSegment.from_file(audio_path)
# #     current_duration = len(audio) / 1000.0

# #     if target_duration <= 0:
# #         return

# #     ratio = target_duration / current_duration

# #     # Keep safe range
# #     if ratio > MAX_STRETCH:
# #         ratio = MAX_STRETCH
# #     elif ratio < MIN_STRETCH:
# #         ratio = MIN_STRETCH

# #     # Only adjust if outside 10% tolerance
# #     if abs(current_duration - target_duration) / target_duration > 0.1:
# #         new_frame_rate = int(audio.frame_rate * ratio)
# #         stretched = audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})
# #         stretched = stretched.set_frame_rate(audio.frame_rate)
# #         stretched.export(audio_path, format="wav")


# # # ==============================
# # # LOAD XTTS
# # # ==============================
# # def load_model():
# #     device = "cuda" if torch.cuda.is_available() else "cpu"
# #     print(f"🧠 Loading XTTS on {device} ...")
# #     tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
# #     print("✅ Model loaded")
# #     return tts


# # # ==============================
# # # MAIN
# # # ==============================
# # def generate():
# #     if not check_files():
# #         return

# #     segments = load_segments()
# #     samples = list_samples()
# #     selected_voice = select_voice(samples)

# #     tts = load_model()

# #     clips_meta = []

# #     print("\n🎙 Generating voices...\n")

# #     for idx, seg in enumerate(segments, 1):

# #         text, emotion = build_emotional_text(seg)
# #         duration_target = seg.get("duration", 0.0)

# #         if not text.strip():
# #             print(f"[{idx}] Empty text — skipping")
# #             continue

# #         print(f"[{idx}/{len(segments)}] Emotion: {emotion}")
# #         print(f"Text: {text[:70]}...\n")

# #         output_path = os.path.join(
# #             OUTPUT_DIR,
# #             f"segment_{idx:03d}.wav"
# #         )

# #         try:
# #             tts.tts_to_file(
# #                 text=text,
# #                 file_path=output_path,
# #                 speaker_wav=[selected_voice],
# #                 language=LANGUAGE_CODE,
# #             )
# #         except Exception as e:
# #             print(f"❌ TTS error: {e}")
# #             continue

# #         # Duration sync
# #         try:
# #             match_duration(output_path, duration_target)
# #         except Exception as e:
# #             print(f"⚠ Duration match error: {e}")

# #         seg_meta = seg.copy()
# #         seg_meta["audio_file"] = output_path
# #         seg_meta["emotion_used"] = emotion

# #         clips_meta.append(seg_meta)

# #         time.sleep(0.1)

# #     metadata = {
# #         "timestamp": datetime.now().isoformat(),
# #         "backend": "xtts_v2",
# #         "voice_sample": selected_voice,
# #         "total_clips": len(clips_meta),
# #         "clips": clips_meta
# #     }

# #     with open(METADATA_OUT, "w", encoding="utf-8") as f:
# #         json.dump(metadata, f, ensure_ascii=False, indent=2)

# #     print("\n✅ Voice generation complete!")
# #     print(f"📁 Audio clips: {OUTPUT_DIR}")
# #     print(f"💾 Metadata saved: {METADATA_OUT}")
# #     print("\nNext: python step6_final_assembly.py")


# # if __name__ == "__main__":
# #     generate()
# import os
# import json
# import time
# from datetime import datetime

# import torch
# from TTS.api import TTS
# from pydub import AudioSegment


# # CONFIG
# TRANSLATED_JSON = "work/translated_segments_interactive.json"
# OUTPUT_DIR = "work/voice_clips"
# METADATA_OUT = "work/voice_clips_metadata.json"
# SAMPLE_ROOT = "sample_voices"
# LANGUAGE_CODE = "en"

# MAX_STRETCH = 1.25
# MIN_STRETCH = 0.85


# EMOTION_MAP = {
#     "hap": "happy",
#     "sad": "sad",
#     "ang": "angry",
#     "fea": "fearful",
#     "sur": "surprised",
#     "neu": "neutral"
# }

# STYLE_PROMPTS = {
#     "happy": "In a bright cheerful anime voice, say:",
#     "sad": "In a soft emotional voice, say:",
#     "angry": "In an intense angry anime voice, say:",
#     "fearful": "In a trembling fearful voice, say:",
#     "surprised": "In a shocked surprised voice, say:",
#     "neutral": ""
# }


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


# def manual_speaker_mapping(unique_speakers, samples):
#     mapping = {}

#     print("\n🎭 MANUAL VOICE ASSIGNMENT\n")

#     for speaker in unique_speakers:
#         print(f"\nAssign voice for speaker: {speaker}")

#         for i, sample in enumerate(samples, 1):
#             print(f"[{i}] {os.path.basename(sample)}")

#         choice = input("Choose sample number: ").strip()
#         while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
#             choice = input("Invalid. Choose again: ").strip()

#         mapping[speaker] = samples[int(choice) - 1]
#         print(f"✅ {speaker} → {os.path.basename(mapping[speaker])}")

#     return mapping
# def choose_voice(samples, message="Choose voice sample"):
#     print(f"\n{message}")
#     for i, sample in enumerate(samples, 1):
#         print(f"[{i}] {os.path.basename(sample)}")

#     choice = input("Choose sample number: ").strip()
#     while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
#         choice = input("Invalid. Choose again: ").strip()

#     return samples[int(choice) - 1]

# # def build_emotional_text(seg):
# #     base_text = seg.get("translated_text", "")
# #     emotion_code = seg.get("emotion", "neu").lower()
# #     emotion = EMOTION_MAP.get(emotion_code, "neutral")

# #     confidence = seg.get("emotion_confidence", 0.0)
# #     if confidence < 0.6:
# #         emotion = "neutral"

# #     prefix = STYLE_PROMPTS.get(emotion, "")
# #     return f"{prefix} {base_text}" if prefix else base_text, emotion

# def build_emotional_text(seg):
#     text = seg.get("translated_text", "")
#     emotion_code = seg.get("emotion", "neu").lower()
#     confidence = seg.get("emotion_confidence", 0.0)

#     if confidence < 0.6:
#         return text, "neutral"

#     if emotion_code == "ang":
#         text = text.rstrip(".") + "!"
#     elif emotion_code == "sad":
#         text = text.rstrip(".") + "..."
#     elif emotion_code == "hap":
#         text = text.rstrip(".") + "!"
#     elif emotion_code == "fea":
#         text = "W-" + text

#     return text, emotion_code

# def match_duration(audio_path, target_duration):
#     audio = AudioSegment.from_file(audio_path)
#     current_duration = len(audio) / 1000.0

#     if target_duration <= 0:
#         return

#     ratio = target_duration / current_duration

#     if ratio > MAX_STRETCH:
#         ratio = MAX_STRETCH
#     elif ratio < MIN_STRETCH:
#         ratio = MIN_STRETCH

#     if abs(current_duration - target_duration) / target_duration > 0.1:
#         new_rate = int(audio.frame_rate * ratio)
#         stretched = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
#         stretched = stretched.set_frame_rate(audio.frame_rate)
#         stretched.export(audio_path, format="wav")


# def load_model():
#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     print(f"\n🧠 Loading XTTS on {device}...")
#     model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
#     print("✅ Model loaded\n")
#     return model


# # def generate():
# #     os.makedirs(OUTPUT_DIR, exist_ok=True)

# #     segments = load_segments()
# #     samples = list_voice_samples()

# #     if not samples:
# #         raise Exception("❌ No voice samples found in sample_voices folder")

# #     unique_speakers = get_unique_speakers(segments)
# #     speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)

# #     tts = load_model()

# #     metadata = []

# #     print("\n🎙 Generating Voice Clips...\n")

# #     for idx, seg in enumerate(segments, 1):

# #         speaker = seg.get("speaker", "UNKNOWN")
# #         sample_voice = speaker_voice_map[speaker]

# #         text, emotion = build_emotional_text(seg)
# #         target_duration = seg.get("duration", 0)

# #         output_path = os.path.join(
# #             OUTPUT_DIR,
# #             f"segment_{idx:03d}_{speaker}.wav"
# #         )

# #         print(f"[{idx}] Speaker: {speaker} | Emotion: {emotion}")

# #         tts.tts_to_file(
# #             text=text,
# #             file_path=output_path,
# #             speaker_wav=[sample_voice],
# #             language=LANGUAGE_CODE
# #         )

# #         match_duration(output_path, target_duration)

# #         seg_meta = seg.copy()
# #         seg_meta["audio_file"] = output_path
# #         seg_meta["voice_sample"] = sample_voice
# #         seg_meta["emotion_used"] = emotion

# #         metadata.append(seg_meta)
# #         time.sleep(0.1)

# #     final_meta = {
# #         "timestamp": datetime.now().isoformat(),
# #         "speakers": speaker_voice_map,
# #         "total_clips": len(metadata),
# #         "clips": metadata
# #     }

# #     with open(METADATA_OUT, "w", encoding="utf-8") as f:
# #         json.dump(final_meta, f, indent=2, ensure_ascii=False)

# #     print("\n✅ Multi-speaker voice generation finished.")
# def generate():
#     os.makedirs(OUTPUT_DIR, exist_ok=True)

#     segments = load_segments()
#     samples = list_voice_samples()

#     if not samples:
#         raise Exception("❌ No voice samples found in sample_voices folder")

#     print("\nVoice Assignment Mode")
#     print("1 - Speaker based")
#     print("2 - Segment based")
#     print("3 - Speaker + override")

#     mode = input("Choose mode: ").strip()

#     speaker_voice_map = {}

#     if mode in ["1", "3"]:
#         unique_speakers = get_unique_speakers(segments)
#         speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)

#     tts = load_model()

#     metadata = []

#     print("\n🎙 Generating Voice Clips...\n")

#     for idx, seg in enumerate(segments, 1):

#         speaker = seg.get("speaker", "UNKNOWN")

#         # -------- Voice Selection Logic --------

#         if mode == "1":
#             sample_voice = speaker_voice_map[speaker]

#         elif mode == "2":
#             sample_voice = choose_voice(
#                 samples,
#                 f"Segment {idx} | Speaker: {speaker}\nText: {seg.get('translated_text','')}"
#             )

#         elif mode == "3":
#             default_voice = speaker_voice_map[speaker]

#             print(f"\nSegment {idx} | Speaker: {speaker}")
#             print(f"Default voice: {os.path.basename(default_voice)}")
#             override = input("Override voice? (y/n): ").strip().lower()

#             if override == "y":
#                 sample_voice = choose_voice(samples, "Choose override voice")
#             else:
#                 sample_voice = default_voice

#         else:
#             raise Exception("Invalid mode selected")

#         # -------- Emotion Processing --------

#         text, emotion = build_emotional_text(seg)
#         target_duration = seg.get("duration", 0)

#         output_path = os.path.join(
#             OUTPUT_DIR,
#             f"segment_{idx:03d}_{speaker}.wav"
#         )

#         print(f"[{idx}] Speaker: {speaker} | Emotion: {emotion}")
#         print(f"Voice: {os.path.basename(sample_voice)}")

#         tts.tts_to_file(
#             text=text,
#             file_path=output_path,
#             speaker_wav=[sample_voice],
#             language=LANGUAGE_CODE
#         )

#         match_duration(output_path, target_duration)

#         seg_meta = seg.copy()
#         seg_meta["audio_file"] = output_path
#         seg_meta["voice_sample"] = sample_voice
#         seg_meta["emotion_used"] = emotion

#         metadata.append(seg_meta)
#         time.sleep(0.1)

#     final_meta = {
#         "timestamp": datetime.now().isoformat(),
#         "speakers": speaker_voice_map,
#         "total_clips": len(metadata),
#         "clips": metadata
#     }

#     with open(METADATA_OUT, "w", encoding="utf-8") as f:
#         json.dump(final_meta, f, indent=2, ensure_ascii=False)

#     print("\n✅ Multi-speaker voice generation finished.")

# if __name__ == "__main__":
#     generate()
import os
import json
import time
from datetime import datetime
import torch
from TTS.api import TTS
from pydub import AudioSegment

# CONFIG (unchanged)
TRANSLATED_JSON = "work/translated_segments_interactive.json"
OUTPUT_DIR = "work/voice_clips"
METADATA_OUT = "work/voice_clips_metadata.json"
SAMPLE_ROOT = "sample_voices"
LANGUAGE_CODE = "en"

MAX_STRETCH = 1.25
MIN_STRETCH = 0.85

# IMPROVED: Emotion → Prosody mapping (XTTS-native control)
EMOTION_PROSODY = {
    "happy":    {"speed": 1.15, "pitch_shift": 1.1,  "temp": 0.4, "desc": "cheerfully"},
    "sad":      {"speed": 0.85, "pitch_shift": 0.9,  "temp": 0.3, "desc": "sadly"},
    "angry":    {"speed": 1.25, "pitch_shift": 1.05, "temp": 0.5, "desc": "angrily"},
    "fearful":  {"speed": 0.95, "pitch_shift": 1.15, "temp": 0.45, "desc": "trembling"},
    "surprised": {"speed": 1.2,  "pitch_shift": 1.2,  "temp": 0.5, "desc": "shocked"},
    "neutral":  {"speed": 1.0,  "pitch_shift": 1.0,   "temp": 0.35, "desc": ""}
}

def load_segments():
    with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("segments", [])

# ... (keep your list_voice_samples, get_unique_speakers, manual_speaker_mapping, choose_voice unchanged)
def list_voice_samples():
    samples = []
    for root, _, files in os.walk(SAMPLE_ROOT):
        for f in files:
            if f.lower().endswith((".wav", ".mp3")):
                samples.append(os.path.join(root, f))
    return sorted(samples)


def get_unique_speakers(segments):
    return sorted(set(seg.get("speaker", "UNKNOWN") for seg in segments))


def manual_speaker_mapping(unique_speakers, samples):
    mapping = {}

    print("\n🎭 MANUAL VOICE ASSIGNMENT\n")

    for speaker in unique_speakers:
        print(f"\nAssign voice for speaker: {speaker}")

        for i, sample in enumerate(samples, 1):
            print(f"[{i}] {os.path.basename(sample)}")

        choice = input("Choose sample number: ").strip()
        while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
            choice = input("Invalid. Choose again: ").strip()

        mapping[speaker] = samples[int(choice) - 1]
        print(f"✅ {speaker} → {os.path.basename(mapping[speaker])}")

    return mapping
def choose_voice(samples, message="Choose voice sample"):
    print(f"\n{message}")
    for i, sample in enumerate(samples, 1):
        print(f"[{i}] {os.path.basename(sample)}")

    choice = input("Choose sample number: ").strip()
    while not choice.isdigit() or not (1 <= int(choice) <= len(samples)):
        choice = input("Invalid. Choose again: ").strip()

    return samples[int(choice) - 1]

def build_emotional_text(seg):
    """Enhanced: Text engineering + prosody hints for XTTS"""
    text = seg.get("translated_text", "").strip()
    emotion_code = seg.get("emotion", "neu").lower()
    confidence = seg.get("emotion_confidence", 0.0)
    
    if confidence < 0.6:
        return text, "neutral"
    
    emotion = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
    
    # Punctuation for natural prosody
    if emotion_code == "angry":
        text = text.rstrip(".?!") + "!!"
    elif emotion_code == "sad":
        text = text.rstrip(".?!") + "..."
    elif emotion_code == "happy":
        text = text.rstrip(".?!") + "!"
    elif emotion_code == "fearful":
        text = "(stammering) " + text
    elif emotion_code == "surprised":
        text = "!? " + text
    
    # Style descriptor (XTTS picks up context)
    styled = f"[{emotion['desc']}] {text}" if emotion["desc"] else text
    
    return styled, emotion_code

def preview_emotion(tts, sample_voice, text_sample, emotion_code):
    """Quick preview of emotion tuning for first segment"""
    emotion = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
    preview_path = "work/preview_emotion.wav"
    
    tts.tts_to_file(
        text=text_sample,
        file_path=preview_path,
        speaker_wav=[sample_voice],
        language=LANGUAGE_CODE,
        speed=emotion["speed"],      # Core emotion control
        temperature=emotion["temp"]
    )
    print(f"🔊 Preview saved: {preview_path}")

def post_process_prosody(audio_path, emotion_code, target_duration):
    """Apply pitch shift + fine-tune speed (pydub post-processing)"""
    audio = AudioSegment.from_file(audio_path)
    emotion = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
    
    # Pitch shift (semitones)
    octaves = (emotion["pitch_shift"] - 1.0) * 0.12  # ~12 semitones per octave
    audio = audio._spawn(audio.raw_data, overrides={
        'frame_rate': int(audio.frame_rate * (2.0 ** octaves))
    }).set_frame_rate(audio.frame_rate)
    
    # Duration matching (existing logic, now emotion-aware)
    current_duration = len(audio) / 1000.0
    if target_duration > 0 and abs(current_duration - target_duration) / target_duration > 0.1:
        ratio = target_duration / current_duration
        ratio = max(MIN_STRETCH, min(MAX_STRETCH, ratio))
        new_rate = int(audio.frame_rate * ratio)
        audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_rate})
        audio = audio.set_frame_rate(audio.frame_rate)
    
    audio.export(audio_path, format="wav")

def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🧠 Loading XTTS v2 on {device}...")
    model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    print("✅ Model loaded\n")
    return model

def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    segments = load_segments()
    samples = list_voice_samples()
    
    if not samples:
        raise Exception("❌ No voice samples found in sample_voices folder")
    
    # Voice assignment modes (your existing logic)
    print("\nVoice Assignment Mode")
    print("1 - Speaker based")
    print("2 - Segment based") 
    print("3 - Speaker + override")
    mode = input("Choose mode: ").strip()
    
    speaker_voice_map = {}
    if mode in ["1", "3"]:
        unique_speakers = get_unique_speakers(segments)
        speaker_voice_map = manual_speaker_mapping(unique_speakers, samples)
    
    tts = load_model()
    metadata = []
    
    # NEW: Emotion preview (optional, for first segment)
    first_seg = segments[0] if segments else None
    if first_seg:
        print("\n🎭 Emotion Preview? (y/n): ", end="")
        if input().lower() == 'y':
            sample_voice = list(samples)[0]  # Default sample
            text_sample, emotion_sample = build_emotional_text(first_seg)
            preview_emotion(tts, sample_voice, text_sample, first_seg.get("emotion", "neu"))
    
    print("\n🎙 Generating Emotion-Tuned Voice Clips...\n")
    
    for idx, seg in enumerate(segments, 1):
        speaker = seg.get("speaker", "UNKNOWN")
        
        # Voice selection (your existing modes)
        if mode == "1":
            sample_voice = speaker_voice_map[speaker]
        # elif mode == "2":
        #     sample_voice = choose_voice(samples, f"Segment {idx} | Speaker: {speaker}")
        elif mode == "2":
            sentence = seg.get("translated_text", "").strip()
            emotion = seg.get("emotion", "neutral")
            duration = seg.get("duration", 0)

            print("\n--------------------------------")
            print(f"Segment {idx}")
            print(f"Speaker   : {speaker}")
            print(f"Emotion   : {emotion}")
            print(f"Duration  : {duration:.2f}s")
            print(f"Dialogue  : {sentence}")
            print("--------------------------------")

            sample_voice = choose_voice(samples, "Choose voice sample")
        elif mode == "3":
            default_voice = speaker_voice_map[speaker]
            print(f"\nSegment {idx} | Speaker: {speaker}")
            print(f"Default: {os.path.basename(default_voice)}")
            override = input("Override voice? (y/n): ").strip().lower()
            sample_voice = choose_voice(samples, "Choose override") if override == "y" else default_voice
        else:
            raise Exception("Invalid mode")
        
        # Emotion processing
        text, emotion_code = build_emotional_text(seg)
        emotion_config = EMOTION_PROSODY.get(emotion_code, EMOTION_PROSODY["neutral"])
        target_duration = seg.get("duration", 0)
        
        output_path = os.path.join(OUTPUT_DIR, f"segment_{idx:03d}_{speaker}.wav")
        
        print(f"[{idx:2d}] {speaker:10} | {emotion_code:8} | {os.path.basename(sample_voice)}")
        print(f"     Speed:{emotion_config['speed']:.2f} Temp:{emotion_config['temp']:.2f}")
        
        # XTTS generation with emotion prosody
        tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=[sample_voice],
            language=LANGUAGE_CODE,
            speed=emotion_config["speed"],           # Faster=excited, slower=sad
            temperature=emotion_config["temp"]       # More varied=emotional
        )
        
        # Post-process pitch + duration
        post_process_prosody(output_path, emotion_code, target_duration)
        
        # Metadata
        seg_meta = seg.copy()
        seg_meta["audio_file"] = output_path
        seg_meta["voice_sample"] = sample_voice
        seg_meta["emotion_used"] = emotion_code
        seg_meta["prosody"] = emotion_config  # Save settings
        metadata.append(seg_meta)
        
        time.sleep(0.1)  # Rate limit
    
    # Save enhanced metadata
    final_meta = {
        "timestamp": datetime.now().isoformat(),
        "tts_model": "xtts_v2",
        "speakers": speaker_voice_map,
        "emotions_used": list(set(m["emotion_used"] for m in metadata)),
        "total_clips": len(metadata),
        "clips": metadata
    }
    
    with open(METADATA_OUT, "w", encoding="utf-8") as f:
        json.dump(final_meta, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Emotion-tuned generation complete! {len(metadata)} clips")
    print(f"📊 Emotions: {final_meta['emotions_used']}")

if __name__ == "__main__":
    generate()
