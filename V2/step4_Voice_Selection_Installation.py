# """
# ╔══════════════════════════════════════════════════════════════╗
# ║         STEP 4 SETUP — Voice Selection & Installation        ║
# ║  Run this ONCE before step4_genvoice_complete.py             ║
# ║  Outputs: work/speaker_config.json                           ║
# ╚══════════════════════════════════════════════════════════════╝

# Usage:
#     python step4_setup.py

# What it does:
#     1. Checks + installs all required packages
#     2. Scans sample_voices/ folder
#     3. Interactive terminal — assign voice + age per speaker
#     4. Saves config to work/speaker_config.json
#     5. step4_genvoice_complete.py reads this config automatically
# """

# import sys
# import os
# import json
# import subprocess
# import itertools
# from pathlib import Path

# # ─────────────────────────────────────────────────────────────
# # TERMINAL COLOURS
# # ─────────────────────────────────────────────────────────────
# class C:
#     RESET  = "\033[0m"
#     BOLD   = "\033[1m"
#     DIM    = "\033[2m"
#     GREEN  = "\033[92m"
#     YELLOW = "\033[93m"
#     RED    = "\033[91m"
#     CYAN   = "\033[96m"
#     BLUE   = "\033[94m"
#     PURPLE = "\033[95m"
#     WHITE  = "\033[97m"
#     BG_DARK = "\033[40m"

# def header(text):
#     width = 60
#     print(f"\n{C.CYAN}{'═' * width}{C.RESET}")
#     print(f"{C.BOLD}{C.WHITE}  {text}{C.RESET}")
#     print(f"{C.CYAN}{'═' * width}{C.RESET}\n")

# def success(text): print(f"  {C.GREEN}✅ {text}{C.RESET}")
# def warn(text):    print(f"  {C.YELLOW}⚠️  {text}{C.RESET}")
# def error(text):   print(f"  {C.RED}❌ {text}{C.RESET}")
# def info(text):    print(f"  {C.CYAN}ℹ  {text}{C.RESET}")
# def dim(text):     print(f"  {C.DIM}{text}{C.RESET}")

# def prompt(text, default=None):
#     if default is not None:
#         hint = f"{C.DIM} [{default}]{C.RESET}"
#     else:
#         hint = ""
#     val = input(f"\n  {C.BOLD}{C.WHITE}{text}{hint}{C.RESET}  › ").strip()
#     if not val and default is not None:
#         return default
#     return val

# def numbered_menu(title, options, descriptions=None, default=0):
#     """Show a numbered menu and return the chosen index."""
#     print(f"\n  {C.BOLD}{title}{C.RESET}")
#     print(f"  {C.DIM}{'─' * 40}{C.RESET}")
#     for i, opt in enumerate(options):
#         marker  = f"{C.GREEN}▶{C.RESET}" if i == default else " "
#         desc    = f"  {C.DIM}{descriptions[i]}{C.RESET}" if descriptions else ""
#         default_tag = f"  {C.DIM}(default){C.RESET}" if i == default else ""
#         print(f"  {marker} {C.CYAN}[{i}]{C.RESET} {C.WHITE}{opt}{C.RESET}{desc}{default_tag}")

#     while True:
#         raw = input(f"\n  {C.BOLD}Enter number (0–{len(options)-1}){C.RESET} › ").strip()
#         if raw == "" :
#             return default
#         if raw.isdigit() and 0 <= int(raw) < len(options):
#             return int(raw)
#         warn(f"Please enter a number between 0 and {len(options)-1}")

# # ─────────────────────────────────────────────────────────────
# # PART 1 — INSTALLATION
# # ─────────────────────────────────────────────────────────────
# PACKAGES = [
#     # (pip_name,          import_name,     description)
#     ("TTS",               "TTS",           "Coqui XTTS-v2 voice cloning"),
#     ("pyrubberband",      "pyrubberband",  "High-quality time-stretching"),
#     ("praat-parselmouth", "parselmouth",   "Voice age/type transformation"),
#     ("scipy",             "scipy",         "Audio filters (EQ, breathiness)"),
#     ("soundfile",         "soundfile",     "WAV read/write"),
#     ("librosa",           "librosa",       "Audio analysis + silence trim"),
#     ("matplotlib",        "matplotlib",    "Waveform comparison plots"),
#     ("numpy",             "numpy",         "Array operations"),
#     ("torch",             "torch",         "PyTorch (GPU support)"),
#     ("torchaudio",        "torchaudio",    "Audio I/O for PyTorch"),
#     ("pyphen",            "pyphen",        "Syllable counting"),
# ]

# OPTIONAL_PACKAGES = [
#     ("knnvc",             "knnvc",         "HuggingFace kNN-VC age conversion (optional)"),
# ]

# SYSTEM_DEPS = {
#     "linux":  "sudo apt-get install -y rubberband-cli ffmpeg",
#     "darwin": "brew install rubberband ffmpeg",
#     "win32":  "# Windows: download rubberband from https://breakfastquay.com/rubberband/",
# }


# def check_package(import_name):
#     """Return True if package can be imported."""
#     try:
#         __import__(import_name)
#         return True
#     except ImportError:
#         return False


# def install_package(pip_name):
#     """pip install a package, return success bool."""
#     result = subprocess.run(
#         [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
#         capture_output=True,
#     )
#     return result.returncode == 0


# def run_installation():
#     header("Part 1 — Package Installation")

