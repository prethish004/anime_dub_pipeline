# # step_emotion_detection.py (Speech Emotion Recognition)
# import json
# import os
# import librosa
# import numpy as np
# import torch
# from transformers import pipeline, AutoProcessor, AutoModelForAudioClassification
# from datetime import datetime
# import warnings
# warnings.filterwarnings('ignore')

# # Configuration
# AUDIO_FILE = "work/audio_16k.wav"
# TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
# OUTPUT_JSON = "work/emotion_detection.json"

# # Emotion Recognition Model
# EMOTION_MODEL = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"

# # Emotion to ElevenLabs Audio Tag Mapping
# EMOTION_TO_TAG = {
#     'angry': '[angry]',
#     'disgust': '[sarcastic]',
#     'fearful': '[nervous]',
#     'happy': '[excited]',
#     'neutral': '',  # No tag for neutral
#     'sad': '[sad]',
#     'surprised': '[surprised]'
# }

# # Emotion Confidence Threshold
# CONFIDENCE_THRESHOLD = 0.3


# def check_prerequisites():
#     """Check if required files exist"""
    
#     if not os.path.exists(AUDIO_FILE):
#         print(f"❌ Audio file not found: {AUDIO_FILE}")
#         print("   Please run step1_extract_audio.py first")
#         return False
    
#     if not os.path.exists(TRANSCRIPTION_FILE):
#         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
#         print("   Please run step3_diarization.py first")
#         return False
    
#     return True


# def load_transcription():
#     """Load transcription from JSON"""
#     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     print(f"📄 Loaded {data['total_segments']} transcription segments")
#     return data


# def load_audio(audio_file):
#     """Load audio file"""
#     try:
#         y, sr = librosa.load(audio_file, sr=16000, mono=True)
#         return y, sr
#     except Exception as e:
#         print(f"❌ Error loading audio: {e}")
#         return None, None


# def load_emotion_model():
#     """Load emotion recognition model"""
    
#     print(f"\n🧠 Loading emotion recognition model...")
#     print(f"   Model: {EMOTION_MODEL}")
    
#     try:
#         device = 0 if torch.cuda.is_available() else -1  # -1 = CPU
#         device_name = "GPU (CUDA)" if device == 0 else "CPU"
#         print(f"   Device: {device_name}")
        
#         # Load processor and model
#         processor = AutoProcessor.from_pretrained(EMOTION_MODEL)
#         model = AutoModelForAudioClassification.from_pretrained(EMOTION_MODEL)
        
#         # Create pipeline
#         classifier = pipeline(
#             "audio-classification",
#             model=model,
#             processor=processor,
#             device=device
#         )
        
#         print(f"✅ Model loaded successfully")
#         return classifier, processor, model
    
#     except Exception as e:
#         print(f"❌ Error loading emotion model: {e}")
#         print(f"\n💡 Troubleshooting:")
#         print(f"   pip install --upgrade transformers torch librosa")
#         return None, None, None


# def detect_emotion_for_segment(audio, sr, classifier, start_time, end_time):
#     """Detect emotion for a single segment"""
    
#     try:
#         # Extract segment audio
#         start_sample = int(start_time * sr)
#         end_sample = int(end_time * sr)
#         audio_segment = audio[start_sample:end_sample]
        
#         # Ensure segment is long enough (at least 0.5 seconds)
#         if len(audio_segment) < sr * 0.5:
#             return {
#                 'emotion': 'neutral',
#                 'confidence': 0.0,
#                 'scores': {},
#                 'status': 'too_short'
#             }
        
#         # Detect emotion
#         results = classifier(audio_segment, sampling_rate=sr, top_k=7)
        
#         # Parse results
#         emotion_scores = {}
#         top_emotion = None
#         top_confidence = 0.0
        
#         for result in results:
#             emotion = result['label'].lower()
#             score = result['score']
#             emotion_scores[emotion] = float(score)
            
#             if score > top_confidence:
#                 top_confidence = score
#                 top_emotion = emotion
        
#         return {
#             'emotion': top_emotion,
#             'confidence': float(top_confidence),
#             'scores': emotion_scores,
#             'status': 'success'
#         }
    
