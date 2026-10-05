# Testing and validation

Repository checks validate source and tooling without operating on your media library, sending messages, or changing macOS authentication. They provide concrete coverage, with runtime verification kept separate.

## Install development tools

Install Git, Python 3.11 or later, Node.js 22.18 or later with npm, Bash, and Make, then run:

```sh
make setup
make hooks
```

The development environment uses pinned Python and Node tooling. Runtime requirements in individual utility directories are independent; CI does not need your webhook, TVDB credentials, FFmpeg installation, or live service configuration to perform static checks.

## Choose a check

| Command | Coverage |
| --- | --- |
| `make help` | Lists available targets |
| `make check` | All-file pre-commit validation followed by isolated validation-helper tests |
| `make test-precommit` | All-file pre-commit hooks, including spelling, formatting, workflow, and secret checks |
| `make syntax` | Parses tracked and new, non-ignored shell, Python, JSON/JSONC, YAML, TOML, and Automator property lists without executing utilities |
| `make lint` | Checks Python lint rules and formatting |
| `make format` | Applies Ruff Python formatting; inspect the resulting diff |
| `make test-types` | Strict Pyright for validation helpers under `scripts/` and tests under `tests/` |
| `make spellcheck` | Checks project text using the workspace vocabulary |
| `make test` | Runs isolated tests for repository validation helpers |

The checked-in pre-commit configuration is the shared hook definition for local commits and CI. Gitleaks scans a disposable snapshot of current tracked and new files permitted by Git ignore rules, so clean CI checkouts receive a full source scan. Local environments and ignored credentials stay outside that snapshot; symbolic links are rejected to protect files outside the checkout. Workflow checks include Actionlint; shell checks include ShellCheck. Python syntax, Ruff lint, and Ruff formatting cover the legacy utilities, while strict typing currently covers new validation tooling and tests.

## Understand the limits

A parsed shell file can still fail because a command is missing, a filename has unexpected characters, permissions differ, or runtime globals are unset. Parsed Automator property lists do not prove that their embedded actions work with a particular macOS release or permission state. Linting and static typing do not prove correctness of rename, conversion, metadata, or API behavior.

The PR workflow runs repository checks on supported runner platforms. Passing it does not configure required status checks or code-owner review in GitHub; those require repository settings. Review the workflow output for the exact checks completed on the current PR commit.

The developer-only Markdown tool currently inherits the upstream [braces denial-of-service advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm). As of October 4, 2026, the advisory lists no patched version; `npm audit` reports five high-severity findings along the same dependency chain. The repository retains the compatible, locked Markdown tool used by Privateerr and Plundarr, uses reviewed lint patterns, and bounds workflow runtime. This dependency is a validation tool and is not installed for the standalone utilities. Review and refresh the lock when an upstream fix becomes available; the current audit is not clean.

## Test behavior safely

For filesystem changes, create a disposable fixture tree with representative files. Include spaces, existing destination names, empty directories, and unrelated files where relevant. Verify the intended change and preservation of data outside the target boundary. Exercise preview and execution separately when a utility implements both modes.

Stub FFmpeg, `ffprobe`, trash commands, and other external processes when the scenario only needs to verify arguments or error handling. Mock TVDB and Discord responses. Never send real messages or use credentials for a formatting check.

Do not source `bash/bash_functions.sh` during validation, run `touchid_for_sudo.sh` against host authentication files, or launch Automator workflows on live Notes or Photos content. Keep any specifically authorized platform review limited to disposable content and state its result separately from static checking.

New validators need focused tests that prove relevant failures are rejected. Do not add tests that merely repeat the implementation or broad runtime suites for a simple documentation edit.

## Prepare verification evidence

Run `make check` and `git diff --check` before opening a PR. State any additional targeted behavior checks, which platforms were exercised, and what remains unverified. Review automatic fixes before committing. A check that was not run should never be reported as passing.
