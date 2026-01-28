# check_translation_accuracy.py
import json
import os
import subprocess
import re
from difflib import SequenceMatcher
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# Configuration
VIDEO_FILE = "input/anime_sample.mp4"
TRANSLATED_JSON = "work/translated_segments.json"
SUBTITLES_OUTPUT = "work/extracted_subtitles.srt"

def check_prerequisites():
    """Check if required files exist"""
    
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Video file not found: {VIDEO_FILE}")
        return False
    
    if not os.path.exists(TRANSLATED_JSON):
        print(f"❌ Translation file not found: {TRANSLATED_JSON}")
        print("   Please run step4_translation_free.py first")
        return False
    
    return True

def extract_subtitles_from_video():
    """Extract embedded subtitles from video using ffmpeg"""
    
    print("🎬 Checking for embedded subtitles...")
    
    try:
        # Check if video has subtitle streams
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 's',
            '-show_entries', 'stream=index:stream_tags=language',
            '-of', 'json',
            VIDEO_FILE
        ]
        
        result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        probe_data = json.loads(result.stdout)
        streams = probe_data.get('streams', [])
        
        if not streams:
            print("⚠️  No embedded subtitles found in video")
            print("   Will try alternative method...")
            return None
        
        print(f"✅ Found {len(streams)} subtitle stream(s)")
        
        # Extract first subtitle stream (usually English)
        extract_cmd = [
            'ffmpeg',
            '-i', VIDEO_FILE,
            '-map', '0:s:0',  # First subtitle stream
            '-y',  # Overwrite
            SUBTITLES_OUTPUT
        ]
        
        subprocess.run(
            extract_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Extracted subtitles to: {SUBTITLES_OUTPUT}")
        return SUBTITLES_OUTPUT
    
    except subprocess.CalledProcessError as e:
        print(f"⚠️  FFmpeg error: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return None

def parse_srt_file(srt_path):
    """Parse SRT subtitle file"""
    
    if not os.path.exists(srt_path):
        return []
    
    print(f"📖 Parsing subtitle file...")
    
    with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Parse SRT format
    # Format:
    # 1
    # 00:00:01,000 --> 00:00:03,000
    # Subtitle text
    
    pattern = r'(\d+)\n(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\n(.*?)(?=\n\n|\Z)'
    
    matches = re.findall(pattern, content, re.DOTALL)
    
    subtitles = []
    for match in matches:
        idx = int(match[0])
        
        # Start time
        start_h, start_m, start_s, start_ms = map(int, match[1:5])
        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
        
        # End time
        end_h, end_m, end_s, end_ms = map(int, match[5:9])
        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
        
        # Text
        text = match[9].strip().replace('\n', ' ')
        
        subtitles.append({
            'index': idx,
            'start': start_time,
            'end': end_time,
            'duration': end_time - start_time,
            'text': text
        })
    
    print(f"✅ Found {len(subtitles)} subtitle entries")
    return subtitles

def load_our_translations():
    """Load our AI translations"""
    
    with open(TRANSLATED_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {len(data['segments'])} AI translations")
    return data['segments']

def match_subtitles_to_translations(subtitles, translations):
    """Match subtitle entries with our translations based on timing"""
    
    print("\n🔗 Matching subtitles with translations...")
    
    matches = []
    
    for trans in translations:
        trans_start = trans['start']
        trans_mid = trans_start + (trans['duration'] / 2)
        
        # Find subtitle that overlaps with this translation
        best_match = None
        best_overlap = 0
        
        for sub in subtitles:
            # Check if timings overlap
            overlap_start = max(trans['start'], sub['start'])
            overlap_end = min(trans['end'], sub['end'])
            overlap = overlap_end - overlap_start
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = sub
        
        if best_match:
            matches.append({
                'ai_translation': trans['translated_text'],
                'reference_subtitle': best_match['text'],
                'time': f"{trans['start']:.1f}s - {trans['end']:.1f}s",
                'japanese': trans.get('original_text', ''),
                'overlap': best_overlap
            })
    
    print(f"✅ Matched {len(matches)} translation pairs")
    return matches

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts"""
    
    # Convert to lowercase and remove punctuation
    text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
    text2_clean = re.sub(r'[^\w\s]', '', text2.lower())
    
    # Sequence matcher (character-level similarity)
    sequence_ratio = SequenceMatcher(None, text1_clean, text2_clean).ratio()
    
    # Word-level similarity
    words1 = set(text1_clean.split())
    words2 = set(text2_clean.split())
    
    if len(words1) == 0 or len(words2) == 0:
        word_overlap = 0
    else:
        common_words = words1.intersection(words2)
        word_overlap = len(common_words) / max(len(words1), len(words2))
    
    # Average of both metrics
    similarity = (sequence_ratio + word_overlap) / 2
    
    return similarity * 100

def calculate_bleu_score(reference, candidate):
    """Calculate BLEU score (translation quality metric)"""
    
    try:
        # Tokenize
        reference_tokens = reference.lower().split()
        candidate_tokens = candidate.lower().split()
        
        # BLEU score with smoothing
        smoothing = SmoothingFunction().method1
        score = sentence_bleu(
            [reference_tokens], 
            candidate_tokens,
            smoothing_function=smoothing
        )
        
        return score * 100
    except:
        return 0

def analyze_matches(matches):
    """Analyze translation accuracy"""
    
    print("\n" + "="*70)
    print("📊 TRANSLATION ACCURACY ANALYSIS")
    print("="*70)
    
    if not matches:
        print("❌ No matches found for comparison")
        return
    
    total_similarity = 0
    total_bleu = 0
    
    results = []
    
    for idx, match in enumerate(matches, 1):
        ai_text = match['ai_translation']
        ref_text = match['reference_subtitle']
        
        # Calculate metrics
        similarity = calculate_similarity(ai_text, ref_text)
        bleu = calculate_bleu_score(ref_text, ai_text)
        
        total_similarity += similarity
        total_bleu += bleu
        
        results.append({
            'index': idx,
            'japanese': match['japanese'],
            'ai_translation': ai_text,
            'reference': ref_text,
            'similarity': similarity,
            'bleu': bleu,
            'time': match['time']
        })
    
    # Calculate averages
    avg_similarity = total_similarity / len(matches)
    avg_bleu = total_bleu / len(matches)
    
    # Display results
    print(f"\n📈 Overall Scores:")
    print(f"   Total comparisons: {len(matches)}")
    print(f"   Average Similarity: {avg_similarity:.1f}%")
    print(f"   Average BLEU Score: {avg_bleu:.1f}%")
    
    # Interpretation
    print(f"\n💡 Quality Assessment:")
    if avg_similarity >= 80:
        print("   ✅ EXCELLENT - Translations are very accurate")
    elif avg_similarity >= 60:
        print("   ✅ GOOD - Translations capture the meaning well")
    elif avg_similarity >= 40:
        print("   ⚠️  FAIR - Some meaning preserved, needs improvement")
    else:
        print("   ❌ POOR - Significant differences from reference")
    
    # Display detailed comparisons
    print("\n" + "="*70)
    print("📋 DETAILED COMPARISON (All Segments)")
    print("="*70)
    
    for result in results:
        print(f"\n[Segment {result['index']}] {result['time']}")
        print(f"🇯🇵 Japanese: {result['japanese']}")
        print(f"🤖 AI Translation: {result['ai_translation']}")
        print(f"📺 Reference (Video): {result['reference']}")
        print(f"📊 Similarity: {result['similarity']:.1f}% | BLEU: {result['bleu']:.1f}%")
        
        # Visual indicator
        if result['similarity'] >= 70:
            print("   ✅ Very close match")
        elif result['similarity'] >= 50:
            print("   ⚠️  Moderate match")
        else:
            print("   ❌ Significant difference")
    
    # Save detailed results
    output_file = "work/translation_accuracy_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_comparisons': len(matches),
                'average_similarity': avg_similarity,
                'average_bleu': avg_bleu
            },
            'detailed_results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed report saved to: {output_file}")

def manual_subtitle_entry():
    """Manually enter subtitles if video doesn't have embedded ones"""
    
    print("\n" + "="*70)
    print("⌨️  MANUAL SUBTITLE ENTRY MODE")
    print("="*70)
    print("\nNo embedded subtitles found in video.")
    print("You can manually enter reference translations for comparison.")
    print("\nOptions:")
    print("1. Enter subtitles manually (for each segment)")
    print("2. Skip accuracy check and continue")
    
    choice = input("\nEnter choice (1/2): ").strip()
    
    if choice != "1":
        print("⏭️  Skipping accuracy check")
        return []
    
    # Load AI translations
    translations = load_our_translations()
    
    print(f"\n📝 Enter reference English subtitle for each segment:")
    print("   (Press Enter to skip a segment)\n")
    
    subtitles = []
    
    for idx, trans in enumerate(translations, 1):
        print(f"\n[{idx}/{len(translations)}]")
        print(f"Time: {trans['start']:.1f}s - {trans['end']:.1f}s")
        print(f"Japanese: {trans.get('original_text', 'N/A')}")
        print(f"AI Translation: {trans['translated_text']}")
        
        ref = input("Reference subtitle: ").strip()
        
        if ref:
            subtitles.append({
                'start': trans['start'],
                'end': trans['end'],
                'duration': trans['duration'],
                'text': ref
            })
    
    return subtitles

def main():
    print("=" * 70)
    print("TRANSLATION ACCURACY CHECKER")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Try to extract subtitles from video
    subtitle_file = extract_subtitles_from_video()
    
    if subtitle_file:
        # Parse extracted subtitles
        subtitles = parse_srt_file(subtitle_file)
    else:
        # Manual entry option
        subtitles = manual_subtitle_entry()
    
    if not subtitles:
        print("\n⚠️  No reference subtitles available for comparison")
        print("   Cannot calculate accuracy without reference translations")
        return
    
    # Load our translations
    translations = load_our_translations()
    
    # Match subtitles with translations
    matches = match_subtitles_to_translations(subtitles, translations)
    
    # Analyze accuracy
    analyze_matches(matches)
    
    print("\n" + "=" * 70)
    print("✅ Accuracy Check Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
