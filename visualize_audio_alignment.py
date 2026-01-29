# # visualize_audio_alignment.py (Audio Waveform Visualization)
# import json
# import os
# import librosa
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.patches as patches
# from matplotlib.patches import Rectangle
# from datetime import datetime

# # Configuration
# ORIGINAL_AUDIO = "work/audio_16k.wav"
# TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
# TRANSLATED_FILE = "work/translated_segments.json"
# VOICE_CLIPS_DIR = "work/voice_clips"
# VOICE_CLIPS_METADATA = "work/voice_clips_metadata.json"

# OUTPUT_DIR = "work/visualizations"


# def check_prerequisites():
#     """Check if required files exist"""
    
#     files_to_check = [
#         ORIGINAL_AUDIO,
#         TRANSCRIPTION_FILE,
#         TRANSLATED_FILE,
#         VOICE_CLIPS_METADATA
#     ]
    
#     for file in files_to_check:
#         if not os.path.exists(file):
#             print(f"❌ Missing: {file}")
#             return False
    
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     return True


# def load_audio(audio_file):
#     """Load audio file"""
#     try:
#         y, sr = librosa.load(audio_file, sr=16000, mono=True)
#         return y, sr
#     except Exception as e:
#         print(f"❌ Error loading audio: {e}")
#         return None, None


# def load_data_files():
#     """Load all JSON data files"""
    
#     files = {}
    
#     try:
#         with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
#             files['transcription'] = json.load(f)
        
#         with open(TRANSLATED_FILE, 'r', encoding='utf-8') as f:
#             files['translated'] = json.load(f)
        
#         with open(VOICE_CLIPS_METADATA, 'r', encoding='utf-8') as f:
#             files['voice_metadata'] = json.load(f)
        
#         return files
    
#     except Exception as e:
#         print(f"❌ Error loading JSON files: {e}")
#         return None


# def create_waveform_strip(audio, sr, title, start_time=0, end_time=None, figsize=(14, 3)):
#     """Create a waveform visualization"""
    
#     if end_time is None:
#         end_time = len(audio) / sr
    
#     # Convert time to samples
#     start_sample = int(start_time * sr)
#     end_sample = int(end_time * sr)
    
#     # Extract audio segment
#     audio_segment = audio[start_sample:end_sample]
    
#     # Create figure
#     fig, ax = plt.subplots(figsize=figsize)
    
#     # Plot waveform
#     times = np.linspace(start_time, end_time, len(audio_segment))
#     ax.plot(times, audio_segment, linewidth=0.5, color='steelblue')
#     ax.fill_between(times, audio_segment, alpha=0.3, color='steelblue')
    
#     # Styling
#     ax.set_title(title, fontsize=12, fontweight='bold')
#     ax.set_xlabel('Time (seconds)')
#     ax.set_ylabel('Amplitude')
#     ax.set_xlim(start_time, end_time)
#     ax.grid(True, alpha=0.3)
    
#     return fig, ax


# def plot_segment_comparison(audio_data, segment_data, sr, segment_idx):
#     """Create side-by-side comparison of a segment"""
    
#     original_audio = audio_data['original']
    
#     trans_seg = segment_data['transcription']['segments'][segment_idx]
#     trans_text = trans_seg['text']
#     speaker = trans_seg.get('speaker', 'UNKNOWN')
#     start_time = trans_seg['start']
#     end_time = trans_seg['end']
#     duration = trans_seg['duration']
    
#     trans_trans = segment_data['translated']['segments'][segment_idx]
#     translated_text = trans_trans['translated_text']
#     estimated_duration = trans_trans['estimated_duration']
#     duration_ratio = trans_trans['duration_ratio']
    
#     # Create figure with multiple subplots
#     fig = plt.figure(figsize=(16, 10))
#     gs = fig.add_gridspec(4, 1, hspace=0.4)
    
#     # Title
#     fig.suptitle(f'Segment {segment_idx + 1} - Audio Alignment Analysis', 
#                  fontsize=16, fontweight='bold', y=0.98)
    
#     # ====== Plot 1: Original Audio Waveform ======
#     ax1 = fig.add_subplot(gs[0])
    
#     # Get audio segment
#     start_sample = int(start_time * sr)
#     end_sample = int(end_time * sr)
#     audio_segment = original_audio[start_sample:end_sample]
    
