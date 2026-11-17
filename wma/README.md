# Water Management Application (WMA)

A Django application for managing water delivery operations, including customers, inventory, sales, payments, expenses, jars, bookings and reports.

## Getting started

Python 3.12 or newer and [uv](https://docs.astral.sh/uv/) are required. Copy `.env.example` to `.env` and adjust the settings for your environment. Install dependencies with `uv sync`, then use `./start.sh --db sqlite --check --no-run` to check the configuration. Run migrations only after confirming that the complete migration history is available (see below); start the development server with `./start.sh`. Redis is configured for caching and must be available for cache-backed features.

See [COMMANDS.md](COMMANDS.md) for commands, [ARCHITECTURE.md](ARCHITECTURE.md) for the code map, [DESIGN.md](DESIGN.md) for interface conventions, [TASKS.md](TASKS.md) for open work, [MEMORY.md](MEMORY.md) for project context, and [RULES.md](RULES.md) and [AGENTS.md](AGENTS.md) for maintenance guidance.

/etc/systemd/system/schoolstack.service

systemctl daemon-reload

sudo systemctl restart schoolstack.service

sudo systemctl restart wmapp.service
## Docker deployment

Install Docker with Compose v2.24+ and uv. Copy `.env.example` to a private environment file, set a unique `SECRET_KEY` and `ALLOWED_HOSTS`, and choose a Docker-shared absolute `VPS_STORAGE_ROOT`. For MySQL set `DB_ENGINE=mysql`, `DB_NAME=wma`, a non-root `DB_USER`, `DB_PASSWORD`, and `MYSQL_ROOT_PASSWORD`. Existing MySQL data retains its original credentials. SQLite uses a persistent `/data/db.sqlite3`; an existing local database is not copied automatically. Redis runs privately in the stack.

```sh
./start.sh --env .env --db sqlite --docker-up
./start.sh --env .env --docker-logs
./start.sh --env .env --docker-down
./start.sh --env .env --docker-build
./start.sh --help
```

The release command builds an immutable image, initializes storage, checks migrations, stops the web service, applies migrations, and waits for a healthy replacement. Data is stored under `<VPS_STORAGE_ROOT>/<PROJECT_NAME>/<DEPLOY_ENV>`. Review and preserve the complete `wmaApp/migrations` history when moving between machines; it is currently ignored by Git. Django streams uploaded media from the persistent media directory for authenticated browser sessions and JWT or Bearer tokens in both development and production. Raster images display inline; other files download. Media responses are private and are not cached. Gunicorn streams each file, so heavy media traffic can use its workers. Configure a reverse proxy for TLS. The default host binding is loopback. Back up the database and media before upgrading an existing installation.
