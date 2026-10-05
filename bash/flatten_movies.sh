#!/usr/bin/env bash

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# flatten_movies.sh: Flatten nested movie files into immediate folders and collect empty folders.
#

#
# Flatten Movie Directories Script
#
# This script flattens a nested directory structure for movie files, moving all movie files
# into directories named after the parent folder containing the movie. It supports a dry run
# mode to preview the changes without making any actual modifications and a run mode to perform
# the actual file operations. Additionally, it moves empty directories and directories containing
# only '@eaDir' to a '____trash' folder.
#
# Usage:
#   ./flatten_movies.sh --dry-run   # To preview the changes
#   ./flatten_movies.sh --run       # To apply the changes
#
# Supported movie file extensions include: .mp4, .mkv, .avi, .mov, .flv, .wmv, .mpeg, .mpg
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
# print_current_structure: Display the current directory tree for a dry run.
#
# Parameters: None.
#
# Returns: Status 0 on success; exits on a failed command.
#
print_current_structure() {
    echo "Current Directory Structure:"
    find . -type d ! -name '@eaDir' | sed 's/[^-][^\/]*\//--/g;s/^/ /;s/--/|--/'
    echo
}

#
# print_flattened_structure: Display the proposed immediate movie folder structure.
#
# Parameters: None.
#
# Returns: Status 0 on success; exits on a failed command.
#
print_flattened_structure() {
    echo "Flattened Directory Structure:"
    for ext in "${MOVIE_EXTENSIONS[@]}"; do
        find . -type f -name "$ext" | while read -r file; do
            dirname=$(basename "$(dirname "$file")")
            echo "|-- $dirname"
            echo "    |-- $(basename "$file")"
        done
    done
    echo
}

#
# move_movie_files: Report or move nested movies into immediate movie folders.
#
# Parameters: None.
#
# Returns: Status 0 on success; exits on a failed operation.
#
move_movie_files() {
    for ext in "${MOVIE_EXTENSIONS[@]}"; do
        find . -type f -name "$ext" | while read -r file; do
            filename=$(basename "$file")
            dirname=$(basename "$(dirname "$file")")
            target_dir="./$dirname"
            target_file="$target_dir/$filename"

            # Check if the file is already in the correct directory
            if [ "$(readlink -f "$file")" == "$(readlink -f "$target_file")" ]; then
                if [ "$MODE" == "--dry-run" ]; then
                    echo "File $file is already in the correct location"
                fi
                continue
            fi

            if [ "$MODE" == "--dry-run" ]; then
                echo "Would create directory $target_dir if it doesn't exist"
                echo "Would move $file to $target_file"
            elif [ "$MODE" == "--run" ]; then
                mkdir -p "$target_dir"
                mv "$file" "$target_file"
            fi
        done
    done
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

    find . -type d ! -name '.' | while read -r dir; do
        # Check if the directory contains only '@eaDir' or is empty
        if [ "$(find "$dir" -mindepth 1 ! -name '@eaDir' | wc -l)" -eq 0 ]; then
            if [ "$MODE" == "--dry-run" ]; then
                echo "Would move empty directory $dir to $TRASH_DIR"
            elif [ "$MODE" == "--run" ]; then
                mv "$dir" "$TRASH_DIR"
            fi
        fi
    done
}

# Print current structure in dry run mode
if [ "$MODE" == "--dry-run" ]; then
    print_current_structure
fi

# Move movie files
move_movie_files

# Print flattened structure in dry run mode
if [ "$MODE" == "--dry-run" ]; then
    print_flattened_structure
fi

# Move empty directories to trash in run mode
move_empty_directories_to_trash

echo "Operation completed in $MODE mode."