#     except Exception as e:
#         print(f"   ⚠️  Error: {str(e)[:50]}")
#         return {
#             'emotion': 'neutral',
#             'confidence': 0.0,
#             'scores': {},
#             'status': f'error: {str(e)[:30]}'
#         }


# def detect_emotions(audio, sr, segments, classifier):
#     """Detect emotions for all segments"""
    
#     print(f"\n🎭 Detecting emotions for {len(segments)} segments...")
#     print("⏳ This may take 5-15 minutes (first time downloads are slower)...\n")
    
#     emotion_results = []
    
#     for idx, seg in enumerate(segments, 1):
#         start_time = seg['start']
#         end_time = seg['end']
#         duration = seg['duration']
        
#         print(f"[{idx}/{len(segments)}] Segment {idx} ({duration:.2f}s)...", end=' ')
        
#         # Detect emotion
#         emotion_data = detect_emotion_for_segment(
#             audio, sr, classifier, start_time, end_time
#         )
        
#         emotion_results.append({
#             'segment_id': idx,
#             'start': start_time,
#             'end': end_time,
#             'duration': duration,
#             'emotion': emotion_data['emotion'],
#             'confidence': emotion_data['confidence'],
#             'scores': emotion_data['scores'],
#             'status': emotion_data['status']
#         })
        
#         # Display result with emoji
#         emotion = emotion_data['emotion']
#         confidence = emotion_data['confidence']
#         emoji = get_emotion_emoji(emotion)
        
#         if confidence >= 0.7:
#             status = "✅ Strong"
#         elif confidence >= 0.5:
#             status = "⚠️  Moderate"
#         elif confidence >= 0.3:
#             status = "⚠️  Weak"
#         else:
#             status = "❌ Unclear"
        
#         print(f"{emoji} {emotion.upper()} ({confidence:.2%}) {status}")
    
#     return emotion_results


# def get_emotion_emoji(emotion):
#     """Get emoji for emotion"""
#     emoji_map = {
#         'angry': '🔴',
#         'disgust': '🤮',
#         'fearful': '😨',
#         'happy': '😊',
#         'neutral': '😐',
#         'sad': '😢',
#         'surprised': '😲'
#     }
#     return emoji_map.get(emotion, '❓')


# def analyze_emotion_distribution(emotion_results):
#     """Analyze emotion distribution statistics"""
    
#     print(f"\n" + "="*70)
#     print("📊 EMOTION DISTRIBUTION ANALYSIS")
#     print("="*70)
    
#     # Count emotions
#     emotion_counts = {}
#     emotion_durations = {}
#     emotion_confidences = {}
    
#     for result in emotion_results:
#         emotion = result['emotion']
#         duration = result['duration']
#         confidence = result['confidence']
        
#         emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
#         emotion_durations[emotion] = emotion_durations.get(emotion, 0) + duration
        
#         if emotion not in emotion_confidences:
#             emotion_confidences[emotion] = []
#         emotion_confidences[emotion].append(confidence)
    
#     # Calculate averages
#     emotion_avg_confidence = {
#         emotion: np.mean(confidences) 
#         for emotion, confidences in emotion_confidences.items()
#     }
    
#     # Display statistics
#     print(f"\nTotal segments: {len(emotion_results)}")
    
#     print(f"\n🎭 Emotion Breakdown:")
#     print(f"   {'Emotion':<12} | {'Count':<6} | {'Duration':<10} | {'Avg Confidence':<15}")
#     print(f"   {'-'*12}-+-{'-'*6}-+-{'-'*10}-+-{'-'*15}")
    
#     for emotion in sorted(emotion_counts.keys()):
#         count = emotion_counts[emotion]
#         total_duration = emotion_durations[emotion]
#         avg_conf = emotion_avg_confidence[emotion]
#         emoji = get_emotion_emoji(emotion)
        
#         print(f"   {emoji} {emotion:<10} | {count:<6} | {total_duration:>8.1f}s | {avg_conf:>13.1%}")
    
