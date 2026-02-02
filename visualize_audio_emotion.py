# visualize_audio_emotion.py (Emotion-Based Audio Visualization)
import json
import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration
ORIGINAL_AUDIO = "work/audio_16k.wav"
TRANSCRIPTION_FILE = "work/transcription_with_speakers.json"
EMOTION_FILE = "work/emotion_detection.json"
TRANSLATED_FILE = "work/translated_segments.json"  # or translated_segments_interactive.json
VOICE_CLIPS_DIR = "work/voice_clips"

OUTPUT_DIR = "work/visualizations_emotion"

# Emotion Color Mapping
EMOTION_COLORS = {
    'angry': '#FF0000',      # Red
    'disgust': '#8B4513',    # Brown
    'fearful': '#FF8C00',    # Orange
    'happy': '#00AA00',      # Green
    'neutral': '#0066FF',    # Blue
    'sad': '#8B008B',        # Purple
    'surprised': '#FFD700',  # Gold/Yellow
    'calm': '#87CEEB'        # Sky Blue
}

EMOTION_NAMES = {
    'angry': 'Angry',
    'disgust': 'Disgusted',
    'fearful': 'Fearful',
    'happy': 'Happy',
    'neutral': 'Neutral',
    'sad': 'Sad',
    'surprised': 'Surprised',
    'calm': 'Calm'
}