#     # System dependencies hint
#     platform = sys.platform
#     sys_cmd  = SYSTEM_DEPS.get(platform, SYSTEM_DEPS["linux"])
#     print(f"  {C.BOLD}System dependencies (run manually if not installed):{C.RESET}")
#     print(f"  {C.DIM}{sys_cmd}{C.RESET}\n")

#     # Python packages
#     print(f"  {C.BOLD}Checking Python packages...{C.RESET}\n")
#     all_ok = True
#     for pip_name, import_name, description in PACKAGES:
#         if check_package(import_name):
#             success(f"{pip_name:<25} {C.DIM}{description}{C.RESET}")
#         else:
#             print(f"  {C.YELLOW}⟳  Installing {pip_name:<22} {C.DIM}{description}...{C.RESET}", end="", flush=True)
#             if install_package(pip_name):
#                 print(f"  {C.GREEN}done{C.RESET}")
#             else:
#                 print(f"  {C.RED}FAILED{C.RESET}")
#                 error(f"Could not install {pip_name}. Try manually: pip install {pip_name}")
#                 all_ok = False

#     # Optional packages
#     print(f"\n  {C.BOLD}Optional packages:{C.RESET}\n")
#     for pip_name, import_name, description in OPTIONAL_PACKAGES:
#         if check_package(import_name):
#             success(f"{pip_name:<25} {C.DIM}{description}{C.RESET}")
#         else:
#             warn(f"{pip_name:<25} {C.DIM}not installed — {description}{C.RESET}")
#             ans = input(f"  Install {pip_name}? (y/N) › ").strip().lower()
#             if ans == "y":
#                 print(f"  Installing {pip_name}...", end="", flush=True)
#                 if install_package(pip_name):
#                     print(f"  {C.GREEN}done{C.RESET}")
#                 else:
#                     print(f"  {C.RED}FAILED{C.RESET}")

#     if all_ok:
#         success("All required packages ready")
#     else:
#         error("Some packages failed — fix manually before continuing")
#         sys.exit(1)


# # ─────────────────────────────────────────────────────────────
# # PART 2 — VOICE LIBRARY SCAN
# # ─────────────────────────────────────────────────────────────
# VOICE_SAMPLES_DIR = "sample_voices"

# def scan_voices():
#     """Scan sample_voices/ and return catalogue list."""
#     catalogue = []
#     for vf in itertools.chain(
#         Path(VOICE_SAMPLES_DIR).rglob("*.wav"),
#         Path(VOICE_SAMPLES_DIR).rglob("*.mp3"),
#     ):
#         duration_s = get_audio_duration(str(vf))
#         display    = (vf.stem
#                       .replace("_voice sample", "")
#                       .replace("_", " ")
#                       .strip()
#                       .title())
#         gender     = vf.parent.name.lower()
#         quality    = "ok" if duration_s >= 6 else "too_short"

#         catalogue.append({
#             "display":    display,
#             "path":       str(vf),
#             "gender":     gender,
#             "duration_s": round(duration_s, 1),
#             "quality":    quality,
#             "filename":   vf.name,
#         })

#     # Sort: female first, then male, alphabetically within each
#     catalogue.sort(key=lambda x: (x["gender"] != "female", x["display"]))
#     return catalogue


# def get_audio_duration(path):
#     """Get audio duration in seconds using soundfile, fallback to 0."""
#     try:
#         import soundfile as sf
#         info = sf.info(path)
#         return info.duration
#     except Exception:
#         try:
#             import librosa
#             y, sr = librosa.load(path, sr=None, duration=1)
#             return librosa.get_duration(path=path)
#         except Exception:
#             return 0.0


# def print_voice_catalogue(catalogue):
#     """Print a formatted voice catalogue table."""
#     print(f"\n  {C.BOLD}{'#':<4} {'Name':<32} {'Gender':<10} {'Dur':>6}  {'Quality'}{C.RESET}")
#     print(f"  {C.DIM}{'─' * 60}{C.RESET}")
#     for i, v in enumerate(catalogue):
#         quality_str = (f"{C.GREEN}ok{C.RESET}"
#                        if v["quality"] == "ok"
#                        else f"{C.YELLOW}short (<6s){C.RESET}")
#         gender_str  = (f"{C.PURPLE}female{C.RESET}"
#                        if v["gender"] == "female"
#                        else f"{C.BLUE}male{C.RESET}")
#         print(
#             f"  {C.CYAN}[{i:<2}]{C.RESET} "
#             f"{v['display']:<32} "
#             f"{gender_str:<18} "
#             f"{C.DIM}{v['duration_s']:>5.1f}s{C.RESET}  "
#             f"{quality_str}"
#         )


# # ─────────────────────────────────────────────────────────────
# # PART 3 — SPEAKER DISCOVERY FROM JSON
# # ─────────────────────────────────────────────────────────────
# INPUT_JSON = "work/translated_segments_step3.json"

# AGE_CATEGORIES = [
#     "adult",
#     "child_young",
#     "child_teen",
#     "old_60s",
#     "old_80s",
#     "robot",
# ]
# AGE_DESCRIPTIONS = [
#     "No transformation — natural voice",
#     "Young child (5–10y) — formant+pitch shifted up 45%",
#     "Teenager (11–16y) — formant+pitch shifted up 20%",
#     "Elderly 60s — slight jitter + breathiness + slower",
#     "Elderly 80s — strong jitter + heavy breathiness + much slower",
#     "Robot — LPC resynthesis with buzz-wave source",
# ]


