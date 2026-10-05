#!/usr/bin/env bash

#
# Copyright 2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# bash_functions.sh: User-defined Bash functions; source only in a trusted shell.
#
# Author: Scott Gigawatt
#

#
# mp3Splitter: Reference for splitting Mp3 files using cue files.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function mp3Splitter() {
    # https://sourceforge.net/p/mp3splt/bugs/178/

    # Ensure mp3splt is installed
    command -v mp3splt > /dev/null 2>&1 || {
        echo >&2 "I require mp3splt but it's not installed.  Aborting."
        return 1
    }

    # Preserve the legacy output directory name used by this reference helper.
    # cspell:ignore splitted
    mp3splt -d splitted file.mp3 0.0 EOF
    mp3splt -c file.cue -d splitted file.mp3
}

#
# set_metadata: Sets the metadata for .mp4 files based on their filename patterns.
# It handles filenames ending with a two-digit episode number followed by a space and ".mp4",
# and filenames following the patterns 'S01E01.mp4' or 'S01E01-E02.mp4' (case insensitive).
# For patterns with two episodes, it uses the first episode number.
#
# Parameters: $1 - The show name written to the artist metadata tag.
#             $2 - The season identifier written to the season metadata tag.
#
# Returns: The last command exit status.
#
function set_metadata() {
    local show_name="$1"
    local season="$2"

    for file in *.mp4; do
        if [[ $file =~ ([0-9]{2})\ .mp4 ]]; then
            episode_number=${BASH_REMATCH[1]}
            set -x
            ffmpeg -i "$file" -metadata artist="$show_name" -metadata Season="$season" -metadata episode="$episode_number" -c copy "new_$file"
            set +x
            mv "new_$file" "$file"
        elif [[ $file =~ [sS]([0-9]{2})[eE]([0-9]{2})(-[eE]([0-9]{2}))? ]]; then
            episode_number=${BASH_REMATCH[2]}
            set -x
            ffmpeg -i "$file" -metadata artist="$show_name" -metadata Season="$season" -metadata episode="$episode_number" -c copy "new_$file"
            set +x
            mv "new_$file" "$file"
        else
            echo "Error: $file does not match the expected format."
        fi
    done
}

#
# setEpisode: Apply caller-provided conversion settings to MP4 episodes.
#
# Parameters: None.
#
# Requires caller-defined artwork, codec, output paths, and metadata variables.
# Optional process_chapters and extra_meta enable chapter inputs and track metadata.
#
# Returns: The last command exit status.
#
function setEpisode() {
    local ext="mp4"
    # Assemble optional ffmpeg arguments without splitting metadata or paths.
    local -a chapter_inputs chapter_metadata track_metadata
    chapter_inputs=()
    chapter_metadata=()
    [[ -z ${process_chapters:-} ]] || chapter_inputs=(-i FFMETADATAFILE)
    [[ -z ${process_chapters:-} ]] || chapter_metadata=(-map_metadata 2)

    for i in *."${ext}"; do
        track_metadata=()
        if [[ -n ${extra_meta:-} ]]; then
            track_metadata=(-metadata "track=$(eval "${meta_current_track}")/$(eval "${meta_total_tracks}")")
        fi

        set -x
        ffmpeg -i "${i}" -i "${album_art}" \
            "${chapter_inputs[@]}" \
            -map 0:0 -map 1:0 \
            "${chapter_metadata[@]}" \
            -c:a:0 "${audio_codec}" -c:v:1 libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" \
            -metadata:s:a:0 title="$(eval "${meta_title}")" \
            -metadata:s:v:1 title="Album cover" \
            -metadata title="$(eval "${meta_title}")" \
            "${track_metadata[@]}" \
            "${ffmpeg_args[@]}" \
            "${convert_dir}/${i%.*}.${target_ext}"
        AtomicParsley "${convert_dir}/${i%.*}.${target_ext}" --artwork REMOVE_ALL --artwork "${album_art}" --overWrite
        set +x
    done
}

#
# all2mp4: Converts video files to MP4 using ffmpeg.
#
# Parameters: $1 - The video file to convert
#
# Returns: The last command exit status.
#
function all2mp4() {
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "Error: ffmpeg is required but not installed. Aborting."
        return 1
    }

    command -v ffprobe > /dev/null 2>&1 || {
        echo >&2 "Error: ffprobe is required but not installed. Aborting."
        return 1
    }

    # Specify the video file to convert
    local video_file="${1}"

    # Default to copying audio unless we detect EAC3, which needs conversion
    local audio_codec_global="copy"

    # Use ffprobe to count the number of audio tracks
    audio_count=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$video_file" | wc -l)

    # Detect EAC3 audio streams, if present convert audio to AAC instead of copying
    if ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$video_file" | ggrep -qiE '^(eac3|ec-3|ac3)$'; then
        echo "EAC3 audio detected, converting audio to AAC."
        audio_codec_global="aac"
    fi

    audio_args=()
    if [ "$audio_count" -gt 0 ]; then
        echo "Found $audio_count audio track(s). Setting language to English."
        for ((i = 0; i < audio_count; i++)); do
            # Get the current audio track language
            audio_language=$(ffprobe -v error -select_streams a:$i -show_entries stream_tags=language -of csv=p=0 "${video_file}")

            # Only include English and undefined audio tracks (treat empty language as English)
            if [[ -z "$audio_language" || "$audio_language" == "eng" || "$audio_language" == "und" ]]; then
                # Detect codec and channel count for this audio stream
                audio_codec_name=$(ffprobe -v error -select_streams a:$i -show_entries stream=codec_name -of csv=p=0 "${video_file}")
                audio_channels=$(ffprobe -v error -select_streams a:$i -show_entries stream=channels -of csv=p=0 "${video_file}")

                # Get the current audio track title
                current_title=$(ffprobe -v error -select_streams a:$i -show_entries stream_tags=title -of csv=p=0 "${video_file}")

                # Determine the base title based on the number of channels
                base_title=$(
                    ffprobe -v error -select_streams a:$i -show_entries stream=channels -of csv=p=0 "${video_file}" |
                        awk '{if($1 == 1) print "Mono Audio"; else if($1 == 2) print "Stereo Audio"; else print "Surround Audio"}'
                )

                # Check if the current title contains "Commentary" (case-insensitive)
                if [[ "$current_title" =~ [Cc]ommentary ]]; then
                    base_title="${base_title} (Commentary)"
                fi

                # If this track is EAC3 and we are reencoding audio, preserve the original channel count
                if [[ "${audio_codec_global}" == "aac" && "${audio_codec_name}" =~ ^(eac3|ec-3|ac3)$ && -n "${audio_channels}" ]]; then
                    audio_args+=("-ac:a:$i" "${audio_channels}")
                fi

                audio_args+=(
                    "-metadata:s:a:$i" language=eng
                    "-metadata:s:a:$i" title="${base_title}"
                )
            else
                # Drop non-English audio tracks
                audio_args+=(
                    -map -0:a:"$i"
                )
            fi
        done
    else
        echo "No audio tracks found in the video file."
    fi

    # Use ffprobe to count the number of subtitle tracks
    subtitle_count=$(ffprobe -v error -select_streams s -show_entries stream=index -of csv=p=0 "$video_file" | wc -l)
    subtitle_args=()
    if [ "$subtitle_count" -gt 0 ]; then
        echo "Found $subtitle_count subtitle track(s). Setting language to English."
        for ((i = 0; i < subtitle_count; i++)); do
            subtitle_language=$(ffprobe -i "$video_file" -select_streams s:$i -show_entries stream_tags=language -of csv=p=0 2> /dev/null)
            echo "Subtitle stream $i language: '${subtitle_language:-unset}'"

            # Check if subtitle track language is empty, English, or Undefined
            if [[ -z "$subtitle_language" || "$subtitle_language" =~ ^(eng|und)$ ]]; then
                # Get the current track title to check for SDH or Forced subtitle types
                subtitle_old_title="$(ffprobe -i "$video_file" -select_streams s:$i -show_entries stream=index:stream_tags=title -of csv=p=0 2> /dev/null)"

                subtitle_new_title=""
                if echo "$subtitle_old_title" | ggrep -i sdh; then
                    subtitle_new_title="Subtitle Track [SDH]"
                elif echo "$subtitle_old_title" | ggrep -i forced; then
                    subtitle_new_title="Subtitle Track [Forced]"
                elif echo "$subtitle_old_title" | ggrep -i cc; then
                    subtitle_new_title="Subtitle Track [CC]"
                fi

                # Build the ffmpeg command args to set the language and title metadata
                subtitle_args+=(
                    "-metadata:s:s:$i" language=eng
                    "-metadata:s:s:$i" title="$subtitle_new_title"
                )

                echo "Adding subtitle track with language: $subtitle_language"
            else
                # Build the ffmpeg command args to exclude the non-english subtitle track
                subtitle_args+=(
                    -map -0:s:"$i"
                )

                echo "Dropping subtitle track with language: $subtitle_language"
            fi
        done
    else
        echo "No subtitle tracks found in the video file."
    fi

    set -x
    ffmpeg -i "${video_file}" \
        -c:v copy \
        -c:a "${audio_codec_global}" \
        -c:s mov_text \
        -map_chapters 0 \
        -map 0 \
        -metadata:s:v:0 title="Video Track" \
        -metadata:s:v:0 language=eng \
        "${audio_args[@]}" \
        "${subtitle_args[@]}" \
        -metadata:s:t:0 title="Text Track" \
        -metadata:s:t:0 language=eng \
        "${video_file%.*}.processed.mp4" -y
    set +x
}