#     # Timeline visualization
#     print(f"\n📈 Emotion Timeline (Visualization):")
#     for result in emotion_results[:10]:  # Show first 10
#         emotion = result['emotion']
#         confidence = result['confidence']
#         emoji = get_emotion_emoji(emotion)
#         bar_length = int(confidence * 20)
#         bar = "█" * bar_length + "░" * (20 - bar_length)
#         print(f"   {emoji} [{result['segment_id']:2d}] {bar} {confidence:.1%}")
    
#     if len(emotion_results) > 10:
#         print(f"   ... and {len(emotion_results) - 10} more segments")
    
#     # Emotion stability check
#     print(f"\n🎯 Emotion Consistency:")
#     max_emotion = max(emotion_counts.items(), key=lambda x: x[1])
#     max_percentage = (max_emotion[1] / len(emotion_results)) * 100
#     print(f"   Most common: {get_emotion_emoji(max_emotion[0])} {max_emotion[0].upper()} ({max_emotion[1]} segments, {max_percentage:.1f}%)")
    
#     if max_percentage > 70:
#         print(f"   💡 Mostly consistent emotion (good for dubbing)")
#     elif max_percentage > 50:
#         print(f"   💡 Mixed emotions (multiple character states)")
#     else:
#         print(f"   💡 Highly varied emotions (dynamic scene)")


# def add_emotion_tags_to_translation(transcription_data, emotion_results):
#     """Add emotion tags to translated text"""
    
#     print(f"\n🏷️  Adding emotion tags to translations...")
    
#     # Create emotion map for easy lookup
#     emotion_map = {result['segment_id']: result for result in emotion_results}
    
#     # Add emotion tags
#     for seg in transcription_data['segments']:
#         segment_id = seg['id'] + 1  # segment_id is 1-indexed
#         emotion_result = emotion_map.get(segment_id)
        
#         if emotion_result:
#             seg['detected_emotion'] = emotion_result['emotion']
#             seg['emotion_confidence'] = emotion_result['confidence']
#             seg['emotion_tag'] = EMOTION_TO_TAG.get(emotion_result['emotion'], '')
#         else:
#             seg['detected_emotion'] = 'neutral'
#             seg['emotion_confidence'] = 0.0
#             seg['emotion_tag'] = ''
    
#     print(f"✅ Emotion tags added to all segments")
#     return transcription_data


# def create_emotion_instruction_prompt(emotion):
#     """Create instruction for voice generation based on emotion"""
    
#     instructions = {
#         'angry': "Speak with anger and intensity. Use a sharp, harsh tone.",
#         'disgust': "Speak with sarcasm and disdain. Sound dismissive.",
#         'fearful': "Speak with nervousness and fear. Sound uncertain and shaky.",
#         'happy': "Speak with excitement and joy. Sound cheerful and energetic.",
#         'neutral': "Speak in a normal, calm tone.",
#         'sad': "Speak with sadness and melancholy. Sound downbeat.",
#         'surprised': "Speak with surprise and shock. Sound astonished."
#     }
    
#     return instructions.get(emotion, "Speak in a natural tone.")


# def save_results(transcription_data, emotion_results):
#     """Save emotion detection results"""
    
#     output_data = {
#         'timestamp': datetime.now().isoformat(),
#         'model': EMOTION_MODEL,
#         'total_segments': len(emotion_results),
#         'emotions': emotion_results,
#         'emotion_to_tag_mapping': EMOTION_TO_TAG,
#         'statistics': {
#             'total_duration': sum(r['duration'] for r in emotion_results),
#             'emotion_distribution': {}
#         }
#     }
    
#     # Calculate emotion distribution
#     emotion_counts = {}
#     for result in emotion_results:
#         emotion = result['emotion']
#         emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
#     output_data['statistics']['emotion_distribution'] = emotion_counts
    
#     # Save emotion results
#     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#         json.dump(output_data, f, ensure_ascii=False, indent=2)
    
#     print(f"\n💾 Emotion detection results saved to: {OUTPUT_JSON}")
    
#     return output_data


# def display_emotion_guide(emotion_results):
#     """Display usage guide for emotion tags in voice generation"""
    
