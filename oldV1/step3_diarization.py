# # # # # # # # step3_diarization.py
# # # # # # # import torch
# # # # # # # import json
# # # # # # # import os
# # # # # # # from pyannote.audio import Pipeline
# # # # # # # from datetime import datetime

# # # # # # # # Configuration
# # # # # # # AUDIO_FILE = "work/audio_16k.wav"
# # # # # # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # # # # # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # # # # # # You'll need a HuggingFace token for pyannote
# # # # # # # # Get it from: https://huggingface.co/settings/tokens
# # # # # # # HF_TOKEN = "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"  # Replace with your actual token

# # # # # # # def check_prerequisites():
# # # # # # #     """Check if required files exist"""
# # # # # # #     if not os.path.exists(AUDIO_FILE):
# # # # # # #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# # # # # # #         print("   Please run step1_extract_audio.py first")
# # # # # # #         return False
    
# # # # # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # # # # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # # # # # #         print("   Please run step2_transcribe.py first")
# # # # # # #         return False
    
# # # # # # #     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
# # # # # # #         print("❌ HuggingFace token not set!")
# # # # # # #         print("\n📝 To get your token:")
# # # # # # #         print("   1. Go to: https://huggingface.co/settings/tokens")
# # # # # # #         print("   2. Click 'New token'")
# # # # # # #         print("   3. Copy the token")
# # # # # # #         print("   4. Paste it in step3_diarization.py (HF_TOKEN variable)")
# # # # # # #         print("\n📝 Also accept the terms:")
# # # # # # #         print("   5. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # # # # # #         print("   6. Click 'Accept' on the user conditions")
# # # # # # #         return False
    
# # # # # # #     return True

# # # # # # # def load_transcription():
# # # # # # #     """Load transcription from JSON"""
# # # # # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # # # # #         data = json.load(f)
    
# # # # # # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # # # # # #     return data

# # # # # # # def run_diarization():
# # # # # # #     """Run speaker diarization on audio"""
    
# # # # # # #     print(f"\n🎤 Running speaker diarization...")
# # # # # # #     print("⏳ This may take 5-10 minutes...")
    
# # # # # # #     try:
# # # # # # #         # Check GPU
# # # # # # #         device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# # # # # # #         print(f"   Device: {device}")
        
# # # # # # #         # Load diarization pipeline
# # # # # # #         print("   Loading pyannote model...")
# # # # # # #         pipeline = Pipeline.from_pretrained(
# # # # # # #             "pyannote/speaker-diarization-3.1",
# # # # # # #             use_auth_token=HF_TOKEN
# # # # # # #         )
# # # # # # #         pipeline = pipeline.to(device)
        
# # # # # # #         print(f"   Processing audio: {AUDIO_FILE}")
        
# # # # # # #         # Run diarization
# # # # # # #         diarization = pipeline(AUDIO_FILE)
        
# # # # # # #         print("✅ Diarization complete!")
        
# # # # # # #         return diarization
    
# # # # # # #     except Exception as e:
# # # # # # #         print(f"❌ Diarization error: {e}")
# # # # # # #         print("\n💡 Common issues:")
# # # # # # #         print("   - Make sure you accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # # # # # #         print("   - Check your HuggingFace token is valid")
# # # # # # #         print("   - Try: pip install --upgrade pyannote.audio")
# # # # # # #         import traceback
# # # # # # #         traceback.print_exc()
# # # # # # #         return None

# # # # # # # def extract_speaker_segments(diarization):
# # # # # # #     """Extract speaker segments from diarization result"""
    
# # # # # # #     speaker_segments = []
# # # # # # #     speakers_found = set()
    
# # # # # # #     for segment, _, speaker in diarization.itertracks(yield_label=True):
# # # # # # #         speaker_segments.append({
# # # # # # #             'speaker': speaker,
# # # # # # #             'start': segment.start,
# # # # # # #             'end': segment.end,
# # # # # # #             'duration': segment.end - segment.start
# # # # # # #         })
# # # # # # #         speakers_found.add(speaker)
    
# # # # # # #     print(f"\n👥 Found {len(speakers_found)} unique speakers:")
# # # # # # #     for speaker in sorted(speakers_found):
# # # # # # #         count = sum(1 for s in speaker_segments if s['speaker'] == speaker)
# # # # # # #         total_time = sum(s['duration'] for s in speaker_segments if s['speaker'] == speaker)
# # # # # # #         print(f"   {speaker}: {count} segments, {total_time:.1f}s total")
    
# # # # # # #     return speaker_segments, speakers_found

# # # # # # # def assign_speakers_to_transcription(transcription_data, speaker_segments):
# # # # # # #     """Match speaker segments with transcription segments"""
    
# # # # # # #     print(f"\n🔗 Matching speakers with transcription...")
    
# # # # # # #     segments = transcription_data['segments']
    
# # # # # # #     for trans_seg in segments:
# # # # # # #         trans_start = trans_seg['start']
# # # # # # #         trans_mid = trans_start + (trans_seg['duration'] / 2)  # Use midpoint
        
# # # # # # #         # Find which speaker segment this transcription belongs to
# # # # # # #         assigned_speaker = None
# # # # # # #         best_overlap = 0
        
# # # # # # #         for spk_seg in speaker_segments:
# # # # # # #             # Check if transcription midpoint falls within speaker segment
# # # # # # #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# # # # # # #                 overlap = min(trans_seg['end'], spk_seg['end']) - max(trans_seg['start'], spk_seg['start'])
# # # # # # #                 if overlap > best_overlap:
# # # # # # #                     best_overlap = overlap
# # # # # # #                     assigned_speaker = spk_seg['speaker']
        
# # # # # # #         # Assign speaker (or "UNKNOWN" if no match)
# # # # # # #         trans_seg['speaker'] = assigned_speaker if assigned_speaker else "UNKNOWN"
    
# # # # # # #     # Count assignments
# # # # # # #     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
# # # # # # #     print(f"✅ Assigned speakers to {assigned}/{len(segments)} segments")
    
# # # # # # #     if assigned < len(segments):
# # # # # # #         unknown = len(segments) - assigned
# # # # # # #         print(f"⚠️  {unknown} segments without clear speaker assignment")
    
# # # # # # #     return transcription_data

# # # # # # # def save_results(data, speaker_segments):
# # # # # # #     """Save combined data to JSON"""
    
# # # # # # #     # Add speaker metadata
# # # # # # #     data['diarization'] = {
# # # # # # #         'timestamp': datetime.now().isoformat(),
# # # # # # #         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
# # # # # # #         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments))
# # # # # # #     }
    
# # # # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # # # #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# # # # # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # # # # # def display_preview(data):
# # # # # # #     """Display preview with speakers"""
    
# # # # # # #     print("\n" + "="*60)
# # # # # # #     print("📋 PREVIEW (First 5 segments with speakers)")
# # # # # # #     print("="*60)
    
# # # # # # #     for seg in data['segments'][:5]:
# # # # # # #         speaker = seg.get('speaker', 'UNKNOWN')
# # # # # # #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] Speaker: {speaker}")
# # # # # # #         print(f"  {seg['text']}")
    
# # # # # # #     if len(data['segments']) > 5:
# # # # # # #         print(f"\n... and {len(data['segments']) - 5} more segments")

# # # # # # # def main():
# # # # # # #     print("=" * 60)
# # # # # # #     print("STEP 3: Speaker Diarization")
# # # # # # #     print("=" * 60)
    
# # # # # # #     # Check prerequisites
# # # # # # #     if not check_prerequisites():
# # # # # # #         return
    
# # # # # # #     # Load transcription
# # # # # # #     transcription_data = load_transcription()
    
# # # # # # #     # Run diarization
# # # # # # #     diarization = run_diarization()
# # # # # # #     if diarization is None:
# # # # # # #         return
    
# # # # # # #     # Extract speaker segments
# # # # # # #     speaker_segments, speakers_found = extract_speaker_segments(diarization)
    
# # # # # # #     # Assign speakers to transcription
# # # # # # #     transcription_data = assign_speakers_to_transcription(
# # # # # # #         transcription_data, 
# # # # # # #         speaker_segments
# # # # # # #     )
    
# # # # # # #     # Save results
# # # # # # #     save_results(transcription_data, speaker_segments)
    
# # # # # # #     # Display preview
# # # # # # #     display_preview(transcription_data)
    
# # # # # # #     print("\n" + "=" * 60)
# # # # # # #     print("✅ Step 3 Complete!")
# # # # # # #     print("=" * 60)
# # # # # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # # # # #     print(f"👥 Total speakers: {len(speakers_found)}")
# # # # # # #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# # # # # # #     print("\nNext: Run step4_gender_age_classification.py")

# # # # # # # if __name__ == "__main__":
# # # # # # #     main()
# # # # # # step3_diarization.py (FIXED for latest pyannote.audio)
# # # # # import torch
# # # # # import json
# # # # # import os
# # # # # import librosa
# # # # # import torch
# # # # # from pyannote.audio import Pipeline
# # # # # from datetime import datetime

# # # # # # Configuration
# # # # # AUDIO_FILE = "work/audio_16k.wav"
# # # # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # # # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # # # # You'll need a HuggingFace token for pyannote
# # # # # # Get it from: https://huggingface.co/settings/tokens
# # # # # HF_TOKEN = "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"  # Replace with your actual token

# # # # # def check_prerequisites():
# # # # #     """Check if required files exist"""
# # # # #     if not os.path.exists(AUDIO_FILE):
# # # # #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# # # # #         print("   Please run step1_extract_audio.py first")
# # # # #         return False
    
# # # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # # # #         print("   Please run step2_transcribe.py first")
# # # # #         return False
    
# # # # #     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
# # # # #         print("❌ HuggingFace token not set!")
# # # # #         print("\n📝 To get your token:")
# # # # #         print("   1. Go to: https://huggingface.co/settings/tokens")
# # # # #         print("   2. Click 'New token'")
# # # # #         print("   3. Copy the token")
# # # # #         print("   4. Paste it in step3_diarization.py (HF_TOKEN variable)")
# # # # #         print("\n📝 Also accept the terms:")
# # # # #         print("   5. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # # # #         print("   6. Click 'Accept' on the user conditions")
# # # # #         return False
    
# # # # #     return True

# # # # # def load_transcription():
# # # # #     """Load transcription from JSON"""
# # # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # # #         data = json.load(f)
    
# # # # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # # # #     return data

# # # # # def load_audio_for_pyannote():
# # # # #     """Load audio as dictionary for pyannote (workaround for TorchCodec issue)"""
# # # # #     print("   Loading audio with librosa (TorchCodec workaround)...")
    