# def discover_speakers():
#     """Read JSON and return list of unique speaker IDs."""
#     if not os.path.exists(INPUT_JSON):
#         error(f"Input JSON not found: {INPUT_JSON}")
#         info("Please run Steps 1–3 first to generate the translated segments JSON.")
#         sys.exit(1)

#     with open(INPUT_JSON, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     speakers = {}
#     for seg in data.get("segments", []):
#         spk = seg.get("speaker", "UNKNOWN")
#         if spk not in speakers:
#             speakers[spk] = {
#                 "count":    0,
#                 "emotions": set(),
#                 "sample_text": seg.get("english", ""),
#             }
#         speakers[spk]["count"]  += 1
#         speakers[spk]["emotions"].add(seg.get("emotion", "neu"))

#     return speakers


# # ─────────────────────────────────────────────────────────────
# # PART 4 — INTERACTIVE SPEAKER CONFIGURATION
# # ─────────────────────────────────────────────────────────────
# def configure_speakers(speakers, catalogue, existing_config=None):
#     """
#     Interactive loop — for each speaker ask:
#       1. Which voice sample to use
#       2. Which age/type category
#     Returns speaker_map dict.
#     """
#     header("Part 3 — Speaker Voice Assignment")

#     print(f"  Found {C.BOLD}{len(speakers)}{C.RESET} unique speakers in your JSON.\n")
#     print(f"  {C.DIM}For each speaker you will:{C.RESET}")
#     print(f"  {C.DIM}  1. Choose a voice sample from your sample_voices/ folder{C.RESET}")
#     print(f"  {C.DIM}  2. Choose an age/type category{C.RESET}")
#     print(f"  {C.DIM}  3. (Optional) provide a kNN-VC reference clip{C.RESET}\n")

#     speaker_map = {}

#     for spk_id, spk_info in sorted(speakers.items()):
#         print(f"\n  {C.BOLD}{C.BG_DARK}{C.WHITE}  Speaker: {spk_id}  {C.RESET}")
#         print(f"  {C.DIM}Lines: {spk_info['count']} | Emotions: {', '.join(spk_info['emotions'])}{C.RESET}")
#         print(f"  {C.DIM}Sample line: \"{spk_info['sample_text'][:60]}...\"  {C.RESET}")

#         # ── VOICE SELECTION ───────────────────────────────────
#         print(f"\n  {C.BOLD}Step A — Choose voice sample{C.RESET}")
#         print_voice_catalogue(catalogue)

#         # Default: try to match gender if available, else 0
#         default_idx = 0
#         if existing_config and spk_id in existing_config:
#             prev_path = existing_config[spk_id].get("voice_sample", "")
#             for j, v in enumerate(catalogue):
#                 if v["path"] == prev_path:
#                     default_idx = j
#                     break

#         voice_idx = numbered_menu(
#             f"Select voice for {spk_id}",
#             [f"{v['display']} ({v['gender']}, {v['duration_s']}s)" for v in catalogue],
#             default=default_idx,
#         )
#         chosen_voice = catalogue[voice_idx]

#         if chosen_voice["quality"] == "too_short":
#             warn(f"This sample is only {chosen_voice['duration_s']}s — "
#                  f"recommend 15s+ for best cloning quality.")

#         success(f"Voice: {chosen_voice['display']}  [{chosen_voice['filename']}]")

#         # ── AGE CATEGORY ──────────────────────────────────────
#         print(f"\n  {C.BOLD}Step B — Choose age / voice type{C.RESET}")
#         default_age = 0
#         if existing_config and spk_id in existing_config:
#             prev_age = existing_config[spk_id].get("age_category", "adult")
#             if prev_age in AGE_CATEGORIES:
#                 default_age = AGE_CATEGORIES.index(prev_age)

#         age_idx = numbered_menu(
#             f"Select age/type for {spk_id}",
#             AGE_CATEGORIES,
#             descriptions=AGE_DESCRIPTIONS,
#             default=default_age,
#         )
#         chosen_age = AGE_CATEGORIES[age_idx]
#         success(f"Age/type: {chosen_age}  — {AGE_DESCRIPTIONS[age_idx]}")

#         # ── kNN-VC REFERENCE CLIP (optional) ─────────────────
#         knnvc_ref = None
#         if chosen_age not in ("adult", "robot"):
#             print(f"\n  {C.BOLD}Step C — kNN-VC reference clip{C.RESET} {C.DIM}(optional){C.RESET}")
#             info("Providing a 5–10s reference clip of a real child/elderly voice "
#                  "enables ML-based conversion instead of DSP.")
#             info("Leave blank to use DSP (Parselmouth) instead.")
#             ref_path = input(f"  Path to reference clip (or press Enter to skip) › ").strip()
#             if ref_path and os.path.exists(ref_path):
#                 knnvc_ref = ref_path
#                 success(f"kNN-VC reference: {ref_path}")
#             elif ref_path:
#                 warn(f"File not found: {ref_path} — using DSP fallback")

#         speaker_map[spk_id] = {
#             "voice_sample":  chosen_voice["path"],
#             "voice_display": chosen_voice["display"],
#             "age_category":  chosen_age,
#             "knnvc_ref":     knnvc_ref,
#         }

#     return speaker_map


# # ─────────────────────────────────────────────────────────────
# # PART 5 — GLOBAL OPTIONS
# # ─────────────────────────────────────────────────────────────
# def configure_global_options(existing_config=None):
#     """Ask user for global pipeline toggles."""
#     header("Part 4 — Global Options")

#     prev = existing_config.get("options", {}) if existing_config else {}

