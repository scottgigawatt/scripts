#!/bin/bash

#
# Ensure Movie Folder Names Match Movie File Names
#
# This script ensures that all movie folder names match the movie file names inside them,
# including the year in parentheses. If a movie file named 'Movie Title (Year).ext' is inside
# a folder named 'Movie Title', the script renames the folder to 'Movie Title (Year)'.
#
# The script also moves empty directories or directories containing only '@eaDir' to a '____trash' folder.
#
# Usage:
#   ./ensure_movie_folder_names.sh --dry-run   # To preview the changes
#   ./ensure_movie_folder_names.sh --run       # To apply the changes
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

# Function to print usage instructions
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

# Function to print the current directory structure
print_current_structure() {
    echo "Current Directory Structure:"
    find . -type d ! -name '@eaDir' | sed 's/[^-][^\/]*\//--/g;s/^/ /;s/--/|--/'
    echo
}

# Function to rename movie folders to match movie file names
rename_movie_folders() {
    for ext in "${MOVIE_EXTENSIONS[@]}"; do
        find . -type f -name "$ext" | while read -r file; do
            filename=$(basename "$file")
            dirname=$(basename "$(dirname "$file")")
            parent_dir=$(dirname "$(dirname "$file")")

            # Extract the movie title and year from the file name
            if [[ "$filename" =~ ^(.*)\ \((.*)\)\..*$ ]]; then
                title="${BASH_REMATCH[1]}"
                year="${BASH_REMATCH[2]}"
                expected_dirname="${title} (${year})"

                # Check if the directory name needs to be updated
                if [ "$dirname" != "$expected_dirname" ]; then
                    if [ "$MODE" == "--dry-run" ]; then
                        echo "Would rename directory '$dirname' to '$expected_dirname'"
                    elif [ "$MODE" == "--run" ]; then
                        mv "$parent_dir/$dirname" "$parent_dir/$expected_dirname"
                    fi
                fi
            fi
        done
    done
}

# Function to move empty directories to the ____trash folder
move_empty_directories_to_trash() {
    TRASH_DIR="./____trash"
    if [ "$MODE" == "--run" ]; then
        mkdir -p "$TRASH_DIR"
    fi

    find . -type d ! -name '.' | while read -r dir; do
        # Check if the directory contains no movie files and only '@eaDir' or is empty
        if [ "$(find "$dir" -mindepth 1 ! -name '@eaDir' -a ! -type d | wc -l)" -eq 0 ]; then
            if [ "$MODE" == "--dry-run" ]; then
                echo "Would move empty directory '$dir' to $TRASH_DIR"
            elif [ "$MODE" == "--run" ]; then
                mv "$dir" "$TRASH_DIR"
            fi
        fi
    done

    # Move @eaDir directories separately to avoid errors
    find . -type d -name '@eaDir' | while read -r dir; do
        if [ "$MODE" == "--dry-run" ]; then
            echo "Would move '@eaDir' directory '$dir' to $TRASH_DIR"
        elif [ "$MODE" == "--run" ]; then
            mv "$dir" "$TRASH_DIR"
        fi
    done
}

# Function to print the updated directory structure
print_updated_structure() {
    echo "Updated Directory Structure:"
    find . -type d ! -name '@eaDir' | sed 's/[^-][^\/]*\//--/g;s/^/ /;s/--/|--/'
    echo
}

# Print current structure in dry run mode
if [ "$MODE" == "--dry-run" ]; then
    print_current_structure
fi

# Rename movie folders
rename_movie_folders

# Move empty directories to trash in run mode
move_empty_directories_to_trash

# Print updated structure in dry run mode
if [ "$MODE" == "--dry-run" ]; then
    print_updated_structure
fi

echo "Operation completed in $MODE mode."