# # # # #     # Load audio
# # # # #     waveform, sample_rate = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
# # # # #     # Convert to torch tensor and add channel dimension
# # # # #     waveform_tensor = torch.from_numpy(waveform).unsqueeze(0)  # Shape: (1, samples)
    
# # # # #     # Create audio dictionary that pyannote can use
# # # # #     audio = {
# # # # #         "waveform": waveform_tensor,
# # # # #         "sample_rate": sample_rate
# # # # #     }
    
# # # # #     return audio

# # # # # def run_diarization(audio):
# # # # #     """Run speaker diarization on audio"""
    
# # # # #     print(f"\n🎤 Running speaker diarization...")
# # # # #     print("⏳ This may take 5-10 minutes...")
    
# # # # #     try:
# # # # #         # Check GPU
# # # # #         device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# # # # #         print(f"   Device: {device}")
        
# # # # #         # Load diarization pipeline (FIXED: use 'token' not 'use_auth_token')
# # # # #         print("   Loading pyannote model...")
# # # # #         pipeline = Pipeline.from_pretrained(
# # # # #             "pyannote/speaker-diarization-3.1",
# # # # #             use_auth_token=HF_TOKEN
# # # # #         )
# # # # #         pipeline = pipeline.to(device)
        
# # # # #         print(f"   Processing audio...")
        
# # # # #         # Run diarization on audio dictionary
# # # # #         diarization = pipeline(audio)
        
# # # # #         print("✅ Diarization complete!")
        
# # # # #         return diarization
    
# # # # #     except Exception as e:
# # # # #         print(f"❌ Diarization error: {e}")
# # # # #         print("\n💡 Common issues:")
# # # # #         print("   - Make sure you accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # # # #         print("   - Check your HuggingFace token is valid")
# # # # #         print("   - Try: pip install --upgrade pyannote.audio")
# # # # #         import traceback
# # # # #         traceback.print_exc()
# # # # #         return None

# # # # # def extract_speaker_segments(diarization):
# # # # #     """Extract speaker segments from diarization result"""
    
# # # # #     speaker_segments = []
# # # # #     speakers_found = set()
    
# # # # #     for segment, _, speaker in diarization.itertracks(yield_label=True):
# # # # #         speaker_segments.append({
# # # # #             'speaker': speaker,
# # # # #             'start': segment.start,
# # # # #             'end': segment.end,
# # # # #             'duration': segment.end - segment.start
# # # # #         })
# # # # #         speakers_found.add(speaker)
    
# # # # #     print(f"\n👥 Found {len(speakers_found)} unique speakers:")
# # # # #     for speaker in sorted(speakers_found):
# # # # #         count = sum(1 for s in speaker_segments if s['speaker'] == speaker)
# # # # #         total_time = sum(s['duration'] for s in speaker_segments if s['speaker'] == speaker)
# # # # #         print(f"   {speaker}: {count} segments, {total_time:.1f}s total")
    
# # # # #     return speaker_segments, speakers_found

# # # # # def assign_speakers_to_transcription(transcription_data, speaker_segments):
# # # # #     """Match speaker segments with transcription segments"""
    
# # # # #     print(f"\n🔗 Matching speakers with transcription...")
    
# # # # #     segments = transcription_data['segments']
    
# # # # #     for trans_seg in segments:
# # # # #         trans_start = trans_seg['start']
# # # # #         trans_end = trans_seg['end']
# # # # #         trans_mid = trans_start + (trans_seg['duration'] / 2)  # Use midpoint
        
# # # # #         # Find which speaker segment this transcription belongs to
# # # # #         assigned_speaker = None
# # # # #         best_overlap = 0
        
# # # # #         for spk_seg in speaker_segments:
# # # # #             # Check if transcription midpoint falls within speaker segment
# # # # #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# # # # #                 overlap = min(trans_end, spk_seg['end']) - max(trans_start, spk_seg['start'])
# # # # #                 if overlap > best_overlap:
# # # # #                     best_overlap = overlap
# # # # #                     assigned_speaker = spk_seg['speaker']
        
# # # # #         # Assign speaker (or "UNKNOWN" if no match)
# # # # #         trans_seg['speaker'] = assigned_speaker if assigned_speaker else "UNKNOWN"
    
# # # # #     # Count assignments
# # # # #     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
# # # # #     print(f"✅ Assigned speakers to {assigned}/{len(segments)} segments")
    
# # # # #     if assigned < len(segments):
# # # # #         unknown = len(segments) - assigned
# # # # #         print(f"⚠️  {unknown} segments without clear speaker assignment")
    
# # # # #     return transcription_data

# # # # # def save_results(data, speaker_segments):
# # # # #     """Save combined data to JSON"""
    
# # # # #     # Add speaker metadata
# # # # #     data['diarization'] = {
# # # # #         'timestamp': datetime.now().isoformat(),
# # # # #         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
# # # # #         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments))
# # # # #     }
    
# # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# # # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # # # def display_preview(data):
# # # # #     """Display preview with speakers"""
    
# # # # #     print("\n" + "="*60)
# # # # #     print("📋 PREVIEW (First 5 segments with speakers)")
# # # # #     print("="*60)
    
# # # # #     for seg in data['segments'][:5]:
# # # # #         speaker = seg.get('speaker', 'UNKNOWN')
# # # # #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] Speaker: {speaker}")
# # # # #         print(f"  {seg['text']}")
    
# # # # #     if len(data['segments']) > 5:
# # # # #         print(f"\n... and {len(data['segments']) - 5} more segments")

# # # # # def main():
# # # # #     print("=" * 60)
# # # # #     print("STEP 3: Speaker Diarization")
# # # # #     print("=" * 60)
    
# # # # #     # Check prerequisites
# # # # #     if not check_prerequisites():
# # # # #         return
    
# # # # #     # Load transcription
# # # # #     transcription_data = load_transcription()
    
# # # # #     # Load audio (workaround for TorchCodec issue on Windows)
# # # # #     audio = load_audio_for_pyannote()
    
# # # # #     # Run diarization
# # # # #     diarization = run_diarization(audio)
# # # # #     if diarization is None:
# # # # #         return
    
# # # # #     # Extract speaker segments
# # # # #     speaker_segments, speakers_found = extract_speaker_segments(diarization)
    
# # # # #     # Assign speakers to transcription
# # # # #     transcription_data = assign_speakers_to_transcription(
# # # # #         transcription_data, 
# # # # #         speaker_segments
# # # # #     )
    
# # # # #     # Save results
# # # # #     save_results(transcription_data, speaker_segments)
    
# # # # #     # Display preview
# # # # #     display_preview(transcription_data)
    
# # # # #     print("\n" + "=" * 60)
# # # # #     print("✅ Step 3 Complete!")
# # # # #     print("=" * 60)
# # # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # # #     print(f"👥 Total speakers: {len(speakers_found)}")
# # # # #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# # # # #     print("\nNext: Run step4_gender_age_classification.py")

# # # # # if __name__ == "__main__":
# # # # #     main()
# # # # # # step3_diarization_simple.py (No gated models needed!)
# # # # # # import json
# # # # # # import os
# # # # # # import librosa
# # # # # # import numpy as np
# # # # # # from sklearn.cluster import AgglomerativeClustering
# # # # # # from datetime import datetime

# # # # # # # Configuration
# # # # # # AUDIO_FILE = "work/audio_16k.wav"
# # # # # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # # # # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # # # # def load_transcription():
# # # # # #     """Load transcription from JSON"""
# # # # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # # # #         data = json.load(f)
    
# # # # # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # # # # #     return data

# # # # # # def extract_voice_features(audio_segment, sr=16000):
# # # # # #     """Extract voice features for speaker identification"""
    
# # # # # #     # Extract MFCC features (voice characteristics)
# # # # # #     mfcc = librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=13)
# # # # # #     mfcc_mean = np.mean(mfcc, axis=1)
    
# # # # # #     # Extract pitch (fundamental frequency)
# # # # # #     pitches, magnitudes = librosa.piptrack(y=audio_segment, sr=sr)
# # # # # #     pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
    
# # # # # #     # Extract spectral centroid (brightness of sound)
# # # # # #     spectral_centroid = librosa.feature.spectral_centroid(y=audio_segment, sr=sr)
# # # # # #     spectral_mean = np.mean(spectral_centroid)
    
# # # # # #     # Combine features
# # # # # #     features = np.concatenate([
# # # # # #         mfcc_mean,
# # # # # #         [pitch_mean],
# # # # # #         [spectral_mean]
# # # # # #     ])
    
# # # # # #     return features

# # # # # # def simple_speaker_diarization(audio, sr, segments):
# # # # # #     """Simple speaker diarization using clustering"""
    
# # # # # #     print(f"\n🎤 Analyzing speakers...")
# # # # # #     print("⏳ Extracting voice features for each segment...")
    
# # # # # #     # Extract features for each segment
# # # # # #     features_list = []
# # # # # #     valid_segments = []
    
# # # # # #     for seg in segments:
# # # # # #         start_sample = int(seg['start'] * sr)
# # # # # #         end_sample = int(seg['end'] * sr)
        
# # # # # #         # Extract audio segment
# # # # # #         audio_segment = audio[start_sample:end_sample]
        
# # # # # #         # Skip if too short
# # # # # #         if len(audio_segment) < sr * 0.3:  # Less than 0.3 seconds
# # # # # #             continue
        
# # # # # #         # Extract features
# # # # # #         features = extract_voice_features(audio_segment, sr)
# # # # # #         features_list.append(features)
# # # # # #         valid_segments.append(seg)
    
# # # # # #     if len(features_list) < 2:
# # # # # #         print("⚠️  Not enough segments for clustering, assigning all to one speaker")
# # # # # #         for seg in segments:
# # # # # #             seg['speaker'] = "SPEAKER_00"
# # # # # #         return segments
    
# # # # # #     # Convert to numpy array
# # # # # #     features_array = np.array(features_list)
    
# # # # # #     # Cluster speakers (assume 2-3 speakers max for anime)
# # # # # #     n_speakers = min(3, len(features_list))  # Max 3 speakers
    
# # # # # #     print(f"   Clustering into {n_speakers} speaker groups...")
    
# # # # # #     clustering = AgglomerativeClustering(
# # # # # #         n_clusters=n_speakers,
# # # # # #         linkage='ward'
# # # # # #     )
    
# # # # # #     speaker_labels = clustering.fit_predict(features_array)
    