#     times = np.linspace(start_time, end_time, len(audio_segment))
#     ax1.plot(times, audio_segment, linewidth=1, color='steelblue', label='Original Audio')
#     ax1.fill_between(times, audio_segment, alpha=0.3, color='steelblue')
    
#     # Highlight speech area in blue
#     rect1 = Rectangle((start_time, ax1.get_ylim()[0]), duration, 
#                        ax1.get_ylim()[1] - ax1.get_ylim()[0], 
#                        alpha=0.2, color='blue', label='Speech Area')
#     ax1.add_patch(rect1)
    
#     ax1.set_title(f'Original Audio - {speaker}', fontweight='bold')
#     ax1.set_ylabel('Amplitude')
#     ax1.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
#     ax1.grid(True, alpha=0.3)
#     ax1.legend(loc='upper right')
    
#     # Add text annotation
#     ax1.text(start_time, ax1.get_ylim()[1] * 0.8, 
#             f'🇯🇵 {trans_text}\n⏱️ {duration:.2f}s', 
#             fontsize=10, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
#     # ====== Plot 2: Translation Info ======
#     ax2 = fig.add_subplot(gs[1])
#     ax2.axis('off')
    
#     info_text = f"""
#     SEGMENT INFORMATION
#     ═══════════════════════════════════════════════════════════════════
    
#     Original Language (Japanese):
#     🇯🇵 {trans_text}
    
#     Translated Language (English):
#     🇬🇧 {translated_text}
    
#     Duration Analysis:
#     ⏱️  Original Duration: {duration:.2f}s
#     ⏱️  Estimated Duration: {estimated_duration:.2f}s
#     📊 Duration Ratio: {duration_ratio:.2f}x ({(duration_ratio - 1) * 100:+.1f}%)
    
#     Quality: {'🎯 Excellent (0.95-1.05x)' if 0.95 <= duration_ratio <= 1.05 else '✅ Good (0.85-1.15x)' if 0.85 <= duration_ratio <= 1.15 else '⚠️  Acceptable'}
#     """
    
#     ax2.text(0.05, 0.95, info_text, transform=ax2.transAxes, 
#             fontsize=10, verticalalignment='top', fontfamily='monospace',
#             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
#     # ====== Plot 3: Generated Voice Audio ======
#     ax3 = fig.add_subplot(gs[2])
    
#     # Try to load generated voice clip
#     voice_file = f"work/voice_clips/segment_{segment_idx + 1:03d}_*.mp3"
    
#     try:
#         # Find the voice file
#         import glob
#         voice_files = glob.glob(voice_file.replace('_*', f"_{speaker}"))
        
#         if voice_files:
#             voice_audio, voice_sr = librosa.load(voice_files[0], sr=16000, mono=True)
            
#             # Plot generated voice
#             voice_times = np.linspace(start_time, start_time + len(voice_audio) / voice_sr, len(voice_audio))
#             ax3.plot(voice_times, voice_audio, linewidth=1, color='green', label='Generated Voice')
#             ax3.fill_between(voice_times, voice_audio, alpha=0.3, color='green')
            
#             # Highlight speech area
#             rect3 = Rectangle((start_time, ax3.get_ylim()[0]), estimated_duration, 
#                              ax3.get_ylim()[1] - ax3.get_ylim()[0], 
#                              alpha=0.2, color='blue', label='Speech Area')
#             ax3.add_patch(rect3)
            
#             ax3.set_title(f'Generated Voice - {speaker}', fontweight='bold')
#             ax3.set_ylabel('Amplitude')
#             ax3.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
#             ax3.grid(True, alpha=0.3)
#             ax3.legend(loc='upper right')
            
#             # Add text
#             ax3.text(start_time, ax3.get_ylim()[1] * 0.8, 
#                     f'🎙️ Generated Voice\n⏱️ {estimated_duration:.2f}s', 
#                     fontsize=10, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
#         else:
#             ax3.text(0.5, 0.5, '⚠️ Voice clip not found', 
#                     ha='center', va='center', fontsize=14, transform=ax3.transAxes)
#             ax3.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
    
#     except Exception as e:
#         ax3.text(0.5, 0.5, f'⚠️ Error loading voice: {e}', 
#                 ha='center', va='center', fontsize=12, transform=ax3.transAxes)
#         ax3.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
    
#     # ====== Plot 4: Comparison Summary ======
#     ax4 = fig.add_subplot(gs[3])
#     ax4.axis('off')
    
