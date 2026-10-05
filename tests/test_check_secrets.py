#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_check_secrets.py: Verify clean-index scanning and private-file boundaries.
#

"""Use temporary Git repositories and an inert scanner to test snapshot coverage."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_secrets import scan_repository, snapshot_files


class SecretSnapshotTests(unittest.TestCase):
    """Assert source selection without reading or recording real credentials."""

    def setUp(self) -> None:
        """Build an isolated Git repository without creating a commit or real secret."""
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="scripts-secret-test-")
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.root = self.directory / "repository with spaces"
        self.root.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        (self.root / ".gitleaks.toml").write_text("[extend]\nuseDefault = true\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(".env\nnode_modules/\n", encoding="utf-8")

    def test_snapshot_reads_current_content_and_respects_ignores(self) -> None:
        """Scan changed and untracked files while retaining spaced filenames and hiding locals."""
        source = self.root / "source with spaces.py"
        source.write_text("original content\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        source.write_text("current content\n", encoding="utf-8")
        (self.root / "new.py").write_text("new content\n", encoding="utf-8")
        (self.root / ".env").write_text("private ignored fixture\n", encoding="utf-8")
        dependency = self.root / "node_modules" / "package.js"
        dependency.parent.mkdir()
        dependency.write_text("ignored dependency\n", encoding="utf-8")
        snapshot = self.directory / "snapshot"
        snapshot.mkdir()
        snapshot_files(self.root, snapshot)
        self.assertEqual((snapshot / source.name).read_text(), "current content\n")
        self.assertTrue((snapshot / "new.py").exists())
        self.assertFalse((snapshot / ".env").exists())
        self.assertFalse((snapshot / "node_modules").exists())

    def test_scanner_gets_source_when_there_is_no_staged_diff(self) -> None:
        """An empty index cannot turn an all-file secret scan into a false pass."""
        source = self.root / "current source.txt"
        source.write_text("fixture marker\n", encoding="utf-8")
        scanner = self.directory / "fake scanner"
        scanner.write_text(
            "#!/bin/sh\n"
            'for argument do snapshot="$argument"; done\n'
            '[ "$1" = dir ] || exit 7\n'
            '[ "$4" = --redact ] || exit 8\n'
            'grep -q "fixture marker" "$snapshot/current source.txt" || exit 9\n'
            "exit 0\n",
            encoding="utf-8",
        )
        scanner.chmod(0o700)
        self.assertEqual(scan_repository(self.root, scanner=str(scanner)), 0)

    def test_symbolic_links_cannot_expose_external_files(self) -> None:
        """Refuse a tracked-looking link before a private external file can be copied."""
        external = self.directory / "private.txt"
        external.write_text("private external fixture\n", encoding="utf-8")
        (self.root / "source.txt").symlink_to(external)
        snapshot = self.directory / "snapshot"
        snapshot.mkdir()

        with self.assertRaisesRegex(ValueError, "symbolic link"):
            snapshot_files(self.root, snapshot)

        self.assertFalse((snapshot / "source.txt").exists())


if __name__ == "__main__":
    unittest.main()