#
# all2mp4_batch: Converts all video files in a TV show folder and its seasons to MP4 using ffmpeg.
#
# Parameters: -f | --folder   - The path to the TV show folder.
#             -i | --in-place - Move the original video files to the Trash.
#
# Returns: The last command exit status.
#
function all2mp4_batch() {
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "Error: ffmpeg is required but not installed. Aborting."
        return 1
    }

    command -v ffprobe > /dev/null 2>&1 || {
        echo >&2 "Error: ffprobe is required but not installed. Aborting."
        return 1
    }

    # Local variables, specify the path to the main TV show folder
    local tv_show_folder trash_originals

    # Loop through the arguments
    while [[ ${#} -gt 0 ]]; do
        case ${1} in
            -f | --folder)
                shift
                tv_show_folder="${1}"
                ;;
            -i | --in-place)
                trash_originals="true"
                ;;
            *)
                echo "Error: unrecognized option: ${1}"
                return 1
                ;;
        esac
        shift
    done

    # Iterate over season folders
    for season_folder in "${tv_show_folder}"/*; do
        if [[ -d "${season_folder}" ]]; then
            # Convert video files to MP4 in the season folder
            for video_file in "${season_folder}"/*; do
                if [[ -f "${video_file}" ]]; then
                    all2mp4 "$video_file"

                    # Trash original files if in-place requested
                    if [[ ${trash_originals} == "true" ]]; then
                        local tv_show_name
                        tv_show_name=$(basename "$tv_show_folder")
                        local season_number
                        season_number=$(basename "$season_folder" | ggrep -oP '\d+' | sed 's/^0*//')
                        local episode_number
                        episode_number=$(basename "$video_file" | ggrep -oP '\d+' | head -n 1 | sed 's/^0*//')
                        local mkv_base_file
                        mkv_base_file="$(basename "$video_file")"
                        local trash_filename
                        trash_filename="$(printf "${HOME}/.Trash/%s-s%02de%02d-%s" "$tv_show_name" "$season_number" "$episode_number" "$mkv_base_file")"
                        mv -v "$video_file" "$trash_filename"
                    fi
                fi
            done
        fi
    done

    unset tv_show_folder trash_originals season_folder audio_count audio_args subtitle_count subtitle_args subtitle_track_title audio_track_title
}

#
# processTvEpisodes: Helper function to preprocess TV shows.
#
# Parameters: -f | --folder   - The path to the TV show folder.
#             -i | --in-place - Move the original files to the Trash.
#
# Returns: The last command exit status.
#
function processTvEpisodes() {
    # Ensure AtomicParsley is installed
    command -v AtomicParsley > /dev/null 2>&1 || {
        echo >&2 "I require AtomicParsley but it's not installed.  Aborting."
        return 1
    }

    # Local variables, specify the path to the main TV show folder
    local tv_show_folder trash_originals

    # Loop through the arguments
    while [[ ${#} -gt 0 ]]; do
        case ${1} in
            -f | --folder)
                shift
                tv_show_folder="${1}"
                ;;
            -i | --in-place)
                trash_originals="true"
                ;;
            *)
                echo "Error: unrecognized option: ${1}"
                return 1
                ;;
        esac
        shift
    done

    # Extract the name of the TV show from the folder path
    local tv_show_name
    tv_show_name=$(basename "$tv_show_folder")

    # Iterate over season folders
    for season_folder in "$tv_show_folder"/*; do
        # Extract season number from folder name
        local season_number
        season_number=$(basename "$season_folder" | ggrep -oP '\d+' | sed 's/^0//')

        # Iterate over episode files
        for episode_file in "$season_folder"/*.mp4; do
            # Extract episode number from file name
            local episode_number
            episode_number=$(basename "$episode_file" | ggrep -oPi 'S\d+E\d+' | head -n 1 | ggrep -oPi 'E\d+' | ggrep -oP '\d+' | sed 's/^0*//')

            # Additional handling for 'xx' formats
            if [ -z "$episode_number" ]; then
                episode_number=$(basename "$episode_file" | ggrep -oPi '\d+' | head -n 1 | sed 's/^0*//')
            fi

            local episode_base_file
            episode_base_file="$(basename "$episode_file")"
            local processed_episode_file="$season_folder"/processed_"$episode_base_file"

            # Set metadata using AtomicParsley
            set -x
            AtomicParsley "$episode_file" \
                --title "Episode $episode_number" \
                --stick "TV Show" \
                --artist "$tv_show_name" \
                --album "$tv_show_name, Season $season_number" \
                --albumArtist "$tv_show_name" \
                --TVShowName "$tv_show_name" \
                --TVEpisodeNum "$episode_number" \
                --TVSeasonNum "$season_number" \
                --track "$episode_number" \
                --output "$processed_episode_file"
            set +x

            # Trash original files if in-place requested
            if [[ ${trash_originals} == "true" ]]; then
                local trash_filename
                trash_filename="$(printf "${HOME}/.Trash/processTvEpisodes_%s-s%02de%02d-%s" "$tv_show_name" "$season_number" "$episode_number" "$episode_base_file")"
                mv -v "$episode_file" "$trash_filename"
                mv -v "$processed_episode_file" "$episode_file"
            fi
        done
    done

    unset tv_show_folder tv_show_name season_folder season_number episode_number trash_originals
}