# # # # # #     # Assign speaker labels
# # # # # #     for i, seg in enumerate(valid_segments):
# # # # # #         seg['speaker'] = f"SPEAKER_{speaker_labels[i]:02d}"
    
# # # # # #     # Count speakers
# # # # # #     unique_speakers = set(seg['speaker'] for seg in valid_segments)
    
# # # # # #     print(f"✅ Found {len(unique_speakers)} speakers:")
# # # # # #     for speaker in sorted(unique_speakers):
# # # # # #         count = sum(1 for s in valid_segments if s['speaker'] == speaker)
# # # # # #         print(f"   {speaker}: {count} segments")
    
# # # # # #     return segments

# # # # # # def analyze_speaker_characteristics(audio, sr, segments):
# # # # # #     """Analyze gender and age of each speaker"""
    
# # # # # #     print(f"\n🔍 Analyzing speaker characteristics...")
    
# # # # # #     speaker_profiles = {}
    
# # # # # #     for seg in segments:
# # # # # #         speaker = seg.get('speaker', 'SPEAKER_00')
        
# # # # # #         if speaker not in speaker_profiles:
# # # # # #             # Get audio for this segment
# # # # # #             start_sample = int(seg['start'] * sr)
# # # # # #             end_sample = int(seg['end'] * sr)
# # # # # #             audio_segment = audio[start_sample:end_sample]
            
# # # # # #             if len(audio_segment) < sr * 0.3:
# # # # # #                 continue
            
# # # # # #             # Extract pitch for gender estimation
# # # # # #             pitches, magnitudes = librosa.piptrack(y=audio_segment, sr=sr)
# # # # # #             valid_pitches = pitches[pitches > 0]
            
# # # # # #             if len(valid_pitches) > 0:
# # # # # #                 mean_pitch = np.mean(valid_pitches)
                
# # # # # #                 # Simple gender classification based on pitch
# # # # # #                 # Male: typically 85-180 Hz
# # # # # #                 # Female: typically 165-255 Hz
# # # # # #                 if mean_pitch < 140:
# # # # # #                     gender = "male"
# # # # # #                     age_group = "adult"
# # # # # #                 elif mean_pitch > 200:
# # # # # #                     gender = "female"
# # # # # #                     age_group = "teen/adult"
# # # # # #                 else:
# # # # # #                     gender = "ambiguous"
# # # # # #                     age_group = "adult"
                
# # # # # #                 speaker_profiles[speaker] = {
# # # # # #                     "gender": gender,
# # # # # #                     "age_group": age_group,
# # # # # #                     "mean_pitch_hz": float(mean_pitch)
# # # # # #                 }
# # # # # #             else:
# # # # # #                 speaker_profiles[speaker] = {
# # # # # #                     "gender": "unknown",
# # # # # #                     "age_group": "adult",
# # # # # #                     "mean_pitch_hz": 0.0
# # # # # #                 }
    
# # # # # #     print(f"📊 Speaker profiles:")
# # # # # #     for speaker, profile in speaker_profiles.items():
# # # # # #         print(f"   {speaker}: {profile['gender']}, {profile['age_group']}, pitch={profile['mean_pitch_hz']:.1f}Hz")
    
# # # # # #     return speaker_profiles

# # # # # # def save_results(data, speaker_profiles):
# # # # # #     """Save combined data to JSON"""
    
# # # # # #     # Add speaker metadata
# # # # # #     data['diarization'] = {
# # # # # #         'timestamp': datetime.now().isoformat(),
# # # # # #         'method': 'simple_clustering',
# # # # # #         'total_speakers': len(speaker_profiles),
# # # # # #         'speaker_profiles': speaker_profiles
# # # # # #     }
    
# # # # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # # # #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# # # # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # # # # def display_preview(data):
# # # # # #     """Display preview with speakers"""
    
# # # # # #     print("\n" + "="*60)
# # # # # #     print("📋 PREVIEW (All segments with speakers)")
# # # # # #     print("="*60)
    
# # # # # #     for seg in data['segments']:
# # # # # #         speaker = seg.get('speaker', 'UNKNOWN')
# # # # # #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] {speaker}")
# # # # # #         print(f"  {seg['text']}")

# # # # # # def main():
# # # # # #     print("=" * 60)
# # # # # #     print("STEP 3: Simple Speaker Diarization")
# # # # # #     print("=" * 60)
    
# # # # # #     # Check prerequisites
# # # # # #     if not os.path.exists(AUDIO_FILE):
# # # # # #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# # # # # #         return
    
# # # # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # # # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # # # # #         return
    
# # # # # #     # Load transcription
# # # # # #     transcription_data = load_transcription()
    
# # # # # #     # Load audio
# # # # # #     print("🎵 Loading audio...")
# # # # # #     audio, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
# # # # # #     # Run simple diarization
# # # # # #     segments = simple_speaker_diarization(
# # # # # #         audio, 
# # # # # #         sr, 
# # # # # #         transcription_data['segments']
# # # # # #     )
    
# # # # # #     # Analyze speaker characteristics
# # # # # #     speaker_profiles = analyze_speaker_characteristics(
# # # # # #         audio, 
# # # # # #         sr, 
# # # # # #         segments
# # # # # #     )
    
# # # # # #     # Save results
# # # # # #     save_results(transcription_data, speaker_profiles)
    
# # # # # #     # Display preview
# # # # # #     display_preview(transcription_data)
    
# # # # # #     print("\n" + "=" * 60)
# # # # # #     print("✅ Step 3 Complete!")
# # # # # #     print("=" * 60)
# # # # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # # # #     print(f"👥 Total speakers: {len(speaker_profiles)}")
# # # # # #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# # # # # #     print("\nNext: Continue with translation (Step 4)")

# # # # # # if __name__ == "__main__":
# # # # # #     main()
# # # # step3_diarization.py (Enhanced with Wav2Vec2 Age/Gender Model)
# # # import torch
# # # import json
# # # import os
# # # import librosa
# # # import numpy as np
# # # from pyannote.audio import Pipeline
# # # from transformers import Wav2Vec2Processor
# # # from transformers.models.wav2vec2.modeling_wav2vec2 import (
# # #     Wav2Vec2Model,
# # #     Wav2Vec2PreTrainedModel,
# # # )
# # # import torch.nn as nn
# # # from datetime import datetime

# # # # Configuration
# # # AUDIO_FILE = "separated/htdemucs/audio_16k/vocals.wav"
# # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # # HuggingFace token
# # # HF_TOKEN = "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"

# # # # Age/Gender model
# # # AGE_GENDER_MODEL = "audeering/wav2vec2-large-robust-24-ft-age-gender"


# # # # ============================================================
# # # # Age/Gender Model Classes (from HuggingFace)
# # # # ============================================================

# # # class ModelHead(nn.Module):
# # #     """Classification head."""
# # #     def __init__(self, config, num_labels):
# # #         super().__init__()
# # #         self.dense = nn.Linear(config.hidden_size, config.hidden_size)
# # #         self.dropout = nn.Dropout(config.final_dropout)
# # #         self.out_proj = nn.Linear(config.hidden_size, num_labels)

# # #     def forward(self, features, **kwargs):
# # #         x = features
# # #         x = self.dropout(x)
# # #         x = self.dense(x)
# # #         x = torch.tanh(x)
# # #         x = self.dropout(x)
# # #         x = self.out_proj(x)
# # #         return x


# # # class AgeGenderModel(Wav2Vec2PreTrainedModel):
# # #     """Speech age/gender classifier."""
# # #     def __init__(self, config):
# # #         super().__init__(config)
# # #         self.config = config
# # #         self.wav2vec2 = Wav2Vec2Model(config)
# # #         self.age = ModelHead(config, 1)
# # #         self.gender = ModelHead(config, 3)
# # #         self.init_weights()

# # #     def forward(self, input_values):
# # #         outputs = self.wav2vec2(input_values)
# # #         hidden_states = outputs[0]
# # #         hidden_states = torch.mean(hidden_states, dim=1)
# # #         logits_age = self.age(hidden_states)
# # #         logits_gender = torch.softmax(self.gender(hidden_states), dim=1)
# # #         return hidden_states, logits_age, logits_gender


# # # # ============================================================
# # # # Main Functions
# # # # ============================================================

# # # def check_prerequisites():
# # #     """Check if required files exist"""
# # #     if not os.path.exists(AUDIO_FILE):
# # #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# # #         print("   Please run step1_extract_audio.py first")
# # #         return False
    
# # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # #         print("   Please run step2_transcribe.py first")
# # #         return False
    
# # #     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
# # #         print("❌ HuggingFace token not set!")
# # #         print("\n📝 To get your token:")
# # #         print("   1. Go to: https://huggingface.co/settings/tokens")
# # #         print("   2. Click 'New token'")
# # #         print("   3. Copy the token")
# # #         print("   4. Paste it in step3_diarization.py (HF_TOKEN variable)")
# # #         print("\n📝 Also accept the terms:")
# # #         print("   5. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # #         print("   6. Click 'Accept' on the user conditions")
# # #         return False
    
# # #     return True


# # # def load_transcription():
# # #     """Load transcription from JSON"""
# # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # #         data = json.load(f)
    
# # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # #     return data


# # # def load_audio_for_pyannote():
# # #     """Load audio as dictionary for pyannote"""
# # #     print("   Loading audio with librosa (TorchCodec workaround)...")
    
# # #     # Load audio
# # #     waveform, sample_rate = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
# # #     # Convert to torch tensor and add channel dimension
# # #     waveform_tensor = torch.from_numpy(waveform).unsqueeze(0)  # Shape: (1, samples)
    
# # #     # Create audio dictionary that pyannote can use
# # #     audio = {
# # #         "waveform": waveform_tensor,
# # #         "sample_rate": sample_rate
# # #     }
    
# # #     return audio, waveform, sample_rate


# # # def run_diarization(audio):
# # #     """Run speaker diarization on audio"""
    
# # #     print(f"\n🎤 Running speaker diarization...")
# # #     print("⏳ This may take 5-10 minutes...")
    
# # #     try:
# # #         # Check GPU
# # #         device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# # #         print(f"   Device: {device}")
        
# # #         # Load diarization pipeline
# # #         print("   Loading pyannote model...")
# # #         # pipeline = Pipeline.from_pretrained(
# # #         #     "pyannote/speaker-diarization-3.1",
# # #         #     use_auth_token=HF_TOKEN
# # #         # )
# # #         # pipeline = pipeline.to(device)
# # #         # In pipeline config (before running)
# # #         pipeline = Pipeline.from_pretrained(
# # #             "pyannote/speaker-diarization-3.1",
# # #             token=HF_TOKEN
# # #         )
# # #         pipeline.segmentation_batch_size = 32  # More sensitive
# # #         pipeline.embedding_batch_size = 32
# # #         pipeline = pipeline.to(device)
# # #         print(f"   Processing audio...")
        
