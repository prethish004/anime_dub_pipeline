# # """
# # fix_duplicate_keyword.py
# # ========================
# # Fixes the SyntaxError caused by duplicate weights_only=False
# # in xtts.py after the previous patcher ran.

# # Run:
# #     python fix_duplicate_keyword.py
# # """

# # import sys
# # import re
# # from pathlib import Path


# # def find_xtts_py():
# #     for p in sys.path:
# #         candidate = Path(p) / "TTS" / "tts" / "models" / "xtts.py"
# #         if candidate.exists():
# #             return candidate
# #     return None


# # def fix(path: Path):
# #     content = path.read_text(encoding="utf-8")

# #     # Count occurrences of the duplicate pattern
# #     count = content.count("weights_only=False, map_location")
# #     count += content.count("weights_only=False, weights_only=False")
# #     print(f"Found {count} pattern(s) to fix in {path}")

# #     # Fix pattern: load_fsspec(..., weights_only=False, map_location=..., weights_only=False)
# #     # Remove the second (trailing) weights_only=False
# #     fixed = re.sub(
# #         r'(load_fsspec\([^)]*?weights_only=False[^)]*?),\s*weights_only=False',
# #         r'\1',
# #         content
# #     )

# #     # Also fix torch.load with duplicate
# #     fixed = re.sub(
# #         r'(torch\.load\([^)]*?weights_only=False[^)]*?),\s*weights_only=False',
# #         r'\1',
# #         fixed
# #     )

# #     # Verify it's now valid by checking no duplicates remain
# #     if "weights_only=False, map_location" in fixed and fixed.count("weights_only=False") > fixed.count("load_fsspec") + fixed.count("torch.load"):
# #         print("WARNING: may still have duplicates — check manually")

# #     if fixed == content:
# #         print("No changes needed — pattern not found.")
# #         print("The file may already be correct or have a different format.")
# #         print(f"\nOpen manually: {path}")
# #         print("Find the line with:  weights_only=False, map_location=...")
# #         print("Remove any duplicate:  , weights_only=False")
# #         return False

# #     path.write_text(fixed, encoding="utf-8")
# #     print(f"Fixed: {path}")
# #     return True


# # def also_fix_io_py():
# #     """Fix io.py if it also has duplicates."""
# #     for p in sys.path:
# #         candidate = Path(p) / "TTS" / "utils" / "io.py"
# #         if candidate.exists():
# #             content = candidate.read_text(encoding="utf-8")
# #             fixed = re.sub(
# #                 r'(torch\.load\([^)]*?weights_only=False[^)]*?),\s*weights_only=False',
# #                 r'\1',
# #                 content
# #             )
# #             if fixed != content:
# #                 candidate.write_text(fixed, encoding="utf-8")
# #                 print(f"Also fixed io.py: {candidate}")
# #             else:
# #                 print(f"io.py looks clean: {candidate}")
# #             return


# # def verify_syntax(path: Path):
# #     """Try to compile the file to verify no syntax errors."""
# #     import py_compile, tempfile, shutil
# #     tmp = Path(tempfile.mktemp(suffix=".py"))
# #     shutil.copy(path, tmp)
# #     try:
# #         py_compile.compile(str(tmp), doraise=True)
# #         print(f"Syntax OK: {path.name}")
# #         return True
# #     except py_compile.PyCompileError as e:
# #         print(f"Still has syntax error: {e}")
# #         return False
# #     finally:
# #         tmp.unlink(missing_ok=True)


# # def main():
# #     print("=" * 50)
# #     print("Fix: duplicate weights_only keyword in xtts.py")
# #     print("=" * 50)

# #     xtts = find_xtts_py()
# #     if not xtts:
# #         print("ERROR: xtts.py not found in sys.path")
# #         print("Make sure your anime_env is activated.")
# #         sys.exit(1)

# #     print(f"\nFile: {xtts}\n")
# #     ok = fix(xtts)
# #     also_fix_io_py()

# #     print()
# #     if ok:
# #         valid = verify_syntax(xtts)
# #         print()
# #         if valid:
# #             print("=" * 50)
# #             print("All fixed! Now run:")
# #             print("   python step4_genvoice_complete.py")
# #             print("=" * 50)
# #         else:
# #             print("Syntax still broken — restore backup and fix manually:")
# #             print(f"  copy {xtts.with_suffix('.py.backup')} {xtts}")
# #             print()
# #             print("Then open xtts.py, find the line:")
# #             print('  load_fsspec(model_path, weights_only=False, map_location=..., weights_only=False)')
# #             print("Change it to:")
# #             print('  load_fsspec(model_path, map_location=torch.device("cpu"), weights_only=False)["model"]')
# #     else:
# #         print("Could not auto-fix. Restore backup:")
# #         print(f"  copy {xtts.with_suffix('.py.backup')} {xtts}")