#
# renameTvEpisodes: Helper function to rename TV shows.
#
# Parameters: -f | --folder   - The path to the TV show folder.
#             -i | --in-place - Move the original files to the Trash.
#
# Returns: The last command exit status.
#
function renameTvEpisodes() {
    set -x
    # Ensure mp4info is installed (brew install mp4v2)
    command -v mp4info > /dev/null 2>&1 || {
        echo >&2 "I require mp4info but it's not installed.  Aborting."
        return 1
    }

    # Ensure AtomicParsley is installed
    command -v AtomicParsley > /dev/null 2>&1 || {
        echo >&2 "I require AtomicParsley but it's not installed.  Aborting."
        return 1
    }

    # Local variables, specify the path to the main TV show folder
    local tv_show_folder trash_originals

    # Loop through the arguments
    while [[ ${#} -gt 0 ]]; do
        case ${1} in
            -f | --folder)
                shift
                tv_show_folder="${1}"
                ;;
            -i | --in-place)
                trash_originals="true"
                ;;
            *)
                echo "Error: unrecognized option: ${1}"
                return 1
                ;;
        esac
        shift
    done

    # Extract the name of the TV show from the folder path
    local tv_show_name
    tv_show_name=$(basename "$tv_show_folder")

    # Iterate over season folders
    for season_folder in "$tv_show_folder"/*; do
        # Extract season number from folder name
        local season_number
        season_number=$(basename "$season_folder" | ggrep -oP '\d+' | sed 's/^0*//')

        # Iterate over episode files
        for episode_file in "$season_folder"/*.mp4; do
            set -x
            # Use mp4info to extract episode number and title
            local episode_base_file
            episode_base_file="$(basename "$episode_file")"

            # Extract episode number from file name
            local episode_number
            episode_number="$(basename "$episode_file" | ggrep -oPi 's\d+e\d+(-e\d+)?' | head -n 1)"

            # Additional handling for 'xx' formats
            if [ -z "$episode_number" ]; then
                episode_number="$(basename "$episode_file" | ggrep -oPi '\d+' | head -n 1)"
            fi

            episode_title="$(mp4info "$episode_file" | ggrep 'Name:' | sed 's/^ *Name: *//' | sed 's/ *$//' | sed 's/^\xc2\xa0*//g')"
            file_suffix=$(echo "${episode_title//:/ -}" | tr '/' '-')
            new_filename=$(printf "%s %s.mp4" "$episode_number" "${file_suffix}")

            # Set the TVEpisode metadata field and rename the episode file
            AtomicParsley "$episode_file" --TVEpisode "$episode_title" --output "$season_folder/$new_filename"

            # Trash original files if in-place requested
            if [[ ${trash_originals} == "true" ]]; then
                local trash_filename
                trash_filename="$(printf "${HOME}/.Trash/renameTvEpisodes_%s-s%02de%02d-%s" "$tv_show_name" "$season_number" "$episode_number" "$episode_base_file")"
                mv -v "$episode_file" "$trash_filename"
            fi
            set +x
        done
    done

    unset tv_show_folder tv_show_name season_folder season_number episode_file episode_number episode_title
}

#
# printToM4bHelp: Prints help information for the toM4b function.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function printToM4bHelp() {
    echo "usage:"
    echo "  ${FUNCNAME[1]} [options]"
    echo ""
    echo "options:"
    echo "  -s | --source-ext           Optional source file extension, default is found audio file extension"
    echo "  -t | --target-ext           Optional target file extension, default is m4b"
    echo "  -a | --artwork              Path to album artwork to use"
    echo "  -c | --chapters             Retain chapters flag"
    echo "  -p | --process-chapters     Add chapter data"
    echo "  -m | --metadata             Add extended metadata tags"
}

#
# toM4b:      Helper function to convert audiobooks.
#
# Parameters: -s | --source_ext           Optional source file extension, default is found audio file extension
#             -t | --target_ext           Optional target file extension, default is m4b
#             -a | --artwork              Path to album artwork to use
#             -c | --chapters             Retain chapters
#             -p | --process-chapters     Add chapter data
#             -m | --metadata             Add extended metadata tags
#
# Returns: The last command exit status.
#
function toM4b() {
    set -x
    # Ensure ffmpeg is installed
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed.  Aborting."
        return 1
    }

    # Ensure AtomicParsley is installed
    command -v AtomicParsley > /dev/null 2>&1 || {
        echo >&2 "I require AtomicParsley but it's not installed.  Aborting."
        return 1
    }

    # Local variables
    local source_ext target_ext album_art map_chapters extra_meta

    # Loop through the arguments
    while [[ ${#} -gt 0 ]]; do
        case ${1} in
            -s | --source_ext)
                shift
                source_ext="${1}"
                ;;
            -t | --target_ext)
                shift
                target_ext="${1}"
                ;;
            -a | --artwork)
                shift
                album_art="${1}"
                ;;
            -c | --chapters)
                map_chapters="true"
                ;;
            -p | --process-chapters)
                process_chapters="true"
                ;;
            -m | --metadata)
                extra_meta="true"
                ;;
            *)
                printToM4bHelp
                return 1
                ;;
        esac
        shift
    done

    # Defaults for album art
    album_art="${album_art:-${PWD}/cover.jpg}"
    album_art=$(resolvePath "${album_art}")

    # List top file type in current directory
    local top_file
    # Preserve the legacy GNU ls exclusion and sorting behavior.
    # shellcheck disable=SC2012
    top_file=$(ls -I "*.jpg" -I "*.png" -I "converted" -I "*.cue" -I "*.txt" | head -1)
    local filename
    filename=$(basename "${top_file}")
    local file_ext="${filename##*.}"

    # Use extension of first file if not provided
    source_ext="${source_ext:-${file_ext}}"
    target_ext="${target_ext:-m4b}"

    # Default audio codec is copy, aac for mp3 files
    local audio_codec="copy"
    [[ "${source_ext}" != "mp3" ]] || audio_codec="aac"

    # Argument array for ffmpeg
    local ffmpeg_args=()

    # Process chapters
    [[ -n "${map_chapters}" ]] || ffmpeg_args+=(-map_chapters -1)

    # Get author from directory name "author - book title" format
    local meta_author
    meta_author="$(basename "${PWD}" | cut -d- -f1 | xargs)"

    # Define extra metadata tags
    local meta_language="eng"
    # These trusted templates expand later inside the existing eval calls.
    # shellcheck disable=SC2016
    local meta_title='echo "$i" | sed -rn "s/[[:digit:]]+ - (.*)\.${source_ext}/\1/p" | sed "s/ *//"'
    local meta_artist
    meta_artist="${meta_author}, $(test -f "${PWD}"/narrator.txt && cat "${PWD}"/narrator.txt)"
    local meta_album_artist="${meta_author}"
    local meta_album
    meta_album="$(basename "${PWD}" | cut -d- -f2 | sed 's/ *//')"
    local meta_grouping
    meta_grouping="$(test -f "${PWD}"/grouping.txt && cat "${PWD}"/grouping.txt)"
    local meta_comment
    meta_comment="$(test -f "${PWD}"/description.txt && cat "${PWD}"/description.txt)"
    local meta_genre
    meta_genre="$(test -f "${PWD}"/genre.txt && cat "${PWD}"/genre.txt)"
    local meta_date
    meta_date="$(test -f "${PWD}"/date.txt && cat "${PWD}"/date.txt)"
    # These trusted templates expand later inside the existing eval calls.
    # shellcheck disable=SC2016
    local meta_current_track='echo "${i}" | ggrep -Po "^\d+" | tr -d "(" | sed "s/^0*//" | sed "s/ *//"'
    # These trusted templates expand later inside the existing eval calls.
    # shellcheck disable=SC2016
    local meta_total_tracks='ls *.${source_ext} | wc -l | xargs'
    local meta_disc="1/1"
    local meta_composer
    meta_composer="$(test -f "${PWD}"/narrator.txt && cat "${PWD}"/narrator.txt)"
    local meta_copyright
    meta_copyright="©$(test -f "${PWD}"/date.txt && cat "${PWD}"/date.txt | cut -d- -f1) ${meta_author}"

    [[ -f "${PWD}"/copyright.txt ]] && meta_copyright="$(cat "${PWD}"/copyright.txt)"

    # Add general metadata tags
    ffmpeg_args+=(-id3v2_version 3)
    ffmpeg_args+=(-metadata:s language="${meta_language}")

    # Add extra metadata tags
    if [[ -n "${extra_meta}" ]]; then
        ffmpeg_args+=(-metadata artist="${meta_artist}")
        ffmpeg_args+=(-metadata author="${meta_artist}")
        ffmpeg_args+=(-metadata album_artist="${meta_album_artist}")
        ffmpeg_args+=(-metadata album="${meta_album}")
        [[ -z "${meta_grouping}" ]] || ffmpeg_args+=(-metadata grouping="${meta_grouping}")
        ffmpeg_args+=(-metadata comment="${meta_comment}")
        ffmpeg_args+=(-metadata genre="${meta_genre}")
        ffmpeg_args+=(-metadata date="${meta_date}")
        ffmpeg_args+=(-metadata disc="${meta_disc}")
        ffmpeg_args+=(-metadata composer="${meta_composer}")
        ffmpeg_args+=(-metadata copyright="${meta_copyright}")
    fi

    # Setup conversion directory
    local convert_dir="${PWD}/converted"
    mkdir -vp "${convert_dir}"

    # Assemble optional ffmpeg arguments without splitting metadata or paths.
    local -a chapter_inputs chapter_metadata track_metadata
    chapter_inputs=()
    chapter_metadata=()
    [[ -z ${process_chapters:-} ]] || chapter_inputs=(-i FFMETADATAFILE)
    [[ -z ${process_chapters:-} ]] || chapter_metadata=(-map_metadata 2)

    for i in *."${source_ext}"; do
        track_metadata=()
        if [[ -n ${extra_meta:-} ]]; then
            track_metadata=(-metadata "track=$(eval "${meta_current_track}")/$(eval "${meta_total_tracks}")")
        fi

        set -x
        ffmpeg -i "${i}" -i "${album_art}" \
            "${chapter_inputs[@]}" \
            -map 0:0 -map 1:0 \
            "${chapter_metadata[@]}" \
            -c:a:0 "${audio_codec}" -c:v:1 libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" \
            -metadata:s:a:0 title="$(eval "${meta_title}")" \
            -metadata:s:v:1 title="Album cover" \
            -metadata title="$(eval "${meta_title}")" \
            "${track_metadata[@]}" \
            "${ffmpeg_args[@]}" \
            "${convert_dir}/${i%.*}.${target_ext}"
        AtomicParsley "${convert_dir}/${i%.*}.${target_ext}" --artwork REMOVE_ALL --artwork "${album_art}" --overWrite
        set +x
    done

    unset source_ext target_ext album_art map_chapters extra_meta
}

