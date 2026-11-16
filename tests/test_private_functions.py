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


if __name__ == "__main__":
    unittest.main()
