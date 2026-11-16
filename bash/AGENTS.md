<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  AGENTS.md: Shell-specific contributor and AI-agent guidance.
  -->

# Shell guidance

Read the root [AGENTS.md](../AGENTS.md) and [coding style](../docs/coding-style.md). Preserve existing Bash interpreters and required features; do not mechanically rewrite arrays or `[[ ... ]]` into POSIX shell.

`bash_functions.sh` is an interactive function library. Its helpers can depend on caller variables, optional commands, and platform-specific behavior. Keep its author attribution and public function names. Do not add global `set -eu` or other shell options that would change the caller's session, and never source this file during automated syntax checks.

`createPlexPlaylist` receives `PLEX_URL`, `PLEX_SECTION_ID`, and `PLEX_TOKEN` from private caller configuration. Keep the token out of URLs, command-line arguments, tracing, and verbose logs; the curl request reads its configuration from stdin. Playlist entries already use server-side paths. `ubundo` and `ubunput` use a private `SSH_HOSTS` list for their `--all` option. Do not restore personal addresses, mount rewrites, or workplace hostnames.

The four movie-directory helpers use the current working directory, implement `--dry-run` and `--run`, and place moved items in `____trash`. Document that local directory accurately. Preserve file contents and unrelated directories in tests; use disposable fixture trees and test spaces or unusual characters when changing traversal.

`touchid_for_sudo.sh` changes macOS authentication files and an iTerm2 preference. Validation must parse it or use controlled command stubs; never invoke it against the host's PAM configuration.

Use four-space indentation, the exact shared function comment block, clear stderr diagnostics, and quoted paths. Explain intentional word splitting or caller-supplied globals beside a narrowly scoped ShellCheck directive. Keep error handling compatible with the declared shell and with whether a file is executed or sourced.
