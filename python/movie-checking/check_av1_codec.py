import os
import argparse
import subprocess
import logging
import shlex


def setup_logger(debug):
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def escape_path(file_path):
    """Escape spaces and special characters in the file path."""
    # Use os.path.normpath to normalize the path and shlex.quote to escape it
    return shlex.quote(os.path.normpath(file_path))


def run_ffprobe_raw(file_path, debug=False):
    """Run ffprobe to extract raw stream information from a video file."""
    # Escape the path for logging and subprocess
    safe_path = escape_path(file_path)
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_streams",
        file_path
    ]
    try:
        # Run ffprobe without shell=True to avoid manual escape issues
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Log the command being executed with the escaped path
        logging.info(f"Running command: ffprobe -v quiet -show_streams {safe_path}")

        if debug:
            logging.debug(f"ffprobe output for {file_path}:\n{result.stdout}")
            logging.debug(f"ffprobe errors (if any) for {file_path}:\n{result.stderr}")

        return result.stdout
    except Exception as e:
        logging.error(f"Failed to run ffprobe on {safe_path}: {e}")
        return None


def analyze_file(file_path, debug=False):
    """Analyze a single file to detect AV1 codec and missing audio tracks."""
    escaped_path = escape_path(file_path)
    logging.info(f"Analyzing file: {escaped_path}")
    output = run_ffprobe_raw(file_path, debug)

    if not output:
        return None, None

    av1_detected = "codec_name=av1" in output
    audio_missing = "codec_type=audio" not in output

    return av1_detected, audio_missing


def recursively_scan_directory(directory):
    """Recursively scan a directory for .mp4 files."""
    mp4_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4"):
                mp4_files.append(os.path.join(root, file))
    return mp4_files


def expand_and_escape_path(path):
    """Expand any quoted or tilde paths to full paths."""
    # Expand tilde (~) to full home directory path
    expanded_path = os.path.expanduser(path)

    # Remove quotes if path is wrapped in single or double quotes
    if (expanded_path.startswith("'") and expanded_path.endswith("'")) or \
       (expanded_path.startswith('"') and expanded_path.endswith('"')):
        expanded_path = expanded_path[1:-1]

    # Normalize and escape spaces
    return os.path.normpath(expanded_path)


def main(directory, single_file, debug):
    setup_logger(debug)

    av1_files = []
    files_missing_audio = []

    if single_file:
        # Expand and escape file path
        single_file = expand_and_escape_path(single_file)
        av1_detected, audio_missing = analyze_file(single_file, debug)
        if av1_detected:
            av1_files.append(single_file)
        if audio_missing:
            files_missing_audio.append(single_file)
    else:
        directory = expand_and_escape_path(directory)
        logging.info(f"Scanning directory: {directory}")
        mp4_files = recursively_scan_directory(directory)
        logging.info(f"Found {len(mp4_files)} .mp4 files to analyze.")

        for file_path in mp4_files:
            av1_detected, audio_missing = analyze_file(file_path, debug)
            if av1_detected:
                av1_files.append(file_path)
            if audio_missing:
                files_missing_audio.append(file_path)

    # Print summary
    print("\n--- Summary ---")
    if av1_files:
        print("Files using AV1 codec:")
        for file in av1_files:
            print(f" - {file}")
    else:
        print("No AV1 files found.")

    if files_missing_audio:
        print("\nFiles missing audio tracks:")
        for file in files_missing_audio:
            print(f" - {file}")
    else:
        print("\nNo files are missing audio tracks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if .mp4 files use AV1 codec and detect missing audio tracks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--directory", help="Directory to recursively scan for .mp4 files.")
    group.add_argument("--file", help="Path to a single .mp4 file to check.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to print detailed command output.")
    args = parser.parse_args()

    main(args.directory, args.file, args.debug)