#     # Check alignment
#     alignment_status = "✅ ALIGNED" if 0.85 <= duration_ratio <= 1.15 else "⚠️ MISALIGNED"
#     alignment_color = 'lightgreen' if 0.85 <= duration_ratio <= 1.15 else 'lightyellow'
    
#     summary_text = f"""
#     ALIGNMENT VERIFICATION
#     ═══════════════════════════════════════════════════════════════════
    
#     Status: {alignment_status}
    
#     ✓ Original Audio Duration:      {duration:.2f}s (Blue box above)
#     ✓ Generated Voice Duration:     {estimated_duration:.2f}s (Blue box in green plot)
#     ✓ Duration Match Ratio:         {duration_ratio:.2f}x
    
#     Frequency Match Analysis:
#     • If waveform patterns match → Audio quality is GOOD
#     • If timing is aligned (±0.2s) → Dubbing will be in sync
#     • If both match → READY for video assembly
#     """
    
#     ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
#             fontsize=10, verticalalignment='top', fontfamily='monospace',
#             bbox=dict(boxstyle='round', facecolor=alignment_color, alpha=0.7))
    
#     return fig


# def create_full_timeline_visualization(audio_data, segment_data, sr, output_file):
#     """Create a full timeline showing all segments"""
    
#     segments = segment_data['transcription']['segments']
#     total_duration = audio_data['original'].shape[0] / sr
    
#     fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
    
#     fig.suptitle('Complete Audio Timeline - All Segments', 
#                  fontsize=16, fontweight='bold')
    
#     # Plot 1: Original Audio
#     original_audio = audio_data['original']
#     times_orig = np.arange(len(original_audio)) / sr
#     axes[0].plot(times_orig, original_audio, linewidth=0.5, color='steelblue', alpha=0.7)
#     axes[0].fill_between(times_orig, original_audio, alpha=0.2, color='steelblue')
    
#     # Add segment boxes
#     for idx, seg in enumerate(segments):
#         color = plt.cm.tab10(idx % 10)
#         rect = Rectangle((seg['start'], axes[0].get_ylim()[0]), 
#                          seg['duration'], 
#                          axes[0].get_ylim()[1] - axes[0].get_ylim()[0],
#                          alpha=0.15, color=color)
#         axes[0].add_patch(rect)
#         axes[0].text(seg['start'] + seg['duration'] / 2, 
#                     axes[0].get_ylim()[1] * 0.7,
#                     f"[{idx+1}]", ha='center', fontsize=8)
    
#     axes[0].set_title('Original Audio - All Segments', fontweight='bold')
#     axes[0].set_ylabel('Amplitude')
#     axes[0].grid(True, alpha=0.3)
    
#     # Plot 2: Segment Duration Comparison
#     segment_nums = list(range(1, len(segments) + 1))
#     original_durations = [seg['duration'] for seg in segment_data['transcription']['segments']]
#     translated_durations = [seg['estimated_duration'] for seg in segment_data['translated']['segments']]
    
#     x = np.arange(len(segment_nums))
#     width = 0.35
    
#     axes[1].bar(x - width/2, original_durations, width, label='Original (Japanese)', color='steelblue', alpha=0.7)
#     axes[1].bar(x + width/2, translated_durations, width, label='Translated (English)', color='green', alpha=0.7)
    
#     axes[1].set_title('Duration Comparison by Segment', fontweight='bold')
#     axes[1].set_ylabel('Duration (seconds)')
#     axes[1].set_xticks(x)
#     axes[1].set_xticklabels([f'Seg {n}' for n in segment_nums])
#     axes[1].legend()
#     axes[1].grid(True, alpha=0.3, axis='y')
    
#     # Plot 3: Duration Ratio
#     duration_ratios = [seg['duration_ratio'] for seg in segment_data['translated']['segments']]
    
#     colors = ['green' if 0.95 <= r <= 1.05 else 'orange' if 0.85 <= r <= 1.15 else 'red' 
#               for r in duration_ratios]
    
#     axes[2].bar(segment_nums, duration_ratios, color=colors, alpha=0.7)
#     axes[2].axhline(y=1.0, color='blue', linestyle='--', linewidth=2, label='Perfect Match (1.0x)')
#     axes[2].axhline(y=0.85, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Acceptable Range (0.85-1.15x)')
#     axes[2].axhline(y=1.15, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    
#     axes[2].set_title('Duration Ratio (Translated / Original)', fontweight='bold')
#     axes[2].set_ylabel('Ratio')
#     axes[2].set_xlabel('Segment Number')
#     axes[2].set_xticks(segment_nums)
#     axes[2].legend()
#     axes[2].grid(True, alpha=0.3, axis='y')
    