# # #         # Run diarization on audio dictionary
# # #         # diarization = pipeline(audio)
# # #         diarization = pipeline(AUDIO_FILE)

# # # # FIXED (force more speakers)
# # #         diarization = pipeline(
# # #             AUDIO_FILE,
# # #             min_speakers=3,        # At least 3 speakers
# # #             max_speakers=20, )      # Up to 20 (for anime cast)
        
# # #         print("✅ Diarization complete!")
        
# # #         return diarization
    
# # #     except Exception as e:
# # #         print(f"❌ Diarization error: {e}")
# # #         print("\n💡 Common issues:")
# # #         print("   - Make sure you accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # #         print("   - Check your HuggingFace token is valid")
# # #         print("   - Try: pip install --upgrade pyannote.audio")
# # #         import traceback
# # #         traceback.print_exc()
# # #         return None


# # # def extract_speaker_segments(diarization):
# # #     """Extract speaker segments from diarization result"""
    
# # #     speaker_segments = []
# # #     speakers_found = set()
# # #     annotation = diarization.speaker_diarization

# # #     for segment, _, speaker in annotation.itertracks(yield_label=True):
# # #     # for segment, _, speaker in diarization.itertracks(yield_label=True):
# # #         speaker_segments.append({
# # #             'speaker': speaker,
# # #             'start': segment.start,
# # #             'end': segment.end,
# # #             'duration': segment.end - segment.start
# # #         })
# # #         speakers_found.add(speaker)
    
# # #     print(f"\n👥 Found {len(speakers_found)} unique speakers:")
# # #     for speaker in sorted(speakers_found):
# # #         count = sum(1 for s in speaker_segments if s['speaker'] == speaker)
# # #         total_time = sum(s['duration'] for s in speaker_segments if s['speaker'] == speaker)
# # #         print(f"   {speaker}: {count} segments, {total_time:.1f}s total")
    
# # #     return speaker_segments, speakers_found


# # # def load_age_gender_model():
# # #     """Load Wav2Vec2 age/gender model"""
    
# # #     print(f"\n🧠 Loading age/gender detection model...")
    
# # #     try:
# # #         device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
# # #         processor = Wav2Vec2Processor.from_pretrained(AGE_GENDER_MODEL)
# # #         model = AgeGenderModel.from_pretrained(AGE_GENDER_MODEL)
# # #         model = model.to(device)
# # #         model.eval()
        
# # #         print(f"✅ Age/gender model loaded on {device}")
        
# # #         return processor, model, device
    
# # #     except Exception as e:
# # #         print(f"⚠️  Could not load age/gender model: {e}")
# # #         print("   Will use fallback method (pitch-based)")
# # #         return None, None, None


# # # def analyze_speaker_age_gender(audio_waveform, sample_rate, speaker_segments, processor, model, device):
# # #     """Analyze age and gender for each speaker using Wav2Vec2 model"""
    
# # #     print(f"\n🔍 Analyzing speaker age and gender...")
    
# # #     speaker_profiles = {}
    
# # #     for speaker in set(s['speaker'] for s in speaker_segments):
# # #         # Get all segments for this speaker
# # #         speaker_segs = [s for s in speaker_segments if s['speaker'] == speaker]
        
# # #         # Use the longest segment for analysis (more reliable)
# # #         longest_seg = max(speaker_segs, key=lambda x: x['duration'])
        
# # #         start_sample = int(longest_seg['start'] * sample_rate)
# # #         end_sample = int(longest_seg['end'] * sample_rate)
        
# # #         audio_segment = audio_waveform[start_sample:end_sample]
        
# # #         # Skip if too short
# # #         if len(audio_segment) < sample_rate * 0.5:
# # #             print(f"   ⚠️  {speaker}: Segment too short, skipping")
# # #             speaker_profiles[speaker] = {
# # #                 'gender': 'unknown',
# # #                 'age_group': 'adult',
# # #                 'age_estimate': 30.0,
# # #                 'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
# # #             }
# # #             continue
        
# # #         try:
# # #             if processor is not None and model is not None:
# # #                 # Use Wav2Vec2 model
# # #                 result = predict_age_gender_wav2vec(
# # #                     audio_segment, 
# # #                     sample_rate, 
# # #                     processor, 
# # #                     model, 
# # #                     device
# # #                 )
# # #             else:
# # #                 # Fallback to pitch-based method
# # #                 result = predict_age_gender_fallback(audio_segment, sample_rate)
            
# # #             speaker_profiles[speaker] = result
            
# # #             print(f"   {speaker}: {result['gender']}, age ~{result['age_estimate']:.0f} ({result['age_group']})")
# # #             print(f"      Gender probs - Female: {result['gender_probabilities']['female']:.2f}, "
# # #                   f"Male: {result['gender_probabilities']['male']:.2f}, "
# # #                   f"Child: {result['gender_probabilities']['child']:.2f}")
        
# # #         except Exception as e:
# # #             print(f"   ⚠️  {speaker}: Error analyzing - {e}")
# # #             speaker_profiles[speaker] = {
# # #                 'gender': 'unknown',
# # #                 'age_group': 'adult',
# # #                 'age_estimate': 30.0,
# # #                 'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
# # #             }
    
# # #     return speaker_profiles


# # # def predict_age_gender_wav2vec(audio, sample_rate, processor, model, device):
# # #     """Predict age/gender using Wav2Vec2 model"""
    
# # #     # Process audio
# # #     inputs = processor(audio, sampling_rate=sample_rate, return_tensors="pt", padding=True)
# # #     input_values = inputs.input_values[0].reshape(1, -1)
# # #     input_values = input_values.to(device)
    
# # #     # Run model
# # #     with torch.no_grad():
# # #         hidden_states, logits_age, logits_gender = model(input_values)
    
# # #     # Extract predictions
# # #     age_prediction = logits_age.detach().cpu().numpy()[0][0]
# # #     gender_probs = logits_gender.detach().cpu().numpy()[0]
    
# # #     # Convert age (0-1 range to 0-100 years)
# # #     age_estimate = age_prediction * 100
    
# # #     # Gender probabilities: [female, male, child]
# # #     gender_dict = {
# # #         'female': float(gender_probs[0]),
# # #         'male': float(gender_probs[1]),
# # #         'child': float(gender_probs[2])
# # #     }
    
# # #     # Determine gender (highest probability)
# # #     if gender_dict['child'] > 0.5:
# # #         gender = 'child'
# # #         age_group = 'child'
# # #     elif gender_dict['female'] > gender_dict['male']:
# # #         gender = 'female'
# # #         age_group = determine_age_group(age_estimate)
# # #     else:
# # #         gender = 'male'
# # #         age_group = determine_age_group(age_estimate)
    
# # #     return {
# # #         'gender': gender,
# # #         'age_group': age_group,
# # #         'age_estimate': float(age_estimate),
# # #         'gender_probabilities': gender_dict
# # #     }


# # # def predict_age_gender_fallback(audio, sample_rate):
# # #     """Fallback: Simple pitch-based gender detection"""
    
# # #     import librosa
    
# # #     # Extract pitch
# # #     pitches, magnitudes = librosa.piptrack(y=audio, sr=sample_rate)
# # #     valid_pitches = pitches[pitches > 0]
    
# # #     if len(valid_pitches) > 0:
# # #         mean_pitch = np.mean(valid_pitches)
        
# # #         # Simple gender classification based on pitch
# # #         if mean_pitch < 140:
# # #             gender = "male"
# # #             age_estimate = 35.0
# # #         elif mean_pitch > 200:
# # #             gender = "female"
# # #             age_estimate = 30.0
# # #         else:
# # #             gender = "ambiguous"
# # #             age_estimate = 32.0
        
# # #         age_group = determine_age_group(age_estimate)
        
# # #         return {
# # #             'gender': gender,
# # #             'age_group': age_group,
# # #             'age_estimate': age_estimate,
# # #             'gender_probabilities': {
# # #                 'female': 0.5 if gender == 'female' else 0.3,
# # #                 'male': 0.5 if gender == 'male' else 0.3,
# # #                 'child': 0.2
# # #             }
# # #         }
# # #     else:
# # #         return {
# # #             'gender': 'unknown',
# # #             'age_group': 'adult',
# # #             'age_estimate': 30.0,
# # #             'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
# # #         }


# # # def determine_age_group(age):
# # #     """Determine age group from age estimate"""
# # #     if age < 13:
# # #         return 'child'
# # #     elif age < 20:
# # #         return 'teen'
# # #     elif age < 40:
# # #         return 'young_adult'
# # #     elif age < 60:
# # #         return 'adult'
# # #     else:
# # #         return 'senior'


# # # def assign_speakers_to_transcription(transcription_data, speaker_segments):
# # #     """Match speaker segments with transcription segments"""
    
# # #     print(f"\n🔗 Matching speakers with transcription...")
    
# # #     segments = transcription_data['segments']
    
# # #     for trans_seg in segments:
# # #         trans_start = trans_seg['start']
# # #         trans_end = trans_seg['end']
# # #         trans_mid = trans_start + (trans_seg['duration'] / 2)
        
# # #         # Find which speaker segment this transcription belongs to
# # #         assigned_speaker = None
# # #         best_overlap = 0.3
        
# # #         for spk_seg in speaker_segments:
# # #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# # #                 overlap = min(trans_end, spk_seg['end']) - max(trans_start, spk_seg['start'])
# # #                 if overlap > best_overlap:
# # #                     best_overlap = overlap
# # #                     assigned_speaker = spk_seg['speaker']
        
# # #         trans_seg['speaker'] = assigned_speaker if assigned_speaker else "UNKNOWN"
    
# # #     # Count assignments
# # #     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
# # #     print(f"✅ Assigned speakers to {assigned}/{len(segments)} segments")
    
# # #     if assigned < len(segments):
# # #         unknown = len(segments) - assigned
# # #         print(f"⚠️  {unknown} segments without clear speaker assignment")
    
# # #     return transcription_data


# # # def save_results(data, speaker_segments, speaker_profiles):
# # #     """Save combined data to JSON"""
    
# # #     data['diarization'] = {
# # #         'timestamp': datetime.now().isoformat(),
# # #         'method': 'pyannote + wav2vec2',
# # #         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
# # #         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments)),
# # #         'speaker_profiles': speaker_profiles
# # #     }
    
# # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")


# # # def display_preview(data):
# # #     """Display preview with speakers"""
    
# # #     print("\n" + "="*60)
# # #     print("📋 PREVIEW (First 5 segments with speakers)")
# # #     print("="*60)
    
# # #     for seg in data['segments'][:5]:
# # #         speaker = seg.get('speaker', 'UNKNOWN')
        
# # #         # Get speaker profile if available
# # #         profiles = data.get('diarization', {}).get('speaker_profiles', {})
# # #         profile = profiles.get(speaker, {})
        
# # #         gender = profile.get('gender', 'unknown')
# # #         age = profile.get('age_estimate', 0)
        
# # #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] {speaker} ({gender}, ~{age:.0f}yo)")
# # #         print(f"  {seg['text']}")
    
# # #     if len(data['segments']) > 5:
# # #         print(f"\n... and {len(data['segments']) - 5} more segments")


# # # def main():
# # #     print("=" * 60)
# # #     print("STEP 3: Speaker Diarization + Age/Gender Detection")
# # #     print("=" * 60)
    
# # #     # Check prerequisites
# # #     if not check_prerequisites():
# # #         return
    
# # #     # Load transcription
# # #     transcription_data = load_transcription()
    
# # #     # Load audio
# # #     audio_dict, audio_waveform, sample_rate = load_audio_for_pyannote()
    
# # #     # Run diarization
# # #     diarization = run_diarization(audio_dict)
# # #     if diarization is None:
# # #         return
    
# # #     # Extract speaker segments
# # #     speaker_segments, speakers_found = extract_speaker_segments(diarization)
    
# # #     # Load age/gender model
# # #     processor, model, device = load_age_gender_model()
    
# # #     # Analyze age/gender for each speaker
# # #     speaker_profiles = analyze_speaker_age_gender(
# # #         audio_waveform,
# # #         sample_rate,
# # #         speaker_segments,
# # #         processor,
# # #         model,
# # #         device
# # #     )
    
# # #     # Assign speakers to transcription
# # #     transcription_data = assign_speakers_to_transcription(
# # #         transcription_data,
# # #         speaker_segments
# # #     )
    
# # #     # Save results
# # #     save_results(transcription_data, speaker_segments, speaker_profiles)
    
# # #     # Display preview
# # #     display_preview(transcription_data)
    
# # #     print("\n" + "=" * 60)
# # #     print("✅ Step 3 Complete!")
# # #     print("=" * 60)
# # #     print(f"📁 Output: {OUTPUT_JSON}")
# # #     print(f"👥 Total speakers: {len(speakers_found)}")
# # #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# # #     print("\nNext: Run step4_translation_free.py")


# # # if __name__ == "__main__":
# # #     main()
# # # # step3_diarization.py - FULLY UPDATED WITH SPEAKER AUDIO EXTRACTION
# # # # 🎯 Perfect for OpenVoice voice cloning (2-3min reference clips per speaker)
# # # # Date: Feb 03, 2026

# # # # import torch
# # # # import json
# # # # import os
# # # # import librosa
# # # # import numpy as np
# # # # import soundfile as sf  # pip install soundfile
# # # # from pyannote.audio import Pipeline
# # # # from transformers import Wav2Vec2Processor
# # # # from transformers.models.wav2vec2.modeling_wav2vec2 import (
# # # #     Wav2Vec2Model,
# # # #     Wav2Vec2PreTrainedModel,
# # # # )
# # # # import torch.nn as nn
# # # # from datetime import datetime
# # # # import warnings
# # # # warnings.filterwarnings("ignore")

# # # # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # # # CONFIGURATION
# # # # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # # AUDIO_FILE = "work/audio_16k.wav"
# # # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # # OUTPUT_JSON = "work/transcription_with_speakers.json"
# # # # SPEAKER_AUDIO_DIR = "work/speaker_segments"  # 🆕 Individual speaker clips for OpenVoice

# # # # HF_TOKEN = "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"
# # # # AGE_GENDER_MODEL = "audeering/wav2vec2-large-robust-24-ft-age-gender"

# # # # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # # # AGE/GENDER MODEL CLASSES (UNCHANGED)
# # # # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # # class ModelHead(nn.Module):
# # # #     """Classification head."""
# # # #     def __init__(self, config, num_labels):
# # # #         super().__init__()
# # # #         self.dense = nn.Linear(config.hidden_size, config.hidden_size)
# # # #         self.dropout = nn.Dropout(config.final_dropout)
# # # #         self.out_proj = nn.Linear(config.hidden_size, num_labels)

# # # #     def forward(self, features, **kwargs):
# # # #         x = features
# # # #         x = self.dropout(x)
# # # #         x = self.dense(x)
# # # #         x = torch.tanh(x)
# # # #         x = self.dropout(x)
# # # #         x = self.out_proj(x)
# # # #         return x

# # # # class AgeGenderModel(Wav2Vec2PreTrainedModel):
# # # #     """Speech age/gender classifier."""
# # # #     def __init__(self, config):
# # # #         super().__init__(config)
# # # #         self.config = config
# # # #         self.wav2vec2 = Wav2Vec2Model(config)
# # # #         self.age = ModelHead(config, 1)
# # # #         self.gender = ModelHead(config, 3)
# # # #         self.init_weights()

# # # #     def forward(self, input_values):
# # # #         outputs = self.wav2vec2(input_values)
# # # #         hidden_states = outputs[0]
# # # #         hidden_states = torch.mean(hidden_states, dim=1)
# # # #         logits_age = self.age(hidden_states)
# # # #         logits_gender = torch.softmax(self.gender(hidden_states), dim=1)
# # # #         return hidden_states, logits_age, logits_gender

# # # # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # # # MAIN FUNCTIONS
# # # # # ═══════════════════════════════════════════════════════════════════════════════════════
# # # # def check_prerequisites():
# # # #     """Check prerequisites and create directories"""
# # # #     if not os.path.exists(AUDIO_FILE):
# # # #         print(f"❌ {AUDIO_FILE} not found! Run step1_extract_audio.py first")
# # # #         return False
    
# # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # #         print(f"❌ {TRANSCRIPTION_FILE} not found! Run step2_transcribe.py first")
# # # #         return False
    
# # # #     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
# # # #         print("❌ Set HF_TOKEN in line 25!")
# # # #         return False
    
# # # #     # 🆕 Create speaker segments directory
# # # #     os.makedirs(SPEAKER_AUDIO_DIR, exist_ok=True)
# # # #     print(f"✅ Created: {SPEAKER_AUDIO_DIR}/")
    
# # # #     return True

# # # # def load_transcription():
# # # #     """Load transcription JSON"""
# # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # #         data = json.load(f)
# # # #     print(f"📄 Loaded {data['total_segments']} segments")
# # # #     return data

# # # # def load_audio():
# # # #     """Load audio for processing"""
# # # #     print("🔊 Loading audio...")
# # # #     waveform, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)
# # # #     print(f"   Duration: {len(waveform)/sr:.1f}s, Sample rate: {sr}Hz")
# # # #     return {
# # # #         "waveform": torch.from_numpy(waveform).unsqueeze(0),
# # # #         "sample_rate": sr
# # # #     }, waveform, sr

# # # # # 🆕 NEW FUNCTION: EXTRACT SPEAKER AUDIO SEGMENTS
# # # # def extract_speaker_audio_segments(diarization, audio_waveform, sample_rate):
# # # #     """🆕 Extract & save audio segments PER SPEAKER for OpenVoice cloning"""
# # # #     print(f"\n💾 Extracting speaker audio segments...")
# # # #     print(f"📁 Saving to: {SPEAKER_AUDIO_DIR}/")
    
# # # #     speaker_segments = []
# # # #     speakers_found = set()
# # # #     speaker_audio = {}  # speaker → list of audio segments
    
# # # #     # Extract all speaker segments
# # # #     for segment, _, speaker in diarization.itertracks(yield_label=True):
# # # #         speakers_found.add(speaker)
# # # #         speaker_segments.append({
# # # #             'speaker': speaker,
# # # #             'start': segment.start,
# # # #             'end': segment.end,
# # # #             'duration': segment.end - segment.start
# # # #         })
        
# # # #         # Extract audio segment (skip very short ones)
# # # #         if segment.duration > 0.3:
# # # #             start_sample = int(segment.start * sample_rate)
# # # #             end_sample = int(segment.end * sample_rate)
# # # #             audio_seg = audio_waveform[start_sample:end_sample]
            
# # # #             if speaker not in speaker_audio:
# # # #                 speaker_audio[speaker] = []
# # # #             speaker_audio[speaker].append({
# # # #                 'audio': audio_seg,
# # # #                 'start': segment.start,
# # # #                 'end': segment.end,
# # # #                 'duration': segment.duration
# # # #             })
    
# # # #     # 🆕 SAVE INDIVIDUAL SEGMENTS + COMBINED REFERENCE CLIPS
# # # #     reference_clips = {}
# # # #     for speaker, segments in speaker_audio.items():
# # # #         total_duration = sum(s['duration'] for s in segments)
# # # #         print(f"\n👤 {speaker}: {len(segments)} segments ({total_duration:.1f}s total)")
        
# # # #         # Save individual segments
# # # #         for i, seg in enumerate(segments):
# # # #             filename = f"{speaker}_seg_{i+1:03d}_{seg['start']:.1f}s.wav"
# # # #             filepath = os.path.join(SPEAKER_AUDIO_DIR, filename)
# # # #             sf.write(filepath, seg['audio'], sample_rate)
# # # #             print(f"   📄 {filename}")
        
# # # #         # 🆕 CREATE REFERENCE CLIP (combine all segments for OpenVoice)
# # # #         if total_duration > 10:  # Need at least 10s for good cloning
# # # #             combined_audio = np.concatenate([s['audio'] for s in segments])
# # # #             ref_filename = f"{speaker}_REFERENCE_{total_duration:.0f}s.wav"
# # # #             ref_path = os.path.join(SPEAKER_AUDIO_DIR, ref_filename)
# # # #             sf.write(ref_path, combined_audio, sample_rate)
            
# # # #             reference_clips[speaker] = {
# # # #                 'reference_file': ref_path,
# # # #                 'total_duration': float(total_duration),
# # # #                 'segment_count': len(segments),
# # # #                 'quality': 'excellent' if total_duration > 120 else 'good' if total_duration > 30 else 'short'
# # # #             }
# # # #             print(f"   🎯 REFERENCE: {ref_filename} ← OpenVoice Ready!")
# # # #         else:
# # # #             print(f"   ⚠️  {speaker}: Too short for cloning ({total_duration:.1f}s)")
    