#     print(f"\n" + "="*70)
#     print("🎤 EMOTION TAGS FOR VOICE GENERATION")
#     print("="*70)
    
#     print(f"\nHow to use with ElevenLabs Voice Generation:")
#     print(f"\nInstead of:")
#     print(f'   Translation: "Feel the pain"')
#     print(f'   ElevenLabs will use neutral tone')
    
#     print(f"\nUse emotion tags:")
#     print(f'   Translation: "[angry] Feel the pain!"')
#     print(f'   ElevenLabs will speak with anger')
    
#     print(f"\n📋 Emotion Tag Reference:")
#     print(f"   {'Emotion':<12} | {'ElevenLabs Tag':<18} | {'Example':<40}")
#     print(f"   {'-'*12}-+-{'-'*18}-+-{'-'*40}")
    
#     examples = {
#         'angry': ('[angry]', '[angry] You will fall!'),
#         'disgust': ('[sarcastic]', '[sarcastic] Oh, wonderful...'),
#         'fearful': ('[nervous]', '[nervous] What is that?!'),
#         'happy': ('[excited]', '[excited] I love this!'),
#         'neutral': ('(none)', 'Just a normal sentence'),
#         'sad': ('[sad]', '[sad] I cannot go on...'),
#         'surprised': ('[surprised]', '[surprised] That\'s impossible!')
#     }
    
#     for emotion, (tag, example) in examples.items():
#         emoji = get_emotion_emoji(emotion)
#         print(f"   {emoji} {emotion:<10} | {tag:<18} | {example:<40}")
    
#     print(f"\n💡 Tips:")
#     print(f"   1. Place tag at START of sentence")
#     print(f"   2. Use ONE tag per segment")
#     print(f"   3. Neutral emotion = NO tag needed")
#     print(f"   4. Tag increases voice emotion intensity by ~20-30%")
#     print(f"   5. Works best with confident emotions (>60% confidence)")


# def display_segment_emotions(emotion_results, transcription_data):
#     """Display emotions for each segment"""
    
#     print(f"\n" + "="*70)
#     print("📋 EMOTION MAPPING FOR ALL SEGMENTS")
#     print("="*70)
    
#     segments = transcription_data['segments']
    
#     print(f"\n{'Seg':<4} | {'Time':<12} | {'Text':<30} | {'Emotion':<10} | {'Conf':<6} | {'Tag':<12}")
#     print(f"{'-'*4}-+-{'-'*12}-+-{'-'*30}-+-{'-'*10}-+-{'-'*6}-+-{'-'*12}")
    
#     for result in emotion_results[:15]:  # Show first 15
#         seg_idx = result['segment_id']
#         segment = segments[seg_idx - 1]
        
#         text = segment['text'][:28].ljust(28)
#         emotion = result['emotion']
#         confidence = result['confidence']
#         tag = EMOTION_TO_TAG.get(emotion, '(none)')
#         emoji = get_emotion_emoji(emotion)
#         time_str = f"{result['start']:.1f}-{result['end']:.1f}s"
        
#         print(f" {seg_idx:<3} | {time_str:<12} | {text} | {emoji} {emotion:<8} | {confidence:>5.1%} | {tag:<12}")
    
#     if len(emotion_results) > 15:
#         print(f"... and {len(emotion_results) - 15} more segments")


# def main():
#     print("=" * 70)
#     print("STEP 5A: Speech Emotion Recognition (SER)")
#     print("=" * 70)
    
#     # Check prerequisites
#     if not check_prerequisites():
#         return
    
#     # Load audio
#     print("\n🎵 Loading audio...")
#     audio, sr = load_audio(AUDIO_FILE)
#     if audio is None:
#         return
#     print(f"   Loaded: {len(audio) / sr:.1f}s @ {sr}Hz")
    
#     # Load transcription
#     transcription_data = load_transcription()
#     segments = transcription_data['segments']
    
#     # Load emotion model
#     classifier, processor, model = load_emotion_model()
#     if classifier is None:
#         return
    
#     # Detect emotions
#     emotion_results = detect_emotions(audio, sr, segments, classifier)
    
#     if not emotion_results:
#         print("\n❌ No emotions detected")
#         return
    