def check_prerequisites():
    """Check if required files exist"""
    
    files_to_check = [
        ORIGINAL_AUDIO,
        TRANSCRIPTION_FILE,
        EMOTION_FILE
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
        
        with open(EMOTION_FILE, 'r', encoding='utf-8') as f:
            files['emotion'] = json.load(f)
        
        # Try to load translated file
        if os.path.exists(TRANSLATED_FILE):
            with open(TRANSLATED_FILE, 'r', encoding='utf-8') as f:
                files['translated'] = json.load(f)
        elif os.path.exists("work/translated_segments_interactive.json"):
            with open("work/translated_segments_interactive.json", 'r', encoding='utf-8') as f:
                files['translated'] = json.load(f)
        else:
            files['translated'] = None
        
        return files
    
    except Exception as e:
        print(f"❌ Error loading JSON files: {e}")
        return None


def create_emotion_timeline(audio, sr, emotion_data, output_file):
    """Create full timeline with emotion colors"""
    
    emotions = emotion_data['emotions']
    total_duration = len(audio) / sr
    
    fig, axes = plt.subplots(3, 1, figsize=(18, 12))
    
    fig.suptitle('🎭 Emotion-Based Audio Timeline Analysis', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # ====== Plot 1: Full Audio Waveform with Emotion Colors ======
    ax1 = axes[0]
    
    times = np.arange(len(audio)) / sr
    ax1.plot(times, audio, linewidth=0.3, color='gray', alpha=0.3, label='Audio')
    
    # Color segments by emotion
    y_min, y_max = np.min(audio), np.max(audio)
    
    for emotion_result in emotions:
        start = emotion_result['start']
        end = emotion_result['end']
        emotion = emotion_result['emotion']
        confidence = emotion_result['confidence']
        
        color = EMOTION_COLORS.get(emotion, '#CCCCCC')
        alpha = 0.3 + (confidence * 0.4)  # Higher confidence = more opaque
        
        # Extract segment audio
        start_idx = int(start * sr)
        end_idx = int(end * sr)
        segment_audio = audio[start_idx:end_idx]
        segment_times = times[start_idx:end_idx]
        
        # Plot colored segment
        ax1.plot(segment_times, segment_audio, 
                linewidth=0.8, color=color, alpha=0.8)
        
        # Add colored background
        rect = Rectangle((start, y_min), end - start, y_max - y_min,
                         alpha=alpha, color=color, edgecolor='none')
        ax1.add_patch(rect)
        
        # Add segment label
        mid_time = (start + end) / 2
        ax1.text(mid_time, y_max * 0.85, f"{emotion_result['segment_id']}", 
                ha='center', fontsize=8, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7, edgecolor='black'))
    
    ax1.set_title('Original Audio - Colored by Detected Emotion', fontweight='bold', fontsize=14)
    ax1.set_ylabel('Amplitude')
    ax1.set_xlim(0, total_duration)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel('Time (seconds)')
    
    # ====== Plot 2: Emotion Distribution Bar ======
    ax2 = axes[1]
    
    # Create emotion timeline bar
    for emotion_result in emotions:
        start = emotion_result['start']
        duration = emotion_result['duration']
        emotion = emotion_result['emotion']
        confidence = emotion_result['confidence']
        
        color = EMOTION_COLORS.get(emotion, '#CCCCCC')
        
        ax2.barh(0, duration, left=start, height=0.8, 
                color=color, edgecolor='black', linewidth=1)
        
        # Add text label
        mid_time = start + duration / 2
        ax2.text(mid_time, 0, f"{emotion_result['segment_id']}\n{emotion[:3].upper()}", 
                ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    
    ax2.set_title('Emotion Timeline (Sequential View)', fontweight='bold', fontsize=14)
    ax2.set_xlim(0, total_duration)
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_yticks([])
    ax2.set_xlabel('Time (seconds)')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # ====== Plot 3: Emotion Statistics ======
    ax3 = axes[2]
    
    # Count emotions
    emotion_counts = {}
    emotion_durations = {}
    
    for emotion_result in emotions:
        emotion = emotion_result['emotion']
        duration = emotion_result['duration']
        
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        emotion_durations[emotion] = emotion_durations.get(emotion, 0) + duration
    
    # Create bar chart
    emotions_list = sorted(emotion_counts.keys())
    counts = [emotion_counts[e] for e in emotions_list]
    durations = [emotion_durations[e] for e in emotions_list]
    colors = [EMOTION_COLORS.get(e, '#CCCCCC') for e in emotions_list]
    labels = [EMOTION_NAMES.get(e, e.capitalize()) for e in emotions_list]
    
    x = np.arange(len(emotions_list))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, counts, width, label='Count', 
                    color=colors, alpha=0.7, edgecolor='black')
    bars2 = ax3.bar(x + width/2, durations, width, label='Duration (s)', 
                    color=colors, alpha=0.9, edgecolor='black')
    
    ax3.set_title('Emotion Distribution Statistics', fontweight='bold', fontsize=14)
    ax3.set_ylabel('Count / Duration')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()


def create_segment_emotion_visualization(audio, sr, segment_data, segment_idx, output_file):
    """Create detailed visualization for a single segment with emotion"""
    
    trans_seg = segment_data['transcription']['segments'][segment_idx]
    emotion_result = segment_data['emotion']['emotions'][segment_idx]
    
    start_time = trans_seg['start']
    end_time = trans_seg['end']
    duration = trans_seg['duration']
    text = trans_seg['text']
    
    emotion = emotion_result['emotion']
    confidence = emotion_result['confidence']
    emotion_scores = emotion_result['scores']
    
    color = EMOTION_COLORS.get(emotion, '#CCCCCC')
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(4, 2, hspace=0.4, wspace=0.3)
    
    fig.suptitle(f'Segment {segment_idx + 1} - Emotion Analysis: {EMOTION_NAMES.get(emotion, emotion.upper())}', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # ====== Plot 1: Original Audio Waveform (Colored) ======
    ax1 = fig.add_subplot(gs[0, :])
    
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    audio_segment = audio[start_sample:end_sample]
    times = np.linspace(start_time, end_time, len(audio_segment))
    
    ax1.plot(times, audio_segment, linewidth=1.5, color=color, label=f'{emotion.capitalize()} Audio')
    ax1.fill_between(times, audio_segment, alpha=0.4, color=color)
    
    y_min, y_max = ax1.get_ylim()
    ax1.set_title(f'Original Audio - {emotion.upper()} ({confidence:.1%} confidence)', 
                  fontweight='bold', color=color)
    ax1.set_ylabel('Amplitude')
    ax1.set_xlim(start_time - 0.1, end_time + 0.1)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    
    # Add text annotation
    ax1.text(start_time + duration/2, y_max * 0.7, 
            f'🇯🇵 {text}\n⏱️  {duration:.2f}s', 
            fontsize=11, ha='center', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.7, edgecolor='black'))
    
    # ====== Plot 2: Emotion Confidence Scores ======
    ax2 = fig.add_subplot(gs[1, 0])
    
    emotions_list = list(emotion_scores.keys())
    scores = [emotion_scores[e] for e in emotions_list]
    colors_list = [EMOTION_COLORS.get(e, '#CCCCCC') for e in emotions_list]
    
    bars = ax2.barh(emotions_list, scores, color=colors_list, edgecolor='black', alpha=0.8)
    
    # Highlight detected emotion
    for i, e in enumerate(emotions_list):
        if e == emotion:
            bars[i].set_linewidth(3)
            bars[i].set_edgecolor('gold')
    
    ax2.set_title('All Emotion Scores', fontweight='bold')
    ax2.set_xlabel('Confidence Score')
    ax2.set_xlim(0, 1.0)
    ax2.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (e, s) in enumerate(zip(emotions_list, scores)):
        ax2.text(s + 0.02, i, f'{s:.2%}', va='center', fontsize=9)
    
    # ====== Plot 3: Emotion Color Legend ======
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')
    
    legend_text = "🎨 Emotion Color Guide:\n\n"
    for e, c in EMOTION_COLORS.items():
        legend_text += f"  ● {EMOTION_NAMES.get(e, e.capitalize())}\n"
    
    ax3.text(0.1, 0.95, legend_text, transform=ax3.transAxes,
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Add colored squares
    y_pos = 0.88
    for e, c in EMOTION_COLORS.items():
        rect = Rectangle((0.02, y_pos), 0.05, 0.05, 
                         transform=ax3.transAxes, facecolor=c, edgecolor='black')
        ax3.add_patch(rect)
        y_pos -= 0.10
    
    # ====== Plot 4: Spectrogram (Colored by emotion) ======
    ax4 = fig.add_subplot(gs[2, :])
    
    D = librosa.amplitude_to_db(np.abs(librosa.stft(audio_segment)), ref=np.max)
    
    # Use emotion color for spectrogram
    cmap = plt.cm.colors.LinearSegmentedColormap.from_list(
        'emotion_cmap', ['white', color, 'black']
    )
    
    img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='hz', 
                                   cmap=cmap, ax=ax4)
    ax4.set_title(f'Spectrogram - {emotion.upper()}', fontweight='bold')
    ax4.set_xlim(0, duration)
    fig.colorbar(img, ax=ax4, format='%+2.0f dB')
    
    # ====== Plot 5: Translation Info (if available) ======
    ax5 = fig.add_subplot(gs[3, :])
    ax5.axis('off')
    
    info_text = f"""
    EMOTION ANALYSIS SUMMARY
    ═══════════════════════════════════════════════════════════════════
    
    Detected Emotion: {emotion.upper()} ({confidence:.1%} confidence)
    Emotion Tag: {segment_data['emotion']['emotion_to_tag_mapping'].get(emotion, '(none)')}
    
    Original (Japanese): {text}
    Duration: {duration:.2f}s
    
    Quality Assessment:
    """
    
    if confidence >= 0.7:
        info_text += "    ✅ Strong emotion detection - Safe to use emotion tag\n"
    elif confidence >= 0.5:
        info_text += "    ⚠️  Moderate emotion detection - Use emotion tag with caution\n"
    elif confidence >= 0.3:
        info_text += "    ⚠️  Weak emotion detection - Consider using neutral\n"
    else:
        info_text += "    ❌ Unclear emotion - Use neutral (no tag)\n"
    
    info_text += f"\n    Top 3 Emotions:\n"
    sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for i, (e, s) in enumerate(sorted_emotions, 1):
        info_text += f"       {i}. {e.capitalize()}: {s:.1%}\n"
    
    ax5.text(0.05, 0.95, info_text, transform=ax5.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.3, edgecolor='black'))
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()