#     # Emotion toggle
#     prev_emot = prev.get("emotion_enabled", True)
#     emot_idx  = numbered_menu(
#         "Emotion fine-tuning (Stage 3)",
#         ["Enabled  — apply emotion-aware loudness + EQ per segment",
#          "Disabled — skip Stage 3, pass timing-aligned audio through"],
#         default=0 if prev_emot else 1,
#     )
#     emotion_enabled = (emot_idx == 0)

#     # Age toggle
#     prev_age = prev.get("age_enabled", True)
#     age_idx  = numbered_menu(
#         "Age / type transformation (Stage 4)",
#         ["Enabled  — apply child/old/robot transform per speaker",
#          "Disabled — skip Stage 4, use cloned voice as-is"],
#         default=0 if prev_age else 1,
#     )
#     age_enabled = (age_idx == 0)

#     # kNN-VC toggle
#     prev_knnvc = prev.get("use_knnvc", False)
#     try:
#         import knnvc
#         knnvc_available = True
#     except ImportError:
#         knnvc_available = False

#     if knnvc_available:
#         knnvc_idx = numbered_menu(
#             "Age conversion method",
#             ["DSP (Parselmouth) — no reference clip needed, fast",
#              "kNN-VC (HuggingFace bshall/knn-vc) — ML, needs reference clips, more natural"],
#             default=1 if prev_knnvc else 0,
#         )
#         use_knnvc = (knnvc_idx == 1)
#     else:
#         warn("kNN-VC not installed — using DSP (Parselmouth) only")
#         info("Install with: pip install knnvc")
#         use_knnvc = False

#     return {
#         "emotion_enabled": emotion_enabled,
#         "age_enabled":     age_enabled,
#         "use_knnvc":       use_knnvc,
#     }


# # ─────────────────────────────────────────────────────────────
# # PART 6 — SAVE + SUMMARY
# # ─────────────────────────────────────────────────────────────
# CONFIG_PATH = "work/speaker_config.json"

# def save_config(speaker_map, options):
#     os.makedirs("work", exist_ok=True)
#     config = {
#         "generated_at": __import__("datetime").datetime.now().isoformat(),
#         "input_json":   INPUT_JSON,
#         "options":      options,
#         "speakers":     speaker_map,
#     }
#     with open(CONFIG_PATH, "w", encoding="utf-8") as f:
#         json.dump(config, f, indent=2, ensure_ascii=False)
#     return config


# def print_summary(config):
#     header("Configuration Summary")

#     opts = config["options"]
#     print(f"  {C.BOLD}Global options:{C.RESET}")
#     print(f"    Emotion fine-tuning : {C.GREEN}ON{C.RESET}" if opts["emotion_enabled"]
#           else f"    Emotion fine-tuning : {C.DIM}OFF{C.RESET}")
#     print(f"    Age/type transform  : {C.GREEN}ON{C.RESET}" if opts["age_enabled"]
#           else f"    Age/type transform  : {C.DIM}OFF{C.RESET}")
#     print(f"    Age conversion mode : {'kNN-VC (ML)' if opts['use_knnvc'] else 'DSP (Parselmouth)'}")

#     print(f"\n  {C.BOLD}Speaker assignments:{C.RESET}")
#     print(f"  {C.DIM}{'Speaker':<14} {'Voice':<28} {'Age/Type'}{C.RESET}")
#     print(f"  {C.DIM}{'─' * 58}{C.RESET}")
#     for spk_id, info_d in sorted(config["speakers"].items()):
#         voice   = info_d.get("voice_display", os.path.basename(info_d["voice_sample"]))
#         age     = info_d["age_category"]
#         knn     = f"  {C.DIM}[kNN-VC ref set]{C.RESET}" if info_d.get("knnvc_ref") else ""
#         age_col = (f"{C.PURPLE}{age}{C.RESET}" if "child" in age
#                    else f"{C.YELLOW}{age}{C.RESET}" if "old" in age
#                    else f"{C.BLUE}{age}{C.RESET}" if age == "robot"
#                    else f"{C.GREEN}{age}{C.RESET}")
#         print(f"  {C.CYAN}{spk_id:<14}{C.RESET} {voice:<28} {age_col}{knn}")

#     print(f"\n  {C.BOLD}Saved to:{C.RESET} {C.GREEN}{CONFIG_PATH}{C.RESET}")
#     print(f"\n  {C.BOLD}Run next:{C.RESET}")
#     print(f"  {C.DIM}python step4_genvoice_complete.py{C.RESET}\n")


# # ─────────────────────────────────────────────────────────────
# # MAIN
# # ─────────────────────────────────────────────────────────────
# def main():
#     print(f"\n{C.BOLD}{C.CYAN}")
#     print("  ╔══════════════════════════════════════════════════════╗")
#     print("  ║     Anime Dubbing Pipeline — Step 4 Setup           ║")
#     print("  ║     Voice Selection & Installation                  ║")
#     print("  ╚══════════════════════════════════════════════════════╝")
#     print(C.RESET)

#     # Load existing config if present (for re-runs with defaults)
#     existing_config = None
#     if os.path.exists(CONFIG_PATH):
#         with open(CONFIG_PATH) as f:
#             existing_config = json.load(f)
#         info(f"Found existing config: {CONFIG_PATH}")
#         ans = input("  Re-use existing defaults? (Y/n) › ").strip().lower()
#         if ans == "n":
#             existing_config = None

#     # ── Part 1: Installation ──────────────────────────────────
#     header("Part 1 — Installation Check")
#     skip_install = False
#     if existing_config:
#         ans = input("  Skip installation check? (Y/n) › ").strip().lower()
#         skip_install = (ans != "n")

