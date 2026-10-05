#!/usr/bin/env bash

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# move_empty_folders_to_trash.sh: Collect empty movie folders in a local trash directory.
#

#
# Move Empty Nested Movie Folders to Trash
#
# This script finds empty nested movie folders in the 'movies' directory and moves them to a '____trash' folder.
# A folder is considered empty if it contains any sub-directories that are also empty or contain only '@eaDir' folders.
# If the root folder contains any movie files, it skips that folder entirely.
#
# Usage:
#   ./move_empty_folders_to_trash.sh --dry-run   # To preview the changes
#   ./move_empty_folders_to_trash.sh --run       # To apply the changes
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
# contains_movie_files: Check for immediate movie files in a directory.
#
# Parameters: $1 - Directory to inspect.
#
# Returns: Status 0 when movie files exist; otherwise status 1.
#
contains_movie_files() {
    local dir="$1"
    for ext in "${MOVIE_EXTENSIONS[@]}"; do
        if [ "$(find "$dir" -maxdepth 1 -type f -name "$ext" | wc -l)" -ne 0 ]; then
            return 0
        fi
    done
    return 1
}

#
# is_empty_directory: Check recursively for files beyond Synology metadata and Finder state.
#
# Parameters: $1 - Directory to inspect.
#
# Returns: Status 0 for an empty directory; otherwise status 1.
#
is_empty_directory() {
    local dir="$1"
    # Check if the directory contains any files other than '@eaDir' and '.DS_Store'
    if [ "$(find "$dir" -mindepth 1 -type f ! -path '*/@eaDir/*' ! -name '.DS_Store' | wc -l)" -ne 0 ]; then
        return 1
    fi
    # Check if the directory contains any non-empty sub-directories
    for subdir in "$dir"/*; do
        if [ -d "$subdir" ] && ! is_empty_directory "$subdir"; then
            return 1
        fi
    done
    return 0
}

#
# move_empty_directories_to_trash: Report or move empty directories into local trash.
#
# Parameters: None.
#
# Returns: Status 0 on success; exits on a failed operation.
#
move_empty_directories_to_trash() {
    TRASH_DIR="./____trash"
    if [ "$MODE" == "--run" ]; then
        mkdir -p "$TRASH_DIR"
    fi

    find . -mindepth 1 -maxdepth 1 -type d ! -name '.' | while read -r dir; do
        if contains_movie_files "$dir"; then
            if [ "$MODE" == "--dry-run" ]; then
                echo "Skipping directory '$dir' because it contains movie files"
            fi
            continue
        fi

        if is_empty_directory "$dir"; then
            if [ "$MODE" == "--dry-run" ]; then
                echo "Would move empty directory '$dir' to $TRASH_DIR"
            elif [ "$MODE" == "--run" ]; then
                mv "$dir" "$TRASH_DIR"
            fi
        fi
    done
}

# Move empty directories to trash
move_empty_directories_to_trash

echo "Operation completed in $MODE mode."
