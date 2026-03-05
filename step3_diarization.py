# # # # # step3_diarization.py
# # # # import torch
# # # # import json
# # # # import os
# # # # from pyannote.audio import Pipeline
# # # # from datetime import datetime

# # # # # Configuration
# # # # AUDIO_FILE = "work/audio_16k.wav"
# # # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # # # You'll need a HuggingFace token for pyannote
# # # # # Get it from: https://huggingface.co/settings/tokens
# # # # HF_TOKEN = "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"  # Replace with your actual token

# # # # def check_prerequisites():
# # # #     """Check if required files exist"""
# # # #     if not os.path.exists(AUDIO_FILE):
# # # #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# # # #         print("   Please run step1_extract_audio.py first")
# # # #         return False
    
# # # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # # #         print("   Please run step2_transcribe.py first")
# # # #         return False
    
# # # #     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
# # # #         print("❌ HuggingFace token not set!")
# # # #         print("\n📝 To get your token:")
# # # #         print("   1. Go to: https://huggingface.co/settings/tokens")
# # # #         print("   2. Click 'New token'")
# # # #         print("   3. Copy the token")
# # # #         print("   4. Paste it in step3_diarization.py (HF_TOKEN variable)")
# # # #         print("\n📝 Also accept the terms:")
# # # #         print("   5. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # # #         print("   6. Click 'Accept' on the user conditions")
# # # #         return False
    
# # # #     return True

# # # # def load_transcription():
# # # #     """Load transcription from JSON"""
# # # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # # #         data = json.load(f)
    
# # # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # # #     return data

# # # # def run_diarization():
# # # #     """Run speaker diarization on audio"""
    
# # # #     print(f"\n🎤 Running speaker diarization...")
# # # #     print("⏳ This may take 5-10 minutes...")
    
# # # #     try:
# # # #         # Check GPU
# # # #         device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# # # #         print(f"   Device: {device}")
        
# # # #         # Load diarization pipeline
# # # #         print("   Loading pyannote model...")
# # # #         pipeline = Pipeline.from_pretrained(
# # # #             "pyannote/speaker-diarization-3.1",
# # # #             use_auth_token=HF_TOKEN
# # # #         )
# # # #         pipeline = pipeline.to(device)
        
# # # #         print(f"   Processing audio: {AUDIO_FILE}")
        
# # # #         # Run diarization
# # # #         diarization = pipeline(AUDIO_FILE)
        
# # # #         print("✅ Diarization complete!")
        
# # # #         return diarization
    
# # # #     except Exception as e:
# # # #         print(f"❌ Diarization error: {e}")
# # # #         print("\n💡 Common issues:")
# # # #         print("   - Make sure you accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
# # # #         print("   - Check your HuggingFace token is valid")
# # # #         print("   - Try: pip install --upgrade pyannote.audio")
# # # #         import traceback
# # # #         traceback.print_exc()
# # # #         return None

# # # # def extract_speaker_segments(diarization):
# # # #     """Extract speaker segments from diarization result"""
    
# # # #     speaker_segments = []
# # # #     speakers_found = set()
    
# # # #     for segment, _, speaker in diarization.itertracks(yield_label=True):
# # # #         speaker_segments.append({
# # # #             'speaker': speaker,
# # # #             'start': segment.start,
# # # #             'end': segment.end,
# # # #             'duration': segment.end - segment.start
# # # #         })
# # # #         speakers_found.add(speaker)
    
# # # #     print(f"\n👥 Found {len(speakers_found)} unique speakers:")
# # # #     for speaker in sorted(speakers_found):
# # # #         count = sum(1 for s in speaker_segments if s['speaker'] == speaker)
# # # #         total_time = sum(s['duration'] for s in speaker_segments if s['speaker'] == speaker)
# # # #         print(f"   {speaker}: {count} segments, {total_time:.1f}s total")
    
# # # #     return speaker_segments, speakers_found

# # # # def assign_speakers_to_transcription(transcription_data, speaker_segments):
# # # #     """Match speaker segments with transcription segments"""
    
# # # #     print(f"\n🔗 Matching speakers with transcription...")
    
# # # #     segments = transcription_data['segments']
    
# # # #     for trans_seg in segments:
# # # #         trans_start = trans_seg['start']
# # # #         trans_mid = trans_start + (trans_seg['duration'] / 2)  # Use midpoint
        
# # # #         # Find which speaker segment this transcription belongs to
# # # #         assigned_speaker = None
# # # #         best_overlap = 0
        
# # # #         for spk_seg in speaker_segments:
# # # #             # Check if transcription midpoint falls within speaker segment
# # # #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# # # #                 overlap = min(trans_seg['end'], spk_seg['end']) - max(trans_seg['start'], spk_seg['start'])
# # # #                 if overlap > best_overlap:
# # # #                     best_overlap = overlap
# # # #                     assigned_speaker = spk_seg['speaker']
        
# # # #         # Assign speaker (or "UNKNOWN" if no match)
# # # #         trans_seg['speaker'] = assigned_speaker if assigned_speaker else "UNKNOWN"
    
# # # #     # Count assignments
# # # #     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
# # # #     print(f"✅ Assigned speakers to {assigned}/{len(segments)} segments")
    
# # # #     if assigned < len(segments):
# # # #         unknown = len(segments) - assigned
# # # #         print(f"⚠️  {unknown} segments without clear speaker assignment")
    
# # # #     return transcription_data

# # # # def save_results(data, speaker_segments):
# # # #     """Save combined data to JSON"""
    
# # # #     # Add speaker metadata
# # # #     data['diarization'] = {
# # # #         'timestamp': datetime.now().isoformat(),
# # # #         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
# # # #         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments))
# # # #     }
    
# # # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # # #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# # # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # # def display_preview(data):
# # # #     """Display preview with speakers"""
    
# # # #     print("\n" + "="*60)
# # # #     print("📋 PREVIEW (First 5 segments with speakers)")
# # # #     print("="*60)
    
# # # #     for seg in data['segments'][:5]:
# # # #         speaker = seg.get('speaker', 'UNKNOWN')
# # # #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] Speaker: {speaker}")
# # # #         print(f"  {seg['text']}")
    
# # # #     if len(data['segments']) > 5:
# # # #         print(f"\n... and {len(data['segments']) - 5} more segments")

# # # # def main():
# # # #     print("=" * 60)
# # # #     print("STEP 3: Speaker Diarization")
# # # #     print("=" * 60)
    
# # # #     # Check prerequisites
# # # #     if not check_prerequisites():
# # # #         return
    
# # # #     # Load transcription
# # # #     transcription_data = load_transcription()
    
# # # #     # Run diarization
# # # #     diarization = run_diarization()
# # # #     if diarization is None:
# # # #         return
    
# # # #     # Extract speaker segments
# # # #     speaker_segments, speakers_found = extract_speaker_segments(diarization)
    
# # # #     # Assign speakers to transcription
# # # #     transcription_data = assign_speakers_to_transcription(
# # # #         transcription_data, 
# # # #         speaker_segments
# # # #     )
    
