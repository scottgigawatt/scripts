# Custom scripts 🛠️

Small shell, Python, and macOS Automator tools for media libraries, document imports, and system conveniences. A little interdimensional chaos belongs in the jokes; your files deserve predictable behavior.

[![License](https://img.shields.io/github/license/scottgigawatt/scripts)](LICENSE) [![Validation](https://github.com/scottgigawatt/scripts/actions/workflows/validate-pr.yml/badge.svg)](https://github.com/scottgigawatt/scripts/actions/workflows/validate-pr.yml) [![Discord](https://img.shields.io/discord/1403601106315116626?label=HADES&logo=discord&logoColor=white&color=5865F2)](https://discord.gg/BpEGzWwGYf)

## Choose a tool

This is a collection of independent utilities, not one application. Read the selected file's usage and dependencies before running it.

| Location | Purpose | Runtime considerations |
| --- | --- | --- |
| [`bash/`](bash/) | Clean, flatten, and rename movie folders; move empty folders to a local trash directory | Bash and filesystem utilities; four folder helpers support `--dry-run` and `--run` |
| [`bash/bash_functions.sh`](bash/bash_functions.sh) | Functions intended for an interactive Bash configuration | Source only after reviewing the selected functions and their external commands |
| [`bash/touchid_for_sudo.sh`](bash/touchid_for_sudo.sh) | Configure macOS sudo Touch ID and an iTerm2 preference | Changes system authentication files; requires suitable administrator permissions |
| [`python/movie-checking/`](python/movie-checking/) | Inspect MP4 streams for AV1 and missing audio | Python and `ffprobe` |
| [`python/movie-rename/`](python/movie-rename/) | Rename movie files, process media, and match subtitles | Some utilities require FFmpeg or the directory's Python dependencies |
| [`python/tv-show-rename/`](python/tv-show-rename/) | Rename episodes using text-file mappings | Python; renames and moves files |
| [`python/tv-show-subtitles/`](python/tv-show-subtitles/) | Merge subtitle files into TV or movie media | Python and FFmpeg; writes media files |
| [`python/tv-show-metadata/`](python/tv-show-metadata/) | Fetch TVDB metadata and update media | Directory-specific Python dependencies, FFmpeg, network access, and your TVDB API key |
| [`python/paperless-ngx/`](python/paperless-ngx/) | Scan source directories, deduplicate by hash, and copy documents | Directory-specific Python dependencies; supports `--dry-run` |
| [`python/discord/`](python/discord/) | Send a configured Discord webhook message | Directory-specific Python dependencies and a private YAML configuration |
| [`automator/`](automator/) | Add a horizontal line in Notes or change a photo title | macOS Automator and application permissions |
| [`notifiarr/notifiarr.conf`](notifiarr/notifiarr.conf) | Historical Notifiarr configuration example | Review against your installed Notifiarr version; keep live credentials outside this repository |

> [!CAUTION]
> Several utilities rename, move, trash, or replace files. Back up important data and first test on a disposable copy. `____trash` is a directory created by the shell helpers, not the operating system's Trash. A dry run is available only where the selected tool implements it.

## Run an individual utility

Use Python 3.11 or later. Utilities with a `requirements.txt` need those packages installed in a virtual environment; standalone utilities may use only Python's standard library. FFmpeg, `ffprobe`, and other command-line dependencies are separate installations. Bash tools retain their declared interpreter, and macOS-specific tools require macOS.

For example, this command inspects one MP4 file without changing it. Replace `YOUR-MOVIE.mp4` with your file path and ensure `ffprobe` is available:

```sh
python3 python/movie-checking/check_av1_codec.py --file YOUR-MOVIE.mp4
```

The folder cleanup helpers operate relative to the current working directory. Run their preview from a disposable copy of the media directory, using the actual path to the helper. Review the printed changes before selecting `--run`.

`createPlexPlaylist` requires privately supplied `PLEX_URL`, `PLEX_SECTION_ID`, and `PLEX_TOKEN`; playlist entries must already use server-side paths. The `ubundo` and `ubunput` functions use a private, space-separated `SSH_HOSTS` list with their `--all` option. Keep this environment configuration outside the repository.

Keep webhook configurations, API keys, private paths, and logs outside commits. A configuration filename is not proof that it is ignored; check with `git check-ignore` before storing sensitive values in a checkout.

## Develop and validate

Install Git, Python 3.11 or later, Node.js 22.18 or later with npm, Bash, and Make. Development tools are pinned separately from utility runtime dependencies.

```sh
make setup
make hooks
make check
```

`make check` runs the same all-file pre-commit checks used for pull requests, followed by the validation-helper tests. Syntax checks parse scripts and Automator files without executing their actions. Strict Python checking currently covers repository validation helpers and tests; legacy utilities receive Ruff lint, formatting, and syntax checks.

Browse the [documentation index](docs/index.md) for all guides and policies. Use [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for setup and pull-request guidance, [`docs/coding-style.md`](docs/coding-style.md) for shared shell/Python conventions, and [`docs/testing.md`](docs/testing.md) for check coverage and safe behavior testing. AI coding tools should start with [`AGENTS.md`](AGENTS.md).

## Get help and report problems

Use the [issue templates](https://github.com/scottgigawatt/scripts/issues/new/choose) for reproducible bugs, features, or documentation fixes. See [`docs/SUPPORT.md`](docs/SUPPORT.md) for useful evidence and the [HADES community](https://discord.gg/BpEGzWwGYf) for non-sensitive questions. Report vulnerabilities privately using [`docs/SECURITY.md`](docs/SECURITY.md).

## License

Project-owned work is licensed under [Apache-2.0](LICENSE). Preserve author attribution and any third-party notices. No portal gun warranty included.
