# Project memory

This file records durable project context and decisions. Update it when a confirmed decision or constraint changes; do not record credentials, personal data, guesses or transient command output. Use `TASKS.md` for actionable work and the source code as the authority for current behavior.

## Confirmed context (2026-11-17)

- WMA is a Django application for water-management operations, with a container deployment workflow.
- Settings default to SQLite and configure Redis caching. Local and deployment environments may override these settings.
- `activation` exists but is not currently enabled in `INSTALLED_APPS`.
- Migration directories are ignored by Git. Existing database installations depend on preserving their migration history; do not regenerate or discard it casually.
- The repository already contained local deployment notes and a short uv command reference; those were retained in README and COMMANDS.
- Media delivery follows the reference deployment: session or JWT/Bearer authentication, with files stored in the persistent media mount.

## Confirmed context (2026-11-22)

- Docker media restores require extracting the original files and thumbnails into the mount at their database-relative paths. Keep backup archives outside the served directory. See [README.md](README.md#restoring-uploaded-media).
- Staff and customer photo replacements use the existing multipart edit requests and respect the management roles and owner boundaries of their respective pages.