# # # #     # Save results
# # # #     save_results(transcription_data, speaker_segments)
    
# # # #     # Display preview
# # # #     display_preview(transcription_data)
    
# # # #     print("\n" + "=" * 60)
# # # #     print("✅ Step 3 Complete!")
# # # #     print("=" * 60)
# # # #     print(f"📁 Output: {OUTPUT_JSON}")
# # # #     print(f"👥 Total speakers: {len(speakers_found)}")
# # # #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# # # #     print("\nNext: Run step4_gender_age_classification.py")

# # # # if __name__ == "__main__":
# # # #     main()
# # # step3_diarization.py (FIXED for latest pyannote.audio)
# # import torch
# # import json
# # import os
# # import librosa
# # import torch
# # from pyannote.audio import Pipeline
# # from datetime import datetime

# # # Configuration
# # AUDIO_FILE = "work/audio_16k.wav"
# # TRANSCRIPTION_FILE = "work/transcription.json"
# # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # You'll need a HuggingFace token for pyannote
# # # Get it from: https://huggingface.co/settings/tokens
# # HF_TOKEN = "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"  # Replace with your actual token

# # def check_prerequisites():
# #     """Check if required files exist"""
# #     if not os.path.exists(AUDIO_FILE):
# #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# #         print("   Please run step1_extract_audio.py first")
# #         return False
    
# #     if not os.path.exists(TRANSCRIPTION_FILE):
# #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# #         print("   Please run step2_transcribe.py first")
# #         return False
    
# #     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
# #         print("❌ HuggingFace token not set!")
# #         print("\n📝 To get your token:")
# #         print("   1. Go to: https://huggingface.co/settings/tokens")
# #         print("   2. Click 'New token'")
# #         print("   3. Copy the token")
# #         print("   4. Paste it in step3_diarization.py (HF_TOKEN variable)")
# #         print("\n📝 Also accept the terms:")
# #         print("   5. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
# #         print("   6. Click 'Accept' on the user conditions")
# #         return False
    
# #     return True

# # def load_transcription():
# #     """Load transcription from JSON"""
# #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# #         data = json.load(f)
    
# #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# #     return data

# # def load_audio_for_pyannote():
# #     """Load audio as dictionary for pyannote (workaround for TorchCodec issue)"""
# #     print("   Loading audio with librosa (TorchCodec workaround)...")
    
# #     # Load audio
# #     waveform, sample_rate = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
# #     # Convert to torch tensor and add channel dimension
# #     waveform_tensor = torch.from_numpy(waveform).unsqueeze(0)  # Shape: (1, samples)
    
# #     # Create audio dictionary that pyannote can use
# #     audio = {
# #         "waveform": waveform_tensor,
# #         "sample_rate": sample_rate
# #     }
    
# #     return audio

# # def run_diarization(audio):
# #     """Run speaker diarization on audio"""
    
# #     print(f"\n🎤 Running speaker diarization...")
# #     print("⏳ This may take 5-10 minutes...")
    
# #     try:
# #         # Check GPU
# #         device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# #         print(f"   Device: {device}")
        
# #         # Load diarization pipeline (FIXED: use 'token' not 'use_auth_token')
# #         print("   Loading pyannote model...")
# #         pipeline = Pipeline.from_pretrained(
# #             "pyannote/speaker-diarization-3.1",
# #             use_auth_token=HF_TOKEN
# #         )
# #         pipeline = pipeline.to(device)
        
# #         print(f"   Processing audio...")
        
# #         # Run diarization on audio dictionary
# #         diarization = pipeline(audio)
        
# #         print("✅ Diarization complete!")
        
# #         return diarization
    
# #     except Exception as e:
# #         print(f"❌ Diarization error: {e}")
# #         print("\n💡 Common issues:")
# #         print("   - Make sure you accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
# #         print("   - Check your HuggingFace token is valid")
# #         print("   - Try: pip install --upgrade pyannote.audio")
# #         import traceback
# #         traceback.print_exc()
# #         return None

# # def extract_speaker_segments(diarization):
# #     """Extract speaker segments from diarization result"""
    
# #     speaker_segments = []
# #     speakers_found = set()
    
# #     for segment, _, speaker in diarization.itertracks(yield_label=True):
# #         speaker_segments.append({
# #             'speaker': speaker,
# #             'start': segment.start,
# #             'end': segment.end,
# #             'duration': segment.end - segment.start
# #         })
# #         speakers_found.add(speaker)
    
# #     print(f"\n👥 Found {len(speakers_found)} unique speakers:")
# #     for speaker in sorted(speakers_found):
# #         count = sum(1 for s in speaker_segments if s['speaker'] == speaker)
# #         total_time = sum(s['duration'] for s in speaker_segments if s['speaker'] == speaker)
# #         print(f"   {speaker}: {count} segments, {total_time:.1f}s total")
    
# #     return speaker_segments, speakers_found

# # def assign_speakers_to_transcription(transcription_data, speaker_segments):
# #     """Match speaker segments with transcription segments"""
    
# #     print(f"\n🔗 Matching speakers with transcription...")
    
# #     segments = transcription_data['segments']
    
# #     for trans_seg in segments:
# #         trans_start = trans_seg['start']
# #         trans_end = trans_seg['end']
# #         trans_mid = trans_start + (trans_seg['duration'] / 2)  # Use midpoint
        
# #         # Find which speaker segment this transcription belongs to
# #         assigned_speaker = None
# #         best_overlap = 0
        
# #         for spk_seg in speaker_segments:
# #             # Check if transcription midpoint falls within speaker segment
# #             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
# #                 overlap = min(trans_end, spk_seg['end']) - max(trans_start, spk_seg['start'])
# #                 if overlap > best_overlap:
# #                     best_overlap = overlap
# #                     assigned_speaker = spk_seg['speaker']
        
# #         # Assign speaker (or "UNKNOWN" if no match)
# #         trans_seg['speaker'] = assigned_speaker if assigned_speaker else "UNKNOWN"
    
# #     # Count assignments
# #     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
# #     print(f"✅ Assigned speakers to {assigned}/{len(segments)} segments")
    
# #     if assigned < len(segments):
# #         unknown = len(segments) - assigned
# #         print(f"⚠️  {unknown} segments without clear speaker assignment")
    
# #     return transcription_data

# # def save_results(data, speaker_segments):
# #     """Save combined data to JSON"""
    
# #     # Add speaker metadata
# #     data['diarization'] = {
# #         'timestamp': datetime.now().isoformat(),
# #         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
# #         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments))
# #     }
    
# #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # def display_preview(data):
# #     """Display preview with speakers"""
    
# #     print("\n" + "="*60)
# #     print("📋 PREVIEW (First 5 segments with speakers)")
# #     print("="*60)
    
# #     for seg in data['segments'][:5]:
# #         speaker = seg.get('speaker', 'UNKNOWN')
# #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] Speaker: {speaker}")
# #         print(f"  {seg['text']}")
    
