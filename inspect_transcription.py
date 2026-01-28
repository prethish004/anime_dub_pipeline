# inspect_transcription.py
import json

# Load transcription
with open('work/transcription.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Model: {data['model']}")
print(f"Language: {data['language']}")
print(f"Total segments: {data['total_segments']}")
print("\n" + "="*60)
print("ALL TRANSCRIPTION SEGMENTS")
print("="*60)

for seg in data['segments']:
    print(f"\n[Segment {seg['id']}]")
    print(f"Time: {seg['start']:.2f}s - {seg['end']:.2f}s (Duration: {seg['duration']:.2f}s)")
    print(f"Text: {seg['text']}")

# Calculate total duration
if data['segments']:
    total_duration = data['segments'][-1]['end']
    print(f"\n📊 Total audio duration: {total_duration:.2f}s ({total_duration/60:.1f} minutes)")