#     # Analyze emotion distribution
#     analyze_emotion_distribution(emotion_results)
    
#     # Display segment emotions
#     display_segment_emotions(emotion_results, transcription_data)
    
#     # Add emotion tags to transcription
#     transcription_data = add_emotion_tags_to_translation(
#         transcription_data, emotion_results
#     )
    
#     # Save results
#     output_data = save_results(transcription_data, emotion_results)
    
#     # Display usage guide
#     display_emotion_guide(emotion_results)
    
#     print(f"\n" + "=" * 70)
#     print("✅ STEP 5A Complete!")
#     print("=" * 70)
#     print(f"\n📁 Output: {OUTPUT_JSON}")
#     print(f"\n💡 Next Steps:")
#     print(f"   1. Use emotion tags in step4_translation_enhanced.py")
#     print(f"   2. Add tags like '[angry]' before translated text")
#     print(f"   3. ElevenLabs will automatically adjust voice tone")
#     print(f"\n📊 Statistics:")
#     print(f"   Total segments analyzed: {len(emotion_results)}")
#     print(f"   Total audio duration: {output_data['statistics']['total_duration']:.1f}s")
#     print(f"   Emotion distribution: {output_data['statistics']['emotion_distribution']}")


# if __name__ == "__main__":
#     main()
# step_emotion_detection.py (FIXED VERSION - Working Model)
import json
import os
import librosa
import numpy as np
import torch
from transformers import pipeline
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration
AUDIO_FILE = "work/audio_16k.wav"
TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
OUTPUT_JSON = "work/emotion_detection.json"

# Emotion Recognition Model (FIXED - Using working model)
EMOTION_MODEL = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

# Emotion to ElevenLabs Audio Tag Mapping
EMOTION_TO_TAG = {
    'angry': '[angry]',
    'disgust': '[sarcastic]',
    'fearful': '[nervous]',
    'happy': '[excited]',
    'neutral': '',  # No tag for neutral
    'sad': '[sad]',
    'surprised': '[surprised]',
    'calm': ''  # Calm = neutral
}

# Emotion Confidence Threshold
CONFIDENCE_THRESHOLD = 0.3


def check_prerequisites():
    """Check if required files exist"""
    
    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Audio file not found: {AUDIO_FILE}")
        print("   Please run step1_extract_audio.py first")
        return False
    
    if not os.path.exists(TRANSCRIPTION_FILE):
        print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
        print("   Please run step3_diarization.py first")
        return False
    
    return True


def load_transcription():
    """Load transcription from JSON"""
    with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {data['total_segments']} transcription segments")
    return data


def load_audio(audio_file):
    """Load audio file"""
    try:
        y, sr = librosa.load(audio_file, sr=16000, mono=True)
        return y, sr
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return None, None


def load_emotion_model():
    """Load emotion recognition model"""
    
    print(f"\n🧠 Loading emotion recognition model...")
    print(f"   Model: {EMOTION_MODEL}")
    print(f"   Info: Wav2Vec2 model (82% accuracy on RAVDESS)")
    
    try:
        device = 0 if torch.cuda.is_available() else -1  # -1 = CPU
        device_name = "GPU (CUDA)" if device == 0 else "CPU"
        print(f"   Device: {device_name}")
        
        # Create pipeline (simpler approach - no manual processor)
        classifier = pipeline(
            "audio-classification",
            model=EMOTION_MODEL,
            device=device
        )
        
        print(f"✅ Model loaded successfully")
        return classifier
    
    except Exception as e:
        print(f"❌ Error loading emotion model: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   pip install --upgrade transformers torch librosa")
        print(f"   pip install --upgrade datasets")
        return None


