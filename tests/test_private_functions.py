#
# Copyright 2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_private_functions.py: Exercise public shell configuration with disposable command stubs.
#

"""Check credential boundaries without sourcing a personal shell or contacting services."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def function_definition(name: str) -> str:
    """Extract one reviewed function without sourcing the operational utility library."""
    source = (ROOT / "bash/bash_functions.sh").read_text(encoding="utf-8")
    match = re.search(rf"^function {re.escape(name)}\(\) ([{{(])\n", source, re.MULTILINE)
    if match is None:
        raise AssertionError(f"Missing function: {name}")
    closing = "}" if match.group(1) == "{" else ")"
    end = source.index(f"\n{closing}\n", match.end()) + len(closing) + 2
    return source[match.start() : end]


class PrivateConfigurationTests(unittest.TestCase):
    """Replace every external command under test with an inert fixture."""

    def run_plex(
        self, configured: bool, invalid: bool = False
    ) -> tuple[subprocess.CompletedProcess[str], list[str], str]:
        """Capture curl arguments and stdin inside a temporary directory."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            curl = directory / "curl"
            curl.write_text(
                '#!/bin/bash\nprintf "%s\\n" "$@" > "$CAPTURE_ARGS"\n'
                'while IFS= read -r line; do printf "%s\\n" "$line"; done > "$CAPTURE_CONFIG"\n',
                encoding="utf-8",
            )
            curl.chmod(0o700)
            arguments = directory / "arguments"
            configuration = directory / "configuration"
            environment = {
                "PATH": str(directory),
                "CAPTURE_ARGS": str(arguments),
                "CAPTURE_CONFIG": str(configuration),
            }
            if configured:
                environment.update(
                    PLEX_URL="https://plex.example.invalid",
                    PLEX_SECTION_ID="1",
                    PLEX_TOKEN='bad"\nconfig' if invalid else "example-token",
                )
            script = (
                'resolvePath() { printf "%s\\n" "$1"; }\n'
                + function_definition("createPlexPlaylist")
                + '\nset -x\ncreatePlexPlaylist "playlist with spaces.m3u"\n'
            )
            result = subprocess.run(
                ["/bin/bash", "-c", script],
                env=environment,
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            return (
                result,
                arguments.read_text().splitlines() if arguments.exists() else [],
                configuration.read_text() if configuration.exists() else "",
            )

    def test_plex_token_only_reaches_curl_stdin(self) -> None:
        """A token never enters argv, the request URL, or an inherited shell trace."""
        result, arguments, configuration = self.run_plex(configured=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('header = "X-Plex-Token: example-token"', configuration)
        self.assertNotIn("example-token", " ".join(arguments) + result.stderr + result.stdout)
        self.assertIn("path=playlist with spaces.m3u", arguments)
        self.assertNotIn("--verbose", arguments)
        self.assertNotIn("-v", arguments)

    def test_plex_missing_configuration_never_invokes_curl(self) -> None:
        """Missing private settings fail before an external request can be attempted."""
        result, arguments, configuration = self.run_plex(configured=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(arguments, [])
        self.assertEqual(configuration, "")

    def test_plex_rejects_config_injection(self) -> None:
        """Unexpected delimiters cannot add directives to curl's stdin configuration."""
        result, arguments, _configuration = self.run_plex(configured=True, invalid=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(arguments, [])
        self.assertNotIn('bad"', result.stderr)

    def test_remote_hosts_come_from_configuration(self) -> None:
        """Only caller-supplied example hostnames reach the inert SSH stub."""
        script = (
            'ssh() { printf "%s\\n" "$@"; }\n'
            + function_definition("ubundo")
            + "\n"
            + 'ubundo --command "printf hello" --user example --all\n'
        )
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            env={"PATH": os.defpath, "SSH_HOSTS": "one.example.invalid two.example.invalid"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("example@one.example.invalid", result.stdout)
        self.assertIn("example@two.example.invalid", result.stdout)
        self.assertEqual(result.stdout.count("printf hello"), 2)

    def test_remote_copy_uses_only_configured_hosts(self) -> None:
        """An inert SCP stub receives only configured hosts and the supplied paths."""
        script = (
            'scp() { printf "%s\\n" "$@"; }\n'
            + function_definition("ubunput")
            + "\n"
            + 'ubunput --local "file with spaces" --remote "/example/path" --user example --all\n'
        )
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            env={"PATH": os.defpath, "SSH_HOSTS": "one.example.invalid two.example.invalid"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("example@one.example.invalid:/example/path", result.stdout)
        self.assertIn("example@two.example.invalid:/example/path", result.stdout)
        self.assertEqual(result.stdout.count("file with spaces"), 2)

    def test_missing_remote_hosts_prevents_contact(self) -> None:
        """Both remote helpers fail before invoking a command without private settings."""
        for name, arguments in [
            ("ubundo", '--command "printf hello" --user example --all'),
            ("ubunput", '--local "file with spaces" --user example --all'),
        ]:
            with self.subTest(function=name):
                script = (
                    'ssh() { printf "unexpected-contact"; }\n'
                    'scp() { printf "unexpected-contact"; }\n'
                    + function_definition(name)
                    + "\n"
                    + name
                    + " "
                    + arguments
                    + "\n"
                )
                result = subprocess.run(
                    ["/bin/bash", "-c", script],
                    env={"PATH": os.defpath},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("unexpected-contact", result.stdout)
                self.assertIn("set SSH_HOSTS", result.stderr)


class OperationalSafetyTests(unittest.TestCase):
    """Exercise failure paths against disposable files and inert external commands."""

    def setUp(self) -> None:
        """Create a private fixture directory for each shell invocation."""
        self.temporary = tempfile.TemporaryDirectory(prefix="scripts-operation-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def run_shell(self, script: str) -> subprocess.CompletedProcess[str]:
        """Execute extracted functions with controlled inputs and no live services."""
        return subprocess.run(
            ["/bin/bash", "-c", script],
            cwd=self.directory,
            env={"PATH": os.defpath},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_failed_metadata_conversion_preserves_original_and_existing_output(self) -> None:
        """Partial converter output never replaces original or preexisting files."""
        original = self.directory / "S01E01.mp4"
        collision = self.directory / "new_S01E01.mp4"
        original.write_text("original media", encoding="utf-8")
        collision.write_text("existing media", encoding="utf-8")
        script = (
            'ffmpeg() { for output; do :; done; printf partial > "$output"; return 27; }\n'
            + function_definition("set_metadata")
            + '\nset_metadata "Example Show" 1\n'
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 27, result.stderr)
        self.assertEqual(original.read_text(), "original media")
        self.assertEqual(collision.read_text(), "existing media")
        self.assertEqual(
            sorted(path.name for path in self.directory.iterdir()), ["S01E01.mp4", "new_S01E01.mp4"]
        )

    def test_successful_metadata_conversion_replaces_only_selected_media(self) -> None:
        """A successful output replaces its source and leaves unrelated files intact."""
        original = self.directory / "S01E01.mp4"
        original.write_text("original media", encoding="utf-8")
        unrelated = self.directory / "notes.txt"
        unrelated.write_text("keep this", encoding="utf-8")
        script = (
            'ffmpeg() { for output; do :; done; printf converted > "$output"; }\n'
            + function_definition("set_metadata")
            + '\nset_metadata "Example Show" 1\n'
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(original.read_text(), "converted")
        self.assertEqual(unrelated.read_text(), "keep this")
        self.assertEqual(len(list(self.directory.iterdir())), 2)

    def test_video_conversion_reports_ffmpeg_failure(self) -> None:
        """The conversion helper cannot hide a failure behind tracing cleanup."""
        script = (
            "ffmpeg() { return 27; }\nffprobe() { :; }\nggrep() { return 1; }\n"
            + function_definition("all2mp4")
            + '\nall2mp4 "fixture.mp4"\n'
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 27, result.stderr)

    def test_failed_batch_conversion_does_not_move_originals(self) -> None:
        """Every in-place batch helper stops before moving a failed source."""
        season = self.directory / "Example Show" / "Season 01"
        season.mkdir(parents=True)
        original = season / "S01E01.mp4"
        original.write_text("original media", encoding="utf-8")
        for name in ["all2mp4_batch", "processTvEpisodes", "renameTvEpisodes"]:
            with self.subTest(function=name):
                script = (
                    "ffmpeg() { :; }\nffprobe() { :; }\n"
                    "all2mp4() { return 27; }\nAtomicParsley() { return 27; }\n"
                    'mp4info() { printf "Name: Example\\n"; }\n'
                    'ggrep() { printf "1\\n"; }\n'
                    "mv() { printf unexpected-move; return 39; }\n"
                    + function_definition(name)
                    + "\n"
                    + name
                    + ' --folder "Example Show" --in-place\n'
                )
                result = self.run_shell(script)
                self.assertEqual(result.returncode, 27, result.stderr)
                self.assertNotIn("unexpected-move", result.stdout)
                self.assertEqual(original.read_text(), "original media")

    def test_failed_join_preserves_existing_intermediate_names(self) -> None:
        """A failed join removes only its own partial files and preserves caller files."""
        for name in ["intermediate1.ts", "intermediate2.ts", "first.mp4", "second.mp4"]:
            (self.directory / name).write_text("existing media", encoding="utf-8")
        script = (
            'ffmpeg() { for output; do :; done; printf partial > "$output"; return 27; }\n'
            + function_definition("join_mp4_files")
            + "\njoin_mp4_files first.mp4 second.mp4 output.mp4\n"
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 27, result.stderr)
        self.assertEqual(len(list(self.directory.iterdir())), 4)
        for path in self.directory.iterdir():
            self.assertEqual(path.read_text(), "existing media")

    def test_failed_episode_conversion_does_not_modify_artwork(self) -> None:
        """A failed episode conversion stops before modifying any existing output."""
        (self.directory / "episode.mp4").write_text("original media", encoding="utf-8")
        script = (
            "ffmpeg() { return 27; }\n"
            "AtomicParsley() { printf unexpected-artwork; }\n"
            + function_definition("setEpisode")
            + "\nsetEpisode\n"
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 27, result.stderr)
        self.assertNotIn("unexpected-artwork", result.stdout)
        self.assertEqual((self.directory / "episode.mp4").read_text(), "original media")

    def test_sync_reports_rsync_failure(self) -> None:
        """A displayed error cannot turn a failed sync into a successful exit."""
        script = (
            'resolvePath() { printf "%s\\n" "$1"; }\n'
            "printCallingFunctionName() { printf folderSync; }\n"
            "colorEcho() { :; }\nbox() { :; }\nfiglet() { :; }\n"
            "sudo() { return 27; }\n"
            + function_definition("folderSync")
            + "\nfolderSync . . <<< yes\n"
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 27, result.stderr)

    def test_key_upload_keeps_port_and_key_data_separate(self) -> None:
        """An SSH port is an argument and shell metacharacters in comments remain data."""
        key = "ssh-ed25519 fixture-key Example's $(printf unexpected) key"
        (self.directory / "key.pub").write_text(key, encoding="utf-8")
        script = (
            'ssh() { printf "<%s>\\n" "$@" >> arguments; '
            'if [[ ${!#} == *"IFS= read"* ]]; then cat >> input; fi; }\n'
            + function_definition("uploadKey")
            + "\nuploadKey --file key.pub --host example@example.invalid --port 2222\n"
        )
        result = self.run_shell(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = (self.directory / "arguments").read_text()
        self.assertIn("<-p>\n<2222>\n<-->\n<example@example.invalid>", arguments)
        self.assertNotIn(key, arguments)
        self.assertEqual((self.directory / "input").read_text(), key + "\n")

    def test_key_upload_rejects_stale_caller_settings_and_setup_failure(self) -> None:
        """Missing arguments and failed remote setup cannot reuse globals or upload data."""
        (self.directory / "key.pub").write_text("fixture key", encoding="utf-8")
        definition = function_definition("uploadKey")
        result = self.run_shell(
            "KEY_FILE=key.pub; REMOTE_HOST=example@example.invalid; REMOTE_PORT=2222\n"
            "ssh() { printf unexpected-contact; }\n"
            + definition
            + "\nuploadKey --host example@example.invalid\n"
        )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("unexpected-contact", result.stdout)
        result = self.run_shell(
            "ssh() { return 27; }\n"
            + definition
            + "\nuploadKey --file key.pub --host example@example.invalid\n"
        )
        self.assertEqual(result.returncode, 27)


if __name__ == "__main__":
    unittest.main()
