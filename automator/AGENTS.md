<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  AGENTS.md: macOS Automator contributor and AI-agent guidance.
  -->

# Automator guidance

Read the root [AGENTS.md](../AGENTS.md). Each `.workflow` directory is a macOS bundle containing property lists, action definitions, and QuickLook preview assets.

Preserve bundle structure, identifiers, action ordering, and embedded scripts. Inspect the relevant `Info.plist` and `document.wflow` before editing; avoid rewriting an entire bundle for a small change or rewriting binary previews unnecessarily.

`make syntax` validates property-list structure without opening applications or executing actions. That check does not prove AppleScript behavior, application permissions, or compatibility with a particular macOS release. Report those limits and perform any authorized runtime review on disposable Notes or Photos content.

Do not run workflows against the user's live documents or photo library during automated checks. New workflow documentation should identify the application, input, permission prerequisites, resulting change, and a safe way to verify it.
