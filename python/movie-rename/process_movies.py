import os
import subprocess
import sys
import pprint
import shlex
import shutil

DEBUG = False
FORCE = False

def run_command(cmd):
    if DEBUG:
        print("Running command:", ' '.join(shlex.quote(arg) for arg in cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    if DEBUG:
        print("Command output:", result.stdout)
        print("Command error (if any):", result.stderr)
    return result

def filter_files_in_folder(folder, extensions):
    """
    Filters files in a folder by extensions.
    """
    return [f for f in os.listdir(folder) if f.lower().endswith(tuple(extensions))]

def get_audio_track_count(video_file_path):
    """
    Retrieves the number of audio tracks in the video file.
    """
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
    """
    Retrieves the language of the specified audio track.
    """
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

def get_audio_channels(video_file_path, track_index):
    """
    Retrieves the number of channels for the specified audio track.
    """
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
    """
    Updates the metadata for all audio tracks to ensure proper naming and language.
    Keeps only English or undefined audio tracks.
    """
    audio_count = get_audio_track_count(video_file_path)
    if audio_count > 0:
        for i in range(audio_count):
            audio_language = get_audio_track_language(video_file_path, i)
            if audio_language in ['eng', 'und']:  # Keep English or undefined tracks
                channels = get_audio_channels(video_file_path, i)
                if channels == 1:
                    base_title = "Mono Audio"
                elif channels == 2:
                    base_title = "Stereo Audio"
                else:
                    base_title = "Surround Audio"

                command.extend([
                    f'-metadata:s:a:{i}', 'language=eng',
                    f'-metadata:s:a:{i}', f'title={base_title}'
                ])
            else:
                # Exclude non-English audio tracks
                print(f"Excluding non-English audio track a:{i} ({audio_language})")
                command.extend(['-map', f'-0:a:{i}'])

def convert_mkv_to_mp4(video_file_path):
    """
    Converts an MKV file to MP4 without re-encoding.
    """
    output_file = os.path.splitext(video_file_path)[0] + ".mp4"
    cmd = [
        'ffmpeg', '-y', '-i', video_file_path,
        '-c:v', 'copy', '-c:a', 'copy',
        '-c:s', 'mov_text',
        output_file
    ]
    print(f"Converting {video_file_path} to MP4.")
    run_command(cmd)
    print(f"Converted {video_file_path} to {output_file}.")
    return output_file

def process_movie_file(video_file_path, subtitle_files, output_file_path):
    """
    Processes a single movie file by updating metadata and merging subtitles.
    After creating the final output file, creates a backup directory and moves all other files into it.
    """
    if os.path.exists(output_file_path) and not FORCE:
        print(f"Output file {output_file_path} already exists. Skipping. Use --force to overwrite.")
        return

    # Build the ffmpeg command
    command = ['ffmpeg', '-y' if FORCE else '-n', '-i', video_file_path]

    # Add subtitle files (ensure full paths)
    for subtitle_file in sorted(subtitle_files, key=lambda x: 'sdh' in x.lower()):
        subtitle_file_path = os.path.join(os.path.dirname(video_file_path), subtitle_file)
        command.extend(['-i', subtitle_file_path])

    # Map video and audio streams
    command.extend(['-map', '0', '-c:v', 'copy', '-c:a', 'copy'])

    # Map subtitles and set metadata
    for i, subtitle_file in enumerate(sorted(subtitle_files, key=lambda x: 'sdh' in x.lower())):
        map_command = ['-map', f"{i + 1}"]
        language_command = ['-metadata:s:s:' + str(i), 'language=eng']

        if 'sdh' in subtitle_file.lower():
            track_name = 'Subtitle Track [SDH]'
        else:
            track_name = 'Subtitle Track'

        metadata_command = ['-metadata:s:s:' + str(i), f'title={track_name}']
        command.extend(map_command + language_command + metadata_command)

    # Set video and audio metadata
    command.extend(['-metadata:s:v:0', 'language=eng'])
    add_audio_metadata_commands(video_file_path, command)

    # Set subtitle codec
    command.extend(['-c:s', 'mov_text'])

    # Add the output file path
    command.append(output_file_path)

    print("Executing ffmpeg command:")
    pprint.pprint(command)

    # Execute the ffmpeg command
    try:
        run_command(command)
        print(f"Processed {video_file_path} successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to process {video_file_path}.")
        print(f"Error: {e.stderr}")
        return

    # Create a backup directory and move all other files into it
    backup_dir = os.path.join(os.path.dirname(video_file_path), "backup")
    os.makedirs(backup_dir, exist_ok=True)

    # Move all files except the output file and the backup directory into the backup directory
    movie_folder = os.path.dirname(video_file_path)
    for file_name in os.listdir(movie_folder):
        file_path = os.path.join(movie_folder, file_name)
        if file_path != output_file_path and file_name != "backup":  # Skip the target output file and the backup directory
            shutil.move(file_path, os.path.join(backup_dir, file_name))
            print(f"Moved {file_path} to {backup_dir}")

    # Rename the output file to the original source input file name
    renamed_output_file = os.path.join(movie_folder, os.path.basename(video_file_path))
    os.rename(output_file_path, renamed_output_file)
    print(f"Renamed output file {output_file_path} to {renamed_output_file}")

def process_movie_folder(movie_folder_path, folders_with_no_subtitles):
    """
    Processes a folder containing movie files and subtitles.
    """
    movie_files = filter_files_in_folder(movie_folder_path, ['.mp4', '.mkv'])
    subtitle_files = filter_files_in_folder(movie_folder_path, ['.srt'])

    # If no video files, skip processing
    if not movie_files:
        print(f"No video files found in {movie_folder_path}. Skipping.")
        return

    # If no subtitle files, record this folder for the summary
    if not subtitle_files:
        print(f"No subtitle files found in {movie_folder_path}. Updating metadata only.")
        folders_with_no_subtitles.append(movie_folder_path)

    # Process each movie file
    for video_file in movie_files:
        video_file_path = os.path.join(movie_folder_path, video_file)

        # Convert MKV to MP4 if necessary
        if video_file_path.endswith('.mkv'):
            video_file_path = convert_mkv_to_mp4(video_file_path)

        base_name = os.path.splitext(video_file)[0]
        output_file_path = os.path.join(movie_folder_path, f"{base_name}.output.mp4")

        # Process the movie file
        process_movie_file(video_file_path, subtitle_files, output_file_path)

def process_all_movie_folders(movies_path):
    """
    Processes all movie folders in the given path.
    """
    movie_folders = sorted([os.path.join(movies_path, d) for d in os.listdir(movies_path) if os.path.isdir(os.path.join(movies_path, d))])
    folders_with_no_subtitles = []

    for movie_folder in movie_folders:
        print(f"Processing movie folder: {movie_folder}")
        process_movie_folder(movie_folder, folders_with_no_subtitles)

    print("All movie folders processed successfully.")

    # Print summary of folders with no subtitles
    if folders_with_no_subtitles:
        print("\nSummary of folders with no subtitles:")
        for folder in folders_with_no_subtitles:
            print(f"  - {folder}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_movies.py <movies_folder_path> [--debug] [--force]")
        sys.exit(1)

    movies_folder_path = sys.argv[1]

    if '--debug' in sys.argv:
        DEBUG = True

    if '--force' in sys.argv:
        FORCE = True

    if not os.path.isdir(movies_folder_path):
        print("Invalid folder path provided.")
        sys.exit(1)

    process_all_movie_folders(movies_folder_path)
