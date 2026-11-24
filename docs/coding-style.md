# Coding style

Scripts shares its relevant coding conventions with Privateerr and Plundarr. Apply those conventions while preserving each utility's platform and existing behavior.

## Whitespace and editor ownership

`.editorconfig` is the portable source of truth: UTF-8, Unix line endings, a final newline, and spaces for indentation. Preserve intentional Markdown hard breaks. Shell, Python, JSON, and JSONC use four spaces; YAML, TOML, AWK, and jq use two. Make recipes use literal tabs.

VS Code settings agree with EditorConfig and disable automatic indentation detection and format-on-save. Ruff owns Python formatting. Prettier is for explicit formatting of supported Markdown and JSON files; it preserves authored prose wrapping and excludes YAML, TOML, jq, and aligned workspace JSONC.

## Script headers

Project-owned scripts and configuration-style files carry copyright, Apache-2.0 license, and filename-summary comments. Preserve earlier author attribution. A shebang has one blank line before the header. Include usage and a brief behavior list when they help explain a tool's contract.

```sh
#!/bin/sh

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# example.sh: Validate a supplied path without modifying its contents.
#
# Usage: example.sh PATH
#
```

Use a Python comment header followed by a useful module docstring. Python files intended to be executed directly need an appropriate shebang and executable mode; importable modules do not need either.

## Shell functions and comments

Every shell function documents its purpose, individual parameters, and return behavior immediately above the declaration. Follow this exact shape:

```sh
#
# function_name: Describe the function's purpose.
#
# Parameters: $1 - Describe the first parameter.
#             $2 - Describe the second parameter.
#
# Returns: Describe the return value or exit behavior.
#
```

Use `Parameters: None.` when there are no positional inputs. Describe required caller variables when an interactive function relies on them. Use one space after `Returns:` and explain meaningful status codes or process termination.

Comments are plain English. Explain intent, constraints, and non-obvious behavior instead of narrating assignments. Put blank lines around logical control-flow blocks. Use a short explanatory comment above a check, loop, or operation only when it adds useful context.

New portable host helpers prefer POSIX `#!/bin/sh`; preserve Bash for established scripts that use arrays, regex matching, or other Bash features. Use POSIX function declarations in `sh` scripts. Quote paths and expansions unless splitting is explicitly intended. Keep diagnostic errors clear, send them to stderr, and preserve the caller's environment when editing sourced libraries.

`.shellcheckrc` shares source resolution between editors and command-line checks. Prefer a correct code fix to a suppression. A targeted suppression must explain the runtime constraint beside the affected code; do not disable a diagnostic repository-wide.

## Python lint, formatting, and types

`ruff.toml` defines Python 3.11 compatibility, line length 100, import ordering, and correctness rules `E4`, `E7`, `E9`, `F`, `I`, `B`, and `UP`. Both Ruff lint and formatting checks apply to project-owned Python, including tests.

Prefer small functions, standard-library facilities, useful module and public-function docstrings, and explicit types at application boundaries. Validate dynamic input, annotate collection and callback contracts, and narrow optional values. Comments explain meaningful fixtures, cleanup, injected failures, and assertion groups without repetitive step labels.

Strict Pyright covers the repository's validation helpers under `scripts/` and tests under `tests/`. Legacy utilities under `python/` receive Ruff and syntax checking; expanding strict scope requires a deliberate migration with appropriate dependencies or narrow typed stubs. Keep the existing strict scope enforced in editors and automation. Do not weaken strict mode or add broad `Any` annotations to hide errors.

Use `make lint` and `make test-types` to check changes. `make format` applies Ruff formatting; inspect its diff before committing. Development tool dependencies remain separate from each utility's runtime requirements.

## YAML, JSON, and automation

Use two-space YAML indentation, including workflows. Keep at least two spaces before inline `#` comments and align comments within logical groups when useful. Comments explain non-obvious security or lifecycle decisions.

Pin GitHub Actions to full commit SHAs with readable version comments. Use minimal permissions and keep pull-request validation free of runtime secrets. Prefer small documented validation helpers over duplicated workflow shell logic. Renovate manages dependency changes; avoid a competing updater for the same dependencies.

Use four spaces in JSON and JSONC. Parse JSONC with a parser that understands comments; do not validate editor settings as strict JSON. Keep examples visibly synthetic and avoid checking real operator configuration into source control.

## Spelling and source review

Run `make spellcheck` across project-owned text. Correct mistakes and put genuine vocabulary in `.vscode/settings.json` under `cSpell.words`. Do not add whole arbitrary strings or credentials to silence warnings.

Run `make check` before handing off a pull request. Inspect the final diff for unintended behavior, dropped attribution, private data, and unrelated changes.