# # # #     print(f"\n🎉 {len(reference_clips)} reference clips ready for OpenVoice!")
# # # #     return speaker_segments, speakers_found, reference_clips

# # # # def run_diarization(audio):
# # # #     """Run pyannote speaker diarization"""
# # # #     print("\n🎤 Running speaker diarization...")
# # # #     print("⏳ ~5-10 minutes...")
    
# # # #     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# # # #     print(f"   Device: {device}")
    
# # # #     pipeline = Pipeline.from_pretrained(
# # # #         "pyannote/speaker-diarization-3.1",
# # # #         use_auth_token=HF_TOKEN
# # # #     )
# # # #     pipeline = pipeline.to(device)
    
# # # #     diarization = pipeline(audio)
# # # #     print("✅ Diarization complete!")
# # # #     return diarization

# # # # def load_age_gender_model():
# # # #     """Load age/gender detection model"""
# # # #     print("\n🧠 Loading age/gender model...")
# # # #     try:
# # # #         device = 'cuda' if torch.cuda.is_available() else 'cpu'
# # # #         processor = Wav2Vec2Processor.from_pretrained(AGE_GENDER_MODEL)
# # # #         model = AgeGenderModel.from_pretrained(AGE_GENDER_MODEL)
# # # #         model = model.to(device)
# # # #         model.eval()
# # # #         print(f"✅ Age/gender model on {device}")
# # # #         return processor, model, device
# # # #     except Exception as e:
# # # #         print(f"⚠️  Age/gender model failed: {e}")
# # # #         print("   Using pitch-based fallback")
# # # #         return None, None, None

# # # # def analyze_speaker_age_gender(audio_waveform, sample_rate, speaker_segments, processor, model, device):
# # # #     """Analyze age/gender for each speaker (UNCHANGED)"""
# # # #     print("\n🔍 Analyzing speaker age/gender...")
# # # #     speaker_profiles = {}
    
# # # #     for speaker in set(s['speaker'] for s in speaker_segments):
# # # #         speaker_segs = [s for s in speaker_segments if s['speaker'] == speaker]
# # # #         longest_seg = max(speaker_segs, key=lambda x: x['duration'])
        
# # # #         start_sample = int(longest_seg['start'] * sample_rate)
# # # #         end_sample = int(longest_seg['end'] * sample_rate)
# # # #         audio_segment = audio_waveform[start_sample:end_sample]
        
# # # #         if len(audio_segment) < sample_rate * 0.5:
# # # #             speaker_profiles[speaker] = {
# # # #                 'gender': 'unknown', 'age_group': 'adult',
# # # #                 'age_estimate': 30.0,
# # # #                 'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
# # # #             }
# # # #             continue
        
# # # #         try:
# # # #             if processor and model:
# # # #                 result = predict_age_gender_wav2vec(audio_segment, sample_rate, processor, model, device)
# # # #             else:
# # # #                 result = predict_age_gender_fallback(audio_segment, sample_rate)
            
# # # #             speaker_profiles[speaker] = result
# # # #             print(f"   {speaker}: {result['gender']}, ~{result['age_estimate']:.0f}yo ({result['age_group']})")
# # # #         except:
# # # #             speaker_profiles[speaker] = {
# # # #                 'gender': 'unknown', 'age_group': 'adult',
# # # #                 'age_estimate': 30.0,
# # # #                 'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
# # # #             }
    
# # # #     return speaker_profiles

# # # # # Helper functions (unchanged - keeping your original logic)
# # # # def predict_age_gender_wav2vec(audio, sample_rate, processor, model, device):
# # # #     inputs = processor(audio, sampling_rate=sample_rate, return_tensors="pt", padding=True)
# # # #     input_values = inputs.input_values.to(device)
    
# # # #     with torch.no_grad():
# # # #         _, logits_age, logits_gender = model(input_values)
    
# # # #     age = logits_age.detach().cpu().numpy()[0][0] * 100
# # # #     gender_probs = logits_gender.detach().cpu().numpy()[0]
    
# # # #     gender_dict = {'female': float(gender_probs[0]), 'male': float(gender_probs[1]), 'child': float(gender_probs[2])}
    
# # # #     if gender_dict['child'] > 0.5:
# # # #         gender, age_group = 'child', 'child'
# # # #     elif gender_dict['female'] > gender_dict['male']:
# # # #         gender, age_group = 'female', determine_age_group(age)
# # # #     else:
# # # #         gender, age_group = 'male', determine_age_group(age)
    
# # # #     return {'gender': gender, 'age_group': age_group, 'age_estimate': float(age), 'gender_probabilities': gender_dict}

# # # # def predict_age_gender_fallback(audio, sample_rate):
# # # #     pitches, _ = librosa.piptrack(y=audio, sr=sample_rate)
# # # #     valid_pitches = pitches[pitches > 0]
    
# # # #     if len(valid_pitches) > 0:
# # # #         mean_pitch = np.mean(valid_pitches)
# # # #         gender = "male" if mean_pitch < 140 else "female" if mean_pitch > 200 else "ambiguous"
# # # #         age = 35.0 if gender == "male" else 30.0
# # # #     else:
# # # #         gender, age = 'unknown', 30.0
    
# # # #     return {
# # # #         'gender': gender, 'age_group': determine_age_group(age),
# # # #         'age_estimate': age,
# # # #         'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
# # # #     }

# # # # def determine_age_group(age):
# # # #     if age < 13: return 'child'
# # # #     elif age < 20: return 'teen'
# # # #     elif age < 40: return 'young_adult'
# # # #     elif age < 60: return 'adult'
# # # #     return 'senior'

# # # # def assign_speakers_to_transcription(transcription_data, speaker_segments):
# # # #     """Match speakers to transcription segments"""
# # # #     print("\n🔗 Matching speakers to transcription...")
    
# # # #     segments = transcription_data['segments']
# # # #     for trans_seg in segments:
# # # #         trans_mid = trans_seg['start'] + (trans_seg['duration'] / 2)
        
# # # #         best_speaker = None
# # # #         best_overlap = 0
        
# # # #         for spk_seg in speaker_segments:
# # # #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# # # #                 overlap = min(trans_seg['end'], spk_seg['end']) - max(trans_seg['start'], spk_seg['start'])
# # # #                 if overlap > best_overlap:
# # # #                     best_overlap = overlap
# # # #                     best_speaker = spk_seg['speaker']
        
# # # #         trans_seg['speaker'] = best_speaker or "UNKNOWN"
    
# # # #     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
# # # #     print(f"✅ {assigned}/{len(segments)} segments assigned")
# # # #     return transcription_data

# # # # def save_results(data, speaker_segments, speaker_profiles, reference_clips):
# # # #     """Save all results"""
# # # #     data['diarization'] = {
# # # #         'timestamp': datetime.now().isoformat(),
# # # #         'method': 'pyannote-3.1 + wav2vec2-age-gender',
# # # #         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
# # # #         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments)),
# # # #         'speaker_profiles': speaker_profiles,
# # # #         'reference_clips': reference_clips  # 🆕 OpenVoice reference files
# # # #     }
    
# # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # #         json.dump(data, f, ensure_ascii=False, indent=2)
# # # #     print(f"💾 Saved: {OUTPUT_JSON}")

# # # # def display_results(data, reference_clips):
# # # #     """Show final results"""
# # # #     print("\n" + "="*70)
# # # #     print("🎉 SPEAKER DIARIZATION + VOICE CLONING READY!")
# # # #     print("="*70)
    
# # # #     # Preview segments
# # # #     print("\n📋 FIRST 5 SEGMENTS:")
# # # #     for seg in data['segments'][:5]:
# # # #         profile = data['diarization']['speaker_profiles'].get(seg['speaker'], {})
# # # #         print(f"[{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['speaker']} "
# # # #               f"({profile.get('gender','?')}, {profile.get('age_group','?')})")
# # # #         print(f"   {seg['text'][:80]}...")
    
# # # #     # 🆕 Show OpenVoice ready clips
# # # #     print(f"\n🎯 OPENVOICE REFERENCE CLIPS ({len(reference_clips)}):")
# # # #     for speaker, info in reference_clips.items():
# # # #         quality = "🟢 EXCELLENT" if info['quality'] == 'excellent' else "🟡 GOOD" if info['quality'] == 'good' else "🔴 SHORT"
# # # #         print(f"   {speaker}: {os.path.basename(info['reference_file'])} "
# # # #               f"({info['total_duration']:.0f}s) {quality}")

# # # # def main():
# # # #     print("="*70)
# # # #     print("🚀 STEP 3: Speaker Diarization + Age/Gender + OpenVoice Prep")
# # # #     print("="*70)
    
# # # #     if not check_prerequisites():
# # # #         return
    
# # # #     # Load data
# # # #     transcription_data = load_transcription()
# # # #     audio_dict, audio_waveform, sample_rate = load_audio()
    
# # # #     # Run diarization
# # # #     diarization = run_diarization(audio_dict)
# # # #     if not diarization:
# # # #         return
    
# # # #     # 🆕 Extract speaker segments AND SAVE AUDIO
# # # #     speaker_segments, speakers_found, reference_clips = extract_speaker_audio_segments(
# # # #         diarization, audio_waveform, sample_rate
# # # #     )
    
# # # #     # Age/gender analysis
# # # #     processor, model, device = load_age_gender_model()
# # # #     speaker_profiles = analyze_speaker_age_gender(
# # # #         audio_waveform, sample_rate, speaker_segments, processor, model, device
# # # #     )
    
# # # #     # Match to transcription
# # # #     transcription_data = assign_speakers_to_transcription(transcription_data, speaker_segments)
    
# # # #     # Save everything
# # # #     save_results(transcription_data, speaker_segments, speaker_profiles, reference_clips)
    
# # # #     # Show results
# # # #     display_results(transcription_data, reference_clips)
    
# # # #     print("\n" + "="*70)
# # # #     print("✅ STEP 3 COMPLETE!")
# # # #     print(f"📁 Audio segments: {SPEAKER_AUDIO_DIR}/")
# # # #     print("🎯 Next: Use reference clips with OpenVoice for voice cloning!")
# # # #     print("🚀 Then: python step4_translation.py")

