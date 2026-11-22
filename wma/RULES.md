# Project maintenance rules

- Preserve existing user changes and data. Inspect the working tree before editing; avoid destructive commands without explicit authorization.
- Keep secrets and private data out of documentation, Git and command output. Use `.env.example` for configuration names and placeholders.
- Treat code and configuration as the source of truth. Document verified behavior, identify assumptions, and update relevant documentation when behavior or operational procedures change.
- Preserve migration history and back up existing database and media before schema or deployment changes. Review migrations before applying them.
- Validate changes with checks appropriate to their scope; report what was tested and any limitations.
- Follow existing application patterns and review authentication, authorization, and data isolation when changing endpoints or views.
- Keep `TASKS.md` for actionable work and `MEMORY.md` for durable confirmed context; avoid duplicating detailed instructions across files.
