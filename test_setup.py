# test_setup.py
import torch
import transformers
import librosa
import ffmpeg
from pydub import AudioSegment

print("✅ Testing setup...")

# Check PyTorch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

# Check Transformers
print(f"Transformers version: {transformers.__version__}")

# Check Librosa
print(f"Librosa version: {librosa.__version__}")

print("\n✅ All packages installed successfully!")
import torch
print(f"Torch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")