#     plt.tight_layout()
#     plt.savefig(output_file, dpi=150, bbox_inches='tight')
#     print(f"✅ Saved: {output_file}")
#     plt.close()


# def main():
#     print("=" * 70)
#     print("AUDIO ALIGNMENT VISUALIZATION")
#     print("=" * 70)
    
#     # Check prerequisites
#     if not check_prerequisites():
#         print("\n❌ Missing required files. Please complete previous steps first.")
#         return
    
#     print("\n✅ All prerequisite files found")
    
#     # Load audio
#     print("\n🎵 Loading audio...")
#     original_audio, sr = load_audio(ORIGINAL_AUDIO)
#     if original_audio is None:
#         return
    
#     print(f"   Loaded: {len(original_audio) / sr:.1f}s @ {sr}Hz")
    
#     # Load JSON data
#     print("\n📄 Loading transcription and translation data...")
#     data_files = load_data_files()
#     if data_files is None:
#         return
    
#     audio_data = {'original': original_audio}
    
#     # Create visualizations
#     print("\n🎨 Creating visualizations...")
    
#     # 1. Full timeline
#     timeline_file = os.path.join(OUTPUT_DIR, "00_full_timeline.png")
#     print(f"\n[1/3] Creating full timeline visualization...")
#     create_full_timeline_visualization(audio_data, data_files, sr, timeline_file)
    
#     # 2. Individual segment comparisons
#     segments = data_files['transcription']['segments']
    
#     print(f"\n[2/3] Creating individual segment comparisons...")
#     for idx in range(len(segments)):
#         print(f"   Segment {idx + 1}/{len(segments)}...", end=' ')
        
#         try:
#             fig = plot_segment_comparison(data_files, data_files, sr, idx)
            
#             segment_file = os.path.join(OUTPUT_DIR, f"{idx + 1:02d}_segment_{idx + 1}.png")
#             fig.savefig(segment_file, dpi=150, bbox_inches='tight')
#             plt.close(fig)
            
#             print("✅")
#         except Exception as e:
#             print(f"⚠️ {e}")
#             continue
    
#     # Summary
#     print("\n" + "=" * 70)
#     print("✅ VISUALIZATION COMPLETE!")
#     print("=" * 70)
#     print(f"\n📁 Output Directory: {OUTPUT_DIR}/")
#     print(f"\n📊 Files Created:")
#     print(f"   ✓ 00_full_timeline.png - Overall timeline with all segments")
    
#     num_segments = len(segments)
#     print(f"   ✓ {num_segments:02d} individual segment visualizations")
    
#     print(f"\n💡 How to Use:")
#     print(f"   1. Open '00_full_timeline.png' to see all segments at once")
#     print(f"   2. Open individual segment files to check alignment details")
#     print(f"   3. Blue boxes show where speech occurs")
#     print(f"   4. Check if original and generated voice waveforms match")
#     print(f"   5. If duration ratio is 0.85-1.15x, alignment is GOOD ✅")
    
#     print(f"\n🎯 Quality Indicators:")
#     print(f"   🎯 Green = Perfect (0.95-1.05x)")
#     print(f"   ✅ Orange = Good (0.85-1.15x)")
#     print(f"   ❌ Red = Poor (<0.85x or >1.15x)")


# if __name__ == "__main__":
#     main()
# visualize_audio_alignment.py (FIXED VERSION)
import json
import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from datetime import datetime
import glob

# Configuration
ORIGINAL_AUDIO = "work/audio_16k.wav"
TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
TRANSLATED_FILE = "work/translated_segments.json"
VOICE_CLIPS_DIR = "work/voice_clips"
VOICE_CLIPS_METADATA = "work/voice_clips_metadata.json"

OUTPUT_DIR = "work/visualizations"


def check_prerequisites():
    """Check if required files exist"""
    
    files_to_check = [
        ORIGINAL_AUDIO,
        TRANSCRIPTION_FILE,
        TRANSLATED_FILE,
        VOICE_CLIPS_METADATA
    ]
    
    for file in files_to_check:
        if not os.path.exists(file):
            print(f"❌ Missing: {file}")
            return False
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return True


