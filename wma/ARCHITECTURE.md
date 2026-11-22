# Architecture

## Components

- `wma/` holds Django settings, root URL routing, WSGI/ASGI entry points and the health check. `/healthz` returns a basic response; it is not a full dependency check.
- `wmaApp/` contains domain models, server-rendered views, templates, admin, and routes. `api/` serves operational and reporting endpoints; `api_cached/` serves cached customer and product lists.
- `activation/` contains activation code, but is commented out in `INSTALLED_APPS`; check its integration before relying on it.
- `utils/` contains ledger, authentication/group, validation, logging and response helpers. `static/` and `templates/` contain shared assets and templates.
- `start.sh`, `Dockerfile`, `docker-compose.yml` and `scripts/` support local operation and container deployment.

## Data and infrastructure

Models cover owners, staff, locations, customers and ledgers, products and tax, purchases, sales, payments, orders, expenses, jars and allocations. Django uses SQLite or MySQL, selected through environment settings; Redis backs Django's cache. WhiteNoise serves static assets; production media needs separate serving and persistent storage. PDF reporting uses WeasyPrint. PWA configuration and service-worker assets live in settings and `static/sw/`.

See `wma/settings.py`, URL modules and models for current behavior. Migration directories are ignored by `.gitignore`; preserve the complete existing history when moving or deploying an installation.
