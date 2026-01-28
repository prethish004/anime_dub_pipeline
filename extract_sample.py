# extract_sample.py
import ffmpeg
import os

input_file = "input/Download.mp4"  # Change this to your file
output_file = "input/anime_sample.mp4"

if not os.path.exists(input_file):
    print(f"❌ File not found: {input_file}")
    print("Please place your anime episode in the 'input/' folder")
    exit()

print("Extracting first 5 minutes...")

# Extract first 5 minutes (300 seconds)
stream = ffmpeg.input(input_file, ss=0, t=300)
stream = ffmpeg.output(stream, output_file, c='copy')
ffmpeg.run(stream, overwrite_output=True, quiet=False)

print(f"✅ Sample created: {output_file}")