def load_audio(audio_file):
    """Load audio file"""
    try:
        y, sr = librosa.load(audio_file, sr=16000, mono=True)
        return y, sr
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return None, None


def load_data_files():
    """Load all JSON data files"""
    
    files = {}
    
    try:
        with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
            files['transcription'] = json.load(f)
        
        with open(TRANSLATED_FILE, 'r', encoding='utf-8') as f:
            files['translated'] = json.load(f)
        
        with open(VOICE_CLIPS_METADATA, 'r', encoding='utf-8') as f:
            files['voice_metadata'] = json.load(f)
        
        return files
    
    except Exception as e:
        print(f"❌ Error loading JSON files: {e}")
        return None


def plot_segment_comparison(original_audio, sr, segment_data, segment_idx):
    """Create side-by-side comparison of a segment - FIXED"""
    
    # Extract segment data
    trans_seg = segment_data['transcription']['segments'][segment_idx]
    trans_text = trans_seg['text']
    speaker = trans_seg.get('speaker', 'UNKNOWN')
    start_time = trans_seg['start']
    end_time = trans_seg['end']
    duration = trans_seg['duration']
    
    trans_trans = segment_data['translated']['segments'][segment_idx]
    translated_text = trans_trans['translated_text']
    estimated_duration = trans_trans['estimated_duration']
    duration_ratio = trans_trans['duration_ratio']
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(4, 1, hspace=0.4)
    
    # Title
    fig.suptitle(f'Segment {segment_idx + 1} - Audio Alignment Analysis', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # ====== Plot 1: Original Audio Waveform ======
    ax1 = fig.add_subplot(gs[0])
    
    # Get audio segment
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    audio_segment = original_audio[start_sample:end_sample]
    
    times = np.linspace(start_time, end_time, len(audio_segment))
    ax1.plot(times, audio_segment, linewidth=1, color='steelblue', label='Original Audio')
    ax1.fill_between(times, audio_segment, alpha=0.3, color='steelblue')
    
    # Highlight speech area in blue
    y_min, y_max = ax1.get_ylim()
    rect1 = Rectangle((start_time, y_min), duration, y_max - y_min, 
                       alpha=0.2, color='blue', label='Speech Area')
    ax1.add_patch(rect1)
    
    ax1.set_title(f'Original Audio (Japanese) - {speaker}', fontweight='bold')
    ax1.set_ylabel('Amplitude')
    ax1.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    
    # Add text annotation
    ax1.text(start_time + duration/2, y_max * 0.8, 
            f'🇯🇵 {trans_text}\n⏱️ {duration:.2f}s', 
            fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # ====== Plot 2: Translation Info ======
    ax2 = fig.add_subplot(gs[1])
    ax2.axis('off')
    
    info_text = f"""
    SEGMENT INFORMATION
    ═══════════════════════════════════════════════════════════════════
    
    Original Language (Japanese):
    🇯🇵 {trans_text}
    
    Translated Language (English):
    🇬🇧 {translated_text}
    
    Duration Analysis:
    ⏱️  Original Duration: {duration:.2f}s
    ⏱️  Estimated Duration: {estimated_duration:.2f}s
    📊 Duration Ratio: {duration_ratio:.2f}x ({(duration_ratio - 1) * 100:+.1f}%)
    
    Quality: {'🎯 Excellent (0.95-1.05x)' if 0.95 <= duration_ratio <= 1.05 else '✅ Good (0.85-1.15x)' if 0.85 <= duration_ratio <= 1.15 else '⚠️  Acceptable'}
    """
    
    ax2.text(0.05, 0.95, info_text, transform=ax2.transAxes, 
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    # ====== Plot 3: Generated Voice Audio ======
    ax3 = fig.add_subplot(gs[2])
    
    # Try to load generated voice clip
    voice_pattern = f"work/voice_clips/segment_{segment_idx + 1:03d}_{speaker}.mp3"
    voice_files = glob.glob(voice_pattern)
    
    if voice_files:
        try:
            voice_audio, voice_sr = librosa.load(voice_files[0], sr=16000, mono=True)
            
            # Plot generated voice
            voice_duration = len(voice_audio) / voice_sr
            voice_times = np.linspace(start_time, start_time + voice_duration, len(voice_audio))
            ax3.plot(voice_times, voice_audio, linewidth=1, color='green', label='Generated Voice')
            ax3.fill_between(voice_times, voice_audio, alpha=0.3, color='green')
            
            # Highlight speech area
            y_min, y_max = ax3.get_ylim()
            rect3 = Rectangle((start_time, y_min), estimated_duration, y_max - y_min,
                             alpha=0.2, color='blue', label='Speech Area')
            ax3.add_patch(rect3)
            
            ax3.set_title(f'Generated Voice (English) - {speaker}', fontweight='bold')
            ax3.set_ylabel('Amplitude')
            ax3.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
            ax3.grid(True, alpha=0.3)
            ax3.legend(loc='upper right')
            
            # Add text
            ax3.text(start_time + estimated_duration/2, y_max * 0.8, 
                    f'🎙️ {translated_text}\n⏱️ {estimated_duration:.2f}s', 
                    fontsize=10, ha='center',
                    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        except Exception as e:
            ax3.text(0.5, 0.5, f'⚠️ Error loading voice: {str(e)}', 
                    ha='center', va='center', fontsize=12, transform=ax3.transAxes)
            ax3.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
            ax3.set_title('Generated Voice (ERROR)', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, f'⚠️ Voice file not found\nLooking for: {voice_pattern}', 
                ha='center', va='center', fontsize=12, transform=ax3.transAxes)
        ax3.set_xlim(max(0, start_time - 0.2), end_time + 0.2)
        ax3.set_title('Generated Voice (NOT FOUND)', fontweight='bold')
    
    # ====== Plot 4: Comparison Summary ======
    ax4 = fig.add_subplot(gs[3])
    ax4.axis('off')
    
    # Check alignment
    alignment_status = "✅ ALIGNED" if 0.85 <= duration_ratio <= 1.15 else "⚠️ MISALIGNED"
    alignment_color = 'lightgreen' if 0.85 <= duration_ratio <= 1.15 else 'lightyellow'
    
    summary_text = f"""
    ALIGNMENT VERIFICATION
    ═══════════════════════════════════════════════════════════════════
    
    Status: {alignment_status}
    
    ✓ Original Audio Duration:      {duration:.2f}s (Blue box in top panel)
    ✓ Generated Voice Duration:     {estimated_duration:.2f}s (Blue box in voice panel)
    ✓ Duration Match Ratio:         {duration_ratio:.2f}x
    
    Frequency Match Analysis:
    • If waveform patterns are similar → Audio quality is GOOD
    • If timing is aligned (±0.2s) → Dubbing will be in sync
    • If both match → READY for video assembly ✅
    """
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor=alignment_color, alpha=0.8))
    
    return fig


def create_full_timeline_visualization(original_audio, sr, segment_data, output_file):
    """Create a full timeline showing all segments"""
    
    segments = segment_data['transcription']['segments']
    total_duration = len(original_audio) / sr
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
    
    fig.suptitle('Complete Audio Timeline - All Segments', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Original Audio
    times_orig = np.arange(len(original_audio)) / sr
    axes[0].plot(times_orig, original_audio, linewidth=0.5, color='steelblue', alpha=0.7)
    axes[0].fill_between(times_orig, original_audio, alpha=0.2, color='steelblue')
    
    # Add segment boxes
    y_min, y_max = axes[0].get_ylim()
    for idx, seg in enumerate(segments):
        color = plt.cm.tab10(idx % 10)
        rect = Rectangle((seg['start'], y_min), 
                         seg['duration'], 
                         y_max - y_min,
                         alpha=0.15, color=color, edgecolor='black', linewidth=1)
        axes[0].add_patch(rect)
        axes[0].text(seg['start'] + seg['duration'] / 2, 
                    y_max * 0.7,
                    f"[{idx+1}]", ha='center', fontsize=8, fontweight='bold')
    
    axes[0].set_title('Original Audio - All Segments', fontweight='bold')
    axes[0].set_ylabel('Amplitude')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim(0, total_duration)
    
    # Plot 2: Segment Duration Comparison
    segment_nums = list(range(1, len(segments) + 1))
    original_durations = [seg['duration'] for seg in segment_data['transcription']['segments']]
    translated_durations = [seg['estimated_duration'] for seg in segment_data['translated']['segments']]
    
    x = np.arange(len(segment_nums))
    width = 0.35
    
    axes[1].bar(x - width/2, original_durations, width, label='Original (Japanese)', color='steelblue', alpha=0.7)
    axes[1].bar(x + width/2, translated_durations, width, label='Translated (English)', color='green', alpha=0.7)
    
    axes[1].set_title('Duration Comparison by Segment', fontweight='bold')
    axes[1].set_ylabel('Duration (seconds)')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f'Seg {n}' for n in segment_nums])
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Duration Ratio
    duration_ratios = [seg['duration_ratio'] for seg in segment_data['translated']['segments']]
    
    colors = ['green' if 0.95 <= r <= 1.05 else 'orange' if 0.85 <= r <= 1.15 else 'red' 
              for r in duration_ratios]
    
    axes[2].bar(segment_nums, duration_ratios, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
    axes[2].axhline(y=1.0, color='blue', linestyle='--', linewidth=2, label='Perfect Match (1.0x)')
    axes[2].axhline(y=0.85, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Acceptable Range (0.85-1.15x)')
    axes[2].axhline(y=1.15, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    
    axes[2].set_title('Duration Ratio (Translated / Original)', fontweight='bold')
    axes[2].set_ylabel('Ratio')
    axes[2].set_xlabel('Segment Number')
    axes[2].set_xticks(segment_nums)
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3, axis='y')
    axes[2].set_xlim(0.5, len(segment_nums) + 0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()


def main():
    print("=" * 70)
    print("AUDIO ALIGNMENT VISUALIZATION (FIXED)")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Missing required files. Please complete previous steps first.")
        return
    
    print("\n✅ All prerequisite files found")
    
    # Load audio
    print("\n🎵 Loading audio...")
    original_audio, sr = load_audio(ORIGINAL_AUDIO)
    if original_audio is None:
        return
    
    print(f"   Loaded: {len(original_audio) / sr:.1f}s @ {sr}Hz")
    
    # Load JSON data
    print("\n📄 Loading transcription and translation data...")
    data_files = load_data_files()
    if data_files is None:
        return
    
    # Create visualizations
    print("\n🎨 Creating visualizations...")
    
    # 1. Full timeline
    timeline_file = os.path.join(OUTPUT_DIR, "00_full_timeline.png")
    print(f"\n[1/3] Creating full timeline visualization...")
    create_full_timeline_visualization(original_audio, sr, data_files, timeline_file)
    
    # 2. Individual segment comparisons
    segments = data_files['transcription']['segments']
    
    print(f"\n[2/3] Creating individual segment comparisons...")
    successful = 0
    failed = 0
    
    for idx in range(len(segments)):
        print(f"   Segment {idx + 1}/{len(segments)}...", end=' ')
        
        try:
            fig = plot_segment_comparison(original_audio, sr, data_files, idx)
            
            segment_file = os.path.join(OUTPUT_DIR, f"{idx + 1:02d}_segment_{idx + 1}.png")
            fig.savefig(segment_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            print("✅")
            successful += 1
        except Exception as e:
            print(f"⚠️ {str(e)[:40]}")
            failed += 1
            continue
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ VISUALIZATION COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Output Directory: {OUTPUT_DIR}/")
    print(f"\n📊 Files Created:")
    print(f"   ✓ 00_full_timeline.png - Overall timeline with all segments")
    print(f"   ✓ {successful} individual segment visualizations (successful)")
    
    if failed > 0:
        print(f"   ⚠️  {failed} segments had issues (check voice files)")
    
    print(f"\n💡 How to Use:")
    print(f"   1. Open '00_full_timeline.png' to see all segments at once")
    print(f"   2. Open individual segment files to check alignment details")
    print(f"   3. Blue boxes show where speech occurs")
    print(f"   4. Check if original and generated voice waveforms match")
    print(f"   5. If duration ratio is 0.85-1.15x, alignment is GOOD ✅")
    
    print(f"\n🎯 Quality Indicators:")
    print(f"   🎯 Green = Perfect (0.95-1.05x)")
    print(f"   ✅ Orange = Good (0.85-1.15x)")
    print(f"   ❌ Red = Poor (<0.85x or >1.15x)")
    
    print(f"\n📊 Visual Guide:")
    print(f"   • Original Audio: Blue waveform (Japanese)")
    print(f"   • Generated Voice: Green waveform (English)")
    print(f"   • Blue boxes: Speech areas (should align)")
    print(f"   • If frequencies match: ✅ Quality is good")


if __name__ == "__main__":
    main()
