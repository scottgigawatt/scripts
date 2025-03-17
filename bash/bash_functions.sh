#!/usr/bin/env bash

#
# toM4b:      Helper function to convert audiobooks.
#
# Parameters: -s | --source-ext           Optional source file extension, default is found audio file extension
#             -t | --target-ext           Optional target file extension, default is m4b
#             -a | --artwork              Path to album artwork to use
#             -c | --chapters             Retain chapters
#             -p | --process-chapters     Add chapter data
#             -m | --metadata             Add extended metadata tags
#
function toM4b() {
    set -x
    # Ensure ffmpeg is installed
    command -v ffmpeg >/dev/null 2>&1 || {
        echo >&2 "I require ffmpeg but it's not installed.  Aborting."
        return 1
    }

    # Ensure AtomicParsley is installed
    command -v AtomicParsley >/dev/null 2>&1 || {
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
                return 1;;
        esac
        shift
    done

    # Defaults for album art
    album_art="${album_art:-${PWD}/cover.jpg}"
    album_art=$(resolvePath "${album_art}")

    # List top file type in current directory
    local top_file=$(ls -I "*.jpg" -I "*.png" -I "converted" -I "*.cue" -I "*.txt" | head -1)
    local filename=$(basename "${top_file}")
    local file_ext="${filename##*.}"

    # Use extension of first file if not provieed
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
    local meta_author="$(basename "${PWD}" | cut -d- -f1 | xargs)"

    # Define extra metadata tags
    local meta_language="eng"
    local meta_title='echo "$i" | sed -rn "s/[[:digit:]]+ - (.*)\.${source_ext}/\1/p" | sed "s/ *//"'
    local meta_artist="${meta_author}, $(test -f "${PWD}"/narrator.txt && cat "${PWD}"/narrator.txt)"
    local meta_album_artist="${meta_author}"
    local meta_album="$(basename "${PWD}" | cut -d- -f2 | sed 's/ *//')"
    local meta_grouping="$(test -f "${PWD}"/grouping.txt && cat "${PWD}"/grouping.txt)"
    local meta_comment="$(test -f "${PWD}"/description.txt && cat "${PWD}"/description.txt)"
    local meta_genre="$(test -f "${PWD}"/genre.txt && cat "${PWD}"/genre.txt)"
    local meta_date="$(test -f "${PWD}"/date.txt && cat "${PWD}"/date.txt)"
    local meta_current_track='echo "${i}" | ggrep -Po "^\d+" | tr -d "(" | sed "s/^0*//" | sed "s/ *//"'
    local meta_total_tracks='ls *.${source_ext} | wc -l | xargs'
    local meta_disc="1/1"
    local meta_composer="$(test -f "${PWD}"/narrator.txt && cat "${PWD}"/narrator.txt)"
    local meta_copyright="©$(test -f "${PWD}"/date.txt && cat "${PWD}"/date.txt | cut -d- -f1) ${meta_author}"

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

    for i in *."${source_ext}"; do \
        set -x
        ffmpeg -i "${i}" -i "${album_art}" \
        -map_metadata -1 \
        $(test -z "${process_chapters}" || echo -i FFMETADATAFILE) \
        -map 0:0 -map 1:0 \
        $(test -z "${process_chapters}" || echo -map_metadata 2) \
        -c:a:0 "${audio_codec}" -c:v:1 libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" \
        -metadata:s:a:0 title="$(eval "${meta_title}")" \
        -metadata:s:v:1 title="Album cover" \
        -metadata title="$(eval "${meta_title}")" \
        $(test -z "${extra_meta}" || echo -metadata track="$(eval "${meta_current_track}")/$(eval "${meta_total_tracks}")") \
        "${ffmpeg_args[@]}" \
        "${convert_dir}/${i%.*}.${target_ext}"; \
        AtomicParsley "${convert_dir}/${i%.*}.${target_ext}" --artwork REMOVE_ALL --artwork "${album_art}" --overWrite; \
        set +x
    done

    unset source_ext target_ext album_art map_chapters extra_meta
}
