#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# check_spelling.py: Check every repository text file with verified scanner coverage.
#

"""Scan all Git-owned text, including embedded scripts and dependency lock contents."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlparse

from scripts.check_syntax import ROOT, repository_files, strip_json_comments


def json_object(value: object, label: str) -> dict[str, object]:
    """Reject malformed configuration or reports instead of assuming scanner success."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")

    return cast(dict[str, object], value)


def load_words(settings_path: Path) -> list[str]:
    """Load the validated editor vocabulary without treating workspace settings as CSpell config."""
    settings: object = json.loads(strip_json_comments(settings_path.read_text(encoding="utf-8")))
    words = json_object(settings, "VS Code settings").get("cSpell.words")

    if not isinstance(words, list):
        raise ValueError("cSpell.words must be a list of strings")

    result: list[str] = []

    for word in cast(list[object], words):
        if not isinstance(word, str):
            raise ValueError("Every cSpell.words entry must be a string")

        result.append(word)

    return result


def classify_files(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """Select text by its bytes rather than an extension or generated-file allowlist."""
    text_files: list[Path] = []
    binary_files: list[Path] = []

    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Refusing to read a symbolic link: {path}")

        content = path.read_bytes()

        try:
            content.decode("utf-8")
            is_binary = b"\0" in content
        except UnicodeDecodeError:
            is_binary = True

        (binary_files if is_binary else text_files).append(path)

    return text_files, binary_files


def validate_coverage(report: dict[str, object], expected: set[Path]) -> None:
    """Reject a successful exit if even one requested text document was silently skipped."""
    result = json_object(report.get("result"), "CSpell result")
    progress = report.get("progress")

    if not isinstance(progress, list):
        raise ValueError("CSpell did not report per-file coverage")

    processed: set[Path] = set()

    for item in cast(list[object], progress):
        record = json_object(item, "CSpell progress")

        if record.get("type") != "ProgressFileComplete":
            continue

        filename = record.get("filename")

        if not isinstance(filename, str) or record.get("processed") is not True:
            raise ValueError("CSpell skipped a requested text file")

        processed.add(Path(filename).resolve())

    if (
        processed != expected
        or result.get("files") != len(expected)
        or result.get("skippedFiles") != 0
        or result.get("errors") != 0
    ):
        raise ValueError("CSpell did not successfully check every requested text file")


def check_text_files(paths: list[Path], words: list[str], root: Path = ROOT) -> int:
    """Force text checks and retain original filenames in diagnostics for temporary aliases."""
    if not paths:
        return 0

    with tempfile.TemporaryDirectory(prefix="scripts-spelling-") as temporary_directory:
        temporary = Path(temporary_directory)
        original_paths: dict[Path, Path] = {}

        for index, path in enumerate(paths):
            check_path = path

            # CSpell categorizes dependency locks as binary even with --force-check.
            # Check identical bytes through a JSON filename without its lock classification.
            if path.name == "package-lock.json":
                check_path = temporary / f"dependency-manifest-{index}.json"
                shutil.copyfile(path, check_path)

            original_paths[check_path.resolve()] = path

        configuration = {
            "version": "0.2",
            "language": "en",
            "words": words,
            "ignoreRegExpList": [
                r"\b[0-9a-f]{40,}\b",
                # Preserve the intentional split-case regular expression in the library.
                # cspell:disable-next-line
                r"(?<=\[Cc\])ommentary",
                r"\\[nrt]",
            ],
            "reporters": [["@cspell/cspell-json-reporter", {"progress": True}]],
        }
        config_path = temporary / "cspell.json"
        config_path.write_text(json.dumps(configuration), encoding="utf-8")
        result = subprocess.run(
            [
                str(ROOT / "node_modules/.bin/cspell"),
                "lint",
                "--config",
                str(config_path),
                "--no-config-search",
                "--no-cache",
                "--no-progress",
                "--no-summary",
                "--force-check",
                "--file",
                *(str(path) for path in original_paths),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        report: object = json.loads(result.stdout)
        report_object = json_object(report, "CSpell report")
        validate_coverage(report_object, set(original_paths))
        issues = report_object.get("issues")

        if not isinstance(issues, list):
            raise ValueError("CSpell did not report spelling issues")

        issue_items = cast(list[object], issues)

        for item in issue_items:
            issue = json_object(item, "CSpell issue")
            uri = issue.get("uri")

            if not isinstance(uri, str):
                raise ValueError("CSpell issue is missing its source filename")

            checked_path = Path(unquote(urlparse(uri).path)).resolve()
            original = original_paths[checked_path]
            print(
                f"{original.relative_to(root)}:{issue.get('row')}:{issue.get('col')}"
                f" - Unknown word ({issue.get('text')})"
            )

        if not issues and result.returncode == 0:
            print(f"CSpell checked all {len(paths)} text files; none were skipped.")

        return result.returncode or int(bool(issue_items))


def main() -> int:
    """Account for every repository file and fail when text coverage is incomplete."""
    try:
        paths = repository_files()
        text_files, binary_files = classify_files(paths)

        for path in binary_files:
            print(f"Binary asset (no UTF-8 text): {path.relative_to(ROOT)}")

        print(
            f"Repository coverage: {len(text_files)} text files, {len(binary_files)} binary assets."
        )
        return check_text_files(text_files, load_words(ROOT / ".vscode/settings.json"))
    except (OSError, ValueError, KeyError) as error:
        print(f"Spell check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