# # # # if __name__ == "__main__":
# # # #     main()
# # import torch
# # import json
# # import os
# # import librosa
# # import numpy as np
# # from pyannote.audio import Pipeline
# # from transformers import Wav2Vec2Processor
# # from transformers.models.wav2vec2.modeling_wav2vec2 import (
# #     Wav2Vec2Model,
# #     Wav2Vec2PreTrainedModel,
# # )
# # import torch.nn as nn
# # from datetime import datetime
# # from speechbrain.inference import EncoderClassifier
# # from speechbrain.inference.interfaces import foreign_class

# # # ============================================================
# # # Configuration
# # # ============================================================
# # AUDIO_FILE = "separated/htdemucs/audio_16k/vocals.wav"
# # RHYTHM_JSON = "work/rhythm_pattern.json" # Input from Step 2.5
# # CROPPED_AUDIO_DIR = "work/cropped_segments/"
# # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # HuggingFace token
# # HF_TOKEN = "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"

# # # Models
# # AGE_GENDER_MODEL = "audeering/wav2vec2-large-robust-24-ft-age-gender"
# # EMOTION_MODEL = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"

# # # ============================================================
# # # Age/Gender Model Classes (from HuggingFace)
# # # ============================================================
# # class ModelHead(nn.Module):
# #     """Classification head."""
# #     def __init__(self, config, num_labels):
# #         super().__init__()
# #         self.dense = nn.Linear(config.hidden_size, config.hidden_size)
# #         self.dropout = nn.Dropout(config.final_dropout)
# #         self.out_proj = nn.Linear(config.hidden_size, num_labels)

# #     def forward(self, features, **kwargs):
# #         x = features
# #         x = self.dropout(x)
# #         x = self.dense(x)
# #         x = torch.tanh(x)
# #         x = self.dropout(x)
# #         x = self.out_proj(x)
# #         return x

# # class AgeGenderModel(Wav2Vec2PreTrainedModel):
# #     """Speech age/gender classifier."""
# #     def __init__(self, config):
# #         super().__init__(config)
# #         self.config = config
# #         self.wav2vec2 = Wav2Vec2Model(config)
# #         self.age = ModelHead(config, 1)
# #         self.gender = ModelHead(config, 3)
# #         self.init_weights()

# #     def forward(self, input_values):
# #         outputs = self.wav2vec2(input_values)
# #         hidden_states = outputs[0]
# #         hidden_states = torch.mean(hidden_states, dim=1)
# #         logits_age = self.age(hidden_states)
# #         logits_gender = torch.softmax(self.gender(hidden_states), dim=1)
# #         return hidden_states, logits_age, logits_gender

# # # ============================================================
# # # Main Functions
# # # ============================================================

# # def check_prerequisites():
# #     if not os.path.exists(AUDIO_FILE):
# #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# #         return False
# #     if not os.path.exists(RHYTHM_JSON):
# #         print(f"❌ Rhythm file not found: {RHYTHM_JSON}. Run Step 2.5 first.")
# #         return False
# #     if not os.path.exists(CROPPED_AUDIO_DIR):
# #         print(f"❌ Cropped audio folder not found. Run Step 2.5 first.")
# #         return False
# #     return True

# # def load_data():
# #     with open(RHYTHM_JSON, 'r', encoding='utf-8') as f:
# #         data = json.load(f)
# #     print(f"📄 Loaded {data['total_segments']} segments from Step 2.5")
# #     return data

# # # def run_diarization():
# # #     """Run speaker diarization on the FULL audio file"""
# # #     print(f"\n🎤 Running Pyannote speaker diarization on FULL audio...")
# # #     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
# # #     try:
# # #         pipeline = Pipeline.from_pretrained(
# # #             "pyannote/speaker-diarization-3.1",
# # #             token=HF_TOKEN
# # #         ).to(device)
        
# # #         # Optimize for anime (multiple quick speakers)
# # #         diarization = pipeline(AUDIO_FILE, min_speakers=2, max_speakers=15)
        
# # #         # Extract segments
# # #         speaker_segments = []
# # #         annotation = diarization.speaker_diarization if hasattr(diarization, 'speaker_diarization') else diarization
        
# # #         for segment, _, speaker in annotation.itertracks(yield_label=True):
# # #             speaker_segments.append({
# # #                 'speaker': speaker,
# # #                 'start': segment.start,
# # #                 'end': segment.end
# # #             })
            
# # #         print(f"✅ Found {len(set(s['speaker'] for s in speaker_segments))} unique speakers globally.")
# # #         return speaker_segments
        
# # #     except Exception as e:
# # #         print(f"❌ Diarization error: {e}")
# # #         return None
# # def run_diarization():
# #     """Run speaker diarization on the FULL audio file using in-memory waveform"""
# #     print(f"\n🎤 Running Pyannote speaker diarization on FULL audio...")
# #     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
# #     try:
# #         # Load the Pyannote pipeline
# #         pipeline = Pipeline.from_pretrained(
# #             "pyannote/speaker-diarization-3.1",
# #             token=HF_TOKEN
# #         ).to(device)
        
# #         # --- FIX FOR TORCHCODEC ERROR ---
# #         # 1. Load audio into memory using librosa
# #         print("   Loading audio into memory to bypass torchcodec error...")
# #         waveform, sample_rate = librosa.load(AUDIO_FILE, sr=16000, mono=True)
        
# #         # 2. Format it exactly how Pyannote expects an in-memory dictionary
# #         waveform_tensor = torch.from_numpy(waveform).unsqueeze(0) # shape (1, samples)
# #         in_memory_audio = {
# #             "waveform": waveform_tensor, 
# #             "sample_rate": sample_rate
# #         }
        
# #         # Optimize for anime (multiple quick speakers)
# #         print("   Processing audio...")
# #         # 3. Pass the dictionary instead of the file path string
# #         diarization = pipeline(in_memory_audio, min_speakers=2, max_speakers=15)
        
# #         # Extract segments
# #         speaker_segments = []
# #         annotation = diarization.speaker_diarization if hasattr(diarization, 'speaker_diarization') else diarization
        
# #         for segment, _, speaker in annotation.itertracks(yield_label=True):
# #             speaker_segments.append({
# #                 'speaker': speaker,
# #                 'start': segment.start,
# #                 'end': segment.end
# #             })
            
# #         print(f"✅ Found {len(set(s['speaker'] for s in speaker_segments))} unique speakers globally.")
# #         return speaker_segments
        
# #     except Exception as e:
# #         print(f"❌ Diarization error: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return None

# # def analyze_cropped_segments(segments):
# #     """Analyze Emotion, Age, and Gender on EXACT CROPPED files"""
# #     print(f"\n🔍 Analyzing Age, Gender, and Emotion on {len(segments)} cropped segments...")
# #     device = 'cuda' if torch.cuda.is_available() else 'cpu'

# #     # 1. Load Age/Gender Model
# #     print("   Loading Age/Gender Wav2Vec2...")
# #     ag_processor = Wav2Vec2Processor.from_pretrained(AGE_GENDER_MODEL)
# #     ag_model = AgeGenderModel.from_pretrained(AGE_GENDER_MODEL).to(device).eval()

# #     # 2. Load Emotion Model (SpeechBrain)
# #     print("   Loading Emotion Model...")
# #     emotion_classifier = foreign_class(
# #         source=EMOTION_MODEL,
# #         pymodule_file="custom_interface.py", 
# #         classname="CustomEncoderWav2vec2Classifier",
# #         run_opts={"device": device}
# #     )

# #     for seg in segments:
# #         seg_id = seg['id']
# #         crop_path = os.path.join(CROPPED_AUDIO_DIR, f"segment_{seg_id:03d}.wav")
        
# #         if not os.path.exists(crop_path):
# #             print(f"   ⚠️ Missing audio for segment {seg_id}")
# #             continue

# #         # Load cropped audio
# #         audio, sr = librosa.load(crop_path, sr=16000, mono=True)
        
# #         # --- AGE / GENDER ---
# #         inputs = ag_processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)
# #         input_values = inputs.input_values.to(device)
# #         with torch.no_grad():
# #             _, logits_age, logits_gender = ag_model(input_values)
            
# #         age_est = float(logits_age.detach().cpu().numpy()[0][0] * 100)
# #         gender_probs = logits_gender.detach().cpu().numpy()[0]
        
# #         gender = 'male'
# #         if gender_probs[0] > gender_probs[1] and gender_probs[0] > gender_probs[2]:
# #             gender = 'female'
# #         elif gender_probs[2] > 0.5:
# #             gender = 'child'

# #         # --- EMOTION ---
# #         out_prob, score, index, text_lab = emotion_classifier.classify_file(crop_path)
# #         emotion = text_lab[0] # Usually ['ang', 'hap', 'sad', 'neu']

# #         # Save to segment
# #         seg['analysis'] = {
# #             'gender': gender,
# #             'age': round(age_est),
# #             'emotion': emotion,
# #             'emotion_confidence': float(score[0])
# #         }
        
# #         print(f"   [Seg {seg_id:03d}] {gender}, ~{round(age_est)}y | Emotion: {emotion}")

# #     return segments

# # def assign_speakers(segments, pyannote_segments):
# #     """Match the Pyannote global speaker ID to our segments based on overlap"""
# #     print("\n🔗 Mapping Pyannote global speakers to JSON segments...")
    
# #     for trans_seg in segments:
# #         trans_mid = trans_seg['start'] + (trans_seg['duration'] / 2)
# #         assigned_speaker = "UNKNOWN"
        
# #         for spk_seg in pyannote_segments:
# #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# #                 assigned_speaker = spk_seg['speaker']
# #                 break
                
# #         trans_seg['speaker'] = assigned_speaker
        
# #     return segments

# # def main():
# #     print("=" * 60)
# #     print("STEP 3: Diarization (Full) & Analysis (Cropped)")
# #     print("=" * 60)
    
# #     if not check_prerequisites(): return
    
# #     # 1. Load Data
# #     data = load_data()
    
# #     # 2. Diarization on Full File
# #     pyannote_segs = run_diarization()
# #     if not pyannote_segs: return
    
# #     # 3. Assign Speakers
# #     data['segments'] = assign_speakers(data['segments'], pyannote_segs)
    
# #     # 4. Analyze Cropped Files (Emotion, Age, Gender)
# #     data['segments'] = analyze_cropped_segments(data['segments'])
    
# #     # 5. Save Output
# #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# #         json.dump(data, f, ensure_ascii=False, indent=2)
        
# #     print("\n" + "=" * 60)
# #     print("✅ Step 3 Complete!")
# #     print(f"📁 Output saved to: {OUTPUT_JSON}")

# # if __name__ == "__main__":
# #     main()
# import os
# import json
# from datetime import datetime
# import numpy as np
# import torch
# import torchaudio