#     if not skip_install:
#         run_installation()
#     else:
#         info("Skipping installation check")

#     # ── Part 2: Voice library scan ────────────────────────────
#     header("Part 2 — Voice Library")
#     if not os.path.isdir(VOICE_SAMPLES_DIR):
#         error(f"Voice samples folder not found: {VOICE_SAMPLES_DIR}/")
#         info("Create the folder and add your .wav / .mp3 voice samples:")
#         print(f"  {C.DIM}sample_voices/")
#         print(f"  ├── female/  (Amber.mp3, Chloe.mp3, ...)")
#         print(f"  └── male/    (madara.mp3, denji.mp3, ...){C.RESET}")
#         sys.exit(1)

#     catalogue = scan_voices()
#     if not catalogue:
#         error("No .wav or .mp3 files found in sample_voices/")
#         sys.exit(1)

#     success(f"Found {len(catalogue)} voice samples")

#     # ── Part 3: Speaker config ────────────────────────────────
#     speakers = discover_speakers()
#     success(f"Found {len(speakers)} unique speakers in {INPUT_JSON}")

#     existing_speakers = existing_config.get("speakers") if existing_config else None
#     speaker_map = configure_speakers(speakers, catalogue, existing_speakers)

#     # ── Part 4: Global options ────────────────────────────────
#     options = configure_global_options(existing_config)

#     # ── Part 5: Save + summary ────────────────────────────────
#     config = save_config(speaker_map, options)
#     print_summary(config)

#     success("Setup complete — ready to run step4_genvoice_complete.py")


# if __name__ == "__main__":
#     main()
"""
STEP 4 SETUP — Voice Selection & Installation
Run ONCE before step4_genvoice_complete.py
Outputs: work/speaker_config.json

Tamil/Tanglish changes vs previous version:
  - Reads language_mode + tts_language from Step 3 JSON
  - Shows correct dub-language sample text per speaker
  - Auto-suggests tamil/ folder voices when Tamil mode detected
  - Warns if non-Tamil voice selected in Tamil mode
  - Saves language_mode + tts_language into speaker_config.json
"""

import sys
import os
import json
import subprocess
import itertools
from pathlib import Path

class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
    CYAN = "\033[96m"; BLUE = "\033[94m"; PURPLE = "\033[95m"
    WHITE = "\033[97m"; BG_DARK = "\033[40m"

def header(text):
    print(f"\n{C.CYAN}{'═'*60}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}  {text}{C.RESET}")
    print(f"{C.CYAN}{'═'*60}{C.RESET}\n")

def success(text): print(f"  {C.GREEN}OK   {C.RESET} {text}")
def warn(text):    print(f"  {C.YELLOW}WARN {C.RESET} {text}")
def error(text):   print(f"  {C.RED}FAIL {C.RESET} {text}")
def info(text):    print(f"  {C.CYAN}INFO {C.RESET} {text}")

def numbered_menu(title, options, descriptions=None, default=0):
    print(f"\n  {C.BOLD}{title}{C.RESET}")
    print(f"  {C.DIM}{'─'*40}{C.RESET}")
    for i, opt in enumerate(options):
        marker = f"{C.GREEN}>{C.RESET}" if i == default else " "
        desc   = f"  {C.DIM}{descriptions[i]}{C.RESET}" if descriptions else ""
        dtag   = f"  {C.DIM}(default){C.RESET}" if i == default else ""
        print(f"  {marker} {C.CYAN}[{i}]{C.RESET} {C.WHITE}{opt}{C.RESET}{desc}{dtag}")
    while True:
        raw = input(f"\n  Enter number (0-{len(options)-1}) > ").strip()
        if raw == "": return default
        if raw.isdigit() and 0 <= int(raw) < len(options):
            return int(raw)
        warn(f"Enter 0 to {len(options)-1}")

# ─────────────────────────────────────────────────────────────
# INSTALLATION
# ─────────────────────────────────────────────────────────────
PACKAGES = [
    ("TTS",               "TTS",          "Coqui XTTS-v2 voice cloning"),
    ("praat-parselmouth", "parselmouth",  "Voice age/type transformation"),
    ("scipy",             "scipy",        "Audio filters"),
    ("soundfile",         "soundfile",    "WAV read/write"),
    ("librosa",           "librosa",      "Audio analysis"),
    ("matplotlib",        "matplotlib",   "Waveform plots"),
    ("numpy",             "numpy",        "Array operations"),
    ("torch",             "torch",        "PyTorch"),
    ("torchaudio",        "torchaudio",   "Audio I/O"),
    ("pyphen",            "pyphen",       "Syllable counting"),
]
OPTIONAL = [("knnvc", "knnvc", "kNN-VC age conversion (optional)")]
SYSTEM_DEPS = {
    "linux":  "sudo apt-get install -y rubberband-cli ffmpeg",
    "darwin": "brew install rubberband ffmpeg",
    "win32":  "Download rubberband: https://breakfastquay.com/rubberband/",
}

def check_pkg(imp):
    try: __import__(imp); return True
    except ImportError: return False

def install_pkg(pip_name):
    r = subprocess.run([sys.executable, "-m", "pip", "install", pip_name, "-q"],
                       capture_output=True)
    return r.returncode == 0

