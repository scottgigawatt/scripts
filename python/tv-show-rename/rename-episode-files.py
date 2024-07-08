import os
import re
import sys
import argparse

def get_episode_titles(file_path):
    """
    Reads episode titles from the provided file path and returns a dictionary
    mapping episode identifiers (e.g., 'S01E01') to their titles.
    """
    titles = {}
    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(r'(S\d+E\d+(-E\d+)?)\s+(.+)', line.strip(), re.IGNORECASE)
            if match:
                key = match.group(1).lower()
                title = match.group(3).strip()
                titles[key] = title
    return titles

def rename_files(show_folder, debug):
    """
    Renames TV show episode files in the specified show folder based on episode titles
    from 'episode-names.txt' files within each season folder.
    """
    debug_file_path = "debug.log"
    debug_file = open(debug_file_path, 'w') if debug else None

    for season_folder in sorted(os.listdir(show_folder)):
        season_path = os.path.join(show_folder, season_folder)
        if os.path.isdir(season_path) and season_folder.lower().startswith('season'):
            episode_titles_path = os.path.join(season_path, 'episode-names.txt')
            if os.path.exists(episode_titles_path):
                episode_titles = get_episode_titles(episode_titles_path)
                if debug:
                    debug_file.write(f"Episode titles for {season_folder}:\n")
                    for key, title in episode_titles.items():
                        debug_file.write(f"  {key}: {title}\n")
                    debug_file.write("\n")

                for episode_file in sorted(os.listdir(season_path)):
                    if episode_file.lower().endswith('.mp4'):
                        episode_file_path = os.path.join(season_path, episode_file)

                        # First try to match multi-episode files
                        episode_match = re.match(r'(s\d+e\d+(-e\d+)+).*\.mp4', episode_file, re.IGNORECASE)

                        if episode_match:
                            episodes_key = episode_match.group(1).lower()
                            episodes_range = episodes_key.split('-')
                            episode_numbers = [episodes_range[0]] + [
                                's' + re.findall(r'\d+', episodes_range[i])[0] + 'e' + re.findall(r'\d+', episodes_range[i + 1])[0]
                                for i in range(len(episodes_range) - 1)
                            ]

                            if debug:
                                debug_file.write(f"Matching file: {episode_file}\n")
                                debug_file.write(f"  Episodes key: {episodes_key}\n")
                                debug_file.write(f"  Episode numbers: {episode_numbers}\n")

                            if all(episode in episode_titles for episode in episode_numbers):
                                episode_names = ' & '.join([episode_titles[episode] for episode in episode_numbers])
                                new_filename = f"{episodes_key} {episode_names}.mp4"
                                new_file_path = os.path.join(season_path, new_filename)

                                if debug:
                                    debug_file.write(f"  New filename: {new_filename}\n")
                                os.rename(episode_file_path, new_file_path)
                                print(f"Renamed: {episode_file_path} -> {new_file_path}")
                            else:
                                if debug:
                                    debug_file.write("  Episode title(s) not found for one or more episodes.\n")
                        else:
                            # If no match, try to match single-episode files
                            episode_match = re.match(r'(s\d+e\d+)', episode_file, re.IGNORECASE)
                            if episode_match:
                                episodes_key = episode_match.group(1).lower()
                                episode_numbers = [episodes_key]

                                if debug:
                                    debug_file.write(f"Matching file (single-episode): {episode_file}\n")
                                    debug_file.write(f"  Episodes key: {episodes_key}\n")
                                    debug_file.write(f"  Episode numbers: {episode_numbers}\n")

                                if all(episode in episode_titles for episode in episode_numbers):
                                    episode_names = ' & '.join([episode_titles[episode] for episode in episode_numbers])
                                    new_filename = f"{episodes_key} {episode_names}.mp4"
                                    new_file_path = os.path.join(season_path, new_filename)

                                    if debug:
                                        debug_file.write(f"  New filename: {new_filename}\n")
                                    os.rename(episode_file_path, new_file_path)
                                    print(f"Renamed: {episode_file_path} -> {new_file_path}")
                                else:
                                    if debug:
                                        debug_file.write("  Episode title(s) not found for the episode.\n")
                            else:
                                if debug:
                                    debug_file.write(f"No match for file: {episode_file}\n")
                    if debug:
                        debug_file.write("\n")

    if debug:
        debug_file.close()
        print(f"Debug information written to {debug_file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename TV show episodes based on episode titles.")
    parser.add_argument("show_folder", help="Path to the TV show folder")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    rename_files(args.show_folder, args.debug)
