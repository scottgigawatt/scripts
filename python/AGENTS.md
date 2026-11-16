<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  AGENTS.md: Python utility contributor and AI-agent guidance.
  -->

# Python utility guidance

Read the root [AGENTS.md](../AGENTS.md) and [coding style](../docs/coding-style.md). Utilities in this directory are independent programs, not one package. Preserve each CLI and document its own runtime dependencies. Python 3.11 is the shared source baseline.

All Python utilities are checked by Ruff lint, Ruff formatting, and syntax parsing. Root strict Pyright currently covers validation helpers and tests outside this directory. Do not describe these legacy utilities as strictly typed until a focused migration adds them to the checker and resolves their dependency contracts.

Prefer typed boundaries and small helpers when changing behavior. Validate external JSON/YAML before use, narrow optional values explicitly, use list arguments for subprocess calls where possible, and add timeouts to new network calls. Avoid shell interpolation of filenames and never log credential-bearing requests.

Media tools may rename, move, trash, or replace input files. Paperless scanning copies documents. TVDB metadata and Discord utilities contact external services. Test these behaviors with temporary directories, controlled subprocesses, and mocked responses; importing a module or enabling debug output is not automatically safe.

Keep license/filename headers and module docstrings, plain-English comments, and the root Ruff settings. Third-party imports belong in the selected utility's `requirements.txt`; development-only validators belong in the repository's development dependency files.
