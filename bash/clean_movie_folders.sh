#!/usr/bin/env bash

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# clean_movie_folders.sh: Move non-movie entries from immediate movie folders into local trash.
#

#
# Move unnecessary files and directories in Movie Folders to Trash
#
# This script finds unnecessary files and directories within the movie folders in the 'movies' directory and moves them to a '____trash' folder.
# A folder is processed to keep only movie files and root-level '@eaDir' directories, moving everything else to the trash.
#
# Usage:
#   ./clean_movie_folders.sh --dry-run   # To preview the changes
#   ./clean_movie_folders.sh --run       # To apply the changes
#
# Error handling:
#   - The script will exit immediately if any command fails (set -o errexit)
#   - The script will exit if any unset variable is used (set -o nounset)
#   - The script will exit if any command in a pipeline fails (set -o pipefail)
#

# Fail fast on any error
set -o errexit
set -o nounset
set -o pipefail

# Supported movie file extensions
MOVIE_EXTENSIONS=("*.mp4" "*.mkv" "*.avi" "*.mov" "*.flv" "*.wmv" "*.mpeg" "*.mpg")

#
# usage: Print command usage and stop after invalid arguments.
#
# Parameters: None.
#
# Returns: Exit with status 1.
#
usage() {
    echo "Usage: $0 --dry-run | --run"
    exit 1
}

# Check if the correct number of arguments are provided
if [ "$#" -ne 1 ]; then
    usage
fi

# Parse the mode argument
MODE="$1"
if [ "$MODE" != "--dry-run" ] && [ "$MODE" != "--run" ]; then
    usage
fi

#
# is_movie_file: Check a basename against supported movie extension patterns.
#
# Parameters: $1 - File basename to inspect.
#
# Returns: Status 0 for a supported movie; otherwise status 1.
#
is_movie_file() {
    local file="$1"
    for ext in "${MOVIE_EXTENSIONS[@]}"; do
        # The extension contains an intentional glob pattern, not a literal value.
        # shellcheck disable=SC2053
        if [[ "$file" == $ext ]]; then
            return 0
        fi
    done
    return 1
}

#
# clean_directory: Move unnecessary immediate entries into the local trash directory.
#
# Parameters: $1 - Movie directory to inspect.
#
# Returns: Status 0 on success; exits on a failed operation.
#
clean_directory() {
    local dir="$1"
    local trash_dir="./____trash"

    # Create the trash directory if it doesn't exist
    if [ "$MODE" == "--run" ]; then
        mkdir -p "$trash_dir"
    fi

    # Find all files and directories inside the current directory
    find "$dir" -mindepth 1 -maxdepth 1 | while read -r item; do
        if [ -d "$item" ]; then
            # If it's a directory, check if it's '@eaDir'
            if [ "$(basename "$item")" != "@eaDir" ]; then
                if [ "$MODE" == "--dry-run" ]; then
                    echo "Would move directory '$item' to $trash_dir"
                elif [ "$MODE" == "--run" ]; then
                    mv "$item" "$trash_dir"
                fi
            fi
        else
            # If it's a file, check if it's a movie file or .DS_Store
            if ! is_movie_file "$(basename "$item")" && [ "$(basename "$item")" != ".DS_Store" ]; then
                if [ "$MODE" == "--dry-run" ]; then
                    echo "Would move file '$item' to $trash_dir"
                elif [ "$MODE" == "--run" ]; then
                    mv "$item" "$trash_dir"
                fi
            fi
        fi
    done
}

# Process each directory in the current directory
find . -mindepth 1 -maxdepth 1 -type d ! -path "./____trash" | while read -r dir; do
    clean_directory "$dir"
done

echo "Operation completed in $MODE mode."
