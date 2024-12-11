import os
import argparse
import logging
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import shutil

def setup_logger(log_file):
    # Overwrite the log file if it already exists
    open(log_file, 'w').close()

    # Clear any existing handlers to prevent duplication
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

def get_movie_folders(movies_folder):
    return [os.path.join(movies_folder, d) for d in os.listdir(movies_folder) if os.path.isdir(os.path.join(movies_folder, d))]

def get_subtitle_files(subtitles_folder):
    return [os.path.join(subtitles_folder, f) for f in os.listdir(subtitles_folder) if f.endswith('.srt')]

def has_subtitles(movie_folder):
    return any(f.endswith('.srt') for f in os.listdir(movie_folder))

def match_subtitles(movie_name, subtitle_files, threshold):
    matches = process.extract(movie_name, subtitle_files, scorer=fuzz.partial_ratio)
    return [match for match in matches if match[1] >= threshold]

def main(movies_folder, subtitles_folder, confidence, dry_run, log_file):
    setup_logger(log_file)

    movie_folders = get_movie_folders(movies_folder)
    subtitle_files = get_subtitle_files(subtitles_folder)

    no_subtitle_folders = []
    high_confidence_matches = []
    folders_with_high_confidence_matches = 0
    moved_files_summary = []

    for movie_folder in movie_folders:
        movie_name = os.path.basename(movie_folder)
        if not has_subtitles(movie_folder):
            no_subtitle_folders.append(movie_folder)
            logging.info(f"Movie folder '{movie_name}' has no subtitles.")
            possible_matches = match_subtitles(movie_name, subtitle_files, confidence)

            if possible_matches:
                logging.info("Potential subtitle matches:")
                for match in possible_matches:
                    logging.info(f" - {match[0]} (Confidence: {match[1]}%)")
                high_confidence = [match for match in possible_matches if match[1] >= confidence]
                if high_confidence:
                    folders_with_high_confidence_matches += 1
                    high_confidence_matches.extend([(movie_name, match[0]) for match in high_confidence])
                    if not dry_run:
                        # Move the first high-confidence subtitle file
                        for match in high_confidence:
                            subtitle_path = match[0]
                            destination = os.path.join(movie_folder, os.path.basename(subtitle_path))
                            shutil.move(subtitle_path, destination)
                            logging.info(f"Moved '{subtitle_path}' to '{destination}'")
                            moved_files_summary.append((movie_name, subtitle_path))
                            break  # Move only the first match per folder

    # Write main summary to log and print totals
    logging.info("\nSummary:")
    logging.info(f"Total movie folders checked: {len(movie_folders)}")
    logging.info(f"Movie folders without subtitles: {len(no_subtitle_folders)}")
    logging.info(f"Movie folders without subtitles that have matches >= {confidence}% confidence: {folders_with_high_confidence_matches}")
    print(f"Total movie folders checked: {len(movie_folders)}")
    print(f"Movie folders without subtitles: {len(no_subtitle_folders)}")
    print(f"Movie folders without subtitles that have matches >= {confidence}% confidence: {folders_with_high_confidence_matches}")

    # Write detailed summary of high confidence matches to log only
    if high_confidence_matches:
        logging.info(f"\nHigh Confidence Matches (>= {confidence}%):")
        for movie_name, subtitle_name in high_confidence_matches:
            logging.info(f"Movie folder: {movie_name} | Subtitle file: {subtitle_name}")

    if not dry_run and moved_files_summary:
        print("\nSummary of Moved High Confidence Subtitle Files:")
        for movie_name, subtitle_path in moved_files_summary:
            print(f"Moved subtitle file '{os.path.basename(subtitle_path)}' to movie folder '{movie_name}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check and match subtitles to movie folders.")
    parser.add_argument("movies_folder", help="Path to the folder containing movie folders.")
    parser.add_argument("subtitles_folder", help="Path to the folder containing subtitles.")
    parser.add_argument("--confidence", type=int, default=90, help="Confidence threshold for subtitle matches (default: 90).")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making changes.")
    parser.add_argument("--log-file", default="subtitle_matcher.log", help="Path to the log file.")

    args = parser.parse_args()
    main(args.movies_folder, args.subtitles_folder, args.confidence, args.dry_run, args.log_file)
