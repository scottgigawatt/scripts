import os
import subprocess
import sys
import requests
import json
import tvdb_v4_official
from pprint import pprint
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def pretty_print_json(data, label):
    print(Fore.YELLOW + f"{label}:")
    pprint(data, indent=2)

def pretty_print_command(command, label):
    print(Fore.CYAN + f"{label}:")
    print(" ".join(command))

def get_series_metadata(tvdb, series_id, debug):
    series_extended = tvdb.get_series_extended(series_id)
    if debug:
        pretty_print_json(series_extended, f"Series Extended Data for ID {series_id}")

    # Extract required information from series metadata
    series_metadata = {
        "contentRating": next((rating["name"] for rating in series_extended["contentRatings"] if rating["country"].lower() == "usa"), None),
        "genres": ", ".join([genre["name"] for genre in series_extended["genres"]]),
        "network": series_extended["originalNetwork"]["name"] if "originalNetwork" in series_extended else None,
        "actors": ", ".join([character["personName"] for character in series_extended["characters"]])
    }
    return series_metadata

def get_season_metadata(tvdb, season_info, debug):
    season_data = tvdb.get_season_extended(season_info["id"])
    if debug:
        pretty_print_json(season_data, f"Season Data for Season {season_info['number']}")

    # Extract required information from season metadata
    season_metadata = {
        "aired": season_data.get("aired", ""),
        "image": season_data.get("image", ""),
        "overview": season_data.get("overview", "")
    }
    return season_metadata

def get_episode_metadata(tvdb, series_id, season, episode, debug):
    try:
        series_extended = tvdb.get_series_extended(series_id)
        if debug:
            pretty_print_json(series_extended, f"Series Extended Data for ID {series_id}")

        for season_info in series_extended["seasons"]:
            if debug:
                pretty_print_json(season_info, "Season Info")

            if season_info["type"]["name"] == "Aired Order" and season_info["number"] == int(season):
                season_data = tvdb.get_season_extended(season_info["id"])
                if debug:
                    pretty_print_json(season_data, f"Season Data for Season {season_info['number']}")

                for ep in season_data["episodes"]:
                    if ep["number"] == int(episode):
                        return ep
        return None
    except Exception as e:
        if debug:
            print(Fore.RED + f"Error fetching metadata for series ID {series_id}, Season {season}, Episode {episode}: {e}")
        return None

def update_metadata(file_path, metadata, series_metadata, season_metadata, debug):
    if debug:
        pretty_print_json(metadata, f"Updating metadata for {file_path}")
        pretty_print_json(series_metadata, "Series Metadata")
        pretty_print_json(season_metadata, "Season Metadata")

    ffmpeg_command = [
        'ffmpeg',
        '-i', file_path,
        '-metadata', f'title={metadata.get("name", "")}',
        '-metadata', f'date={season_metadata.get("aired", "")}',
        '-metadata', f'genre={series_metadata.get("genres", "")}',
        '-metadata', f'description={metadata.get("overview", "")}',
        '-metadata', f'network={series_metadata.get("network", "")}',
        '-metadata', f'episode_id={metadata.get("id", "")}',
        '-metadata', f'cast={series_metadata.get("actors", "")}',
        '-metadata', f'director={metadata.get("director", "")}',
        '-metadata', f'producer={metadata.get("director", "")}',  # Assuming same as director if producer is not provided
        '-metadata', f'writer={metadata.get("writer", "")}',
        '-metadata', f'contentRating={series_metadata.get("contentRating", "")}',
        '-c', 'copy',
        f'{os.path.splitext(file_path)[0]}_updated.mp4'
    ]
    if debug:
        pretty_print_command(ffmpeg_command, "FFmpeg Command")
    subprocess.run(ffmpeg_command, check=True)

    artwork_url = season_metadata.get('image', None)
    if artwork_url:
        artwork_path = os.path.join(os.path.dirname(file_path), 'artwork.jpg')
        response = requests.get(artwork_url)
        with open(artwork_path, 'wb') as f:
            f.write(response.content)
        atomicparsley_command = [
            'AtomicParsley', f'{os.path.splitext(file_path)[0]}_updated.mp4',
            '--artwork', artwork_path,
            '--overWrite'
        ]
        if debug:
            pretty_print_command(atomicparsley_command, "AtomicParsley Command")
        subprocess.run(atomicparsley_command, check=True)

def process_tv_show(folder_path, series_id, api_key, debug):
    tvdb = tvdb_v4_official.TVDB(api_key)

    # Cache series metadata
    series_metadata = get_series_metadata(tvdb, series_id, debug)

    for root, dirs, files in os.walk(folder_path):
        if 'Season ' in root:
            files = sorted(files)  # Process files in alphabetical order

            # Cache season metadata
            season_number = root.split(os.path.sep)[-1].split(' ')[-1]
            season_info = next((s for s in tvdb.get_series_extended(series_id)["seasons"] if s["number"] == int(season_number)), None)
            season_metadata = get_season_metadata(tvdb, season_info, debug)

            for file in files:
                if file.endswith('.mp4'):
                    episode = str(int(os.path.splitext(file)[0].split(' ')[0]))  # Remove leading zeros
                    file_path = os.path.join(root, file)

                    if debug:
                        print(Fore.GREEN + f"Searching for: Series ID: {series_id}, Season: {season_number}, Episode: {episode}")

                    metadata = get_episode_metadata(tvdb, series_id, season_number, episode, debug)
                    if metadata:
                        update_metadata(file_path, metadata, series_metadata, season_metadata, debug)
                        print(Fore.GREEN + f'Updated metadata for {file_path}')
                    else:
                        print(Fore.RED + f'No metadata found for {file_path}')

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python update_tv_metadata.py <folder_path> <series_id> <api_key> [--debug]")
        sys.exit(1)

    folder_path = sys.argv[1]
    series_id = sys.argv[2]
    api_key = sys.argv[3]
    debug = len(sys.argv) == 5 and sys.argv[4] == '--debug'

    if not os.path.isdir(folder_path):
        print("Invalid folder path provided.")
        sys.exit(1)

    process_tv_show(folder_path, series_id, api_key, debug)
