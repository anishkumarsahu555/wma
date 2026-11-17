# Commands

Run from the repository root. Review `./start.sh --help` for all options and the selected environment before running operations that modify data.

```sh
uv sync                              # Install locked dependencies
./start.sh --db sqlite --check --no-run  # Django system check
./start.sh --db sqlite --test --no-run   # Run tests
./start.sh                           # Local development server
./start.sh --dry-run --prod          # Preview production launch
./start.sh --env .env --db sqlite --docker-up  # Build, migrate and start Docker stack
./start.sh --env .env --docker-logs
./start.sh --env .env --docker-down  # Stop services; preserve host storage
```

`./start.sh --migrate --no-run` changes the database; verify migration history and back up existing data first. `./start.sh --reset-db` flushes data. `./start.sh --collectstatic --no-run` writes to `STATIC_ROOT`.

## Existing uv notes

1. install uv
pip install uv
2. initialise uv
   uv init --python 3.12
3. sync uv
   uv sync
4. add packages
   uv add weasyprint