#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# check_secrets.py: Scan current Git-owned content even when the index has no changes.
#

"""Give the pinned secret scanner a disposable snapshot of the current source files."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.check_syntax import ROOT, repository_files


def snapshot_files(root: Path, destination: Path) -> None:
    """Copy Git-owned and new files while excluding ignores and rejecting symbolic links."""
    for source in repository_files(root):
        relative_path = source.relative_to(root)

        # A link could expose a private file outside the repository boundary.
        if source.is_symlink():
            raise ValueError(f"Refusing to scan a symbolic link: {relative_path}")

        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def scan_repository(root: Path = ROOT, scanner: str = "gitleaks") -> int:
    """Scan source content with the pinned hook binary; redact every reported finding."""
    with tempfile.TemporaryDirectory(prefix="scripts-secret-scan-") as temporary_directory:
        snapshot = Path(temporary_directory)
        snapshot_files(root, snapshot)
        result = subprocess.run(
            [
                scanner,
                "dir",
                "--config",
                str(root / ".gitleaks.toml"),
                "--redact",
                "--no-banner",
                str(snapshot),
            ],
            cwd=root,
            check=False,
        )

    return result.returncode


def main() -> int:
    """Reject snapshot or scanner failures without printing source-file contents."""
    try:
        return scan_repository()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Secret scan failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