def detect_emotion_for_segment(audio, sr, classifier, start_time, end_time):
    """Detect emotion for a single segment"""
    
    try:
        # Extract segment audio
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        audio_segment = audio[start_sample:end_sample]
        
        # Ensure segment is long enough (at least 0.5 seconds)
        if len(audio_segment) < sr * 0.5:
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'scores': {},
                'status': 'too_short'
            }
        
        # Detect emotion (pass numpy array directly)
        results = classifier(audio_segment, sampling_rate=sr)
        
        # Parse results
        emotion_scores = {}
        top_emotion = None
        top_confidence = 0.0
        
        for result in results:
            emotion = result['label'].lower()
            score = result['score']
            emotion_scores[emotion] = float(score)
            
            if score > top_confidence:
                top_confidence = score
                top_emotion = emotion
        
        return {
            'emotion': top_emotion,
            'confidence': float(top_confidence),
            'scores': emotion_scores,
            'status': 'success'
        }
    
    except Exception as e:
        print(f"   ⚠️  Error: {str(e)[:50]}")
        return {
            'emotion': 'neutral',
            'confidence': 0.0,
            'scores': {},
            'status': f'error: {str(e)[:30]}'
        }


def detect_emotions(audio, sr, segments, classifier):
    """Detect emotions for all segments"""
    
    print(f"\n🎭 Detecting emotions for {len(segments)} segments...")
    print("⏳ This may take 5-15 minutes (first time downloads are slower)...\n")
    
    emotion_results = []
    
    for idx, seg in enumerate(segments, 1):
        start_time = seg['start']
        end_time = seg['end']
        duration = seg['duration']
        
        print(f"[{idx}/{len(segments)}] Segment {idx} ({duration:.2f}s)...", end=' ')
        
        # Detect emotion
        emotion_data = detect_emotion_for_segment(
            audio, sr, classifier, start_time, end_time
        )
        
        emotion_results.append({
            'segment_id': idx,
            'start': start_time,
            'end': end_time,
            'duration': duration,
            'emotion': emotion_data['emotion'],
            'confidence': emotion_data['confidence'],
            'scores': emotion_data['scores'],
            'status': emotion_data['status']
        })
        
        # Display result with emoji
        emotion = emotion_data['emotion']
        confidence = emotion_data['confidence']
        emoji = get_emotion_emoji(emotion)
        
        if confidence >= 0.7:
            status = "✅ Strong"
        elif confidence >= 0.5:
            status = "⚠️  Moderate"
        elif confidence >= 0.3:
            status = "⚠️  Weak"
        else:
            status = "❌ Unclear"
        
        print(f"{emoji} {emotion.upper()} ({confidence:.2%}) {status}")
    
    return emotion_results


def get_emotion_emoji(emotion):
    """Get emoji for emotion"""
    emoji_map = {
        'angry': '🔴',
        'disgust': '🤮',
        'fearful': '😨',
        'happy': '😊',
        'neutral': '😐',
        'sad': '😢',
        'surprised': '😲',
        'calm': '😌'
    }
    return emoji_map.get(emotion, '❓')


def analyze_emotion_distribution(emotion_results):
    """Analyze emotion distribution statistics"""
    
    print(f"\n" + "="*70)
    print("📊 EMOTION DISTRIBUTION ANALYSIS")
    print("="*70)
    
    # Count emotions
    emotion_counts = {}
    emotion_durations = {}
    emotion_confidences = {}
    
    for result in emotion_results:
        emotion = result['emotion']
        duration = result['duration']
        confidence = result['confidence']
        
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        emotion_durations[emotion] = emotion_durations.get(emotion, 0) + duration
        
        if emotion not in emotion_confidences:
            emotion_confidences[emotion] = []
        emotion_confidences[emotion].append(confidence)
    
    # Calculate averages
    emotion_avg_confidence = {
        emotion: np.mean(confidences) 
        for emotion, confidences in emotion_confidences.items()
    }
    
    # Display statistics
    print(f"\nTotal segments: {len(emotion_results)}")
    
    print(f"\n🎭 Emotion Breakdown:")
    print(f"   {'Emotion':<12} | {'Count':<6} | {'Duration':<10} | {'Avg Confidence':<15}")
    print(f"   {'-'*12}-+-{'-'*6}-+-{'-'*10}-+-{'-'*15}")
    
    for emotion in sorted(emotion_counts.keys()):
        count = emotion_counts[emotion]
        total_duration = emotion_durations[emotion]
        avg_conf = emotion_avg_confidence[emotion]
        emoji = get_emotion_emoji(emotion)
        
        print(f"   {emoji} {emotion:<10} | {count:<6} | {total_duration:>8.1f}s | {avg_conf:>13.1%}")
    
    # Timeline visualization
    print(f"\n📈 Emotion Timeline (Visualization):")
    for result in emotion_results[:10]:  # Show first 10
        emotion = result['emotion']
        confidence = result['confidence']
        emoji = get_emotion_emoji(emotion)
        bar_length = int(confidence * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"   {emoji} [{result['segment_id']:2d}] {bar} {confidence:.1%}")
    
    if len(emotion_results) > 10:
        print(f"   ... and {len(emotion_results) - 10} more segments")
    
    # Emotion stability check
    print(f"\n🎯 Emotion Consistency:")
    max_emotion = max(emotion_counts.items(), key=lambda x: x[1])
    max_percentage = (max_emotion[1] / len(emotion_results)) * 100
    print(f"   Most common: {get_emotion_emoji(max_emotion[0])} {max_emotion[0].upper()} ({max_emotion[1]} segments, {max_percentage:.1f}%)")
    
    if max_percentage > 70:
        print(f"   💡 Mostly consistent emotion (good for dubbing)")
    elif max_percentage > 50:
        print(f"   💡 Mixed emotions (multiple character states)")
    else:
        print(f"   💡 Highly varied emotions (dynamic scene)")