# #     if len(data['segments']) > 5:
# #         print(f"\n... and {len(data['segments']) - 5} more segments")

# # def main():
# #     print("=" * 60)
# #     print("STEP 3: Speaker Diarization")
# #     print("=" * 60)
    
# #     # Check prerequisites
# #     if not check_prerequisites():
# #         return
    
# #     # Load transcription
# #     transcription_data = load_transcription()
    
# #     # Load audio (workaround for TorchCodec issue on Windows)
# #     audio = load_audio_for_pyannote()
    
# #     # Run diarization
# #     diarization = run_diarization(audio)
# #     if diarization is None:
# #         return
    
# #     # Extract speaker segments
# #     speaker_segments, speakers_found = extract_speaker_segments(diarization)
    
# #     # Assign speakers to transcription
# #     transcription_data = assign_speakers_to_transcription(
# #         transcription_data, 
# #         speaker_segments
# #     )
    
# #     # Save results
# #     save_results(transcription_data, speaker_segments)
    
# #     # Display preview
# #     display_preview(transcription_data)
    
# #     print("\n" + "=" * 60)
# #     print("✅ Step 3 Complete!")
# #     print("=" * 60)
# #     print(f"📁 Output: {OUTPUT_JSON}")
# #     print(f"👥 Total speakers: {len(speakers_found)}")
# #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# #     print("\nNext: Run step4_gender_age_classification.py")

# # if __name__ == "__main__":
# #     main()
# # # step3_diarization_simple.py (No gated models needed!)
# # # import json
# # # import os
# # # import librosa
# # # import numpy as np
# # # from sklearn.cluster import AgglomerativeClustering
# # # from datetime import datetime

# # # # Configuration
# # # AUDIO_FILE = "work/audio_16k.wav"
# # # TRANSCRIPTION_FILE = "work/transcription.json"
# # # OUTPUT_JSON = "work/transcription_with_speakers.json"

# # # def load_transcription():
# # #     """Load transcription from JSON"""
# # #     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
# # #         data = json.load(f)
    
# # #     print(f"📄 Loaded {data['total_segments']} transcription segments")
# # #     return data

# # # def extract_voice_features(audio_segment, sr=16000):
# # #     """Extract voice features for speaker identification"""
    
# # #     # Extract MFCC features (voice characteristics)
# # #     mfcc = librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=13)
# # #     mfcc_mean = np.mean(mfcc, axis=1)
    
# # #     # Extract pitch (fundamental frequency)
# # #     pitches, magnitudes = librosa.piptrack(y=audio_segment, sr=sr)
# # #     pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
    
# # #     # Extract spectral centroid (brightness of sound)
# # #     spectral_centroid = librosa.feature.spectral_centroid(y=audio_segment, sr=sr)
# # #     spectral_mean = np.mean(spectral_centroid)
    
# # #     # Combine features
# # #     features = np.concatenate([
# # #         mfcc_mean,
# # #         [pitch_mean],
# # #         [spectral_mean]
# # #     ])
    
# # #     return features

# # # def simple_speaker_diarization(audio, sr, segments):
# # #     """Simple speaker diarization using clustering"""
    
# # #     print(f"\n🎤 Analyzing speakers...")
# # #     print("⏳ Extracting voice features for each segment...")
    
# # #     # Extract features for each segment
# # #     features_list = []
# # #     valid_segments = []
    
# # #     for seg in segments:
# # #         start_sample = int(seg['start'] * sr)
# # #         end_sample = int(seg['end'] * sr)
        
# # #         # Extract audio segment
# # #         audio_segment = audio[start_sample:end_sample]
        
# # #         # Skip if too short
# # #         if len(audio_segment) < sr * 0.3:  # Less than 0.3 seconds
# # #             continue
        
# # #         # Extract features
# # #         features = extract_voice_features(audio_segment, sr)
# # #         features_list.append(features)
# # #         valid_segments.append(seg)
    
# # #     if len(features_list) < 2:
# # #         print("⚠️  Not enough segments for clustering, assigning all to one speaker")
# # #         for seg in segments:
# # #             seg['speaker'] = "SPEAKER_00"
# # #         return segments
    
# # #     # Convert to numpy array
# # #     features_array = np.array(features_list)
    
# # #     # Cluster speakers (assume 2-3 speakers max for anime)
# # #     n_speakers = min(3, len(features_list))  # Max 3 speakers
    
# # #     print(f"   Clustering into {n_speakers} speaker groups...")
    
# # #     clustering = AgglomerativeClustering(
# # #         n_clusters=n_speakers,
# # #         linkage='ward'
# # #     )
    
# # #     speaker_labels = clustering.fit_predict(features_array)
    
# # #     # Assign speaker labels
# # #     for i, seg in enumerate(valid_segments):
# # #         seg['speaker'] = f"SPEAKER_{speaker_labels[i]:02d}"
    
# # #     # Count speakers
# # #     unique_speakers = set(seg['speaker'] for seg in valid_segments)
    
# # #     print(f"✅ Found {len(unique_speakers)} speakers:")
# # #     for speaker in sorted(unique_speakers):
# # #         count = sum(1 for s in valid_segments if s['speaker'] == speaker)
# # #         print(f"   {speaker}: {count} segments")
    
# # #     return segments

# # # def analyze_speaker_characteristics(audio, sr, segments):
# # #     """Analyze gender and age of each speaker"""
    
# # #     print(f"\n🔍 Analyzing speaker characteristics...")
    
# # #     speaker_profiles = {}
    
# # #     for seg in segments:
# # #         speaker = seg.get('speaker', 'SPEAKER_00')
        
# # #         if speaker not in speaker_profiles:
# # #             # Get audio for this segment
# # #             start_sample = int(seg['start'] * sr)
# # #             end_sample = int(seg['end'] * sr)
# # #             audio_segment = audio[start_sample:end_sample]
            
# # #             if len(audio_segment) < sr * 0.3:
# # #                 continue
            
# # #             # Extract pitch for gender estimation
# # #             pitches, magnitudes = librosa.piptrack(y=audio_segment, sr=sr)
# # #             valid_pitches = pitches[pitches > 0]
            
# # #             if len(valid_pitches) > 0:
# # #                 mean_pitch = np.mean(valid_pitches)
                
# # #                 # Simple gender classification based on pitch
# # #                 # Male: typically 85-180 Hz
# # #                 # Female: typically 165-255 Hz
# # #                 if mean_pitch < 140:
# # #                     gender = "male"
# # #                     age_group = "adult"
# # #                 elif mean_pitch > 200:
# # #                     gender = "female"
# # #                     age_group = "teen/adult"
# # #                 else:
# # #                     gender = "ambiguous"
# # #                     age_group = "adult"
                
# # #                 speaker_profiles[speaker] = {
# # #                     "gender": gender,
# # #                     "age_group": age_group,
# # #                     "mean_pitch_hz": float(mean_pitch)
# # #                 }
# # #             else:
# # #                 speaker_profiles[speaker] = {
# # #                     "gender": "unknown",
# # #                     "age_group": "adult",
# # #                     "mean_pitch_hz": 0.0
# # #                 }
    
