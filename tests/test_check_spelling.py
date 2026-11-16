#
# Copyright 2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_check_spelling.py: Prove every text format is checked and skipped files fail validation.
#

"""Exercise the real spell checker against formats omitted by extension-based scans."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from scripts.check_spelling import check_text_files, classify_files, load_words, validate_coverage
from scripts.check_syntax import ROOT

# This misspelling is a deliberate negative fixture, never accepted vocabulary.
# cspell:disable-next-line
TYPO = "misspelldfixture"


class SpellingCoverageTests(unittest.TestCase):
    """Use temporary content to exercise coverage and real CSpell failures."""

    def setUp(self) -> None:
        """Create independent test documents without importing any operational utility."""
        self.temporary = tempfile.TemporaryDirectory(prefix="scripts-spelling-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.words = load_words(ROOT / ".vscode/settings.json")

    def write(self, name: str, content: str) -> Path:
        """Create a document with a filename and format chosen by the scenario."""
        path = self.directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def check(self, paths: list[Path]) -> tuple[int, str]:
        """Capture diagnostics without printing the intentionally misspelled fixture."""
        output = StringIO()

        with redirect_stdout(output):
            status = check_text_files(paths, self.words, root=self.directory)

        return status, output.getvalue()

    def test_text_selection_uses_content_for_every_name(self) -> None:
        """Extensionless, hidden, generated, and unfamiliar filenames cannot evade selection."""
        text = [
            self.write("LICENSE", "License terms\n"),
            self.write(".secrets.baseline", '{"version": "example"}\n'),
            self.write("package-lock.json", '{"name": "example"}\n'),
            self.write("requirements-dev.txt", "example\n"),
            self.write("new format with spaces.unknown", "Readable text\n"),
        ]
        binary = self.directory / "binary.data"
        binary.write_bytes(b"\x89PNG\r\n\x1a\n\0")
        selected, binary_assets = classify_files([*text, binary])
        self.assertEqual(selected, text)
        self.assertEqual(binary_assets, [binary])

    def test_supposedly_binary_extension_with_text_is_checked(self) -> None:
        """A filename never determines whether its actual content is readable text."""
        path = self.write("text.png", "Readable text\n")
        text, binary = classify_files([path])
        self.assertEqual(text, [path])
        self.assertEqual(binary, [])

    def test_lock_content_typo_is_detected_and_maps_to_original_path(self) -> None:
        """CSpell's built-in lock exclusion cannot hide misspelled JSON strings."""
        path = self.write("package-lock.json", '{"description": "' + TYPO + '"}\n')
        status, diagnostics = self.check([path])
        self.assertEqual(status, 1)
        self.assertIn("package-lock.json:1:", diagnostics)
        self.assertIn(TYPO, diagnostics)
        self.assertNotIn("dependency-manifest", diagnostics)

    def test_extensionless_and_unfamiliar_sources_are_rejected(self) -> None:
        """License and arbitrary text formats receive real dictionary validation."""
        paths = [
            self.write("LICENSE", TYPO + "\n"),
            self.write("source with spaces.unknown", TYPO + "\n"),
        ]
        status, diagnostics = self.check(paths)
        self.assertEqual(status, 1)
        self.assertIn("LICENSE:1:", diagnostics)
        self.assertIn("source with spaces.unknown:1:", diagnostics)

    def test_embedded_automator_comment_typo_is_detected(self) -> None:
        """XML serialization cannot hide misspelled embedded script commentary."""
        path = self.write(
            "document.wflow",
            '<?xml version="1.0"?><plist><string>-- ' + TYPO + "</string></plist>\n",
        )
        status, diagnostics = self.check([path])
        self.assertEqual(status, 1)
        self.assertIn("document.wflow:1:", diagnostics)

    def test_clean_text_has_complete_coverage(self) -> None:
        """Normal text and locked dependency content are both explicitly accounted for."""
        paths = [
            self.write("LICENSE", "License terms\n"),
            self.write("package-lock.json", '{"description": "Readable text"}\n'),
        ]
        status, diagnostics = self.check(paths)
        self.assertEqual(status, 0)
        self.assertIn("all 2 text files; none were skipped", diagnostics)

    def test_successful_scanner_exit_cannot_hide_a_skipped_file(self) -> None:
        """Reject both explicit skips and incomplete progress regardless of nominal success."""
        path = self.directory / "missing.txt"
        expected = {path.resolve()}
        skipped: dict[str, object] = {
            "result": {"files": 1, "skippedFiles": 1, "errors": 0},
            "progress": [
                {"type": "ProgressFileComplete", "filename": str(path), "processed": False}
            ],
        }
        incomplete: dict[str, object] = {
            "result": {"files": 1, "skippedFiles": 0, "errors": 0},
            "progress": [],
        }

        for report in [skipped, incomplete]:
            with self.assertRaises(ValueError):
                validate_coverage(report, expected)


if __name__ == "__main__":
    unittest.main()
