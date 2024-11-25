import os
import re
import sys
import shutil
from datetime import datetime

def parse_movie_info(name):
    """
    Extracts the movie name and year from a folder or file name.
    Returns a tuple (movie_name, movie_year).
    """
    match = re.search(r"^(.*?)[.\s]*\(?(\d{4})\)?", name)
    if not match:
        return None, None
    movie_name = re.sub(r"[.\s]+", " ", match.group(1)).strip()
    movie_year = match.group(2)
    return movie_name, movie_year

def parse_quality_and_resolution(name):
    """
    Extracts quality and resolution from a file name.
    Returns a tuple (quality, resolution) with correctly formatted casing.
    """
    quality_match = re.search(r"(BluRay|WEBRip|BDRip|HULU|WEB-DL|WEBDL|BRRip)", name, re.IGNORECASE)
    resolution_match = re.search(r"(\d{3,4}p)", name, re.IGNORECASE)

    if quality_match:
        quality = quality_match.group(1).lower()
        if quality in ["webrip", "web-dl", "webdl"]:
            quality = "WEBRip" if "rip" in quality else "WEBDL"
        elif quality == "bluray":
            quality = "Bluray"
        else:
            quality = quality.capitalize()
    else:
        quality = "UnknownQuality"

    resolution = resolution_match.group(1) if resolution_match else "UnknownResolution"
    return quality, resolution

def move_to_trash(path):
    """
    Moves a file or folder to the trash. Ensures unique names by appending a timestamp or counter.
    """
    trash_dir = os.path.expanduser("~/.local/share/Trash/files")
    os.makedirs(trash_dir, exist_ok=True)

    base_name = os.path.basename(path)
    trash_path = os.path.join(trash_dir, base_name)

    # Ensure unique destination path
    if os.path.exists(trash_path):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        trash_path = os.path.join(trash_dir, f"{base_name}_{timestamp}")
        counter = 1
        while os.path.exists(trash_path):  # Add a counter if still not unique
            trash_path = os.path.join(trash_dir, f"{base_name}_{timestamp}_{counter}")
            counter += 1

    shutil.move(path, trash_path)
    print(f"Moved to trash: {path} -> {trash_path}")

def process_subtitles(folder_path, movie_name, movie_year, default_quality, default_resolution, deleted_subtitle_folders):
    """
    Processes subtitle files in subfolders. Moves English subtitles to the main folder,
    renames them using default quality and resolution if they are unknown, and moves
    non-English subtitles and empty subtitle folders to the trash.
    """
    for root, dirs, files in os.walk(folder_path, topdown=False):  # Process subfolders bottom-up
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.lower().endswith(".srt"):
                if "eng" in file_name.lower() or "english" in file_name.lower():
                    # Move English subtitles to the main folder
                    quality, resolution = parse_quality_and_resolution(file_name)
                    # Use default quality and resolution if unknown
                    quality = quality if quality != "UnknownQuality" else default_quality
                    resolution = resolution if resolution != "UnknownResolution" else default_resolution
                    if "sdh" in file_name.lower():
                        new_file_name = f"{movie_name} ({movie_year}) {quality}-{resolution}.SDH.srt"
                    else:
                        new_file_name = f"{movie_name} ({movie_year}) {quality}-{resolution}.srt"
                    new_file_path = os.path.join(folder_path, new_file_name)
                    shutil.move(file_path, new_file_path)
                    print(f"Moved and renamed subtitle: {file_name} -> {new_file_name}")
                else:
                    # Move non-English subtitles to the trash
                    move_to_trash(file_path)

        # Check if subtitle folders are empty after processing
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):  # Folder is empty
                move_to_trash(dir_path)
                deleted_subtitle_folders.append(dir_path)

def rename_movie_folder_and_files(base_path):
    """
    Renames movie folders and files in the specified base path.
    Folders are renamed to "<movie_name> (<movie_year>)".
    Files are renamed to match the format "<movie_name> (<movie_year>) <quality>-<resolution>.<extension>".
    Processes subtitle files in subfolders and moves empty folders to the trash.
    """
    skipped_folders = []
    deleted_empty_folders = []
    deleted_subtitle_folders = []

    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path):
            continue  # Skip if not a folder

        # Handle empty folders
        if not os.listdir(folder_path):
            print(f"Empty folder detected: {folder_name}")
            move_to_trash(folder_path)
            deleted_empty_folders.append(folder_name)
            continue

        # Parse movie name and year from folder name
        movie_name, movie_year = parse_movie_info(folder_name)
        if not movie_name or not movie_year:
            print(f"Skipping folder (unable to parse): {folder_name}")
            continue

        # Rename folder
        new_folder_name = f"{movie_name} ({movie_year})"
        new_folder_path = os.path.join(base_path, new_folder_name)

        # Skip if the target folder already exists
        if os.path.exists(new_folder_path):
            print(f"Skipping folder (duplicate name): {folder_name}")
            skipped_folders.append(folder_name)
            continue

        os.rename(folder_path, new_folder_path)
        print(f"Renamed folder: {folder_name} -> {new_folder_name}")

        # Initialize default quality and resolution
        default_quality, default_resolution = "UnknownQuality", "UnknownResolution"

        # Rename files within the folder
        for file_name in os.listdir(new_folder_path):
            file_path = os.path.join(new_folder_path, file_name)
            if not os.path.isfile(file_path):
                continue  # Skip if not a file

            # Determine file extension
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext in ['.mkv', '.mp4']:
                # Rename movie files
                default_quality, default_resolution = parse_quality_and_resolution(file_name)
                new_file_name = f"{movie_name} ({movie_year}) {default_quality}-{default_resolution}{file_ext}"
                new_file_path = os.path.join(new_folder_path, new_file_name)
                os.rename(file_path, new_file_path)
                print(f"Renamed file: {file_name} -> {new_file_name}")
            elif file_ext == '.srt':
                # Skip as subtitles are processed later
                continue
            else:
                # Move unsupported files to trash
                move_to_trash(file_path)

        # Process subtitle files in subfolders
        process_subtitles(new_folder_path, movie_name, movie_year, default_quality, default_resolution, deleted_subtitle_folders)

    # Print summary of skipped folders
    if skipped_folders:
        print("\nSummary of skipped folders (duplicates):")
        for folder in skipped_folders:
            print(f"  - {folder}")

    # Print summary of deleted empty movie folders
    if deleted_empty_folders:
        print("\nSummary of deleted empty movie folders:")
        for folder in deleted_empty_folders:
            print(f"  - {folder}")

    # Print summary of deleted subtitle folders
    if deleted_subtitle_folders:
        print("\nSummary of deleted empty subtitle folders:")
        for folder in deleted_subtitle_folders:
            print(f"  - {folder}")

if __name__ == "__main__":
    # Ensure the script is run with a valid command-line argument
    if len(sys.argv) != 2:
        print("Usage: python rename_movies.py <path_to_movie_folders>")
        sys.exit(1)

    # Get the base path from the command-line argument
    base_path = sys.argv[1]

    # Validate that the provided path exists and is a directory
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        print(f"Invalid path: {base_path}. Please provide a valid directory.")
        sys.exit(1)

    # Rename movie folders and files
    rename_movie_folder_and_files(base_path)
