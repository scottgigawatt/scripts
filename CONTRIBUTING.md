# Contributing to Scripts 🛠️

Keep changes focused, verifiable, and kind to the files they touch. The multiverse has enough accidental rewrites.

## Before you start

Read the [README](README.md), [coding style](docs/coding-style.md), [documentation style](docs/documentation-style.md), and [security policy](SECURITY.md). Check existing issues and discuss large behavior changes before restructuring unrelated utilities.

The repository contains independent tools for different platforms. Preserve existing command-line interfaces, directory layouts, author attribution, and supported shell interpreters unless the change explicitly updates them.

## Set up your checkout

Install Git, Python 3.11 or later, Node.js 22.18 or later with npm, Bash, and Make. Clone the repository and install its development tooling:

```sh
git clone https://github.com/scottgigawatt/scripts.git
cd scripts
make setup
make hooks
make help
```

`make setup` creates the development virtual environment and installs pinned Node tools. `make hooks` installs the pre-commit hook. Install a utility's own runtime requirements separately when working on its behavior; validation does not need real credentials or media libraries.

## Follow the shared conventions

Use four spaces in shell, Python, JSON, and JSON with Comments; use two spaces in YAML, TOML, AWK, and jq. `.editorconfig` is the portable source of truth, and VS Code settings agree with it.

Install the recommendations in `.vscode/extensions.json` if you use VS Code. Workspace format-on-save is disabled. Ruff owns Python formatting; Prettier is available for explicit formatting of supported Markdown and JSON files. YAML, TOML, jq, and aligned workspace JSONC are excluded from Prettier.

Code comments are plain English and explain intent or constraints. Shell functions document their purpose, parameters, and return behavior using the exact shape in [coding style](docs/coding-style.md). Documentation keeps the repository's light interdimensional voice while leaving commands, diagnostics, risks, and security instructions literal.

## Validate your change

```sh
make check
```

For targeted checks, use `make syntax`, `make lint`, `make test-types`, `make spellcheck`, or `make test`. Use `make format` to apply Python formatting deliberately, then inspect the diff and rerun the applicable checks. [Testing guidance](docs/testing.md) explains what each target covers.

All project-owned Python receives Ruff lint and formatting checks. Strict Pyright currently covers validation helpers under `scripts/` and tests under `tests/`; legacy utilities under `python/` remain outside the strict type-checking scope. New validation helpers must stay strictly typed. Extending strict checking to legacy utilities requires a focused migration with suitable dependency stubs and behavior tests.

Never run a media, authentication, or webhook utility merely to verify formatting. Test behavior with disposable files, stubbed external commands, and mocked network calls. State any remaining runtime or platform limitations in the pull request.

## Prepare a pull request

1. Start from current `main` and create a focused feature branch with the `wee/` prefix.
2. Make the requested change and update its usage, dependencies, and documentation together.
3. Run `make check` and inspect `git diff --check`.
4. Check that no credentials, private configuration, logs, or unrelated files entered the diff.
5. Write a concise commit message that describes the change; an opening emoji and a little humor are welcome.
6. Open a pull request with a concrete explanation and validation evidence. Assign `scottgigawatt` and add relevant labels.

Pinned GitHub Action commits and development tool versions change through reviewed dependency updates. Renovate manages those updates; do not add a competing updater for the same dependencies.

Leave the pull request open for maintainer review. A green workflow confirms its reported checks, while merging and repository branch-protection settings remain maintainer decisions.

## Report sensitive problems

Use [private vulnerability reporting](SECURITY.md) for credential leaks or security problems. Public issues and the [support community](SUPPORT.md) are for non-sensitive collaboration.
