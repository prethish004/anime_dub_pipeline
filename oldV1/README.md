# 🎬 AI Anime Dubbing Pipeline

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**Automatically dub anime videos from Japanese to English using AI.**  
A complete end-to-end pipeline with speaker detection, age/gender analysis, translation, and AI voice synthesis.

---

## 🌟 Features

- ✅ Automatic audio extraction from anime videos  
- ✅ Japanese speech recognition using Whisper Large V3  
- ✅ Speaker diarization (who speaks when) using PyAnnote  
- ✅ Age & gender detection using Wav2Vec2  
- ✅ Smart Japanese → English translation with timing alignment  
- ✅ High-quality AI voice generation using ElevenLabs  
- ✅ Automatic voice casting based on speaker profile  
- ✅ Final video assembly with synced dubbed audio  
- ✅ Translation accuracy checker against reference subtitles  

---

## 🎥 Overview

**Input:** Japanese anime video  
**Output:** Fully dubbed English anime video with natural voices

```

Original: 痛みを感じろ
↓
Dubbed: "Feel the pain"

````

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg installed
- 8GB+ RAM recommended
- Optional: CUDA-enabled GPU

---

### Installation

```bash
git clone https://github.com/yourusername/anime_dub_pipeline.git
cd anime_dub_pipeline
````

Create virtual environment:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install FFmpeg:

```bash
# Windows
choco install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

Download NLTK data:

```bash
python -c "import nltk; nltk.download('punkt')"
```

---

## 🔑 Required API Keys

### HuggingFace (Free)

* Create token: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
* Accept model terms:

  * pyannote/speaker-diarization-3.1
  * pyannote/speaker-diarization-community-1

### ElevenLabs

* [https://elevenlabs.io](https://elevenlabs.io)
* Free tier: ~10 minutes audio / month

### Ollama (Local, Free)

```bash
ollama pull gemma2:9b
```

---

## 📖 Usage

Run pipeline step-by-step:

```bash
python step1_extract_audio.py
python step2_transcribe.py
python step3_diarization.py
python step4_translation.py
python step5_voice_generation.py
python step6_final_assembly.py
```

Optional accuracy check:

```bash
python check_translation_accuracy.py
```

---

## 📁 Project Structure

```
anime_dub_pipeline/
├── input/                       # Input anime videos
├── work/                        # Intermediate files
├── output/                      # Final dubbed video
├── step1_extract_audio.py
├── step2_transcribe.py
├── step3_diarization.py
├── step4_translation.py
├── step5_voice_generation.py
├── step6_final_assembly.py
├── check_translation_accuracy.py
├── requirements.txt
├── README.md
└── LICENSE
```

---

## ⚙️ Configuration

### API Keys

**step3_diarization.py**

```python
HF_TOKEN = "hf_your_token_here"
```

**step5_voice_generation.py**

```python
ELEVENLABS_API_KEY = "your_key_here"
```

### Voice Mapping

Edit `VOICE_LIBRARY` in `step5_voice_generation.py` to customize voices.

---

## 🧠 How It Works

1. Extract audio from video
2. Transcribe Japanese speech
3. Detect speakers
4. Identify age & gender
5. Translate dialogue
6. Generate AI voices
7. Assemble final dubbed video

---

## 📊 Performance (30s clip)

| Stage         | CPU     | GPU    |
| ------------- | ------- | ------ |
| Transcription | ~30s    | ~10s   |
| Diarization   | ~5 min  | ~2 min |
| Translation   | ~2 min  | ~2 min |
| Voice Gen     | ~3 min  | ~3 min |
| **Total**     | ~11 min | ~8 min |

---

## 🛠️ Troubleshooting

* **FFmpeg not found** → Install FFmpeg
* **CUDA OOM** → Force CPU mode
* **HuggingFace 403** → Accept model terms
* **ElevenLabs quota exceeded** → Upgrade plan or reduce usage
* **Ollama not responding** → Run `ollama serve`

---

## 🚧 Future Enhancements

* Emotion-aware voice synthesis
* Lip-sync support
* Batch episode processing
* Web interface
* Subtitle generation
* Multi-language dubbing
* Voice cloning

---

## 🤝 Contributing

1. Fork the repository
2. Create branch (`feature/new-feature`)
3. Commit changes
4. Push branch
5. Open Pull Request

---

## 📄 License

MIT License – see the [LICENSE](LICENSE) file.

---

## ⚠️ Disclaimer

* For **educational & personal use only**
* Respect copyright laws
* Commercial use may require paid API plans

---

## 🙏 Acknowledgments

* OpenAI Whisper
* PyAnnote Audio
* Audeering Wav2Vec2
* Ollama
* ElevenLabs
* FFmpeg

---

## 💬 Contact

**Prethish GA**
GitHub: [https://github.com/yourusername](https://github.com/yourusername)

---

⭐ If you like this project, please give it a star!

````

---

## ✅ What to do next

```bash
git add README.md
git commit -m "Add detailed project README"
git push
````
<div align="center"> Made with ❤️ by developers who love anime </div> ```