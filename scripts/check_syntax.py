#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# check_syntax.py: Parse repository sources without importing or running utilities.
#

"""Check tracked source syntax without touching media, services, or system settings."""

from __future__ import annotations

import ast
import json
import plistlib
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def strip_json_comments(source: str) -> str:
    """Remove JSONC comments while preserving strings and diagnostic line numbers."""
    result: list[str] = []
    index = 0
    in_string = False

    while index < len(source):
        character = source[index]

        # Escaped quotes and URL slashes belong to strings, never to comments.
        if in_string:
            result.append(character)

            if character == "\\" and index + 1 < len(source):
                index += 1
                result.append(source[index])
            elif character == '"':
                in_string = False

            index += 1
            continue

        if character == '"':
            in_string = True
        elif source.startswith("//", index):
            end = source.find("\n", index)
            index = len(source) if end == -1 else end
            continue
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)

            if end == -1:
                raise ValueError("Unterminated JSON block comment")

            result.extend("\n" if item == "\n" else " " for item in source[index : end + 2])
            index = end + 2
            continue

        result.append(character)
        index += 1

    return "".join(result)


def repository_files(root: Path = ROOT) -> list[Path]:
    """Collect Git-owned and new paths allowed by Git ignore rules without breaking names with spaces."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    names = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return sorted({root / name for name in names if name and (root / name).is_file()})


def check_file(path: Path) -> None:
    """Parse one recognized file; shell parsing always uses the no-execution flag."""
    suffix = path.suffix.lower()

    if suffix in {".sh", ".bash"}:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        interpreter = "bash" if "bash" in first_line else "sh"
        result = subprocess.run(
            [interpreter, "-n", str(path)], capture_output=True, text=True, check=False
        )

        if result.returncode:
            raise ValueError(result.stderr.strip() or "Shell syntax check failed")

    elif suffix == ".py":
        ast.parse(path.read_bytes(), filename=str(path), feature_version=(3, 11))
    elif suffix in {".json", ".jsonc", ".json5"} or path.name == ".secrets.baseline":
        json.loads(strip_json_comments(path.read_text(encoding="utf-8")))
    elif suffix in {".yaml", ".yml"}:
        # Safe loading validates data and never constructs arbitrary Python objects.
        list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    elif suffix == ".toml":
        tomllib.loads(path.read_text(encoding="utf-8"))
    elif suffix in {".plist", ".wflow"}:
        plistlib.loads(path.read_bytes())


def check_files(paths: Iterable[Path]) -> list[str]:
    """Return all diagnostics so one invalid file does not conceal later failures."""
    errors: list[str] = []

    for path in paths:
        try:
            check_file(path)
        except (
            OSError,
            SyntaxError,
            ValueError,
            yaml.YAMLError,
            plistlib.InvalidFileException,
        ) as error:
            errors.append(f"{path}: {error}")

    return errors


def main() -> int:
    """Validate repository syntax and exit nonzero when any parser rejects a file."""
    paths = repository_files()
    errors = check_files(paths)

    for error in errors:
        print(error, file=sys.stderr)

    if errors:
        return 1

    print(f"Syntax checks passed across {len(paths)} repository files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
