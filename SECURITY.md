# Security policy 🛡️

Keep reports private when the details could expose credentials or help someone attack a user's system.

## Supported source

Security fixes target the current `main` branch. Older checkouts and independently modified copies are not maintained separately. The historical Notifiarr configuration is an example, not a maintained Notifiarr distribution; report upstream application vulnerabilities to the relevant project too.

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/scottgigawatt/scripts/security/advisories/new). Include the affected script and commit, platform, reproduction steps, impact, and sanitized evidence.

Do not disclose vulnerability details in public issues, pull requests, or Discord. If private reporting is unavailable, open an issue asking for a private reporting channel without describing the vulnerability publicly. There is no guaranteed response deadline; this repository is maintained by an individual.

## Protect private data

Never publish webhook URLs, API keys, account tokens, private configuration, personal paths, or unredacted logs. Store live credentials outside tracked examples. Review secret-scanner findings before changing an allowlist or baseline, and keep any intentional example exception narrow.

If a real credential has been exposed, revoke or rotate it with the service provider; deleting it from the latest file does not remove it from history or copies.

## Understand validation boundaries

Pre-commit and pull-request checks scan source for secrets, validate syntax, and run language-specific checks. Pinned GitHub Actions and development tool versions reduce unexpected dependency changes, with updates handled through reviewed PRs.

These checks do not sandbox a utility when you run it. Media helpers can alter files, the Touch ID helper changes authentication configuration, Automator actions operate through macOS applications, and API utilities can contact external services. Review the selected tool and use disposable data before running it against important content.

See [SUPPORT.md](SUPPORT.md) for non-sensitive bugs and setup questions.