# # #     print(f"📊 Speaker profiles:")
# # #     for speaker, profile in speaker_profiles.items():
# # #         print(f"   {speaker}: {profile['gender']}, {profile['age_group']}, pitch={profile['mean_pitch_hz']:.1f}Hz")
    
# # #     return speaker_profiles

# # # def save_results(data, speaker_profiles):
# # #     """Save combined data to JSON"""
    
# # #     # Add speaker metadata
# # #     data['diarization'] = {
# # #         'timestamp': datetime.now().isoformat(),
# # #         'method': 'simple_clustering',
# # #         'total_speakers': len(speaker_profiles),
# # #         'speaker_profiles': speaker_profiles
# # #     }
    
# # #     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
# # #         json.dump(data, f, ensure_ascii=False, indent=2)
    
# # #     print(f"\n💾 Saved to: {OUTPUT_JSON}")

# # # def display_preview(data):
# # #     """Display preview with speakers"""
    
# # #     print("\n" + "="*60)
# # #     print("📋 PREVIEW (All segments with speakers)")
# # #     print("="*60)
    
# # #     for seg in data['segments']:
# # #         speaker = seg.get('speaker', 'UNKNOWN')
# # #         print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] {speaker}")
# # #         print(f"  {seg['text']}")

# # # def main():
# # #     print("=" * 60)
# # #     print("STEP 3: Simple Speaker Diarization")
# # #     print("=" * 60)
    
# # #     # Check prerequisites
# # #     if not os.path.exists(AUDIO_FILE):
# # #         print(f"❌ Audio file not found: {AUDIO_FILE}")
# # #         return
    
# # #     if not os.path.exists(TRANSCRIPTION_FILE):
# # #         print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
# # #         return
    
# # #     # Load transcription
# # #     transcription_data = load_transcription()
    
# # #     # Load audio
# # #     print("🎵 Loading audio...")
# # #     audio, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
# # #     # Run simple diarization
# # #     segments = simple_speaker_diarization(
# # #         audio, 
# # #         sr, 
# # #         transcription_data['segments']
# # #     )
    
# # #     # Analyze speaker characteristics
# # #     speaker_profiles = analyze_speaker_characteristics(
# # #         audio, 
# # #         sr, 
# # #         segments
# # #     )
    
# # #     # Save results
# # #     save_results(transcription_data, speaker_profiles)
    
# # #     # Display preview
# # #     display_preview(transcription_data)
    
# # #     print("\n" + "=" * 60)
# # #     print("✅ Step 3 Complete!")
# # #     print("=" * 60)
# # #     print(f"📁 Output: {OUTPUT_JSON}")
# # #     print(f"👥 Total speakers: {len(speaker_profiles)}")
# # #     print(f"📝 Total segments: {len(transcription_data['segments'])}")
# # #     print("\nNext: Continue with translation (Step 4)")

# # # if __name__ == "__main__":
# # #     main()
# step3_diarization.py (Enhanced with Wav2Vec2 Age/Gender Model)
import torch
import json
import os
import librosa
import numpy as np
from pyannote.audio import Pipeline
from transformers import Wav2Vec2Processor
from transformers.models.wav2vec2.modeling_wav2vec2 import (
    Wav2Vec2Model,
    Wav2Vec2PreTrainedModel,
)
import torch.nn as nn
from datetime import datetime

# Configuration
AUDIO_FILE = "separated/htdemucs/audio_16k/vocals.wav"
TRANSCRIPTION_FILE = "work/transcription.json"
OUTPUT_JSON = "work/transcription_with_speakers.json"

# HuggingFace token
HF_TOKEN = "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"

# Age/Gender model
AGE_GENDER_MODEL = "audeering/wav2vec2-large-robust-24-ft-age-gender"


# ============================================================
# Age/Gender Model Classes (from HuggingFace)
# ============================================================

class ModelHead(nn.Module):
    """Classification head."""
    def __init__(self, config, num_labels):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, num_labels)

    def forward(self, features, **kwargs):
        x = features
        x = self.dropout(x)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class AgeGenderModel(Wav2Vec2PreTrainedModel):
    """Speech age/gender classifier."""
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.wav2vec2 = Wav2Vec2Model(config)
        self.age = ModelHead(config, 1)
        self.gender = ModelHead(config, 3)
        self.init_weights()

    def forward(self, input_values):
        outputs = self.wav2vec2(input_values)
        hidden_states = outputs[0]
        hidden_states = torch.mean(hidden_states, dim=1)
        logits_age = self.age(hidden_states)
        logits_gender = torch.softmax(self.gender(hidden_states), dim=1)
        return hidden_states, logits_age, logits_gender


# ============================================================
# Main Functions
# ============================================================

def check_prerequisites():
    """Check if required files exist"""
    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Audio file not found: {AUDIO_FILE}")
        print("   Please run step1_extract_audio.py first")
        return False
    
    if not os.path.exists(TRANSCRIPTION_FILE):
        print(f"❌ Transcription file not found: {TRANSCRIPTION_FILE}")
        print("   Please run step2_transcribe.py first")
        return False
    
    if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
        print("❌ HuggingFace token not set!")
        print("\n📝 To get your token:")
        print("   1. Go to: https://huggingface.co/settings/tokens")
        print("   2. Click 'New token'")
        print("   3. Copy the token")
        print("   4. Paste it in step3_diarization.py (HF_TOKEN variable)")
        print("\n📝 Also accept the terms:")
        print("   5. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("   6. Click 'Accept' on the user conditions")
        return False
    
    return True


def load_transcription():
    """Load transcription from JSON"""
    with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {data['total_segments']} transcription segments")
    return data


def load_audio_for_pyannote():
    """Load audio as dictionary for pyannote"""
    print("   Loading audio with librosa (TorchCodec workaround)...")
    
    # Load audio
    waveform, sample_rate = librosa.load(AUDIO_FILE, sr=16000, mono=True)
    
    # Convert to torch tensor and add channel dimension
    waveform_tensor = torch.from_numpy(waveform).unsqueeze(0)  # Shape: (1, samples)
    
    # Create audio dictionary that pyannote can use
    audio = {
        "waveform": waveform_tensor,
        "sample_rate": sample_rate
    }
    
    return audio, waveform, sample_rate


def run_diarization(audio):
    """Run speaker diarization on audio"""
    
    print(f"\n🎤 Running speaker diarization...")
    print("⏳ This may take 5-10 minutes...")
    
    try:
        # Check GPU
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"   Device: {device}")
        
        # Load diarization pipeline
        print("   Loading pyannote model...")
        # pipeline = Pipeline.from_pretrained(
        #     "pyannote/speaker-diarization-3.1",
        #     use_auth_token=HF_TOKEN
        # )
        # pipeline = pipeline.to(device)
        # In pipeline config (before running)
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=HF_TOKEN
        )
        pipeline.segmentation_batch_size = 32  # More sensitive
        pipeline.embedding_batch_size = 32
        pipeline = pipeline.to(device)
        print(f"   Processing audio...")
        
        # Run diarization on audio dictionary
        # diarization = pipeline(audio)
        diarization = pipeline(AUDIO_FILE)

