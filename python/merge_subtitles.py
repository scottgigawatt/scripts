import os
import subprocess
import sys

def merge_subtitles(folder_path):
    # Get a list of all mp4 files in the directory and sort them alphabetically
    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp4')])

    for video_file in files:
        base_name = os.path.splitext(video_file)[0]
        video_file_path = os.path.join(folder_path, video_file)
        subtitle_file_path = os.path.join(folder_path, f"{base_name}.srt")
        output_file_path = os.path.join(folder_path, f"{base_name}_output.mp4")

        # Check if the corresponding subtitle file exists
        if not os.path.isfile(subtitle_file_path):
            print(f"Subtitle file not found for {video_file}")
            continue

        # Construct ffmpeg command
        command = [
            'ffmpeg',
            '-i', video_file_path,
            '-i', subtitle_file_path,
            '-map', '0',
            '-map', '1',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'mov_text',
            '-metadata:s:v:0', 'language=eng',
            '-metadata:s:a:0', 'language=eng',
            '-metadata:s:s:0', 'language=eng',
            output_file_path
        ]

        # Run ffmpeg command
        subprocess.run(command, check=True)
        print(f"Processed {video_file} successfully.")

    print("All files processed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_subtitles.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print("Invalid folder path provided.")
        sys.exit(1)

    merge_subtitles(folder_path)
