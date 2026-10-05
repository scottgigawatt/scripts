#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# check_spelling.py: Reuse the editor vocabulary for repository spelling checks.
#

"""Run the locked CSpell tool with vocabulary shared by VS Code and automation."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import cast

from scripts.check_syntax import ROOT, repository_files, strip_json_comments

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".sh",
    ".bash",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".json5",
    ".txt",
    ".conf",
}
EXCLUDED_NAMES = {"package-lock.json", ".secrets.baseline", "requirements-dev.txt"}


def load_words(settings_path: Path) -> list[str]:
    """Validate and load only the editor's word list, rather than its full settings."""
    settings: object = json.loads(strip_json_comments(settings_path.read_text(encoding="utf-8")))

    if not isinstance(settings, dict):
        raise ValueError("VS Code settings must be a JSON object")

    words: object = cast(dict[str, object], settings).get("cSpell.words")

    if not isinstance(words, list):
        raise ValueError("cSpell.words must be a list of strings")

    result: list[str] = []

    for word in cast(list[object], words):
        if not isinstance(word, str):
            raise ValueError("Every cSpell.words entry must be a string")

        result.append(word)

    return result


def main() -> int:
    """Check authored text while excluding generated locks, hashes, and binary files."""
    paths = [
        str(path.relative_to(ROOT))
        for path in repository_files()
        if path.name not in EXCLUDED_NAMES
        and (
            path.suffix in TEXT_SUFFIXES
            or path.name
            in {
                "Makefile",
                "CODEOWNERS",
                ".editorconfig",
                ".gitignore",
                ".prettierignore",
                ".shellcheckrc",
            }
        )
    ]
    configuration = {
        "version": "0.2",
        "language": "en",
        "words": load_words(ROOT / ".vscode/settings.json"),
        "ignoreRegExpList": [
            r"\b[0-9a-f]{40,}\b",
            # The split-case regular expression in the legacy library is intentional.
            # cspell:disable-next-line
            r"(?<=\[Cc\])ommentary",
            r"\\[nrt]",  # String escape characters must not become word prefixes.
        ],
    }

    # A temporary config keeps CSpell from interpreting editor settings as its own schema.
    with tempfile.TemporaryDirectory(prefix="scripts-spelling-") as temporary_directory:
        config_path = Path(temporary_directory) / "cspell.json"
        config_path.write_text(json.dumps(configuration), encoding="utf-8")
        result = subprocess.run(
            [
                str(ROOT / "node_modules/.bin/cspell"),
                "--config",
                str(config_path),
                "--no-progress",
                "--no-summary",
                *paths,
            ],
            cwd=ROOT,
            check=False,
        )

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