# from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
# from openai import OpenAI
# from dotenv import load_dotenv
# import re

# load_dotenv()

# # ========= CONFIG =========
# WORK_DIR = "work"
# VOCALS_PATH = "work/stems/htdemucs_6s/raw_audio/vocals.wav"
# TRANSCRIPT_JSON = os.path.join(WORK_DIR, "transcription_with_speakers.json")
# EMOTION_JSON = os.path.join(WORK_DIR, "emotion_detection.json")
# TRANSLATED_JSON = os.path.join(WORK_DIR, "translated_segments_step3.json")

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# client = OpenAI(api_key=OPENAI_API_KEY)

# # emotion2vec+ (9-class)
# EMO2VEC_ID = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"  # 12-class emotion2vec-style
# SPEECHBRAIN_ID = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"     # 4-class fallback ✅

# device = "cuda" if torch.cuda.is_available() else "cpu"

# # ========= LOAD MODELS =========
# print("🔄 Loading emotion models...")

# emo2_feat = AutoFeatureExtractor.from_pretrained(EMO2VEC_ID)
# emo2_model = AutoModelForAudioClassification.from_pretrained(EMO2VEC_ID).to(device)
# emo2_model.eval()

# sb_feat = AutoFeatureExtractor.from_pretrained(SPEECHBRAIN_ID)
# sb_model = AutoModelForAudioClassification.from_pretrained(SPEECHBRAIN_ID).to(device)
# sb_model.eval()

# print("✅ Emotion models loaded")

# # ========= HELPERS =========

# def load_audio(path, target_sr=16000):
#     wav, sr = torchaudio.load(path)
#     if sr != target_sr:
#         wav = torchaudio.functional.resample(wav, sr, target_sr)
#         sr = target_sr
#     # mono
#     if wav.size(0) > 1:
#         wav = wav.mean(dim=0, keepdim=True)
#     return wav.squeeze(0), sr

# def classify_emotion_segment(audio_np, sr, duration):
#     """
#     Route: if duration >= 0.5s -> emotion2vec+, else SpeechBrain fallback.
#     Returns (primary_label, confidence, model_used, raw_probs_dict)
#     """
#     # audio_np = audio_np.astype(np.float32)
#     if audio_np.dtype != np.float32:
#         audio_np = audio_np.astype(np.float32)

#     if duration >= 0.5:
#         inputs = emo2_feat(
#             audio_np,
#             sampling_rate=sr,
#             return_tensors="pt",
#             padding=True
#         ).to(device)
#         with torch.no_grad():
#             logits = emo2_model(**inputs).logits
#             probs = torch.softmax(logits, dim=-1)[0]
#             idx = int(torch.argmax(probs))
#             label = emo2_model.config.id2label[idx]
#             conf = float(probs[idx])
#             dist = {emo2_model.config.id2label[i]: float(probs[i]) for i in range(len(probs))}
#         return label, conf, "emotion2vec_plus_large", dist
#     else:
#         inputs = sb_feat(
#             audio_np,
#             sampling_rate=sr,
#             return_tensors="pt",
#             padding=True
#         ).to(device)
#         with torch.no_grad():
#             logits = sb_model(**inputs).logits
#             probs = torch.softmax(logits, dim=-1)[0]
#             idx = int(torch.argmax(probs))
#             label = sb_model.config.id2label[idx]
#             conf = float(probs[idx])
#             dist = {sb_model.config.id2label[i]: float(probs[i]) for i in range(len(probs))}
#         return label, conf, "speechbrain_fallback", dist

# # emotion → syllables/second
# EMOTION_RATE = {
#     "angry": 5.0,
#     "disgusted": 4.2,
#     "fearful": 4.8,
#     "happy": 4.5,
#     "neutral": 4.0,
#     "other": 4.0,
#     "sad": 3.5,
#     "surprised": 4.8,
#     "unknown": 4.0
# }

# def estimate_syllable_budget(duration, emotion_label):
#     rate = EMOTION_RATE.get(emotion_label.lower(), 4.0)
#     target = int(duration * rate)
#     return max(3, target)

# def build_translation_prompt(seg, emotion_label, syllable_target, prev_english):
#     jp = seg["text"]
#     duration = seg["duration"]
#     gender = seg.get("gender", "unknown")
#     speaker = seg["speaker"]

#     context_block = ""
#     if prev_english:
#         context_block = f"""
# Previous English line (same scene, already dubbed):
# \"{prev_english}\"
# """

#     prompt = f"""
# You are an expert anime ADR script adapter.

# Your task: adapt this Japanese line into natural, performable English for dubbing.
# Do NOT translate literally. Preserve **intent + emotion**, and match timing and lip rhythm.

# Context:
# - Speaker id: {speaker}
# - Gender: {gender}
# - Emotion: {emotion_label}
# - Original duration: {duration:.2f} seconds
# - Target syllable budget: ~{syllable_target} English syllables

# Rules:
# - Sound like spoken anime dub dialogue, not subtitles.
# - Use vocabulary and phrasing natural for an anime character with this emotion.
# - You may change sentence structure, add fillers ("well", "hey", "come on"), or adjust intensity.
# - Keep meaning and emotional direction the same.
# - No explanatory notes, no brackets, no stage directions.

# Timing rules:
# - Aim for {syllable_target} syllables.
# - Stay within ±20% of that budget.
# - Keep the line that can be spoken in ~{duration:.2f} seconds at typical {emotion_label} pace.

# {context_block}
# Japanese line:
# \"{jp}\"

# Return ONLY a JSON object in this exact format:

# {{
#   "english": "final English dub line",
#   "alt": "optional slight alternate phrasing (same timing), or repeat english",
#   "notes": "brief note on how you adapted for timing and emotion (max 1 short sentence)"
# }}
# """
#     return prompt

# # ========= STEP 1: EMOTION DETECTION =========

# print("\n🎭 STEP 3A: Emotion detection per segment")

# with open(TRANSCRIPT_JSON, "r", encoding="utf-8") as f:
#     data = json.load(f)

# segments = data["segments"]
# full_audio, sr = load_audio(VOCALS_PATH, target_sr=16000)

# emotion_results = []
# for seg in segments:
#     s = seg["start"]
#     e = seg["end"]
#     s_idx = int(s * sr)
#     e_idx = int(e * sr)
#     chunk = full_audio[s_idx:e_idx].numpy()
#     if len(chunk) < int(0.1 * sr):
#         label, conf, used, dist = "unknown", 0.0, "none", {}
#     else:
#         label, conf, used, dist = classify_emotion_segment(chunk, sr, seg["duration"])
#     seg_emotion = {
#         "segment_id": seg["id"],
#         "speaker": seg["speaker"],
#         "start": s,
#         "end": e,
#         "duration": seg["duration"],
#         "emotion": label,
#         "confidence": conf,
#         "model": used,
#         "distribution": dist
#     }
#     emotion_results.append(seg_emotion)
#     print(f"  Seg {seg['id']:02d}: {seg['speaker']} {s:.1f}-{e:.1f}s → {label} ({conf:.2f}) via {used}")

# with open(EMOTION_JSON, "w", encoding="utf-8") as f:
#     json.dump({"timestamp": datetime.now().isoformat(),
#                "emotions": emotion_results}, f, ensure_ascii=False, indent=2)

# print(f"✅ Emotion data saved: {EMOTION_JSON}")

# # ========= STEP 3B: EMOTION-AWARE TRANSLATION =========

# print("\n🌐 STEP 3B: Emotion-aware translation")

# # Map segment_id → emotion info
# emo_map = {e["segment_id"]: e for e in emotion_results}

# translated_segments = []
# prev_english = None

# for seg in segments:
#     emo = emo_map.get(seg["id"], {})
#     emo_label = emo.get("emotion", "neutral")
#     syllables = estimate_syllable_budget(seg["duration"], emo_label)

#     prompt = build_translation_prompt(seg, emo_label, syllables, prev_english)

#     resp = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.7,
#         response_format={"type": "json_object"}
#     )
#     content = resp.choices[0].message.content.strip()
#     try:
#         obj = json.loads(content)
#     except Exception:
#         obj = {"english": content, "alt": content, "notes": "raw output"}

#     english = obj.get("english", "").strip()
#     alt = obj.get("alt", "").strip()

#     translated_segments.append({
#         "segment_id": seg["id"],
#         "speaker": seg["speaker"],
#         "start": seg["start"],
#         "end": seg["end"],
#         "duration": seg["duration"],
#         "original_text": seg["text"],
#         "gender": seg.get("gender"),
#         "emotion": emo_label,
#         "emotion_confidence": emo.get("confidence", 0.0),
#         "english": english,
#         "alt": alt,
#         "notes": obj.get("notes", "")
#     })

#     prev_english = english  # for context to next line
#     print(f"  Seg {seg['id']:02d}: {seg['text']} → {english}")

# output = {
#     "timestamp": datetime.now().isoformat(),
#     "total_segments": len(translated_segments),
#     "segments": translated_segments
# }

# with open(TRANSLATED_JSON, "w", encoding="utf-8") as f:
#     json.dump(output, f, ensure_ascii=False, indent=2)

# print(f"\n✅ Step 3 complete. Saved: {TRANSLATED_JSON}")
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

def translate_segment(seg, emotion_label, syllable_target, prev_english=""):
    """GPT translation with emotion + context."""
    jp_text = seg["text"]
    duration = seg["duration"]
    gender = seg.get("gender", "neutral")
    speaker = seg["speaker"]
    
    context = ""
    if prev_english:
        context = f"\nPrevious English line: \"{prev_english}\""
    
    prompt = f"""You are an anime ADR script adapter.

Translate/adapt Japanese → natural English dub line.

CONTEXT:
- Speaker: {speaker} ({gender})
- Emotion: {emotion_label}  
- Duration: {duration:.2f}s
- Target syllables: ~{syllable_target}

INSTRUCTIONS:
1. Preserve emotional tone and character personality
2. Match speaking rhythm for lip-sync (syllable count)
3. Sound like spoken dialogue, not subtitles
4. You can rephrase freely for natural flow/timing

{context}

Japanese: "{jp_text}"

JSON response only:
{{
  "english": "dub line here",
  "syllables": 0,
  "notes": "brief timing/emotion note"
}}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        content = resp.choices[0].message.content.strip()
        obj = json.loads(content)
        english = obj.get("english", jp_text).strip()
        notes = obj.get("notes", "")
        syl_est = estimate_syllable_budget(duration, emotion_label)  # placeholder
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