import os
import subprocess
import sys
import pprint
import shlex

DEBUG = False

def run_command(cmd):
    if DEBUG:
        print("Running command:", ' '.join(shlex.quote(arg) for arg in cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    if DEBUG:
        print("Command output:", result.stdout)
        print("Command error (if any):", result.stderr)
    return result

def get_audio_track_count(video_file_path):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a',
        '-show_entries', 'stream=index',
        '-of', 'csv=p=0',
        video_file_path
    ]
    result = run_command(cmd)
    return len(result.stdout.strip().split('\n'))

def get_audio_track_language(video_file_path, track_index):
    cmd = [
        'ffprobe',
        '-v', 'error',
        f'-select_streams', f'a:{track_index}',
        '-show_entries', 'stream_tags=language',
        '-of', 'csv=p=0',
        video_file_path
    ]
    result = run_command(cmd)
    return result.stdout.strip()

def get_audio_track_title(video_file_path, track_index):
    cmd = [
        'ffprobe',
        '-v', 'error',
        f'-select_streams', f'a:{track_index}',
        '-show_entries', 'stream_tags=title',
        '-of', 'csv=p=0',
        video_file_path
    ]
    result = run_command(cmd)
    return result.stdout.strip()

def get_audio_channels(video_file_path, track_index):
    cmd = [
        'ffprobe',
        '-v', 'error',
        f'-select_streams', f'a:{track_index}',
        '-show_entries', 'stream=channels',
        '-of', 'csv=p=0',
        video_file_path
    ]
    result = run_command(cmd)
    return int(result.stdout.strip())

def add_audio_metadata_commands(video_file_path, command):
    audio_count = get_audio_track_count(video_file_path)
    if audio_count > 0:
        print(f"Found {audio_count} audio track(s). Setting language to English.")
        for i in range(audio_count):
            audio_language = get_audio_track_language(video_file_path, i)
            if audio_language == 'eng' or audio_language == 'und':
                current_title = get_audio_track_title(video_file_path, i)
                channels = get_audio_channels(video_file_path, i)
                if channels == 1:
                    base_title = "Mono Audio"
                elif channels == 2:
                    base_title = "Stereo Audio"
                else:
                    base_title = "Surround Audio"

                if "commentary" in current_title.lower():
                    base_title += " (Commentary)"

                command.extend([
                    f'-metadata:s:a:{i}', 'language=eng',
                    f'-metadata:s:a:{i}', f'title={base_title}'
                ])
            else:
                command.extend([
                    f'-map', f'-0:a:{i}'
                ])
    else:
        print("No audio tracks found in the video file.")

def merge_subtitles_in_season(season_folder_path):
    files = sorted([f for f in os.listdir(season_folder_path) if f.endswith('.mp4')])

    for video_file in files:
        base_name = os.path.splitext(video_file)[0]
        video_file_path = os.path.join(season_folder_path, video_file)
        subtitle_file_path = os.path.join(season_folder_path, f"{base_name}.srt")
        output_file_path = os.path.join(season_folder_path, f"{base_name}.output.mp4")

        if not os.path.isfile(subtitle_file_path):
            print(f"Subtitle file not found for {video_file}. Skipping.")
            continue

        command = [
            'ffmpeg',
            '-y',  # Overwrite output files without asking
            '-i', video_file_path,
            '-i', subtitle_file_path,
            '-map', '0',
            '-map', '1',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'mov_text',
            '-metadata:s:v:0', 'language=eng',
            '-metadata:s:s:0', 'language=eng'
        ]

        add_audio_metadata_commands(video_file_path, command)

        command.append(output_file_path)

        print("Executing ffmpeg command:")
        pprint.pprint(command)

        run_command(command)
        print(f"Processed {video_file} successfully in {season_folder_path}.")

def merge_subtitles_in_movie_folder(movie_folder_path):
    files = [f for f in os.listdir(movie_folder_path) if f.endswith('.mp4')]
    if not files:
        print(f"No MP4 files found in {movie_folder_path}.")
        return

    video_file = files[0]
    video_file_path = os.path.join(movie_folder_path, video_file)
    subtitle_files = [f for f in os.listdir(movie_folder_path) if f.endswith('.srt')]
    if not subtitle_files:
        print(f"No subtitle files found in {movie_folder_path}. Skipping {video_file}.")
        return

    base_name = os.path.splitext(video_file)[0]
    output_file_path = os.path.join(movie_folder_path, f"{base_name}.output.mp4")

    command = ['ffmpeg', '-y', '-i', video_file_path]

    for subtitle_file in subtitle_files:
        subtitle_file_path = os.path.join(movie_folder_path, subtitle_file)
        command.extend(['-i', subtitle_file_path])

    command.extend(['-map', '0', '-c:v', 'copy', '-c:a', 'copy'])

    for i, subtitle_file in enumerate(subtitle_files):
        map_command = ['-map', str(i + 1)]
        language_command = ['-metadata:s:s:' + str(i), 'language=eng']

        if 'sdh' in subtitle_file.lower():
            track_name = 'Subtitle Track [SDH]'
        elif 'forced' in subtitle_file.lower():
            track_name = 'Subtitle Track [Forced]'
        elif 'cc' in subtitle_file.lower():
            track_name = 'Subtitle Track [CC]'
        else:
            track_name = 'Subtitle Track'

        metadata_command = ['-metadata:s:s:' + str(i), f'title={track_name}']
        command.extend(map_command + language_command + metadata_command)

    add_audio_metadata_commands(video_file_path, command)

    command.extend(['-metadata:s:v:0', 'language=eng', '-metadata:s:a:0', 'language=eng', '-c:s', 'mov_text'])
    command.append(output_file_path)

    print("Executing ffmpeg command:")
    pprint.pprint(command)

    run_command(command)
    print(f"Processed {video_file} successfully in {movie_folder_path}.")

def process_tv_show_folder(tv_show_folder_path):
    season_folders = sorted([os.path.join(tv_show_folder_path, d) for d in os.listdir(tv_show_folder_path) if os.path.isdir(os.path.join(tv_show_folder_path, d))])

    for season_folder in season_folders:
        print(f"Processing season folder: {season_folder}")
        merge_subtitles_in_season(season_folder)

    print("All season folders processed successfully.")

def process_movie_folder(movie_folder_path):
    movie_folders = sorted([os.path.join(movie_folder_path, d) for d in os.listdir(movie_folder_path) if os.path.isdir(os.path.join(movie_folder_path, d))])

    for movie_folder in movie_folders:
        print(f"Processing movie folder: {movie_folder}")
        merge_subtitles_in_movie_folder(movie_folder)

    print("All movie folders processed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python merge_subtitles.py <tv|movies> <folder_path> [--debug]")
        sys.exit(1)

    mode = sys.argv[1]
    folder_path = sys.argv[2]

    if len(sys.argv) == 4 and sys.argv[3] == '--debug':
        DEBUG = True

    if not os.path.isdir(folder_path):
        print("Invalid folder path provided.")
        sys.exit(1)

    if mode == 'tv':
        process_tv_show_folder(folder_path)
    elif mode == 'movies':
        process_movie_folder(folder_path)
    else:
        print("Invalid mode provided. Use 'tv' or 'movies'.")
        sys.exit(1)
