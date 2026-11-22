# Tasks

Keep this list current as work is requested, completed, or explicitly deferred. Do not infer completion from an unchecked item; link relevant issues or decisions when available.

## Open maintenance questions

- [ ] Determine how the complete migration history should be versioned and transferred safely; migration directories are currently ignored.
- [ ] Review deployment settings, secrets, backups, TLS, media serving and Django deployment checks for each target environment.
- [ ] Establish and document expected test coverage and a repeatable verification workflow.
- [ ] Reconcile the restored Docker database's migration records and add the pending indexes before deploying the staff and customer photo upload fix (2026-11-22).

## Completed

- [x] Add a documentation index and baseline project, architecture, design, command and maintenance notes (2026-11-17).
- [x] Align authenticated media delivery with the reference deployment (2026-11-17).
- [x] Restore the Docker deployment's uploaded images and thumbnails from backup and verify authenticated delivery (2026-11-22).
- [x] Save replacement profile photos from the staff and customer edit forms and verify thumbnail generation (2026-11-22).