# FIXED (force more speakers)
        diarization = pipeline(
            AUDIO_FILE,
            min_speakers=3,        # At least 3 speakers
            max_speakers=7, )      # Up to 7 (for anime cast)
        
        print("✅ Diarization complete!")
        
        return diarization
    
    except Exception as e:
        print(f"❌ Diarization error: {e}")
        print("\n💡 Common issues:")
        print("   - Make sure you accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("   - Check your HuggingFace token is valid")
        print("   - Try: pip install --upgrade pyannote.audio")
        import traceback
        traceback.print_exc()
        return None


def extract_speaker_segments(diarization):
    """Extract speaker segments from diarization result"""
    
    speaker_segments = []
    speakers_found = set()
    annotation = diarization.speaker_diarization

    for segment, _, speaker in annotation.itertracks(yield_label=True):
    # for segment, _, speaker in diarization.itertracks(yield_label=True):
        speaker_segments.append({
            'speaker': speaker,
            'start': segment.start,
            'end': segment.end,
            'duration': segment.end - segment.start
        })
        speakers_found.add(speaker)
    
    print(f"\n👥 Found {len(speakers_found)} unique speakers:")
    for speaker in sorted(speakers_found):
        count = sum(1 for s in speaker_segments if s['speaker'] == speaker)
        total_time = sum(s['duration'] for s in speaker_segments if s['speaker'] == speaker)
        print(f"   {speaker}: {count} segments, {total_time:.1f}s total")
    
    return speaker_segments, speakers_found


def load_age_gender_model():
    """Load Wav2Vec2 age/gender model"""
    
    print(f"\n🧠 Loading age/gender detection model...")
    
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        processor = Wav2Vec2Processor.from_pretrained(AGE_GENDER_MODEL)
        model = AgeGenderModel.from_pretrained(AGE_GENDER_MODEL)
        model = model.to(device)
        model.eval()
        
        print(f"✅ Age/gender model loaded on {device}")
        
        return processor, model, device
    
    except Exception as e:
        print(f"⚠️  Could not load age/gender model: {e}")
        print("   Will use fallback method (pitch-based)")
        return None, None, None


def analyze_speaker_age_gender(audio_waveform, sample_rate, speaker_segments, processor, model, device):
    """Analyze age and gender for each speaker using Wav2Vec2 model"""
    
    print(f"\n🔍 Analyzing speaker age and gender...")
    
    speaker_profiles = {}
    
    for speaker in set(s['speaker'] for s in speaker_segments):
        # Get all segments for this speaker
        speaker_segs = [s for s in speaker_segments if s['speaker'] == speaker]
        
        # Use the longest segment for analysis (more reliable)
        longest_seg = max(speaker_segs, key=lambda x: x['duration'])
        
        start_sample = int(longest_seg['start'] * sample_rate)
        end_sample = int(longest_seg['end'] * sample_rate)
        
        audio_segment = audio_waveform[start_sample:end_sample]
        
        # Skip if too short
        if len(audio_segment) < sample_rate * 0.5:
            print(f"   ⚠️  {speaker}: Segment too short, skipping")
            speaker_profiles[speaker] = {
                'gender': 'unknown',
                'age_group': 'adult',
                'age_estimate': 30.0,
                'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
            }
            continue
        
        try:
            if processor is not None and model is not None:
                # Use Wav2Vec2 model
                result = predict_age_gender_wav2vec(
                    audio_segment, 
                    sample_rate, 
                    processor, 
                    model, 
                    device
                )
            else:
                # Fallback to pitch-based method
                result = predict_age_gender_fallback(audio_segment, sample_rate)
            
            speaker_profiles[speaker] = result
            
            print(f"   {speaker}: {result['gender']}, age ~{result['age_estimate']:.0f} ({result['age_group']})")
            print(f"      Gender probs - Female: {result['gender_probabilities']['female']:.2f}, "
                  f"Male: {result['gender_probabilities']['male']:.2f}, "
                  f"Child: {result['gender_probabilities']['child']:.2f}")
        
        except Exception as e:
            print(f"   ⚠️  {speaker}: Error analyzing - {e}")
            speaker_profiles[speaker] = {
                'gender': 'unknown',
                'age_group': 'adult',
                'age_estimate': 30.0,
                'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
            }
    
    return speaker_profiles


def predict_age_gender_wav2vec(audio, sample_rate, processor, model, device):
    """Predict age/gender using Wav2Vec2 model"""
    
    # Process audio
    inputs = processor(audio, sampling_rate=sample_rate, return_tensors="pt", padding=True)
    input_values = inputs.input_values[0].reshape(1, -1)
    input_values = input_values.to(device)
    
    # Run model
    with torch.no_grad():
        hidden_states, logits_age, logits_gender = model(input_values)
    
    # Extract predictions
    age_prediction = logits_age.detach().cpu().numpy()[0][0]
    gender_probs = logits_gender.detach().cpu().numpy()[0]
    
    # Convert age (0-1 range to 0-100 years)
    age_estimate = age_prediction * 100
    
    # Gender probabilities: [female, male, child]
    gender_dict = {
        'female': float(gender_probs[0]),
        'male': float(gender_probs[1]),
        'child': float(gender_probs[2])
    }
    
    # Determine gender (highest probability)
    if gender_dict['child'] > 0.5:
        gender = 'child'
        age_group = 'child'
    elif gender_dict['female'] > gender_dict['male']:
        gender = 'female'
        age_group = determine_age_group(age_estimate)
    else:
        gender = 'male'
        age_group = determine_age_group(age_estimate)
    
    return {
        'gender': gender,
        'age_group': age_group,
        'age_estimate': float(age_estimate),
        'gender_probabilities': gender_dict
    }


def predict_age_gender_fallback(audio, sample_rate):
    """Fallback: Simple pitch-based gender detection"""
    
    import librosa
    
    # Extract pitch
    pitches, magnitudes = librosa.piptrack(y=audio, sr=sample_rate)
    valid_pitches = pitches[pitches > 0]
    
    if len(valid_pitches) > 0:
        mean_pitch = np.mean(valid_pitches)
        
        # Simple gender classification based on pitch
        if mean_pitch < 140:
            gender = "male"
            age_estimate = 35.0
        elif mean_pitch > 200:
            gender = "female"
            age_estimate = 30.0
        else:
            gender = "ambiguous"
            age_estimate = 32.0
        
        age_group = determine_age_group(age_estimate)
        
        return {
            'gender': gender,
            'age_group': age_group,
            'age_estimate': age_estimate,
            'gender_probabilities': {
                'female': 0.5 if gender == 'female' else 0.3,
                'male': 0.5 if gender == 'male' else 0.3,
                'child': 0.2
            }
        }
    else:
        return {
            'gender': 'unknown',
            'age_group': 'adult',
            'age_estimate': 30.0,
            'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
        }


def determine_age_group(age):
    """Determine age group from age estimate"""
    if age < 13:
        return 'child'
    elif age < 20:
        return 'teen'
    elif age < 40:
        return 'young_adult'
    elif age < 60:
        return 'adult'
    else:
        return 'senior'


def assign_speakers_to_transcription(transcription_data, speaker_segments):
    """Match speaker segments with transcription segments"""
    
    print(f"\n🔗 Matching speakers with transcription...")
    
    segments = transcription_data['segments']
    
    for trans_seg in segments:
        trans_start = trans_seg['start']
        trans_end = trans_seg['end']
        trans_mid = trans_start + (trans_seg['duration'] / 2)
        
        # Find which speaker segment this transcription belongs to
        assigned_speaker = None
        best_overlap = 0.3
        
        for spk_seg in speaker_segments:
            if spk_seg['start'] <= trans_mid <= spk_seg['end']:
                overlap = min(trans_end, spk_seg['end']) - max(trans_start, spk_seg['start'])
                if overlap > best_overlap:
                    best_overlap = overlap
                    assigned_speaker = spk_seg['speaker']
        
        trans_seg['speaker'] = assigned_speaker if assigned_speaker else "UNKNOWN"
    
    # Count assignments
    assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
    print(f"✅ Assigned speakers to {assigned}/{len(segments)} segments")
    
    if assigned < len(segments):
        unknown = len(segments) - assigned
        print(f"⚠️  {unknown} segments without clear speaker assignment")
    
    return transcription_data


def save_results(data, speaker_segments, speaker_profiles):
    """Save combined data to JSON"""
    
    data['diarization'] = {
        'timestamp': datetime.now().isoformat(),
        'method': 'pyannote + wav2vec2',
        'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
        'speaker_list': sorted(set(s['speaker'] for s in speaker_segments)),
        'speaker_profiles': speaker_profiles
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to: {OUTPUT_JSON}")


def display_preview(data):
    """Display preview with speakers"""
    
    print("\n" + "="*60)
    print("📋 PREVIEW (First 5 segments with speakers)")
    print("="*60)
    
    for seg in data['segments'][:5]:
        speaker = seg.get('speaker', 'UNKNOWN')
        
        # Get speaker profile if available
        profiles = data.get('diarization', {}).get('speaker_profiles', {})
        profile = profiles.get(speaker, {})
        
        gender = profile.get('gender', 'unknown')
        age = profile.get('age_estimate', 0)
        
        print(f"\n[{seg['start']:.2f}s - {seg['end']:.2f}s] {speaker} ({gender}, ~{age:.0f}yo)")
        print(f"  {seg['text']}")
    
    if len(data['segments']) > 5:
        print(f"\n... and {len(data['segments']) - 5} more segments")


def main():
    print("=" * 60)
    print("STEP 3: Speaker Diarization + Age/Gender Detection")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Load transcription
    transcription_data = load_transcription()
    
    # Load audio
    audio_dict, audio_waveform, sample_rate = load_audio_for_pyannote()
    
    # Run diarization
    diarization = run_diarization(audio_dict)
    if diarization is None:
        return
    
    # Extract speaker segments
    speaker_segments, speakers_found = extract_speaker_segments(diarization)
    
    # Load age/gender model
    processor, model, device = load_age_gender_model()
    
    # Analyze age/gender for each speaker
    speaker_profiles = analyze_speaker_age_gender(
        audio_waveform,
        sample_rate,
        speaker_segments,
        processor,
        model,
        device
    )
    
    # Assign speakers to transcription
    transcription_data = assign_speakers_to_transcription(
        transcription_data,
        speaker_segments
    )
    
    # Save results
    save_results(transcription_data, speaker_segments, speaker_profiles)
    
    # Display preview
    display_preview(transcription_data)
    
    print("\n" + "=" * 60)
    print("✅ Step 3 Complete!")
    print("=" * 60)
    print(f"📁 Output: {OUTPUT_JSON}")
    print(f"👥 Total speakers: {len(speakers_found)}")
    print(f"📝 Total segments: {len(transcription_data['segments'])}")
    print("\nNext: Run step4_translation_free.py")


if __name__ == "__main__":
    main()
# step3_diarization.py - FULLY UPDATED WITH SPEAKER AUDIO EXTRACTION
# 🎯 Perfect for OpenVoice voice cloning (2-3min reference clips per speaker)
# Date: Feb 03, 2026

# import torch
# import json
# import os
# import librosa
# import numpy as np
# import soundfile as sf  # pip install soundfile
# from pyannote.audio import Pipeline
# from transformers import Wav2Vec2Processor
# from transformers.models.wav2vec2.modeling_wav2vec2 import (
#     Wav2Vec2Model,
#     Wav2Vec2PreTrainedModel,
# )
# import torch.nn as nn
# from datetime import datetime
# import warnings
# warnings.filterwarnings("ignore")

# # ═══════════════════════════════════════════════════════════════════════════════════════
# # CONFIGURATION
# # ═══════════════════════════════════════════════════════════════════════════════════════
# AUDIO_FILE = "work/audio_16k.wav"
# TRANSCRIPTION_FILE = "work/transcription.json"
# OUTPUT_JSON = "work/transcription_with_speakers.json"
# SPEAKER_AUDIO_DIR = "work/speaker_segments"  # 🆕 Individual speaker clips for OpenVoice

# HF_TOKEN = "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"
# AGE_GENDER_MODEL = "audeering/wav2vec2-large-robust-24-ft-age-gender"

# # ═══════════════════════════════════════════════════════════════════════════════════════
# # AGE/GENDER MODEL CLASSES (UNCHANGED)
# # ═══════════════════════════════════════════════════════════════════════════════════════
# class ModelHead(nn.Module):
#     """Classification head."""
#     def __init__(self, config, num_labels):
#         super().__init__()
#         self.dense = nn.Linear(config.hidden_size, config.hidden_size)
#         self.dropout = nn.Dropout(config.final_dropout)
#         self.out_proj = nn.Linear(config.hidden_size, num_labels)

#     def forward(self, features, **kwargs):
#         x = features
#         x = self.dropout(x)
#         x = self.dense(x)
#         x = torch.tanh(x)
#         x = self.dropout(x)
#         x = self.out_proj(x)
#         return x

# class AgeGenderModel(Wav2Vec2PreTrainedModel):
#     """Speech age/gender classifier."""
#     def __init__(self, config):
#         super().__init__(config)
#         self.config = config
#         self.wav2vec2 = Wav2Vec2Model(config)
#         self.age = ModelHead(config, 1)
#         self.gender = ModelHead(config, 3)
#         self.init_weights()

#     def forward(self, input_values):
#         outputs = self.wav2vec2(input_values)
#         hidden_states = outputs[0]
#         hidden_states = torch.mean(hidden_states, dim=1)
#         logits_age = self.age(hidden_states)
#         logits_gender = torch.softmax(self.gender(hidden_states), dim=1)
#         return hidden_states, logits_age, logits_gender

# # ═══════════════════════════════════════════════════════════════════════════════════════
# # MAIN FUNCTIONS
# # ═══════════════════════════════════════════════════════════════════════════════════════
# def check_prerequisites():
#     """Check prerequisites and create directories"""
#     if not os.path.exists(AUDIO_FILE):
#         print(f"❌ {AUDIO_FILE} not found! Run step1_extract_audio.py first")
#         return False
    
#     if not os.path.exists(TRANSCRIPTION_FILE):
#         print(f"❌ {TRANSCRIPTION_FILE} not found! Run step2_transcribe.py first")
#         return False
    
#     if HF_TOKEN == "YOUR_HF_TOKEN_HERE":
#         print("❌ Set HF_TOKEN in line 25!")
#         return False
    
#     # 🆕 Create speaker segments directory
#     os.makedirs(SPEAKER_AUDIO_DIR, exist_ok=True)
#     print(f"✅ Created: {SPEAKER_AUDIO_DIR}/")
    
#     return True

# def load_transcription():
#     """Load transcription JSON"""
#     with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     print(f"📄 Loaded {data['total_segments']} segments")
#     return data

# def load_audio():
#     """Load audio for processing"""
#     print("🔊 Loading audio...")
#     waveform, sr = librosa.load(AUDIO_FILE, sr=16000, mono=True)
#     print(f"   Duration: {len(waveform)/sr:.1f}s, Sample rate: {sr}Hz")
#     return {
#         "waveform": torch.from_numpy(waveform).unsqueeze(0),
#         "sample_rate": sr
#     }, waveform, sr

# # 🆕 NEW FUNCTION: EXTRACT SPEAKER AUDIO SEGMENTS
# def extract_speaker_audio_segments(diarization, audio_waveform, sample_rate):
#     """🆕 Extract & save audio segments PER SPEAKER for OpenVoice cloning"""
#     print(f"\n💾 Extracting speaker audio segments...")
#     print(f"📁 Saving to: {SPEAKER_AUDIO_DIR}/")
    
#     speaker_segments = []
#     speakers_found = set()
#     speaker_audio = {}  # speaker → list of audio segments
    
#     # Extract all speaker segments
#     for segment, _, speaker in diarization.itertracks(yield_label=True):
#         speakers_found.add(speaker)
#         speaker_segments.append({
#             'speaker': speaker,
#             'start': segment.start,
#             'end': segment.end,
#             'duration': segment.end - segment.start
#         })
        
#         # Extract audio segment (skip very short ones)
#         if segment.duration > 0.3:
#             start_sample = int(segment.start * sample_rate)
#             end_sample = int(segment.end * sample_rate)
#             audio_seg = audio_waveform[start_sample:end_sample]
            
#             if speaker not in speaker_audio:
#                 speaker_audio[speaker] = []
#             speaker_audio[speaker].append({
#                 'audio': audio_seg,
#                 'start': segment.start,
#                 'end': segment.end,
#                 'duration': segment.duration
#             })
    
#     # 🆕 SAVE INDIVIDUAL SEGMENTS + COMBINED REFERENCE CLIPS
#     reference_clips = {}
#     for speaker, segments in speaker_audio.items():
#         total_duration = sum(s['duration'] for s in segments)
#         print(f"\n👤 {speaker}: {len(segments)} segments ({total_duration:.1f}s total)")
        
#         # Save individual segments
#         for i, seg in enumerate(segments):
#             filename = f"{speaker}_seg_{i+1:03d}_{seg['start']:.1f}s.wav"
#             filepath = os.path.join(SPEAKER_AUDIO_DIR, filename)
#             sf.write(filepath, seg['audio'], sample_rate)
#             print(f"   📄 {filename}")
        
#         # 🆕 CREATE REFERENCE CLIP (combine all segments for OpenVoice)
#         if total_duration > 10:  # Need at least 10s for good cloning
#             combined_audio = np.concatenate([s['audio'] for s in segments])
#             ref_filename = f"{speaker}_REFERENCE_{total_duration:.0f}s.wav"
#             ref_path = os.path.join(SPEAKER_AUDIO_DIR, ref_filename)
#             sf.write(ref_path, combined_audio, sample_rate)
            
#             reference_clips[speaker] = {
#                 'reference_file': ref_path,
#                 'total_duration': float(total_duration),
#                 'segment_count': len(segments),
#                 'quality': 'excellent' if total_duration > 120 else 'good' if total_duration > 30 else 'short'
#             }
#             print(f"   🎯 REFERENCE: {ref_filename} ← OpenVoice Ready!")
#         else:
#             print(f"   ⚠️  {speaker}: Too short for cloning ({total_duration:.1f}s)")
    
#     print(f"\n🎉 {len(reference_clips)} reference clips ready for OpenVoice!")
#     return speaker_segments, speakers_found, reference_clips

# def run_diarization(audio):
#     """Run pyannote speaker diarization"""
#     print("\n🎤 Running speaker diarization...")
#     print("⏳ ~5-10 minutes...")
    
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(f"   Device: {device}")
    
#     pipeline = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization-3.1",
#         use_auth_token=HF_TOKEN
#     )
#     pipeline = pipeline.to(device)
    
#     diarization = pipeline(audio)
#     print("✅ Diarization complete!")
#     return diarization

# def load_age_gender_model():
#     """Load age/gender detection model"""
#     print("\n🧠 Loading age/gender model...")
#     try:
#         device = 'cuda' if torch.cuda.is_available() else 'cpu'
#         processor = Wav2Vec2Processor.from_pretrained(AGE_GENDER_MODEL)
#         model = AgeGenderModel.from_pretrained(AGE_GENDER_MODEL)
#         model = model.to(device)
#         model.eval()
#         print(f"✅ Age/gender model on {device}")
#         return processor, model, device
#     except Exception as e:
#         print(f"⚠️  Age/gender model failed: {e}")
#         print("   Using pitch-based fallback")
#         return None, None, None

# def analyze_speaker_age_gender(audio_waveform, sample_rate, speaker_segments, processor, model, device):
#     """Analyze age/gender for each speaker (UNCHANGED)"""
#     print("\n🔍 Analyzing speaker age/gender...")
#     speaker_profiles = {}
    
#     for speaker in set(s['speaker'] for s in speaker_segments):
#         speaker_segs = [s for s in speaker_segments if s['speaker'] == speaker]
#         longest_seg = max(speaker_segs, key=lambda x: x['duration'])
        
#         start_sample = int(longest_seg['start'] * sample_rate)
#         end_sample = int(longest_seg['end'] * sample_rate)
#         audio_segment = audio_waveform[start_sample:end_sample]
        
#         if len(audio_segment) < sample_rate * 0.5:
#             speaker_profiles[speaker] = {
#                 'gender': 'unknown', 'age_group': 'adult',
#                 'age_estimate': 30.0,
#                 'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
#             }
#             continue
        
#         try:
#             if processor and model:
#                 result = predict_age_gender_wav2vec(audio_segment, sample_rate, processor, model, device)
#             else:
#                 result = predict_age_gender_fallback(audio_segment, sample_rate)
            
#             speaker_profiles[speaker] = result
#             print(f"   {speaker}: {result['gender']}, ~{result['age_estimate']:.0f}yo ({result['age_group']})")
#         except:
#             speaker_profiles[speaker] = {
#                 'gender': 'unknown', 'age_group': 'adult',
#                 'age_estimate': 30.0,
#                 'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
#             }
    
#     return speaker_profiles

# # Helper functions (unchanged - keeping your original logic)
# def predict_age_gender_wav2vec(audio, sample_rate, processor, model, device):
#     inputs = processor(audio, sampling_rate=sample_rate, return_tensors="pt", padding=True)
#     input_values = inputs.input_values.to(device)
    
#     with torch.no_grad():
#         _, logits_age, logits_gender = model(input_values)
    
#     age = logits_age.detach().cpu().numpy()[0][0] * 100
#     gender_probs = logits_gender.detach().cpu().numpy()[0]
    
#     gender_dict = {'female': float(gender_probs[0]), 'male': float(gender_probs[1]), 'child': float(gender_probs[2])}
    
#     if gender_dict['child'] > 0.5:
#         gender, age_group = 'child', 'child'
#     elif gender_dict['female'] > gender_dict['male']:
#         gender, age_group = 'female', determine_age_group(age)
#     else:
#         gender, age_group = 'male', determine_age_group(age)
    
#     return {'gender': gender, 'age_group': age_group, 'age_estimate': float(age), 'gender_probabilities': gender_dict}

# def predict_age_gender_fallback(audio, sample_rate):
#     pitches, _ = librosa.piptrack(y=audio, sr=sample_rate)
#     valid_pitches = pitches[pitches > 0]
    
#     if len(valid_pitches) > 0:
#         mean_pitch = np.mean(valid_pitches)
#         gender = "male" if mean_pitch < 140 else "female" if mean_pitch > 200 else "ambiguous"
#         age = 35.0 if gender == "male" else 30.0
#     else:
#         gender, age = 'unknown', 30.0
    
#     return {
#         'gender': gender, 'age_group': determine_age_group(age),
#         'age_estimate': age,
#         'gender_probabilities': {'female': 0.33, 'male': 0.33, 'child': 0.33}
#     }

# def determine_age_group(age):
#     if age < 13: return 'child'
#     elif age < 20: return 'teen'
#     elif age < 40: return 'young_adult'
#     elif age < 60: return 'adult'
#     return 'senior'

# def assign_speakers_to_transcription(transcription_data, speaker_segments):
#     """Match speakers to transcription segments"""
#     print("\n🔗 Matching speakers to transcription...")
    
#     segments = transcription_data['segments']
#     for trans_seg in segments:
#         trans_mid = trans_seg['start'] + (trans_seg['duration'] / 2)
        
#         best_speaker = None
#         best_overlap = 0
        
#         for spk_seg in speaker_segments:
#             if spk_seg['start'] <= trans_mid <= spk_seg['end']:
#                 overlap = min(trans_seg['end'], spk_seg['end']) - max(trans_seg['start'], spk_seg['start'])
#                 if overlap > best_overlap:
#                     best_overlap = overlap
#                     best_speaker = spk_seg['speaker']
        
#         trans_seg['speaker'] = best_speaker or "UNKNOWN"
    
#     assigned = sum(1 for s in segments if s['speaker'] != "UNKNOWN")
#     print(f"✅ {assigned}/{len(segments)} segments assigned")
#     return transcription_data

# def save_results(data, speaker_segments, speaker_profiles, reference_clips):
#     """Save all results"""
#     data['diarization'] = {
#         'timestamp': datetime.now().isoformat(),
#         'method': 'pyannote-3.1 + wav2vec2-age-gender',
#         'total_speakers': len(set(s['speaker'] for s in speaker_segments)),
#         'speaker_list': sorted(set(s['speaker'] for s in speaker_segments)),
#         'speaker_profiles': speaker_profiles,
#         'reference_clips': reference_clips  # 🆕 OpenVoice reference files
#     }
    
#     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)
#     print(f"💾 Saved: {OUTPUT_JSON}")

# def display_results(data, reference_clips):
#     """Show final results"""
#     print("\n" + "="*70)
#     print("🎉 SPEAKER DIARIZATION + VOICE CLONING READY!")
#     print("="*70)
    
#     # Preview segments
#     print("\n📋 FIRST 5 SEGMENTS:")
#     for seg in data['segments'][:5]:
#         profile = data['diarization']['speaker_profiles'].get(seg['speaker'], {})
#         print(f"[{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['speaker']} "
#               f"({profile.get('gender','?')}, {profile.get('age_group','?')})")
#         print(f"   {seg['text'][:80]}...")
    
#     # 🆕 Show OpenVoice ready clips
#     print(f"\n🎯 OPENVOICE REFERENCE CLIPS ({len(reference_clips)}):")
#     for speaker, info in reference_clips.items():
#         quality = "🟢 EXCELLENT" if info['quality'] == 'excellent' else "🟡 GOOD" if info['quality'] == 'good' else "🔴 SHORT"
#         print(f"   {speaker}: {os.path.basename(info['reference_file'])} "
#               f"({info['total_duration']:.0f}s) {quality}")

# def main():
#     print("="*70)
#     print("🚀 STEP 3: Speaker Diarization + Age/Gender + OpenVoice Prep")
#     print("="*70)
    
#     if not check_prerequisites():
#         return
    
#     # Load data
#     transcription_data = load_transcription()
#     audio_dict, audio_waveform, sample_rate = load_audio()
    
#     # Run diarization
#     diarization = run_diarization(audio_dict)
#     if not diarization:
#         return
    
#     # 🆕 Extract speaker segments AND SAVE AUDIO
#     speaker_segments, speakers_found, reference_clips = extract_speaker_audio_segments(
#         diarization, audio_waveform, sample_rate
#     )
    
#     # Age/gender analysis
#     processor, model, device = load_age_gender_model()
#     speaker_profiles = analyze_speaker_age_gender(
#         audio_waveform, sample_rate, speaker_segments, processor, model, device
#     )
    
#     # Match to transcription
#     transcription_data = assign_speakers_to_transcription(transcription_data, speaker_segments)
    
#     # Save everything
#     save_results(transcription_data, speaker_segments, speaker_profiles, reference_clips)
    
#     # Show results
#     display_results(transcription_data, reference_clips)
    
#     print("\n" + "="*70)
#     print("✅ STEP 3 COMPLETE!")
#     print(f"📁 Audio segments: {SPEAKER_AUDIO_DIR}/")
#     print("🎯 Next: Use reference clips with OpenVoice for voice cloning!")
#     print("🚀 Then: python step4_translation.py")

# if __name__ == "__main__":
#     main()
