import os
import argparse
import logging
import re

def parse_episode_names(file_path):
    """Parse the episode-names.txt file and return a dictionary mapping episode titles to correct season/episode numbers."""
    episode_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Use regular expression to split on the first occurrence of whitespace after the season/episode key
            match = re.match(r"(\S+)\s+(.+)", line.strip())
            if match:
                episode_key, episode_title = match.groups()
                episode_dict[episode_title.strip().lower()] = episode_key.strip().lower()
    return episode_dict

def rename_and_move_episodes(folder, episode_dict, debug=False):
    """Rename the episodes in the given folder based on the episode_dict mapping and move them to season folders."""
    if debug:
        logging.basicConfig(filename=os.path.join(folder, 'debug.log'), level=logging.DEBUG)

    # Get the list of files and sort them alphabetically
    files = sorted(os.listdir(folder))

    for filename in files:
        if filename.endswith(".mp4") or filename.endswith(".mkv"):
            parts = filename.split(' ', 1)
            if len(parts) == 2:
                current_key, episode_title = parts
                episode_title, file_extension = os.path.splitext(episode_title)  # Separate the title and extension
                correct_key = episode_dict.get(episode_title.lower())
                if correct_key:
                    new_filename = f"{correct_key} {episode_title}{file_extension}"
                    season_folder = f"Season {correct_key[1:3]}"
                    season_folder_path = os.path.join(folder, season_folder)

                    # Create season folder if it does not exist
                    if not os.path.exists(season_folder_path):
                        os.makedirs(season_folder_path)

                    if debug:
                        logging.debug(f"Renaming '{filename}' to '{new_filename}' and moving to '{season_folder}'")
                        print(f"Renaming '{filename}' to '{new_filename}' and moving to '{season_folder}'")

                    # Rename and move the file
                    os.rename(os.path.join(folder, filename), os.path.join(season_folder_path, new_filename))

def main():
    parser = argparse.ArgumentParser(description='Rename TV show episodes to correct season and episode numbers and move them to season folders.')
    parser.add_argument('folder', type=str, help='Folder containing the episodes to rename')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Get the path to the episode-names.txt file in the same directory as the episodes
    episode_names_path = os.path.join(args.folder, 'episode-names.txt')

    episode_dict = parse_episode_names(episode_names_path)
    rename_and_move_episodes(args.folder, episode_dict, args.debug)

if __name__ == "__main__":
    main()
