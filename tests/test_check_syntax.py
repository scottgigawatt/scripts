#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_check_syntax.py: Prove safe parsing and reliable discovery of repository files.
#

"""Exercise syntax failures, path handling, and the checker execution boundary."""

from __future__ import annotations

import json
import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_spelling import load_words
from scripts.check_syntax import check_files, repository_files, strip_json_comments


class SyntaxChecks(unittest.TestCase):
    """Use temporary files only; never import or execute a repository utility."""

    def setUp(self) -> None:
        """Create an isolated directory for parser inputs and execution markers."""
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="scripts-syntax-test-")
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write(self, name: str, content: str) -> Path:
        """Write a test fixture under the temporary directory."""
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_python_is_parsed_without_execution(self) -> None:
        """A valid source file can contain a failing import and a destructive action."""
        marker = self.root / "must not exist"
        path = self.write(
            "Python file with spaces.py",
            f"import nonexistent_test_dependency\nopen({str(marker)!r}, 'w').write('ran')\n",
        )
        self.assertEqual(check_files([path]), [])
        self.assertFalse(marker.exists())

    def test_shell_is_parsed_without_execution(self) -> None:
        """No-execution parsing also protects shell commands and preserves spaced paths."""
        marker = self.root / "must not exist"
        path = self.write("shell file with spaces.sh", f"#!/bin/sh\ntouch '{marker}'\n")
        self.assertEqual(check_files([path]), [])
        self.assertFalse(marker.exists())

    def test_bash_features_use_bash_parser(self) -> None:
        """Existing Bash arrays remain valid instead of being forced through POSIX sh."""
        path = self.write("bash file.sh", "#!/usr/bin/env bash\nvalues=(one two)\n")
        self.assertEqual(check_files([path]), [])

    def test_all_invalid_inputs_are_reported(self) -> None:
        """Parser failures accumulate across shell, Python, YAML, JSON, TOML, and XML."""
        paths = [
            self.write("invalid.sh", "#!/bin/sh\nif true; then\n"),
            self.write("invalid.py", "def broken(:\n"),
            self.write("invalid.yaml", "value: [\n"),
            self.write("invalid.json", '{"value": }'),
            self.write("invalid.toml", "value = [\n"),
            self.write("invalid.plist", "not a plist"),
        ]
        errors = check_files(paths)
        self.assertEqual(len(errors), len(paths))

        for path, error in zip(paths, errors, strict=True):
            self.assertIn(path.name, error)

    def test_valid_configuration_formats(self) -> None:
        """JSONC, YAML, TOML, and binary Automator-compatible plists parse safely."""
        paths = [
            self.write("settings.json", '{// comment\n"url": "https://example.com"}'),
            self.write("valid.yaml", "value: true\n"),
            self.write("valid.toml", 'value = "text"\n'),
        ]
        workflow = self.root / "workflow with spaces.wflow"
        workflow.write_bytes(plistlib.dumps({"actions": []}, fmt=plistlib.FMT_BINARY))
        self.assertEqual(check_files([*paths, workflow]), [])

    def test_json_comments_do_not_change_strings(self) -> None:
        """Escapes, comment-like string content, and multiline comments retain meaning."""
        original = {"url": "https://example.com/*path*/", "quote": 'say "hello"'}
        source = "/*first\nsecond*/\n" + json.dumps(original) + " // last comment"
        self.assertEqual(json.loads(strip_json_comments(source)), original)
        self.assertEqual(strip_json_comments(source).count("\n"), source.count("\n"))

        with self.assertRaisesRegex(ValueError, "Unterminated"):
            strip_json_comments("/* missing end")

    def test_discovery_respects_git_and_spaces(self) -> None:
        """Git discovery checks tracked and new files, skips ignores and deleted paths."""
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        tracked = self.write("tracked source with spaces.py", "value = 1\n")
        deleted = self.write("deleted.py", "value = 1\n")
        self.write(".gitignore", "ignored.py\n")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        deleted.unlink()
        untracked = self.write("new source.py", "value = 2\n")
        ignored = self.write("ignored.py", "def broken(:\n")
        paths = repository_files(self.root)
        self.assertIn(tracked, paths)
        self.assertIn(untracked, paths)
        self.assertNotIn(deleted, paths)
        self.assertNotIn(ignored, paths)

    def test_editor_vocabulary_schema(self) -> None:
        """Spelling uses only validated words and rejects malformed editor values."""
        path = self.write("settings.json", '{"cSpell.words": ["Privateerr", "Plundarr"]}')
        self.assertEqual(load_words(path), ["Privateerr", "Plundarr"])

        invalid_settings: list[object] = [[], {"cSpell.words": "incorrect"}, {"cSpell.words": [4]}]

        for value in invalid_settings:
            path.write_text(json.dumps(value), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_words(path)


if __name__ == "__main__":
    unittest.main()