def run_installation():
    header("Part 1 — Package Installation")
    print(f"  System dep: {C.DIM}{SYSTEM_DEPS.get(sys.platform,'')}{C.RESET}\n")
    all_ok = True
    for pip_name, imp, desc in PACKAGES:
        if check_pkg(imp):
            success(f"{pip_name:<25} {C.DIM}{desc}{C.RESET}")
        else:
            print(f"  {C.YELLOW}Installing {pip_name}...{C.RESET}", end="", flush=True)
            if install_pkg(pip_name): print(f" {C.GREEN}done{C.RESET}")
            else: print(f" {C.RED}FAILED{C.RESET}"); all_ok = False
    for pip_name, imp, desc in OPTIONAL:
        if not check_pkg(imp):
            warn(f"{pip_name} not installed — {desc}")
            if input(f"  Install {pip_name}? (y/N) > ").strip().lower() == "y":
                install_pkg(pip_name)
    if not all_ok:
        error("Fix failed packages then re-run"); sys.exit(1)
    success("All packages ready")

# ─────────────────────────────────────────────────────────────
# VOICE LIBRARY
# ─────────────────────────────────────────────────────────────
VOICE_DIR = "sample_voices"

def get_dur(path):
    try:
        import soundfile as sf
        return sf.info(path).duration
    except: return 0.0

def scan_voices():
    cat = []
    for vf in itertools.chain(Path(VOICE_DIR).rglob("*.wav"),
                               Path(VOICE_DIR).rglob("*.mp3")):
        dur  = get_dur(str(vf))
        name = vf.stem.replace("_voice sample","").replace("_"," ").strip().title()
        folder = vf.parent.name.lower()
        cat.append({"display": name, "path": str(vf), "gender": folder,
                    "duration_s": round(dur,1),
                    "quality": "ok" if dur >= 6 else "too_short",
                    "filename": vf.name})
    cat.sort(key=lambda x: (x["gender"] != "female", x["display"]))
    return cat

def print_catalogue(cat):
    print(f"\n  {C.BOLD}{'#':<4} {'Name':<32} {'Folder':<12} {'Dur':>6}  Quality{C.RESET}")
    print(f"  {C.DIM}{'─'*62}{C.RESET}")
    for i, v in enumerate(cat):
        q = f"{C.GREEN}ok{C.RESET}" if v["quality"]=="ok" else f"{C.YELLOW}short{C.RESET}"
        folder = v["gender"]
        if "tamil" in folder: fc = f"{C.CYAN}{folder}{C.RESET}"
        elif folder == "female": fc = f"{C.PURPLE}{folder}{C.RESET}"
        else: fc = f"{C.BLUE}{folder}{C.RESET}"
        print(f"  {C.CYAN}[{i:<2}]{C.RESET} {v['display']:<32} {fc:<20} "
              f"{C.DIM}{v['duration_s']:>5.1f}s{C.RESET}  {q}")

# ─────────────────────────────────────────────────────────────
# SPEAKER DISCOVERY
# ─────────────────────────────────────────────────────────────
INPUT_JSON  = "work/translated_segments_step3.json"
CONFIG_PATH = "work/speaker_config.json"
AGE_CATS    = ["adult","child_young","child_teen","old_60s","old_80s","robot"]
AGE_DESCS   = [
    "No change — natural voice",
    "Child 5-10y — formant+pitch up 45%",
    "Teen 11-16y  — formant+pitch up 20%",
    "Elderly 60s — jitter + breathiness",
    "Elderly 80s — heavy jitter + breathiness",
    "Robot — LPC buzz-wave resynthesis",
]

def discover_speakers():
    if not os.path.exists(INPUT_JSON):
        error(f"Not found: {INPUT_JSON} — run Steps 1-3 first"); sys.exit(1)
    with open(INPUT_JSON,"r",encoding="utf-8") as f:
        data = json.load(f)

    # ── Read language config from Step 3 output ───────────────
    lang_mode  = data.get("language_mode", "english")
    tts_lang   = data.get("tts_language",  "en")
    text_field = data.get("output_field",  "english")

    print(f"  Language mode  : {C.CYAN}{lang_mode}{C.RESET}")
    print(f"  TTS language   : {C.CYAN}{tts_lang}{C.RESET}  "
          f"(XTTS language code passed to tts_to_file)")
    print(f"  Dub text field : {C.CYAN}{text_field}{C.RESET}\n")

    speakers = {}
    for seg in data.get("segments", []):
        spk = seg.get("speaker", "UNKNOWN")
        if spk not in speakers:
            # Show the actual dub text in the correct language
            sample = (seg.get(text_field)
                      or seg.get("english")
                      or seg.get("tamil", ""))
            speakers[spk] = {"count": 0, "emotions": set(), "sample": sample}
        speakers[spk]["count"] += 1
        speakers[spk]["emotions"].add(seg.get("emotion", "neu"))

    return speakers, lang_mode, tts_lang, text_field

