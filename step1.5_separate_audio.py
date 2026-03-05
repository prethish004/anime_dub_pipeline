# import os
# import subprocess
# import librosa
# import soundfile as sf

# # -----------------------------
# # INPUT FILE
# # -----------------------------
# input_path = "work/audio_16k.wav"

# # Make sure file exists
# if not os.path.exists(input_path):
#     raise FileNotFoundError(f"File not found: {input_path}")

# print("🎧 Starting separation...")

# # -----------------------------
# # RUN DEMUCS
# # -----------------------------
# subprocess.run([
#     "demucs",
#     "-n", "htdemucs",
#     input_path
# ])

# print("✅ Separation complete!")

# # -----------------------------
# # OUTPUT PATHS
# # -----------------------------
# file_name = os.path.splitext(os.path.basename(input_path))[0]
# base_output = f"separated/htdemucs/{file_name}/"

# vocals_path = os.path.join(base_output, "vocals.wav")
# drums_path = os.path.join(base_output, "drums.wav")
# bass_path = os.path.join(base_output, "bass.wav")
# other_path = os.path.join(base_output, "other.wav")

# # -----------------------------
# # MERGE BACKGROUND SOUNDS
# # -----------------------------
# print("🔊 Merging background noise...")

# vocals, sr = librosa.load(vocals_path, sr=None)
# drums, _ = librosa.load(drums_path, sr=None)
# bass, _ = librosa.load(bass_path, sr=None)
# other, _ = librosa.load(other_path, sr=None)

# background = drums + bass + other

# sf.write("background_noise.wav", background, sr)

# print("💾 Saved:")
# print("   - Vocals: ", vocals_path)
# print("   - Background: background_noise.wav")

# print("🚀 Done!")