# # if __name__ == "__main__":
# #     main()
# """
# fix_io_final.py
# ===============
# Surgically fixes TTS/utils/io.py so load_fsspec never passes
# weights_only twice to torch.load.

# Run once:
#     python fix_io_final.py
# """

# import sys
# from pathlib import Path


# def find_io_py():
#     for p in sys.path:
#         candidate = Path(p) / "TTS" / "utils" / "io.py"
#         if candidate.exists():
#             return candidate
#     return None


# def main():
#     io_path = find_io_py()
#     if not io_path:
#         print("ERROR: TTS/utils/io.py not found — is anime_env activated?")
#         sys.exit(1)

#     print(f"Found: {io_path}")
#     content = io_path.read_text(encoding="utf-8")

#     # Show the current load_fsspec function so we know what we are editing
#     lines = content.splitlines()
#     for i, line in enumerate(lines):
#         if "def load_fsspec" in line or "torch.load" in line:
#             print(f"  Line {i+1}: {line}")

#     # ── THE FIX ──────────────────────────────────────────────
#     # The function signature is:
#     #   def load_fsspec(path, map_location=None, **kwargs):
#     #       ...
#     #       return torch.load(f, map_location=map_location, weights_only=False, **kwargs)
#     #
#     # Problem: caller passes weights_only=False in kwargs AND
#     # it is also hardcoded in the torch.load call → duplicate.
#     #
#     # Fix: pop weights_only from kwargs before the torch.load call.
#     # We replace the torch.load line with a version that pops first.

#     OLD1 = "return torch.load(f, map_location=map_location, weights_only=False, **kwargs)"
#     NEW1 = (
#         "kwargs.pop('weights_only', None)  # prevent duplicate kwarg\n"
#         "        return torch.load(f, map_location=map_location, weights_only=False, **kwargs)"
#     )

#     # Also handle variant without weights_only already in line
#     OLD2 = "return torch.load(f, map_location=map_location, **kwargs)"
#     NEW2 = (
#         "kwargs.pop('weights_only', None)  # prevent duplicate kwarg\n"
#         "        return torch.load(f, map_location=map_location, weights_only=False, **kwargs)"
#     )

#     if OLD1 in content:
#         fixed = content.replace(OLD1, NEW1)
#         print("\nApplied fix: stripped duplicate weights_only from kwargs")
#     elif OLD2 in content:
#         fixed = content.replace(OLD2, NEW2)
#         print("\nApplied fix: added weights_only=False + kwargs guard")
#     else:
#         # Show the actual torch.load line so user can fix manually
#         print("\nCould not find expected pattern. Current torch.load line in io.py:")
#         for i, line in enumerate(lines):
#             if "torch.load" in line:
#                 print(f"  Line {i+1}: {line.strip()}")
#         print("\nManual fix — open io.py and change the torch.load line to:")
#         print("    kwargs.pop('weights_only', None)")
#         print("    return torch.load(f, map_location=map_location, weights_only=False, **kwargs)")
#         sys.exit(1)

#     # Backup + write
#     backup = io_path.with_suffix(".py.bak2")
#     io_path.with_suffix(".py").__class__  # just a reference
#     backup.write_text(content, encoding="utf-8")
#     io_path.write_text(fixed, encoding="utf-8")
#     print(f"Backup: {backup}")
#     print(f"Fixed:  {io_path}")

#     # Verify syntax
#     import py_compile, tempfile, shutil
#     tmp = Path(tempfile.mktemp(suffix=".py"))
#     shutil.copy(io_path, tmp)
#     try:
#         py_compile.compile(str(tmp), doraise=True)
#         print("\nSyntax OK")
#         print("\n" + "="*50)
#         print("Done! Now run:")
#         print("   python step4_genvoice_complete.py")
#         print("="*50)
#     except py_compile.PyCompileError as e:
#         print(f"\nSyntax error after patch: {e}")
#         print("Restoring backup...")
#         shutil.copy(backup, io_path)
#         print("Restored. Fix manually — see instructions above.")
#     finally:
#         tmp.unlink(missing_ok=True)


