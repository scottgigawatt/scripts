<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  AGENTS.md: Contributor and AI-agent operating instructions for Scripts.
  -->

# AGENTS.md

## Project purpose and layout

Scripts is a collection of independent shell, Python, and macOS Automator utilities. It is not a single deployed application. Preserve the tool-specific platform, dependency, and command-line contracts.

- `bash/`: Bash functions and filesystem/macOS helpers; read `bash/AGENTS.md` before editing.
- `python/`: Independent media, TVDB, Discord, and document utilities; read `python/AGENTS.md` before editing.
- `automator/`: macOS workflow bundles; read `automator/AGENTS.md` before editing.
- `notifiarr/`: A historical configuration example; preserve its example-only credential boundary.
- `scripts/`: Repository validation helpers.
- `tests/`: Isolated tests for repository tooling.
- `docs/`: Contributor, security, and support policies plus coding, documentation, and testing guidance; start with `docs/index.md`.
- `.github/`: Validation/security workflows, templates, dependency policy, and CODEOWNERS.

## Work boundaries

Inspect the current branch, status, relevant code, and applicable guidance before editing. Preserve unrelated local changes and existing author attribution. Work from current `main` in a feature branch using the `wee/` prefix. Avoid broad rewrites when a focused fix is sufficient.

Do not execute production utilities against real media, documents, system authentication files, or external services during validation. Never source `bash/bash_functions.sh` just to check syntax. Use parsing, disposable fixture directories, stub commands, and mocked requests instead. Do not assume `--help` or a debug option prevents side effects.

Do not print or commit credentials, webhook URLs, API keys, operator paths, private logs, or personal runtime configuration. Secret-scan findings need correction or a narrow, reviewed example exception; never broaden allowlists or regenerate a baseline to hide a real finding.

## Shared coding style

Keep relevant conventions aligned with Privateerr and Plundarr while preserving Scripts' architecture. [Coding style](docs/coding-style.md) defines exact script headers and shell function comment blocks.

- Four spaces in shell, Python, JSON, and JSONC; two spaces in YAML, TOML, AWK, and jq.
- `.editorconfig` owns portable whitespace rules; VS Code settings must agree. Keep format-on-save disabled.
- Plain-English comments explain intent, constraints, and non-obvious behavior. Separate logical blocks with blank lines.
- New portable host helpers prefer `#!/bin/sh`; existing Bash tools retain Bash features and declared interpreters.
- Shebangs have one blank line before the copyright, Apache-2.0, filename-summary, and usage header.
- Every shell function documents purpose, individual parameters, and return behavior immediately above its declaration. Use `Parameters: None.` when appropriate.
- Python modules have a license/filename header and useful module docstring. Prefer small helpers, explicit boundary types, and standard-library facilities where practical.
- `ruff.toml` owns Python correctness, import order, modernization, and formatting rules. Run both lint and formatting checks.
- `pyrightconfig.json` owns strict checks for validation helpers and tests. Keep its current scope explicit: legacy utility scripts receive Ruff and syntax checks while a dedicated typed migration remains separate. Do not weaken strict mode, add blanket `Any`, or exclude a failing new helper to silence findings.
- `.shellcheckrc` owns source resolution. Any targeted ShellCheck suppression needs a nearby reason tied to an intentional constraint.
- Add genuine project vocabulary to `.vscode/settings.json` under `cSpell.words`; fix misspellings and never add secret values.

Keep utility runtime dependencies separate from repository development tooling. Update the selected utility's requirements when its imports change. Do not introduce a Docker runtime just to imitate a sibling's containerized validation.

## Documentation and public voice

Follow [documentation style](docs/documentation-style.md). Keep public writing useful with light interdimensional humor in short introductions or transitions. Commands, paths, warnings, security advice, diagnostics, and destructive actions remain literal. Code comments are plain English.

Use searchable sentence-case headings with decorative emoji afterward. Ordinary prose paragraphs occupy one physical source line. Copyable commands use `sh` fences without prompts or comments; reserve `bash` for Bash-specific syntax and `console` for transcripts. Use relative repository links and lowercase kebab-case ordinary article filenames.

## Automation and validation

Use two-space workflow YAML indentation, descriptive step names, and full commit-SHA action pins. Preserve least-privilege permissions, fork-safe checks, and concurrency cancellation. Keep PR validation free of production secrets and side effects. Renovate owns dependency updates; do not add competing Dependabot automation.

Start with the smallest applicable checks during development and complete `make check` before the final handoff. Available targets include `make help`, `make setup`, `make hooks`, `make syntax`, `make lint`, `make format`, `make test-types`, `make spellcheck`, `make test-precommit`, and `make test`. Run `git diff --check` and inspect all changed files. Report checks actually performed and any unverified platform or runtime behavior.

New or changed validators need focused tests that catch meaningful failures; avoid tests that merely mirror implementation. Filesystem behavior tests must use disposable paths and verify preservation of unrelated files.

## Branches, commits, and pull requests

Use `wee/` feature branches. Commit messages start with an emoji and may be funny while still describing the change. PR descriptions lead with the concrete problem and resulting behavior, then summarize changes and actual validation. Assign `scottgigawatt` and apply suitable existing labels when opening a requested PR.

Leave pull requests open for owner review. Do not merge, publish external messages, change repository protection settings, or delete unrelated branches without explicit authorization. CODEOWNERS requests ownership; required reviews and status checks depend on repository settings and are not configured by that file alone.