def add_emotion_tags_to_translation(transcription_data, emotion_results):
    """Add emotion tags to translated text"""
    
    print(f"\n🏷️  Adding emotion tags to translations...")
    
    # Create emotion map for easy lookup
    emotion_map = {result['segment_id']: result for result in emotion_results}
    
    # Add emotion tags
    for seg in transcription_data['segments']:
        segment_id = seg['id'] + 1  # segment_id is 1-indexed
        emotion_result = emotion_map.get(segment_id)
        
        if emotion_result:
            seg['detected_emotion'] = emotion_result['emotion']
            seg['emotion_confidence'] = emotion_result['confidence']
            seg['emotion_tag'] = EMOTION_TO_TAG.get(emotion_result['emotion'], '')
        else:
            seg['detected_emotion'] = 'neutral'
            seg['emotion_confidence'] = 0.0
            seg['emotion_tag'] = ''
    
    print(f"✅ Emotion tags added to all segments")
    return transcription_data


def save_results(transcription_data, emotion_results):
    """Save emotion detection results"""
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'model': EMOTION_MODEL,
        'total_segments': len(emotion_results),
        'emotions': emotion_results,
        'emotion_to_tag_mapping': EMOTION_TO_TAG,
        'statistics': {
            'total_duration': sum(r['duration'] for r in emotion_results),
            'emotion_distribution': {}
        }
    }
    
    # Calculate emotion distribution
    emotion_counts = {}
    for result in emotion_results:
        emotion = result['emotion']
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    output_data['statistics']['emotion_distribution'] = emotion_counts
    
    # Save emotion results
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Emotion detection results saved to: {OUTPUT_JSON}")
    
    return output_data


def display_emotion_guide(emotion_results):
    """Display usage guide for emotion tags in voice generation"""
    
    print(f"\n" + "="*70)
    print("🎤 EMOTION TAGS FOR VOICE GENERATION")
    print("="*70)
    
    print(f"\nHow to use with ElevenLabs Voice Generation:")
    print(f"\nInstead of:")
    print(f'   Translation: "Feel the pain"')
    print(f'   ElevenLabs will use neutral tone')
    
    print(f"\nUse emotion tags:")
    print(f'   Translation: "[angry] Feel the pain!"')
    print(f'   ElevenLabs will speak with anger')
    
    print(f"\n📋 Emotion Tag Reference:")
    print(f"   {'Emotion':<12} | {'ElevenLabs Tag':<18} | {'Example':<40}")
    print(f"   {'-'*12}-+-{'-'*18}-+-{'-'*40}")
    
    examples = {
        'angry': ('[angry]', '[angry] You will fall!'),
        'disgust': ('[sarcastic]', '[sarcastic] Oh, wonderful...'),
        'fearful': ('[nervous]', '[nervous] What is that?!'),
        'happy': ('[excited]', '[excited] I love this!'),
        'neutral': ('(none)', 'Just a normal sentence'),
        'sad': ('[sad]', '[sad] I cannot go on...'),
        'surprised': ('[surprised]', '[surprised] That\'s impossible!'),
        'calm': ('(none)', 'Everything is fine.')
    }
    
    for emotion, (tag, example) in examples.items():
        emoji = get_emotion_emoji(emotion)
        print(f"   {emoji} {emotion:<10} | {tag:<18} | {example:<40}")
    
    print(f"\n💡 Tips:")
    print(f"   1. Place tag at START of sentence")
    print(f"   2. Use ONE tag per segment")
    print(f"   3. Neutral/Calm emotion = NO tag needed")
    print(f"   4. Tag increases voice emotion intensity by ~20-30%")
    print(f"   5. Works best with confident emotions (>60% confidence)")


