"""
fix_xtts_pytorch26.py
=====================
Patches the TTS library to work with PyTorch 2.6+
Run ONCE before step4_genvoice_complete.py:

    python fix_xtts_pytorch26.py

What it does:
  Finds the TTS io.py file in your environment and patches
  torch.load() calls to use weights_only=False so XTTS
  checkpoints load correctly under PyTorch 2.6.
"""

import sys
import os
import shutil
from pathlib import Path


def find_tts_io():
    """Find TTS/utils/io.py in the current Python environment."""
    for path in sys.path:
        candidate = Path(path) / "TTS" / "utils" / "io.py"
        if candidate.exists():
            return candidate
    # Also try site-packages directly
    for p in sys.path:
        for root, dirs, files in os.walk(p):
            if "io.py" in files and "TTS" in root and "utils" in root:
                return Path(root) / "io.py"
    return None


def patch_io_file(io_path: Path):
    """
    Patch torch.load calls in TTS/utils/io.py to add weights_only=False.
    Creates a .backup file before modifying.
    """
    content = io_path.read_text(encoding="utf-8")

    # Check if already patched
    if "weights_only=False" in content:
        print(f"✅ Already patched: {io_path}")
        return True

    # Backup original
    backup = io_path.with_suffix(".py.backup")
    shutil.copy(io_path, backup)
    print(f"📄 Backup saved: {backup}")

    # Patch: add weights_only=False to torch.load calls
    # Pattern 1: torch.load(f, map_location=map_location, **kwargs)
    patched = content.replace(
        'torch.load(f, map_location=map_location, **kwargs)',
        'torch.load(f, map_location=map_location, weights_only=False, **kwargs)'
    )

    # Pattern 2: torch.load(f, map_location=map_location)
    patched = patched.replace(
        'torch.load(f, map_location=map_location)',
        'torch.load(f, map_location=map_location, weights_only=False)'
    )

    # Pattern 3: plain torch.load(path) variants
    patched = patched.replace(
        'torch.load(model_path, map_location=torch.device("cpu"))',
        'torch.load(model_path, map_location=torch.device("cpu"), weights_only=False)'
    )

    if patched == content:
        print("⚠️  No matching torch.load patterns found — manual patch needed")
        print(f"   Open: {io_path}")
        print('   Find:    torch.load(f, map_location=map_location')
        print('   Add:     weights_only=False  as an argument')
        return False

    io_path.write_text(patched, encoding="utf-8")
    print(f"✅ Patched: {io_path}")
    return True


def patch_xtts_file(tts_root: Path):
    """
    Also patch TTS/tts/models/xtts.py which has its own torch.load call.
    """
    xtts_path = tts_root / "tts" / "models" / "xtts.py"
    if not xtts_path.exists():
        print(f"⚠️  xtts.py not found at {xtts_path}")
        return False

    content = xtts_path.read_text(encoding="utf-8")

    if "weights_only=False" in content:
        print(f"✅ xtts.py already patched: {xtts_path}")
        return True

    backup = xtts_path.with_suffix(".py.backup")
    shutil.copy(xtts_path, backup)
    print(f"📄 Backup saved: {backup}")

    # The specific line from the traceback
    patched = content.replace(
        'checkpoint = load_fsspec(model_path, map_location=torch.device("cpu"))["model"]',
        'checkpoint = load_fsspec(model_path, map_location=torch.device("cpu"), weights_only=False)["model"]'
    )

    # Generic load_fsspec patterns
    patched = patched.replace(
        'load_fsspec(model_path, map_location=',
        'load_fsspec(model_path, weights_only=False, map_location='
    )

    if patched == content:
        print("⚠️  No matching patterns in xtts.py — trying load_fsspec wrapper instead")
        return False

    xtts_path.write_text(patched, encoding="utf-8")
    print(f"✅ Patched xtts.py: {xtts_path}")
    return True


def add_safe_globals():
    """
    Alternative approach: register XTTS classes as safe globals
    for torch.serialization. This is the PyTorch-recommended method.
    Writes a small sitecustomize.py that runs at Python startup.
    """
    site_pkg = None
    for p in sys.path:
        if "site-packages" in p and os.path.isdir(p):
            site_pkg = Path(p)
            break

    if not site_pkg:
        print("⚠️  Could not find site-packages — skipping safe_globals approach")
        return False

    customize = site_pkg / "sitecustomize.py"
    patch_code = '''
# Auto-added by fix_xtts_pytorch26.py
# Registers XTTS config classes as safe globals for torch.serialization
try:
    import torch
    import torch.serialization
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsAudioConfig
    torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
except Exception:
    pass  # TTS not installed yet — skip
'''

    existing = customize.read_text(encoding="utf-8") if customize.exists() else ""
    if "fix_xtts_pytorch26" in existing:
        print(f"✅ sitecustomize.py already patched")
        return True

    with open(customize, "a", encoding="utf-8") as f:
        f.write(patch_code)
    print(f"✅ Registered XTTS safe globals in: {customize}")
    return True


def main():
    print("=" * 55)
    print("XTTS + PyTorch 2.6 Compatibility Patcher")
    print("=" * 55)

    import torch
    torch_ver = torch.__version__
    print(f"\nPyTorch version : {torch_ver}")
    print(f"Python          : {sys.version.split()[0]}")

    major, minor = [int(x) for x in torch_ver.split(".")[:2]]
    if major < 2 or (major == 2 and minor < 6):
        print(f"\n✅ PyTorch {torch_ver} is below 2.6 — this fix is not needed.")
        print("   If you still see errors, check your TTS installation.")
        return

    print(f"\n⚠️  PyTorch {torch_ver} detected — applying compatibility fix...\n")

    # Find TTS installation
    io_path = find_tts_io()
    if not io_path:
        print("❌ TTS library not found in sys.path")
        print("   Install with: pip install TTS")
        sys.exit(1)

    tts_root = io_path.parent.parent   # TTS/utils/io.py -> TTS/
    print(f"TTS found at : {tts_root}\n")

    # Apply patches
    print("── Approach 1: Patch torch.load in TTS files ──")
    io_ok   = patch_io_file(io_path)
    xtts_ok = patch_xtts_file(tts_root)

    print("\n── Approach 2: Register safe globals (backup method) ──")
    globals_ok = add_safe_globals()

    print("\n" + "=" * 55)
    if io_ok or xtts_ok or globals_ok:
        print("✅ Fix applied successfully!")
        print("\nNow run:")
        print("   python step4_genvoice_complete.py")
    else:
        print("⚠️  Automatic patch failed — manual fix needed.")
        print("\nOption A — Downgrade PyTorch (recommended):")
        print("   pip install torch==2.5.1 torchaudio==2.5.1")
        print("   (add --index-url https://download.pytorch.org/whl/cu121 for GPU)")
        print("\nOption B — Manual patch:")
        print(f"   Open: {io_path}")
        print('   Find all:  torch.load(f, map_location=map_location')
        print('   Add after: , weights_only=False')
    print("=" * 55)


if __name__ == "__main__":
    main()