# ─────────────────────────────────────────────────────────────
# SPEAKER CONFIG
# ─────────────────────────────────────────────────────────────
def configure_speakers(speakers, cat, lang_mode, existing=None):
    header("Part 3 — Speaker Voice Assignment")
    is_tamil = lang_mode in ("tamil", "tanglish")

    if is_tamil:
        info("Tamil/Tanglish mode detected")
        info("Voice samples MUST be Tamil speech for correct phonemes")
        info("Add Tamil WAVs to sample_voices/tamil/ folder")
        print()

    spk_map = {}
    for spk_id, spk_info in sorted(speakers.items()):
        print(f"\n  {C.BOLD}{C.BG_DARK}{C.WHITE}  {spk_id}  {C.RESET}")
        print(f"  {C.DIM}Lines: {spk_info['count']} | "
              f"Emotions: {', '.join(spk_info['emotions'])}{C.RESET}")
        print(f"  {C.DIM}Sample [{lang_mode}]: \"{spk_info['sample'][:65]}\"{C.RESET}")

        # Voice selection
        print(f"\n  {C.BOLD}A — Voice sample{C.RESET}")
        if is_tamil:
            info("Prefer voices from sample_voices/tamil/")
        print_catalogue(cat)

        # Default: prefer Tamil folder in Tamil mode, else index 0
        default_idx = 0
        if existing and spk_id in existing:
            prev = existing[spk_id].get("voice_sample","")
            for j, v in enumerate(cat):
                if v["path"] == prev: default_idx = j; break
        elif is_tamil:
            for j, v in enumerate(cat):
                if "tamil" in v["gender"].lower(): default_idx = j; break

        vi = numbered_menu(
            f"Voice for {spk_id}",
            [f"{v['display']} ({v['gender']}, {v['duration_s']}s)" for v in cat],
            default=default_idx)
        cv = cat[vi]

        if cv["quality"] == "too_short":
            warn(f"Only {cv['duration_s']}s — 15s+ recommended for XTTS cloning")
        if is_tamil and "tamil" not in cv["gender"].lower():
            warn("Non-Tamil voice selected — Tamil speech may sound unnatural")
            warn("Consider adding a Tamil voice sample to sample_voices/tamil/")

        success(f"Voice: {cv['display']}  [{cv['filename']}]")

        # Age category
        print(f"\n  {C.BOLD}B — Age / voice type{C.RESET}")
        default_age = 0
        if existing and spk_id in existing:
            pa = existing[spk_id].get("age_category","adult")
            if pa in AGE_CATS: default_age = AGE_CATS.index(pa)

        ai = numbered_menu(f"Age/type for {spk_id}", AGE_CATS,
        descriptions=AGE_DESCS, default=default_age)
        chosen_age = AGE_CATS[ai]
        success(f"Age/type: {chosen_age}")

        # kNN-VC reference
        # knnvc_ref = None
        # if chosen_age not in ("adult","robot"):
        #     print(f"\n  {C.BOLD}C — kNN-VC reference clip{C.RESET} "
        #           f"{C.DIM}(optional — leave blank for DSP){C.RESET}")
        #     rp = input("  Reference clip path (Enter to skip) > ").strip()
        #     if rp and os.path.exists(rp): knnvc_ref = rp; success(f"Ref: {rp}")
        #     elif rp: warn(f"Not found: {rp} — using DSP")
        # kNN-VC reference
        knnvc_ref = None
        if chosen_age not in ("adult", "robot"):
            print(f"\n  {C.BOLD}C — kNN-VC reference clip{C.RESET} "
                  f"{C.DIM}(optional — select a voice sample or skip for DSP){C.RESET}")

            # Build menu from sample_voices folder — [0] = Skip
            knnvc_options  = ["Skip — use DSP instead"]
            knnvc_paths    = [None]
            knnvc_descs    = ["Parselmouth/Praat formant shifting (default)"]

            for v in cat:
                knnvc_options.append(f"{v['display']} ({v['gender']}, {v['duration_s']}s)")
                knnvc_paths.append(v["path"])
                knnvc_descs.append(v["filename"])

            # Restore previous selection if re-running setup
            default_knn = 0
            if existing and spk_id in (existing or {}):
                prev_ref = existing[spk_id].get("knnvc_ref", None)
                if prev_ref:
                    for j, p in enumerate(knnvc_paths):
                        if p == prev_ref:
                            default_knn = j
                            break

            ki = numbered_menu(
                f"kNN-VC reference for {spk_id}",
                knnvc_options,
                descriptions=knnvc_descs,
                default=default_knn,
            )

            if ki == 0:
                info("Skipped — DSP will be used for age transformation")
            else:
                knnvc_ref = knnvc_paths[ki]
                success(f"kNN-VC ref: {knnvc_options[ki]}")
        # 1. Add these new category lists near AGE_CATS
        TONE_CATS  = ["neutral", "ecchi", "horny", "soft", "sexy", "calm", "hard", "kid", "inner_thought"]
        # TONE_DESCS =[
        #     "High-arousal non-verbals (moans/panting) [1]",
        #     "Seductive with deep breathy pauses ",
        #     "Gentle, whispery delivery ",
        #     "Sultry, velvety tone ",
        #     "Relaxed and smooth pacing ",
        #     "Aggressive, commanding energy ",
        #     "Pediatric voice (+1 octave shift) [2]",
        #     "Inside-the-head effect (LPF + Reverb) "
        # ]
        TONE_DESCS = [
            "High-arousal non-verbals (moans/panting) [1]",
            "Seductive with deep breathy pauses ",
            "Gentle, whispery delivery ",
            "Sultry, velvety tone ",
            "Relaxed and smooth pacing ",
            "Aggressive, commanding energy ",
            "Pediatric voice (+1 octave shift) [2]",
            "Inside-the-head effect (LPF + Reverb) ",
            "Internalized monologue (whisper + reverb) ",
        ]

        # 2. Inside configure_speakers(speakers, cat, lang_mode, existing=None):
        # Add this block after the Age Selection (chosen_age)
        
        print(f"\n  {C.BOLD}C — Vocal Tone / Style{C.RESET}")
        default_tone = 0
        if existing and spk_id in existing:
            pt = existing[spk_id].get("tone_category", "neutral")
            if pt in TONE_CATS: default_tone = TONE_CATS.index(pt)
            
        ti = numbered_menu(f"Vocal tone for {spk_id}", TONE_CATS, 
                           descriptions=TONE_DESCS, default=default_tone)
        chosen_tone = TONE_CATS[ti]
        success(f"Tone: {chosen_tone}")
        
        # 3. Update the spk_map assignment to include the tone
        spk_map[spk_id] = {
            "voice_sample":  cv["path"],
            "voice_display": cv["display"],
            "age_category":  chosen_age,
            "tone_category": chosen_tone, # NEW
            "knnvc_ref":     knnvc_ref,
        }
        # spk_map[spk_id] = {
        #     "voice_sample":  cv["path"],
        #     "voice_display": cv["display"],
        #     "age_category":  chosen_age,
        #     "knnvc_ref":     knnvc_ref,
        # }
    return spk_map

