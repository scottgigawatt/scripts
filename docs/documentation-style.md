# Documentation style ✍️

Help readers complete a task without decoding the theme first. Scripts may have a little interdimensional personality; operational instructions stay plain.

## Start with the reader

Identify the audience and one or two outcomes before writing. Put prerequisites before procedures, order steps as readers perform them, and place optional detail after the main path.

Use a quickstart for the shortest safe route, a how-to for an outcome with verification, a reference for lookup facts, and troubleshooting guidance for a symptom with a verifiable recovery path. Explain platform and dependency boundaries where they affect the task.

## Write plainly first

Use active voice and address the reader as you in procedures. Lead with the conclusion or action, use exact command and UI names, and put one main idea in each sentence or paragraph. Keep ordinary prose paragraphs on one physical source line and use visual editor wrapping.

Humor belongs in short introductions, transitions, or sign-offs. Commands, paths, diagnostics, security instructions, warnings, and destructive actions remain literal. A joke must never carry the operational meaning.

## Make headings searchable

Use sentence-case headings with useful keywords first. Emoji may follow as decoration but never replace a warning or word. Do not skip heading levels, and introduce a section before adding a subsection.

## Format for the task

- Use numbered lists for procedures and bullets for unordered choices.
- Use tables when readers need to compare multiple attributes.
- Use `sh` fences for copyable commands without prompts or explanatory comments; use `bash` only when the syntax requires it.
- Use `console` for terminal transcripts and `text` for non-executable output.
- Use uppercase kebab-case placeholders such as `YOUR-MOVIE.mp4` and explain their replacements outside the command block.
- Use descriptive link text, relative repository links, and specific upstream documentation pages.
- State the working directory when a utility acts relative to it.
- Describe a real dry-run option only when the utility implements it; document writes and deletion separately from debug output.

## Reserve alerts for critical information

GitHub alerts are for information readers must notice while scanning. Most pages need no more than one or two. Use `[!NOTE]` for context, `[!TIP]` for a useful shortcut, `[!IMPORTANT]` for required information, `[!WARNING]` for immediate attention, and `[!CAUTION]` for destructive outcomes or other risks.

Do not wrap routine commands in alerts or place alerts back to back. Put the required action or risk in the alert itself.

## Keep structure useful

Use `<details>` only for optional examples or long diagnostics. Never hide prerequisites, primary steps, or risks. Keep task lists in issue and PR templates; use numbered steps for static procedures. Diagrams need adjacent prose explaining the same relationship.

Preserve established names such as `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md`. Use lowercase kebab-case for ordinary guides. Update links and referenced paths together when moving a document.

## Review the result

Check commands, paths, requirements, and examples against current source. Review rendered GitHub Markdown, including tables, alerts, and narrow-screen readability. Run `make check` and `git diff --check`. Confirm that no private configuration, credential, log, or deployment-specific value entered the text.
