import os
import subprocess
import sys
import pprint

def merge_subtitles_in_season(season_folder_path):
    # Get a list of all mp4 files in the directory and sort them alphabetically
    files = sorted([f for f in os.listdir(season_folder_path) if f.endswith('.mp4')])

    for video_file in files:
        base_name = os.path.splitext(video_file)[0]
        video_file_path = os.path.join(season_folder_path, video_file)
        subtitle_file_path = os.path.join(season_folder_path, f"{base_name}.srt")
        output_file_path = os.path.join(season_folder_path, f"{base_name}.output.mp4")

        # Check if the corresponding subtitle file exists
        if not os.path.isfile(subtitle_file_path):
            print(f"Subtitle file not found for {video_file}. Skipping.")
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

        # Print the ffmpeg command
        print("Executing ffmpeg command:")
        pprint.pprint(command)

        # Run ffmpeg command
        subprocess.run(command, check=True)
        print(f"Processed {video_file} successfully in {season_folder_path}.")

def process_tv_show_folder(tv_show_folder_path):
    # Get a list of all subdirectories in the TV show folder (i.e., season folders) and sort them alphabetically
    season_folders = sorted([os.path.join(tv_show_folder_path, d) for d in os.listdir(tv_show_folder_path) if os.path.isdir(os.path.join(tv_show_folder_path, d))])

    for season_folder in season_folders:
        print(f"Processing season folder: {season_folder}")
        merge_subtitles_in_season(season_folder)

    print("All season folders processed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_subtitles.py <tv_show_folder_path>")
        sys.exit(1)

    tv_show_folder_path = sys.argv[1]
    if not os.path.isdir(tv_show_folder_path):
        print("Invalid TV show folder path provided.")
        sys.exit(1)

    process_tv_show_folder(tv_show_folder_path)