def create_emotion_comparison_chart(emotion_data, output_file):
    """Create emotion comparison and statistics chart"""
    
    emotions = emotion_data['emotions']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('🎭 Complete Emotion Analysis', fontsize=18, fontweight='bold')
    
    # ====== Plot 1: Emotion Count Pie Chart ======
    ax1 = axes[0, 0]
    
    emotion_counts = {}
    for e in emotions:
        emotion = e['emotion']
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    labels = [EMOTION_NAMES.get(e, e.capitalize()) for e in emotion_counts.keys()]
    sizes = list(emotion_counts.values())
    colors = [EMOTION_COLORS.get(e, '#CCCCCC') for e in emotion_counts.keys()]
    
    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                         startangle=90, textprops={'fontsize': 11})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax1.set_title('Emotion Distribution by Count', fontweight='bold', fontsize=14)
    
    # ====== Plot 2: Emotion Duration Bar Chart ======
    ax2 = axes[0, 1]
    
    emotion_durations = {}
    for e in emotions:
        emotion = e['emotion']
        duration = e['duration']
        emotion_durations[emotion] = emotion_durations.get(emotion, 0) + duration
    
    emotions_list = list(emotion_durations.keys())
    durations = [emotion_durations[e] for e in emotions_list]
    colors_list = [EMOTION_COLORS.get(e, '#CCCCCC') for e in emotions_list]
    labels_list = [EMOTION_NAMES.get(e, e.capitalize()) for e in emotions_list]
    
    bars = ax2.bar(labels_list, durations, color=colors_list, edgecolor='black', alpha=0.8)
    ax2.set_title('Total Duration by Emotion', fontweight='bold', fontsize=14)
    ax2.set_ylabel('Duration (seconds)')
    ax2.set_xlabel('Emotion')
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # ====== Plot 3: Confidence Distribution ======
    ax3 = axes[1, 0]
    
    for emotion_name in emotion_counts.keys():
        confidences = [e['confidence'] for e in emotions if e['emotion'] == emotion_name]
        color = EMOTION_COLORS.get(emotion_name, '#CCCCCC')
        label = EMOTION_NAMES.get(emotion_name, emotion_name.capitalize())
        
        ax3.hist(confidences, bins=10, alpha=0.6, color=color, 
                label=label, edgecolor='black')
    
    ax3.set_title('Emotion Confidence Distribution', fontweight='bold', fontsize=14)
    ax3.set_xlabel('Confidence Score')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # ====== Plot 4: Timeline Scatter ======
    ax4 = axes[1, 1]
    
    for e in emotions:
        mid_time = (e['start'] + e['end']) / 2
        confidence = e['confidence']
        emotion = e['emotion']
        color = EMOTION_COLORS.get(emotion, '#CCCCCC')
        
        ax4.scatter(mid_time, confidence, c=color, s=200, 
                   edgecolors='black', linewidth=2, alpha=0.7)
        ax4.text(mid_time, confidence + 0.03, str(e['segment_id']), 
                ha='center', fontsize=8, fontweight='bold')
    
    ax4.set_title('Emotion Confidence Over Time', fontweight='bold', fontsize=14)
    ax4.set_xlabel('Time (seconds)')
    ax4.set_ylabel('Confidence')
    ax4.set_ylim(0, 1.1)
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0.7, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Strong (>70%)')
    ax4.axhline(y=0.5, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Moderate (>50%)')
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()


def main():
    print("=" * 70)
    print("🎨 EMOTION-BASED AUDIO VISUALIZATION")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Missing required files. Please complete previous steps first.")
        return
    
    print("\n✅ All prerequisite files found")
    
    # Load audio
    print("\n🎵 Loading audio...")
    audio, sr = load_audio(ORIGINAL_AUDIO)
    if audio is None:
        return
    
    print(f"   Loaded: {len(audio) / sr:.1f}s @ {sr}Hz")
    
    # Load data
    print("\n📄 Loading data files...")
    data_files = load_data_files()
    if data_files is None:
        return
    
    segments = data_files['transcription']['segments']
    
    print("\n🎨 Creating emotion visualizations...")
    
    # 1. Full timeline with emotions
    print(f"\n[1/4] Creating emotion timeline...")
    timeline_file = os.path.join(OUTPUT_DIR, "00_emotion_timeline.png")
    create_emotion_timeline(audio, sr, data_files['emotion'], timeline_file)
    
    # 2. Emotion comparison chart
    print(f"\n[2/4] Creating emotion statistics chart...")
    comparison_file = os.path.join(OUTPUT_DIR, "01_emotion_statistics.png")
    create_emotion_comparison_chart(data_files['emotion'], comparison_file)
    
    # 3. Individual segment visualizations
    print(f"\n[3/4] Creating individual segment visualizations...")
    for idx in range(min(len(segments), 15)):  # First 15 segments
        print(f"   Segment {idx + 1}/{min(len(segments), 15)}...", end=' ')
        
        try:
            segment_file = os.path.join(OUTPUT_DIR, f"segment_{idx + 1:02d}_emotion.png")
            create_segment_emotion_visualization(audio, sr, data_files, idx, segment_file)
            print("✅")
        except Exception as e:
            print(f"⚠️  Error: {str(e)[:40]}")
            continue
    
    print(f"\n[4/4] Creating emotion color legend...")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ EMOTION VISUALIZATION COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Output Directory: {OUTPUT_DIR}/")
    print(f"\n📊 Files Created:")
    print(f"   ✓ 00_emotion_timeline.png - Full timeline with emotion colors")
    print(f"   ✓ 01_emotion_statistics.png - Emotion distribution charts")
    print(f"   ✓ segment_XX_emotion.png - Individual segment analyses")
    
    print(f"\n🎨 Color Guide:")
    for emotion, color in EMOTION_COLORS.items():
        name = EMOTION_NAMES.get(emotion, emotion.capitalize())
        print(f"   {name:<12} : {color}")
    
    print(f"\n💡 How to Use:")
    print(f"   1. Open '00_emotion_timeline.png' to see all emotions at once")
    print(f"   2. Open '01_emotion_statistics.png' for distribution analysis")
    print(f"   3. Open individual segment files for detailed emotion analysis")
    print(f"   4. Colors represent emotions throughout the visualization")
    print(f"   5. Brighter colors = higher confidence")
    
    print(f"\n✨ Features:")
    print(f"   • Waveforms colored by detected emotion")
    print(f"   • Emotion timeline showing sequential emotions")
    print(f"   • Statistical charts (pie, bar, scatter)")
    print(f"   • Individual segment spectrograms")
    print(f"   • Confidence score visualizations")


if __name__ == "__main__":
    main()