def display_segment_emotions(emotion_results, transcription_data):
    """Display emotions for each segment"""
    
    print(f"\n" + "="*70)
    print("📋 EMOTION MAPPING FOR ALL SEGMENTS")
    print("="*70)
    
    segments = transcription_data['segments']
    
    print(f"\n{'Seg':<4} | {'Time':<12} | {'Text':<30} | {'Emotion':<10} | {'Conf':<6} | {'Tag':<12}")
    print(f"{'-'*4}-+-{'-'*12}-+-{'-'*30}-+-{'-'*10}-+-{'-'*6}-+-{'-'*12}")
    
    for result in emotion_results[:15]:  # Show first 15
        seg_idx = result['segment_id']
        segment = segments[seg_idx - 1]
        
        text = segment['text'][:28].ljust(28)
        emotion = result['emotion']
        confidence = result['confidence']
        tag = EMOTION_TO_TAG.get(emotion, '(none)')
        emoji = get_emotion_emoji(emotion)
        time_str = f"{result['start']:.1f}-{result['end']:.1f}s"
        
        print(f" {seg_idx:<3} | {time_str:<12} | {text} | {emoji} {emotion:<8} | {confidence:>5.1%} | {tag:<12}")
    
    if len(emotion_results) > 15:
        print(f"... and {len(emotion_results) - 15} more segments")


def main():
    print("=" * 70)
    print("STEP 5A: Speech Emotion Recognition (SER)")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Load audio
    print("\n🎵 Loading audio...")
    audio, sr = load_audio(AUDIO_FILE)
    if audio is None:
        return
    print(f"   Loaded: {len(audio) / sr:.1f}s @ {sr}Hz")
    
    # Load transcription
    transcription_data = load_transcription()
    segments = transcription_data['segments']
    
    # Load emotion model
    classifier = load_emotion_model()
    if classifier is None:
        return
    
    # Detect emotions
    emotion_results = detect_emotions(audio, sr, segments, classifier)
    
    if not emotion_results:
        print("\n❌ No emotions detected")
        return
    
    # Analyze emotion distribution
    analyze_emotion_distribution(emotion_results)
    
    # Display segment emotions
    display_segment_emotions(emotion_results, transcription_data)
    
    # Add emotion tags to transcription
    transcription_data = add_emotion_tags_to_translation(
        transcription_data, emotion_results
    )
    
    # Save results
    output_data = save_results(transcription_data, emotion_results)
    
    # Display usage guide
    display_emotion_guide(emotion_results)
    
    print(f"\n" + "=" * 70)
    print("✅ STEP 5A Complete!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_JSON}")
    print(f"\n💡 Next Steps:")
    print(f"   1. Use emotion tags in step4_translation_enhanced.py")
    print(f"   2. Add tags like '[angry]' before translated text")
    print(f"   3. ElevenLabs will automatically adjust voice tone")
    print(f"\n📊 Statistics:")
    print(f"   Total segments analyzed: {len(emotion_results)}")
    print(f"   Total audio duration: {output_data['statistics']['total_duration']:.1f}s")
    print(f"   Emotion distribution: {output_data['statistics']['emotion_distribution']}")


if __name__ == "__main__":
    main()