#
# modTime:    Transfers created and modified dates between files.
#
# Parameters: $1 - The source file.
#             $2 - The target file.
#
# Returns: The last command exit status.
#
function modTime() {
    # Ensure dependencies are installed
    command -v exiftool > /dev/null 2>&1 || {
        echo >&2 "I require exiftool but it's not installed. Aborting."
        return 1
    }

    # Check for proper usage
    if [[ $# -ne 2 ]]; then
        echo "usage: ${FUNCNAME[0]} <source_file> <target_file>"
        return 1
    fi

    local source_file
    source_file=$(resolvePath "${1}")
    local target_file
    target_file=$(resolvePath "${2}")
    local created_time
    created_time=$(stat -f %SB -t "%Y:%m:%d %H:%M:%S" "${source_file}")

    exiftool -overwrite_original_in_place -tagsFromFile "${source_file}" -All:All "${target_file}"
    exiftool -overwrite_original_in_place -quicktime:createdate="${created_time}" -MediaCreateDate="${created_time}" "${target_file}"
    setfile -d "${created_time}" "${target_file}"
    touch -r "${source_file}" "${target_file}"
}

#
# modFiles:   Transfers created and modified dates from files that have the
#             same name but different extensions.
#
# Parameters: $1 - The source directory.
#             $2 - The target file extension.
#
# Returns: The last command exit status.
#
function modFiles() {
    # Check for proper usage
    if [[ ${#} -ne 2 ]]; then
        echo "usage: ${FUNCNAME[0]} <source_directory> <target_file_ext>"
        return 1
    fi

    local source_dir
    source_dir=$(resolvePath "${1}")
    local target_ext="${2}"
    local src_file tgt_file

    for i in "${source_dir}"/*."${target_ext}"; do
        src_file=$(gls -1 "${i%.*}".* | grep -v "${i}")
        tgt_file="${i}"

        modTime "${src_file}" "${tgt_file}"
    done
}

#
# createPlexPlaylist: Upload a playlist whose paths already match the Plex server.
#
# Parameters: $1 - The M3U playlist path.
#             PLEX_URL - The Plex server URL, supplied by the caller.
#             PLEX_SECTION_ID - The library section identifier.
#             PLEX_TOKEN - The access token from private local configuration.
#
# Returns: The curl exit status, or 1 when required configuration is missing.
#
function createPlexPlaylist() (
    # Keep credentials out of shell traces, URLs, and command-line arguments.
    set +x

    if [[ ${#} -ne 1 || -z ${PLEX_URL:-} || -z ${PLEX_SECTION_ID:-} || -z ${PLEX_TOKEN:-} ]]; then
        printf '%s\n' 'usage: set PLEX_URL, PLEX_SECTION_ID, and PLEX_TOKEN; createPlexPlaylist <m3u_playlist>' >&2
        return 1
    fi

    # Plex tokens are alphanumeric; reject configuration-file delimiters.
    if [[ ! ${PLEX_TOKEN} =~ ^[a-zA-Z0-9_-]+$ || ! ${PLEX_SECTION_ID} =~ ^[0-9]+$ ]]; then
        printf '%s\n' 'error: invalid Plex token or section identifier' >&2
        return 1
    fi

    local playlist
    playlist=$(resolvePath "${1}") || return 1

    # Path mappings belong in the playlist or private configuration, not source.
    printf 'header = "X-Plex-Token: %s"\n' "${PLEX_TOKEN}" |
        curl --config - --silent --show-error --fail --request POST --get \
            --data-urlencode "sectionID=${PLEX_SECTION_ID}" \
            --data-urlencode "path=${playlist}" "${PLEX_URL%/}/playlists/upload"
)

#
# analyzeMp3s: Analyze and print audio file information.
#
# Parameters: $1 - The directory to analyze.
#
# Returns: The last command exit status.
#
function analyzeMp3s() {
    # Validate audio file path
    local file_path="${1}"
    if [[ -z "${file_path}" ]]; then
        file_path="${PWD}"
    else
        file_path=$(resolvePath "${file_path}")
    fi

    #
    # Bitrate
    #
    # find "${file_path}" -type f -exec exiftool -S -filepath -AudioBitrate {} \; |
    # awk '$1 == "AudioBitrate:" && $2 < 320 { gsub("FilePath: ","", f); printf "%s\n", f} { f = $0 }'
    # awk '$1 == "AudioBitrate:" && $2 < 320 { gsub("FilePath: ","", f); printf "%s,%s\n", $2, f} { f = $0 }'

    #
    # Duration
    #
    find "${file_path}" -type f -exec afinfo {} \; 2> /dev/null |
        awk '/File:/ { song=$0 } /estimated duration/ { if ($3 > 30.0) print song }'
}

#
# setLanguage: Sets language for a media file.
#
# Parameters: $1 - The input file.
#             $2 - ISO 639-2 codes for language.
#
# Returns: The last command exit status.
#
function setLanguage() {
    # Check for proper usage
    if [[ ${#} -ne 2 ]]; then
        echo "usage: ${FUNCNAME[0]} <file> <language>"
        return 1
    fi

    # local meta_title
    # meta_title="$(mediainfo "${1}" | grep -m1 "Track name" | cut -d':' -f2 | sed  "s/^ *//g")"
    # meta_title_new="SMBW - ${meta_title}"
    # echo "$meta_title_new"

    # Validate audio file path
    local file lang filename extension

    file=$(resolvePath "${1}")
    lang="${2}"
    filename=$(basename -- "${file}")
    extension="${filename##*.}"

    # Convert the flac file to MP3 format
    ffmpeg -y -i "${file}" -map 0 -c copy -metadata:s language="${lang}" -map_metadata 0 -id3v2_version 3 "${file%.*}_${lang}.${extension}"
    #ffmpeg -y -i "${file}" -map 0 -c copy -metadata title="${meta_title_new}" -metadata:s language="${lang}" -map_metadata 0 -id3v2_version 3 "${file%.*}_${lang}.${extension}"
}

#
# toMp3: Converts audio files to MP3 format.
#
# Parameters: $1 - The audio file to convert.
#
# Returns: The last command exit status.
#
function toMp3() {
    # Check for proper usage
    if [[ ${#} -ne 1 ]]; then
        echo "usage: ${FUNCNAME[0]} <audio_file>"
        return 1
    fi

    # Validate audio file path
    local audio_file="${1}"
    audio_file=$(resolvePath "${audio_file}")

    # Convert the flac file to MP3 format
    ffmpeg -i "${audio_file}" -ab 320k -map_metadata 0 -id3v2_version 3 "${audio_file%.*}.mp3"
}

#
# toRingtone: Converts the provided audio file to m4r ringtone format.
#
# Parameters: $1 - The audio file to convert.
#
# Returns: The last command exit status.
#
function toRingtone() {
    # Check for proper usage
    if [[ ${#} -ne 1 ]]; then
        echo "usage: ${FUNCNAME[0]} <audio_file>"
        return 1
    fi

    # Validate audio file path
    local audio_file="${1}"
    audio_file=$(resolvePath "${audio_file}")

    # Convert the audio file to the m4r ringtone format
    #afconvert -f m4af -d aac -map_metadata 0 -id3v2_version 3 "${audio_file}" "${audio_file%.*}.m4r"
    afconvert -f m4af -d aac -map_metadata 0 "${audio_file}" "${audio_file%.*}.m4r"
}

#
# trimAudio:  Uses ffmpeg to trim an MP3 file.
#
# Parameters: $1 - The name of the audio file.
#             $2 - The start time, HH:mm:ss.
#             $3 - The duration to retain, HH:mm:ss.
#
# Returns: The last command exit status.
#
function trimAudio() {
    # Ensure dependencies are installed
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed. Aborting."
        return 1
    }

    # Check for proper usage
    if [[ ${#} -ne 3 ]]; then
        echo "usage: ${FUNCNAME[0]} <mp3_file> <start_time> <end_time>"
        return 1
    fi

    # Get parameters
    local audio_file="${1}"
    local start_time="${2}"
    local end_time="${3}"
    local trim_prefix="trimmed"
    local dir_name file_name trim_file

    # Set file names
    audio_file=$(resolvePath "${audio_file}")
    dir_name=$(dirname "${audio_file}")
    file_name=$(basename "${audio_file}")
    trim_file="${dir_name}/${trim_prefix}_${file_name}"

    # Trim the audio file
    ffmpeg -ss "${start_time}" -t "${end_time}" -i "${audio_file}" -c:v copy "${trim_file}"
}

#
# toLowerCase: Returns a lower-cased version of a string.
#
# Parameters: $@ - The string(s) to parse.
#
# Returns: The last command exit status.
#
function toLowerCase() {
    echo "${@}" | tr '[:upper:]' '[:lower:]'
}

#
# iterm2_print_user_vars: Set the short hostname variable for iTerm2 badges.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function iterm2_print_user_vars() {
    iterm2_set_user_var shortHost "$(hostname -s)"
}

#
# splitMp4:   Uses ffmpeg to split an MP4 file into two parts.
#
# Parameters: $1 - The name of the MP4 file.
#             $2 - The time at which the MP4 file should be split, HH:mm:ss.
#
# Returns: The last command exit status.
#
function splitMp4() {
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed. Aborting."
        return 1
    }

    if [[ ${#} -ne 2 ]]; then
        echo "usage: ${FUNCNAME[0]} <mp4_file> <hh:mm:ss.ms>"
        return 1
    fi

    local mp4_file="${1}"
    local split_time="${2}"
    local prefix file1 file2

    prefix=$(grep -Eo "^\d\d-\d\d" <<< "${mp4_file}")
    if [[ -n ${prefix} ]]; then
        file1="$(cut -d"-" -f1 <<< "${prefix}") $(echo "${mp4_file}" | grep -Eo "\....$")"
        file2="$(cut -d"-" -f2 <<< "${prefix}") $(echo "${mp4_file}" | grep -Eo "\....$")"
    else
        file1="${mp4_file%.*}-part1.mp4"
        file2="${mp4_file%.*}-part2.mp4"
    fi

    ffmpeg -i "${mp4_file}" -t "${split_time}" -c copy "${file1}" -ss "${split_time}" -c copy "${file2}"
}

join_mp4_files() {
    local input1="$1"
    local input2="$2"
    local output="$3"

    # Re-encode inputs to ensure compatibility
    ffmpeg -i "$input1" -c:v libx264 -c:a aac -strict experimental -f mpegts intermediate1.ts
    ffmpeg -i "$input2" -c:v libx264 -c:a aac -strict experimental -f mpegts intermediate2.ts

    # Concatenate intermediate .ts files into the final output
    ffmpeg -i "concat:intermediate1.ts|intermediate2.ts" -c copy -bsf:a aac_adtstoasc "$output"

    # Clean up intermediate files
    rm intermediate1.ts intermediate2.ts
}

#
# wmv2mp4:    Uses ffmpeg to convert an WMV to an MP4 file.
#
# Parameters: $1 - The name of the WMV file.
#
# Returns: The last command exit status.
#
function wmv2mp4() {
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed. Aborting."

        return 1
    }

    if [[ ${#} -ne 1 ]]; then
        echo "usage: ${FUNCNAME[0]} <wmv_file>"

        return 1
    fi

    local wmv_file="${1}"

    ffmpeg -i "${wmv_file}" -c:v:1 copy "${wmv_file%.*}.mp4"
}

#
# avi2mp4:    Uses ffmpeg to convert an AVI to an MP4 file.
#
# Parameters: $1 - The name of the AVI file.
#
# Returns: The last command exit status.
#
function avi2mp4() {
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed. Aborting."

        return 1
    }

    if [[ ${#} -ne 1 ]]; then
        echo "usage: ${FUNCNAME[0]} <avi_file>"

        return 1
    fi

    local avi_file="${1}"

    ffmpeg -i "${avi_file}" -map 0 -metadata:s language="eng" -map_metadata 0 -id3v2_version 3 -movflags use_metadata_tags -c copy "${avi_file%.*}.mp4"
}

#
# mov2mp4:    Uses ffmpeg to convert a MOV to an MP4 file.
#
# Parameters: $1 - The name of the MOV file.
#
# Returns: The last command exit status.
#
function mov2mp4() {
    command -v ffmpeg > /dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed. Aborting."

        return 1
    }

    if [[ ${#} -ne 1 ]]; then
        echo "usage: ${FUNCNAME[0]} <mov_file>"

        return 1
    fi

    local mov_file="${1}"

    ffmpeg -i "${mov_file}" \
        -map 0 \
        -metadata:s language="eng" \
        -map_metadata 0 \
        -id3v2_version 3 \
        -movflags use_metadata_tags \
        -c copy "${mov_file%.*}.mp4"

    # ffmpeg -i "${mov_file}" \
    #     -map 0 \
    #     -metadata:s language="eng" \
    #     -map_metadata 0 \
    #     -id3v2_version 3 \
    #     -movflags use_metadata_tags \
    #     -acodec aac -strict experimental -ac 2 \
    #     -vcodec h264 -preset slow -y "${mov_file%.*}.mp4"

    exiftool -overwrite_original_in_place -tagsFromFile "${mov_file}" -All:All "${mov_file%.*}.mp4"
    modTime "${mov_file}" "${mov_file%.*}.mp4"
}

#
# joinBy:     Joins the provided array by a delimiter.
#
# Parameters: $1 - The delimiter used to join the values.
#             $2 onward - The values to join.
#
# Returns: The last command exit status.
#
function joinBy {
    local DELIMITER=${1}
    shift
    echo -n "${1}"
    shift
    printf "%s" "${@/#/$DELIMITER}"
}

#
# quit:       Quits an OS X application cleanly.
#
# Parameters: $* - The list of OS X applications to quit.
#
# Returns: The last command exit status.
#
function quit() {
    for app in "${@}"; do
        osascript -e 'quit app "'"${app}"'"'
    done
}

#
# relaunch:   Relaunches an OS X application.
#
# Parameters: $* - The list of OS X applications to relaunch.
#
# Returns: The last command exit status.
#
function relaunch() {
    for app in "${@}"; do
        osascript -e 'quit app "'"${app}"'"'
        sleep 2
        open -a "${app}"
    done
}

#
# colorEcho:  Prints the user specified string to the screen using the specified
#             color.  If no color is provided, the default no color option is used.
#
# Parameters: $1 - The string to print.
#             $2 - The color to use for printing the string.
#
#             NOTE: The following color options are available:
#
#                   [0|1]30, [dark|light] black
#                   [0|1]31, [dark|light] red
#                   [0|1]32, [dark|light] green
#                   [0|1]33, [dark|light] brown
#                   [0|1]34, [dark|light] blue
#                   [0|1]35, [dark|light] purple
#                   [0|1]36, [dark|light] cyan
#
# Returns: The last command exit status.
#
function colorEcho() {
    # Check for proper usage
    if [[ ${#} == 0 || ${#} -gt 2 ]]; then
        echo "usage: ${FUNCNAME[0]} <string> [<0|1>3<0-6>]"
        return 1
    fi

    # Set default color to white
    MSSG=${1}
    CLRCODE=${2}
    LIGHTDARK=1
    MSGCOLOR=0

    # If color code was provided, then set it
    if [[ ${#} == 2 ]]; then
        LIGHTDARK=${CLRCODE:0:1}
        MSGCOLOR=${CLRCODE:1}
    fi

    # Print out the message
    echo -e -n "${MSSG}" | awk '{print "\033['"${LIGHTDARK}"';'"${MSGCOLOR}"'m" $0 "\033[1;0m"}'
}

#
# box:        Creates a box of '#' characters around a given string.
#
# Parameters: $1 - The string displayed inside the box.
#             $2 - The optional border character, defaulting to #.
#
# Returns: The last command exit status.
#
function box() {
    t="$1xxxx"
    c=${2:-#}
    echo -e "${t//?/$c}"
    echo -e "$c $1 $c"
    echo -e "${t//?/$c}"
}

#
# boxconfirm: Displays a custom confirmation box with the specified message
#             and returns true if the user types in something that is =~ [yes].
#
# Parameters: $1 - The custom confirmation text string to display.
#             $2 - The optional color of the box, default is green.
#
# Returns: Status 0 if the answer contains y, e, or s; otherwise status 255.
#
function boxconfirm() {
    # Configuration variables
    ANSWER=-1
    CONFIRM_MSG=${1}
    COLOR=32

    # Check to see if an optional color was provided
    if [[ ${2} != "" ]]; then
        COLOR=${2}
    fi

    echo ""
    box "${CONFIRM_MSG}" | awk '{print "\033[1;'"${COLOR}"'m" $0 "\033[1;0m"}'
    echo ""
    echo -n "---> "
    read -r ANS
    echo ""

    # Check for a variety of yes responses
    if [[ ${ANS} =~ [yes] ]]; then
        ANSWER=0
    fi

    return ${ANSWER}
}

#
# tarbz2:     Wrapper function for the 'tar' Unix tool that simply omits resource
#             forks, and other extraneous garbage files to which no user should
#             be subjected, from being included in the specified bzip2 compressed
#             archive.
#
# Parameters: $@ - The name of the bzip2 compressed archive to create and
#                    list of source files to be included in the archive.
#
# Returns: The last command exit status.
#
function tarbz2() {
    COPY_EXTENDED_ATTRIBUTES_DISABLE=true \
        COPYFILE_DISABLE=1 \
        tar -c --exclude='._*' --exclude='.svn' --exclude='.DS_Store' \
        --exclude='*.bak' --exclude='*~' --exclude='*.swp' -vjf "${@}"
}

#
# untarbz2:   Wrapper function for the 'tar' Unix tool that decompresses the
#             specified bzip2 compressed archive.
#
# Parameters: $@ - The name of the bzip2 archive to decompress.
#
# Returns: The last command exit status.
#
function untarbz2() {
    tar -xvjf "${@}"
}

#
# targz:      Simple wrapper function for the 'tar' Unix tool that simply omits
#             resource forks, and other extraneous garbage files to which no user
#             should be subjected, from being included in the specified gzip
#             compressed archive.
#
# Parameters: $@ - The name of the gzip compressed archive to create and
#                    list of source files to be included in the archive.
#
# Returns: The last command exit status.
#
function targz() {
    COPY_EXTENDED_ATTRIBUTES_DISABLE=true \
        COPYFILE_DISABLE=1 \
        tar -c --exclude='._*' --exclude='.svn' --exclude='.DS_Store' \
        --exclude='*.bak' --exclude='*~' --exclude='*.swp' -vzf "${@}"
}

#
# untargz:    Simple wrapper function for the 'tar' Unix tool that decompresses
#             the specified gzip compressed archive.
#
# Parameters: $@ - The name of the gzip archive to decompress.
#
# Returns: The last command exit status.
#
function untargz() {
    tar -xvzf "${@}"
}

#
# gofind:     Lists all files in the current working directory and its sub-folders
#             matching the regular expression '*$@*'.
#
# Parameters: $@ - A keyword in the filename to find, or the filename itself.
#
# Returns: The last command exit status.
#
function gofind() {
    find . -type f -iname "*${*}*" -exec gls -pGFNlh --color=auto --group-directories-first {} \;
}

#
# lsext:      Lists all files in the current working directory and its sub-folders
#             with the given extension.
#
# Parameters: $1 - The file extension to list, e.g. "jpg", "txt", or "mp3"
#
# Returns: The last command exit status.
#
function lsext() {
    find . -type f -iname "*.${1}" -exec gls -pGFNlh --color=auto --group-directories-first {} \;
}

#
# rmext:      Deletes all files in the current working directory and its sub-folders
#             with the given extension.
#
# Parameters: $1 - The file extension to delete, e.g. "jpg", "txt", or "mp3"
#
# Returns: The last command exit status.
#
function rmext() {
    find . -iname "*.${1}" -ok rm '{}' ';'
}

#
# mach: Displays system information about this machine.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function mach() {
    echo -e "\nMachine information:"
    uname -a
    echo -e "\nDistribution Information:"
    lsb_release -a
    echo -e "\nUsers logged on:"
    w -h
    echo -e "\nCurrent date:"
    date
    echo -e "\nMachine status:"
    uptime
    echo -e "\nMemory status:"
    top -l 1 | head | awk 'NR>=6&&NR<9'
    echo -e "\nFilesystem status:"
    df -h
}

#
# rpass: Generates a random 12 character alphanumeric password, minus l's and o's
#        for readability and to avoid confusion.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function rpass() {
    openssl rand -base64 1000 | tr "[:upper:]" "[:lower:]" |
        tr -cd "[:alnum:]" |
        tr -d "lo" |
        cut -c 1-12
}

#
# resolvePath: Resolves and displays the specified path as an absolute path.
#
# Parameters: $1 - The path to resolve and display.
#
# Returns: The last command exit status.
#
function resolvePath() {
    local resolved_path
    local dir

    if [[ "${1}" == */ ]]; then
        echo "$(cd "${1}" && pwd)/"
    else
        dir="$(dirname "${1}")"
        resolved_path="$(cd "${dir}" && pwd)/$(basename "${1}")"

        if [[ -e "${resolved_path}" ]]; then
            echo "${resolved_path}"
        fi
    fi
}

#
# gitMerge:   Fetches remote changes for the specified remote repository and
#             branch and merges them into the specified local branch, or the
#             local branch of the same name of the remote branch, if the local
#             branch name is not provided.
#
# Parameters: $1 - The remote repository.
#             $2 - The remote branch to merge.
#             $3 - The optional local target branch name.
#
# Returns: The last command exit status.
#
function gitMerge() {
    # Ensure arguments were passed
    if [[ ${#} -lt 1 || ${#} -gt 3 ]]; then
        echo "usage:"
        echo "  ${FUNCNAME[0]} <remote_repository> <remote_branch> [local_branch]"

        return 1
    fi

    # Set the upstream and local branch names
    local REMOTE_REPO="${1}"
    local REMOTE_BRANCH="${2}"
    local LOCAL_BRANCH="${REMOTE_BRANCH}"

    # Use the local branch if one was provided
    if [[ -n ${3// /} ]]; then
        LOCAL_BRANCH="${3}"
    fi

    # Get the URL of the remote repository
    local REMOTE_REPO_URL
    REMOTE_REPO_URL="$(git config --get "remote.${REMOTE_REPO}.url")"

    # Check to ensure the remote repository exists for the current git repository
    if [[ -z ${REMOTE_REPO_URL// /} ]]; then
        echo "${FUNCNAME[0]}: error: remote repository '${REMOTE_REPO}' does not exist for the current git repository"

        return 1
    fi

    # Ensure the remote branch exists for the remote repository
    if ! git ls-remote --exit-code --heads "${REMOTE_REPO_URL}" "${REMOTE_BRANCH}" > /dev/null 2>&1; then
        echo "${FUNCNAME[0]}: error: remote branch '${REMOTE_BRANCH}' does not exist for remote repository '${REMOTE_REPO}'"

        return 1
    fi

    # Ensure the local branch exists
    if ! git rev-parse --verify "${LOCAL_BRANCH}" > /dev/null 2>&1; then
        echo "local branch '${LOCAL_BRANCH}' does not exist, creating..."

        git checkout -b "${LOCAL_BRANCH}" "${REMOTE_REPO}/${REMOTE_BRANCH}"
    fi

    # Fetch remote changes, update the local branch and merge the remote branch changes
    git fetch "${REMOTE_REPO}"
    git checkout "${LOCAL_BRANCH}"
    git pull origin "${LOCAL_BRANCH}"
    git merge "${REMOTE_REPO}/${REMOTE_BRANCH}"
}

#
# resetGitBranch: Deletes a git branch and recreates it.
#
# Parameters: $1 - The Git branch to reset.
#
# Returns: The last command exit status.
#
function resetGitBranch() {
    # Ensure arguments were passed
    if [[ ${#} -ne 1 ]]; then
        echo "usage:"
        echo "  ${FUNCNAME[0]} <git_branch>"

        return 1
    fi

    # Get the Git branch name to reset
    GIT_BRANCH="${1}"

    # Delete the branch remotely
    git push origin --delete "${GIT_BRANCH}"

    # Delete the branch locally
    git branch -D "${GIT_BRANCH}"

    # Create the branch locally and set it to track the upstream branch
    git checkout -b "${GIT_BRANCH}" upstream/"${GIT_BRANCH}"

    # Update any submodules
    git submodule update --init --recursive

    # Pull the latest changes
    git pull

    # Pull the latest changes from upstream
    git fetch upstream

    # Ensure we are on the correct branch
    git checkout "${GIT_BRANCH}"

    # Merge any upstream changes into the local branch
    git merge upstream/"${GIT_BRANCH}"

    # Print the current repository status
    git status
}

#
# printUploadKeyHelp: Prints help information for the uploadKey function.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function printUploadKeyHelp() {
    echo "usage:"
    echo "  ${FUNCNAME[1]} [options]"
    echo ""
    echo "options:"
    echo "  -f | --file   Local file containing public key(s) to be added to authorized_keys"
    echo "                    File syntax matches id_rsa.pub or authorized_keys files"
    echo "  -h | --host   Remote user and host to which the key(s) will be uploaded (e.g. user@host)"
    echo "  -p | --port   Optional SSH port of the remote host"
}

#
# uploadKey:  Uploads SSH key(s) to the specified remote host.
#
# Parameters: -f | --file - Local file containing public keys to upload.
#             -h | --host - Remote user and host receiving the keys.
#             -p | --port - Optional SSH port of the remote host.
#
# Returns: The last command exit status.
#
function uploadKey() {
    # Ensure arguments were passed
    if [[ ${#} -eq 0 ]]; then
        printUploadKeyHelp
        return 1
    fi

    # Loop through the arguments
    while [[ ${#} -gt 0 ]]; do
        case ${1} in
            -f | --file)
                shift
                KEY_FILE=${1}
                ;;
            -h | --host)
                shift
                REMOTE_HOST=${1}
                ;;
            -p | --port)
                shift
                REMOTE_PORT=${1}
                ;;
            *)
                printUploadKeyHelp
                return 1
                ;;
        esac
        shift
    done

    # Ensure key(s) file is set
    if [[ -n ${KEY_FILE// /} ]]; then
        # Ensure key(s) file exists
        if [[ ! -f ${KEY_FILE} ]]; then
            echo "${FUNCNAME[0]}: error: private key(s) not found at '${KEY_FILE}'" >&2
            return 1
        fi

        # Set absolute path of key(s) file
        KEY_FILE=$(resolvePath "${KEY_FILE}")
    fi

    # Ensure remote host is set
    if [[ -z ${REMOTE_HOST// /} ]]; then
        echo "${FUNCNAME[0]}: error: remote host not provided for key upload" >&2
        return 1
    fi

    # Check if remote port is set and is an integer
    if [[ -n ${REMOTE_PORT// /} ]]; then
        if [[ ! ${REMOTE_PORT} =~ ^[0-9]+$ ]]; then
            echo "${FUNCNAME[0]}: error: '${REMOTE_PORT}' is not a valid port" >&2
            return 1
        fi

        REMOTE_HOST="${REMOTE_HOST} -p ${REMOTE_PORT}"
    fi

    # Ensure ~/.ssh and authorized_keys exists on remote host
    ssh -q "${REMOTE_HOST}" "umask 0077; mkdir -p ~/.ssh && [[ -f ~/.ssh/authorized_keys ]] || touch ~/.ssh/authorized_keys"

    # Read in keys from file
    while read -r KEY; do
        K_TAG=$(echo "${KEY}" | cut -f3 -d" ")
        K_HST=$(echo "${REMOTE_HOST}" | cut -f1 -d" ")
        MSG_EXISTS="Key '${K_TAG}' exists for '${K_HST}', skipping"
        MSG_ADDED="Key '${K_TAG}' uploaded for '${K_HST}'"
        R_TST="grep -q '${KEY}' ~/.ssh/authorized_keys && echo \"${MSG_EXISTS}\""
        R_CMD="umask 0077; echo '${KEY}' >> ~/.ssh/authorized_keys && echo \"${MSG_ADDED}\""

        # Add key to authorized_keys if it is not already there
        ssh -n "${REMOTE_HOST}" "(${R_TST}) || (${R_CMD})"
    done < "${KEY_FILE}"
}

#
# greetUser: Display a short fortune rendered as a terminal greeting.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function greetUser() {
    echo
    colorEcho "$(fortune -s | figlet -c -f"straight")" 132
    echo
}

#
# logoutUser: Displays a personalized user logout message to the terminal window.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function logoutUser() {
    colorEcho "$(figlet -c -f"big" Tscheuss\!)" 132
    sleep .3
}

#
# hailHypnoToad: Sends praise to the almighty Hypno Toad.
#
#                Message: ALL GLORY to the HYPNO TOAD!
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function hailHypnoToad() {
    colorEcho "$(figlet -c All Glory to the)" 133
    colorEcho "$(cat ~/.hypnotoad)" 132
    colorEcho "$(figlet -c -f"big" HYPNO TOAD\!)" 133
    afplay ~/.sounds/Hypnotoad.mp3 &
}

#
# animatedWait: Displays an animated wait.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function animatedWait() {
    pid=$!
    spin='-\|/'
    i=0

    # Display a fancy animation
    while kill -0 ${pid} 2> /dev/null; do
        i=$(((i + 1) % 4))
        printf "\rWaiting for '%s.*' in repository '%s' ... %s ", "${BASE_FILE}" "${REPO_DIR}" "${spin:$i:1}"
        sleep .1
    done

    echo "Done!"
}

#
# printUbundoHelp: Prints the help information for the ubundo function.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function printUbundoHelp() {
    echo "usage:"
    echo "  ${FUNCNAME[1]} [options]"
    echo ""
    echo "options:"
    echo "  -c | --command   The command to execute"
    echo "  -u | --user      Execute the command as the provided user"
    echo "  -a | --all       Execute the command on all Ubuntu hosts"
}

#
# ubundo:     Issues the provided command to Ubuntu Linux hosts.
#
# Parameters: -c | --command   The command to execute
#             -u | --user      Execute the command as the provided user
#             -a | --all       Execute the command on all Ubuntu hosts
#
# Returns: The last command exit status.
#
function ubundo() {
    # Parse function parameters
    while [[ ${#} -gt 0 ]]; do
        case "${1}" in
            -c | --command)
                shift
                local COMMAND="${1}"
                ;;
            -u | --user)
                shift
                local R_USER="${1}"
                ;;
            -a | --all)
                local DO_ALL="true"
                ;;
            *)
                shift
                printUbundoHelp
                return 1
                ;;
        esac
        shift
    done

    # Check if command to issue was provided
    if [[ -z ${COMMAND// /} ]]; then
        printUbundoHelp
        return 1
    fi

    # Hosts are supplied by private local configuration, separated by spaces.
    local -a remote_hosts
    if [[ -z ${SSH_HOSTS:-} ]]; then
        printf '%s\n' 'error: set SSH_HOSTS to the hosts to contact' >&2
        return 1
    fi
    read -r -a remote_hosts <<< "${SSH_HOSTS}"

    # Issue command on configured SSH hosts
    if [[ "${DO_ALL}" = "true" ]]; then
        for box in "${remote_hosts[@]}"; do
            ssh -t "${R_USER}@${box}" "${COMMAND}"
        done
    fi
}

#
# printUbunputHelp: Prints the help information for the ubunput function.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function printUbunputHelp() {
    echo "usage:"
    echo "  ${FUNCNAME[1]} [options]"
    echo ""
    echo "options:"
    echo "  -l | --local     The local file to copy to remote hosts"
    echo "  -r | --remote    The optional remote location for the secure file copy"
    echo "  -u | --user      Perform the copy as the provided user"
    echo "  -a | --all       Perform the copy to all Ubuntu hosts"
}

#
# ubunput:    Securely copies the specified file(s) to all Ubuntu Linux hosts.
#
# Parameters: -l | --local     The local file to copy to all hosts
#             -r | --remote    The optional remote location for the secure file copy
#             -u | --user      Perform the copy as the provided user
#             -a | --all       Perform the copy to all Ubuntu hosts
#
# Returns: The last command exit status.
#
function ubunput() {
    # Parse function parameters
    while [[ ${#} -gt 0 ]]; do
        case "${1}" in
            -l | --local)
                shift
                local L_FILE="${1}"
                ;;
            -r | --remote)
                shift
                local R_FILE="${1}"
                ;;
            -u | --user)
                shift
                local R_USER="${1}"
                ;;
            -a | --all)
                local DO_ALL="true"
                ;;
            *)
                printUbunputHelp
                return 1
                ;;
        esac
        shift
    done

    # Check if command to issue was provided
    if [[ -z ${L_FILE// /} ]]; then
        printUbunputHelp
        return 1
    fi

    # Hosts are supplied by private local configuration, separated by spaces.
    local -a remote_hosts
    if [[ -z ${SSH_HOSTS:-} ]]; then
        printf '%s\n' 'error: set SSH_HOSTS to the hosts to contact' >&2
        return 1
    fi
    read -r -a remote_hosts <<< "${SSH_HOSTS}"

    # Issue command on configured SSH hosts
    if [[ "${DO_ALL}" = "true" ]]; then
        for box in "${remote_hosts[@]}"; do
            scp "${L_FILE}" "${R_USER}@${box}:${R_FILE}"
        done
    fi
}

#
# printCallingFunctionName: Prints the name of the parent function that called this one.
#
# Parameters: None.
#
# Returns: The last command exit status.
#
function printCallingFunctionName() {
    # Get the name of the current shell
    local shellName
    shellName=$(basename "$SHELL")

    # Check if the shell is Bash or Zsh
    if [[ "$shellName" == "bash" ]]; then
        echo "${FUNCNAME[2]}"
    elif [[ "$shellName" == "zsh" ]]; then
        # Zsh supplies funcstack when this compatibility branch is used.
        # shellcheck disable=SC2154
        echo "${funcstack[2]}"
    fi
}

#
# folderSync: This is an rsync-based function for synchronizing two folders.
#
#             WARNING: This function uses the "--delete" option which will
#                      "delete extraneous files from dest dirs", as stated
#                      in the rsync manual page.
#
#             The following options are enabled for the synchronization:
#
#             -a,              archive mode; same as -rlptgoD (no -H)
#             --no-D,          don't transfer character or block device files
#             --delay-updates, put all updated files into place at end
#             --delete,        delete extraneous files from dest dirs
#             --progress,      show individual file progress during transfer
#             -vv,             verbose mode
#             -h,              output numbers in a human-readable format
#             -r,              recurse into directories
#             -l,              copy symlinks as symlinks
#             -p,              preserve permissions
#             -t,              preserve times
#             -g,              preserve group
#             -o,              preserve owner (super-user only)
#
#             The following options are NOT enabled for the synchronization:
#
#             -E               preserve resource forks (extended attributes)
#             -i,              output a change-summary for all updates
#
#             The following options are NOT enabled for non-local disks:
#
#             -g,              preserve group
#             -o,              preserve owner (super-user only)
#
# Parameters: $1 - The source folder for the synchronization.
#             $2 - The destination folder for the synchronization.
#
# Returns: Status 1 on invalid input or cancellation; otherwise the final status message status.
#
function folderSync() {
    local func_name src dest opts msg warning ans

    # Name of this function
    func_name=$(printCallingFunctionName)

    # Check for proper usage and valid parameters
    if [[ ${#} != 2 ]]; then
        echo "usage: ${func_name} <source_directory> <target_directory>"
        return 1
    fi

    # Check for valid parameters
    if [[ ! -e ${1} || ! -e ${2} ]]; then
        echo "error: ${func_name}: invalid source or target directory" >&2
        return 1
    fi

    # Do not preserve file ownership if disk is non-local
    if echo "${2}" | grep /Volumes > /dev/null; then
        opts=("-rlpt" "--delay-updates" "--delete" "--progress" "-vv" "-h" "--exclude" '#recycle')
    else
        opts=("-a" "--no-D" "--delay-updates" "--delete" "--progress" "-vv" "-h" "--exclude" '#recycle')
    fi

    # Confirmation and warning messages
    msg="  Are you sure you wish to perform the following folder sync? (yes/no)  "
    warning="WARNING! Mind the trailing '/'. Do you mean the folder, or its contents?"

    # Resolve source and destination paths
    src=$(resolvePath "${1}")
    dest=$(resolvePath "${2}")

    # Display a confirmation showing the folders to be synced
    colorEcho "$(
        echo ""
        box "${msg}"
    )" 131
    colorEcho "$(
        echo ""
        box "${warning}"
    )" 133
    printf "\nSource:\n"
    colorEcho "    ${src}" 136
    printf "\nDestination:\n"
    colorEcho "    ${dest}" 136

    # Read answer
    printf "\n---> "
    read -r ans
    printf "\n"

    # Check the user's response
    case "${ans}" in
        [yY][eE][sS] | [Yy])
            if sudo rsync "${opts[@]}" "${src}" "${dest}"; then
                colorEcho "$(figlet -c -f'script' Sync complete.)" 132
            else
                colorEcho "$(figlet -c -f'block' error)" 131
            fi
            ;;
        *)
            echo "${func_name}: folder sync canceled, no changes were made."
            return 1
            ;;
    esac
}