# ─────────────────────────────────────────────────────────────
# GLOBAL OPTIONS
# ─────────────────────────────────────────────────────────────
def configure_options(existing=None):
    header("Part 4 — Global Options")
    prev = existing.get("options",{}) if existing else {}

    ei = numbered_menu("Emotion fine-tuning",
        ["Enabled — emotion loudness + EQ", "Disabled — skip"],
        default=0 if prev.get("emotion_enabled",True) else 1)
    ai = numbered_menu("Age/type transformation",
        ["Enabled — child/old/robot per speaker", "Disabled — skip"],
        default=0 if prev.get("age_enabled",True) else 1)

    use_knnvc = False
    try:
        import knnvc
        ki = numbered_menu("Age conversion method",
            ["DSP (Parselmouth) — fast", "kNN-VC (ML) — more natural"],
            default=1 if prev.get("use_knnvc",False) else 0)
        use_knnvc = (ki == 1)
    except ImportError:
        warn("kNN-VC not installed — DSP only (pip install knnvc to enable)")

    return {"emotion_enabled": ei==0, "age_enabled": ai==0, "use_knnvc": use_knnvc}

# ─────────────────────────────────────────────────────────────
# SAVE + SUMMARY
# ─────────────────────────────────────────────────────────────
def save_config(spk_map, opts, lang_mode, tts_lang, text_field):
    os.makedirs("work", exist_ok=True)
    from datetime import datetime
    cfg = {
        "generated_at":  datetime.now().isoformat(),
        "input_json":    INPUT_JSON,
        "language_mode": lang_mode,    # read by step4_genvoice_complete.py
        "tts_language":  tts_lang,     # "en" or "ta"
        "text_field":    text_field,   # "english" or "tamil"
        "options":       opts,
        "speakers":      spk_map,
    }
    with open(CONFIG_PATH,"w",encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg

def print_summary(cfg):
    header("Configuration Summary")
    opts = cfg["options"]
    print(f"  Language  : {C.CYAN}{cfg.get('language_mode','english')}{C.RESET}")
    print(f"  TTS code  : {C.CYAN}{cfg.get('tts_language','en')}{C.RESET}")
    print(f"  Text field: {C.CYAN}{cfg.get('text_field','english')}{C.RESET}")
    print(f"  Emotion   : {C.GREEN+'ON' if opts['emotion_enabled'] else C.DIM+'OFF'}{C.RESET}")
    print(f"  Age/type  : {C.GREEN+'ON' if opts['age_enabled'] else C.DIM+'OFF'}{C.RESET}")
    print(f"\n  {'Speaker':<14} {'Voice':<28} Age")
    print(f"  {C.DIM}{'─'*55}{C.RESET}")
    for sid, d in sorted(cfg["speakers"].items()):
        v = d.get("voice_display", os.path.basename(d["voice_sample"]))
        a = d["age_category"]
        print(f"  {C.CYAN}{sid:<14}{C.RESET} {v:<28} {a}")
    print(f"\n  Saved: {C.GREEN}{CONFIG_PATH}{C.RESET}")
    print(f"  Next:  python step4_genvoice_complete.py\n")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    print(f"\n{C.BOLD}{C.CYAN}  Anime Dubbing — Step 4 Setup{C.RESET}\n")

    existing = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f: existing = json.load(f)
        info(f"Existing config found: {CONFIG_PATH}")
        if input("  Re-use existing defaults? (Y/n) > ").strip().lower() == "n":
            existing = None

    header("Part 1 — Installation")
    skip = False
    if existing:
        skip = input("  Skip install check? (Y/n) > ").strip().lower() != "n"
    if not skip: run_installation()
    else: info("Skipping installation check")

    header("Part 2 — Voice Library")
    if not os.path.isdir(VOICE_DIR):
        error(f"Folder not found: {VOICE_DIR}/")
        print(f"  Create:\n  {C.DIM}sample_voices/female/  sample_voices/male/  sample_voices/tamil/{C.RESET}")
        sys.exit(1)
    cat = scan_voices()
    if not cat: error("No voice files found in sample_voices/"); sys.exit(1)
    success(f"Found {len(cat)} voice samples")

    speakers, lang_mode, tts_lang, text_field = discover_speakers()
    success(f"Found {len(speakers)} unique speakers")

    spk_map = configure_speakers(
        speakers, cat, lang_mode,
        existing.get("speakers") if existing else None)

    opts = configure_options(existing)
    cfg  = save_config(spk_map, opts, lang_mode, tts_lang, text_field)
    print_summary(cfg)
    success("Setup complete")

if __name__ == "__main__":
    main()