# if __name__ == "__main__":
#     main()
"""
fix_fsspec_closed_file.py
=========================
Fixes: ValueError: I/O operation on closed file
in TTS/utils/io.py load_fsspec function.

The root cause: fsspec opens a file handle in a 'with' block,
but torch.load needs to seek the buffer AFTER the context manager
closes it. The fix rewrites load_fsspec to read the file into
a BytesIO buffer first, then pass the buffer to torch.load —
so the file handle lifetime doesn't matter.

Run once:
    python fix_fsspec_closed_file.py
"""

import sys
from pathlib import Path


def find_io_py():
    for p in sys.path:
        candidate = Path(p) / "TTS" / "utils" / "io.py"
        if candidate.exists():
            return candidate
    return None


FIXED_LOAD_FSSPEC = '''def load_fsspec(
    path: str,
    map_location=None,
    cache: bool = True,
    **kwargs,
):
    """Like torch.load but can load from other locations (e.g. s3://, gs://).
    Reads entire file into memory first to avoid closed-file seek errors
    with fsspec + PyTorch 2.5+.
    """
    import io as _io
    import torch
    import fsspec

    kwargs.pop("weights_only", None)  # prevent duplicate kwarg

    with fsspec.open(path, "rb", cache_storage="/tmp/tts_cache" if cache else None) as f:
        data = f.read()

    buffer = _io.BytesIO(data)
    return torch.load(buffer, map_location=map_location, weights_only=False)
'''


def main():
    io_path = find_io_py()
    if not io_path:
        print("ERROR: TTS/utils/io.py not found")
        print("Make sure anime_env is activated.")
        sys.exit(1)

    print(f"Found: {io_path}")
    content = io_path.read_text(encoding="utf-8")

    # Make a backup
    backup = io_path.with_suffix(".py.fsspec_backup")
    if not backup.exists():
        backup.write_text(content, encoding="utf-8")
        print(f"Backup: {backup}")
    else:
        print(f"Backup already exists: {backup}")

    # Find the start and end of the load_fsspec function
    lines = content.splitlines()
    start_line = None
    end_line   = None

    for i, line in enumerate(lines):
        if "def load_fsspec(" in line:
            start_line = i
        elif start_line is not None and i > start_line:
            # End of function = next def/class at same indent level, or EOF
            stripped = line
            if stripped and not stripped.startswith(" ") and not stripped.startswith("\t"):
                if stripped.startswith("def ") or stripped.startswith("class "):
                    end_line = i
                    break

    if start_line is None:
        print("ERROR: could not find 'def load_fsspec(' in io.py")
        print("The function may have been renamed or the file structure changed.")
        print(f"\nOpen manually: {io_path}")
        print("Replace the entire load_fsspec function with:")
        print("─" * 50)
        print(FIXED_LOAD_FSSPEC)
        sys.exit(1)

    if end_line is None:
        end_line = len(lines)  # function goes to end of file

    print(f"\nFound load_fsspec: lines {start_line+1}–{end_line}")
    print("Original function:")
    for ln in lines[start_line:end_line]:
        print(f"  {ln}")

    # Rebuild file: everything before + fixed function + everything after
    before = "\n".join(lines[:start_line])
    after  = "\n".join(lines[end_line:])

    # Preserve any imports already at top
    new_content = before + "\n" + FIXED_LOAD_FSSPEC + "\n" + after

    io_path.write_text(new_content, encoding="utf-8")
    print(f"\nReplaced load_fsspec with BytesIO-buffered version")
    print(f"Fixed: {io_path}")

    # Verify syntax
    import py_compile, tempfile, shutil
    tmp = Path(tempfile.mktemp(suffix=".py"))
    shutil.copy(io_path, tmp)
    try:
        py_compile.compile(str(tmp), doraise=True)
        print("Syntax OK")
        print("\n" + "=" * 50)
        print("Done! Now run:")
        print("   python step4_genvoice_complete.py")
        print("=" * 50)
    except py_compile.PyCompileError as e:
        print(f"\nSyntax error: {e}")
        print("Restoring backup...")
        shutil.copy(backup, io_path)
        print("Restored — fix manually:")
        print(f"  Open: {io_path}")
        print("  Replace the entire load_fsspec function with:")
        print("─" * 50)
        print(FIXED_LOAD_FSSPEC)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()