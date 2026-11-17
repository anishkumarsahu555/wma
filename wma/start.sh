#!/usr/bin/env bash
# ==============================================================================
# Water Management Server Startup Script (`start.sh`)
# Manages environment preparation, checks, migrations, and server execution.
# ==============================================================================

set -euo pipefail

# Resolve the checkout independently of the caller's working directory.
CALLER_DIR="$PWD"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Text formatting
BOLD="$(printf '\033[1m')"
GREEN="$(printf '\033[0;32m')"
YELLOW="$(printf '\033[1;33m')"
BLUE="$(printf '\033[0;34m')"
RED="$(printf '\033[0;31m')"
RESET="$(printf '\033[0m')"

log_info()    { echo -e "${BLUE}[INFO]${RESET} $*"; }
log_success() { echo -e "${GREEN}[OK]${RESET} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${RESET} $*"; }
log_error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }

# Default Configuration Values
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="8000"
HOST="$DEFAULT_HOST"
SERVER_PORT="$DEFAULT_PORT"
PORT_EXPLICIT=false
HOST_EXPLICIT=false
WORKERS=1
TIMEOUT=120
ENV_FILE="${ENV_FILE:-}"
DO_SYNC=false
DO_CHECK=false
DO_CHECK_DEPLOY=false
DO_MIGRATE=false
DO_CHECK_MIGRATIONS=false
DO_TEST=false
DO_COLLECTSTATIC=false
DO_SUPERUSER=false
DO_PROD=false
DO_DRY_RUN=false
DO_SHELL=false
DO_RESET_DB=false
DO_DOCKER=""
DOCKER_DB=""
NO_RUN=false
NORELOAD=false

show_help() {
    cat << EOF
${BOLD}Water Management — Server Launcher${RESET}
${BOLD}Usage:${RESET} ./start.sh [OPTIONS]

${BOLD}Server Options:${RESET}
  -b, --host, --bind <HOST>   IP address / host to bind server to (default: 127.0.0.1; 0.0.0.0 in --prod)
  -p, --port <PORT>           Local listener or Docker published/internal port (local default: 8000)
  --prod, --production        Run using production Gunicorn WSGI server instead of dev runserver
  -w, --workers <NUM>         Number of Gunicorn worker processes (default: 1, prod only)
  --timeout <SECONDS>         Gunicorn request timeout in seconds (default: 120, prod only)
  --env-file <PATH>           Path to environment file (default: automatic discovery)
  -e, --env <PATH>            Alias for --env-file; also selects Docker configuration
  --db <sqlite|mysql>         Select database for local commands or Docker (sqlite3 also accepted)
  --docker-build             Build the configured image without starting services
  --docker-up                Build, initialize, migrate once, and verify Docker release
  --docker-logs              Follow the selected stack's logs
  --docker-down              Stop the selected stack, preserving host storage
  Docker accepts --env, --db and --port in any order; other flags are local.

${BOLD}Preparation & Maintenance Flags:${RESET}
  -s, --sync                  Run 'uv sync' to install/sync dependencies before launching
  -c, --check                 Run Django system integrity check ('python manage.py check')
  --check-deploy              Run Django deployment readiness check ('check --deploy')
  -m, --migrate               Run database migrations ('python manage.py migrate')
  --check-migrations         Refuse startup when migrations are pending (no schema changes)
  -t, --test                  Run test suite ('python manage.py test') before starting
  --collectstatic             Collect static assets into STATIC_ROOT ('collectstatic --noinput')
  --createsuperuser           Create an administrative user before launching
  --reset-db                  Flush/reset database (with confirmation prompt)
  --shell                     Open Django interactive shell and exit
  -n, --no-run               Run preparation actions without starting a server
  --noreload                 Disable Django development auto-reloader
  In production, --check also runs Django's --deploy checks.

${BOLD}Informational Flags:${RESET}
  -d, --dry-run               Print planned actions and execution command without starting
  -h, --help                  Display this help message and exit

${BOLD}Examples:${RESET}
  ./start.sh                                     # Quick local development start
  ./start.sh -m -s                               # Sync dependencies, migrate DB, and run
  ./start.sh --host 0.0.0.0 --port 8080          # Run dev server on custom IP and port
  ./start.sh --prod -m --collectstatic           # Run production server with migrations & static assets
  ./start.sh -c -t                               # Run health check, tests, and start
  ./start.sh --dry-run --prod                    # Inspect launch command for production
  ./start.sh --db sqlite -c -n                   # Check SQLite without starting a server
  ./start.sh --noreload -p 8080                  # Start without the auto-reloader
  ./start.sh --env /private/app.env --db mysql --docker-up
  ./start.sh --env /private/staging.env --db mysql --port 8004 --docker-up
EOF
    exit 0
}

require_value() {
    [[ -n "${2:-}" && "$2" != -* ]] || { log_error "$1 requires a value"; exit 1; }
}

positive_integer() {
    [[ "$2" =~ ^[0-9]+$ && ${#2} -le 9 ]] && ((10#$2 > 0)) || {
        log_error "$1 requires a positive integer"; exit 1;
    }
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            ;;
        -b|--host|--bind)
            require_value "$1" "${2:-}"
            HOST="$2"
            HOST_EXPLICIT=true
            shift 2
            ;;
        -p|--port)
            require_value "$1" "${2:-}"
            positive_integer "$1" "$2"
            ((10#$2 <= 65535)) || { log_error 'Port must be 1-65535'; exit 1; }
            SERVER_PORT="$2"
            PORT_EXPLICIT=true
            shift 2
            ;;
        -w|--workers)
            require_value "$1" "${2:-}"
            positive_integer "$1" "$2"
            WORKERS="$2"
            shift 2
            ;;
        --timeout)
            require_value "$1" "${2:-}"
            positive_integer "$1" "$2"
            TIMEOUT="$2"
            shift 2
            ;;
        -e|--env-file|--env)
            require_value "$1" "${2:-}"
            ENV_FILE="$2"
            shift 2
            ;;
        --db)
            case "${2:-}" in
                sqlite|sqlite3) DOCKER_DB=sqlite3 ;;
                mysql) DOCKER_DB=mysql ;;
                *) log_error '--db requires sqlite or mysql'; exit 1 ;;
            esac
            shift 2
            ;;
        --docker-build|--docker-up|--docker-logs|--docker-down)
            [[ -z "$DO_DOCKER" ]] || { log_error 'Choose one Docker action'; exit 1; }
            DO_DOCKER="$1"
            shift
            ;;
        -s|--sync)
            DO_SYNC=true
            shift
            ;;
        -c|--check)
            DO_CHECK=true
            shift
            ;;
        --check-deploy)
            DO_CHECK_DEPLOY=true
            shift
            ;;
        -m|--migrate)
            DO_MIGRATE=true
            shift
            ;;
        --check-migrations)
            DO_CHECK_MIGRATIONS=true
            shift
            ;;
        -t|--test)
            DO_TEST=true
            shift
            ;;
        --collectstatic)
            DO_COLLECTSTATIC=true
            shift
            ;;
        --createsuperuser)
            DO_SUPERUSER=true
            shift
            ;;
        --prod|--production)
            DO_PROD=true
            shift
            ;;
        -n|--no-run)
            NO_RUN=true
            shift
            ;;
        --noreload)
            NORELOAD=true
            shift
            ;;
        --dry-run|-d)
            DO_DRY_RUN=true
            shift
            ;;
        --shell)
            DO_SHELL=true
            shift
            ;;
        --reset-db)
            DO_RESET_DB=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use ./start.sh --help to see all available options."
            exit 1
            ;;
    esac
done

# Apply mode defaults after parsing so explicit --host wins in either order.
if [[ "$DO_PROD" == true && "$HOST_EXPLICIT" == false ]]; then HOST=0.0.0.0; fi
if [[ -n "$ENV_FILE" && "$ENV_FILE" != /* ]]; then ENV_FILE="$CALLER_DIR/$ENV_FILE"; fi

if [[ -n "$DO_DOCKER" ]]; then
    [[ "$DO_DRY_RUN" == false ]] || { log_error 'Docker dry-run is not supported; use Compose config --quiet'; exit 1; }
    # Compose gives exported values priority over the selected environment file.
    if [[ "$PORT_EXPLICIT" == true ]]; then export PORT="$SERVER_PORT"; fi
    exec bash "$SCRIPT_DIR/scripts/docker-deploy.sh" "$DO_DOCKER" "$ENV_FILE" "$DOCKER_DB"
fi

if [[ -n "$DOCKER_DB" ]]; then
    export DB_ENGINE="$DOCKER_DB" DATABASE_ENGINE="$DOCKER_DB"
fi

# ------------------------------------------------------------------------------
# 1. Environment & Prerequisite Checks
# ------------------------------------------------------------------------------
log_info "Initializing Water Management environment..."

if ! command -v uv &> /dev/null; then
    log_error "Astral 'uv' package manager was not found on PATH."
    log_error "Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if [[ -n "$ENV_FILE" ]]; then
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file '$ENV_FILE' does not exist."
        exit 1
    fi
    export ENV_FILE
fi

# ------------------------------------------------------------------------------
# 2. Dependency Synchronization
# ------------------------------------------------------------------------------
if [[ "$DO_SYNC" == true ]]; then
    log_info "Synchronizing project dependencies with 'uv sync'..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv sync"
    else
        uv sync
        log_success "Dependencies synchronized successfully."
    fi
fi

# ------------------------------------------------------------------------------
# 3. Database Maintenance (Reset, Migrations)
# ------------------------------------------------------------------------------
if [[ "$DO_RESET_DB" == true ]]; then
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py flush --no-input"
    else
        log_warn "You requested --reset-db. This will delete all table data."
        read -r -p "Are you sure you want to proceed? [y/N] " confirmation
        if [[ "$confirmation" =~ ^[Yy]$ ]]; then
            log_info "Flushing database..."
            uv run python manage.py flush --no-input
            log_success "Database flushed."
        else
            log_info "Database reset cancelled."
        fi
    fi
fi



# ------------------------------------------------------------------------------
# 4. Integrity, Deployment, & Unit Tests
# ------------------------------------------------------------------------------
if [[ "$DO_CHECK" == true ]]; then
    log_info "Running Django system check..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        if [[ "$DO_PROD" == true ]]; then
            echo "  [dry-run] uv run python manage.py check --deploy"
        else
            echo "  [dry-run] uv run python manage.py check"
        fi
    else
        if [[ "$DO_PROD" == true ]]; then
            uv run python manage.py check --deploy
        else
            uv run python manage.py check
        fi
        log_success "System check passed (0 issues)."
    fi
fi

# Like the Guwahati launcher, finish requested tests before modifying the database.
if [[ "$DO_TEST" == true ]]; then
    log_info "Running test suite..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py test"
    else
        uv run python manage.py test
        log_success "Test suite completed successfully."
    fi
fi

if [[ "$DO_MIGRATE" == true ]]; then
    log_info "Applying database migrations..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py migrate --noinput"
    else
        uv run python manage.py migrate --noinput
        log_success "Database migrations up to date."
    fi
fi

if [[ "$DO_CHECK_MIGRATIONS" == true ]]; then
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py migrate --check"
    else
        uv run python manage.py migrate --check
    fi
fi

if [[ "$DO_CHECK_DEPLOY" == true && !( "$DO_CHECK" == true && "$DO_PROD" == true ) ]]; then
    log_info "Running Django deployment check (--deploy)..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py check --deploy"
    else
        uv run python manage.py check --deploy
    fi
fi

# ------------------------------------------------------------------------------
# 5. Static Assets & Superuser Creation
# ------------------------------------------------------------------------------
if [[ "$DO_COLLECTSTATIC" == true ]]; then
    log_info "Collecting static files..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py collectstatic --noinput"
    else
        uv run python manage.py collectstatic --noinput
        log_success "Static assets collected."
    fi
fi

if [[ "$DO_SUPERUSER" == true ]]; then
    log_info "Prompting superuser creation..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py createsuperuser"
    else
        uv run python manage.py createsuperuser
    fi
fi

# ------------------------------------------------------------------------------
# 6. Django Shell Mode
# ------------------------------------------------------------------------------
if [[ "$DO_SHELL" == true ]]; then
    log_info "Starting interactive Django Python shell..."
    if [[ "$DO_DRY_RUN" == true ]]; then
        echo "  [dry-run] uv run python manage.py shell"
    else
        exec uv run python manage.py shell
    fi
    exit 0
fi

# ------------------------------------------------------------------------------
# 7. Server Execution
# ------------------------------------------------------------------------------
if [[ "$NO_RUN" == true ]]; then
    log_success 'Preparation completed (--no-run); no server started.'
    exit 0
fi

if [[ "$DO_PROD" == true ]]; then
    BIND_ADDR="${HOST}:${SERVER_PORT}"
    log_info "Starting ${BOLD}Gunicorn (Production WSGI)${RESET} on ${GREEN}${BIND_ADDR}${RESET} with ${WORKERS} workers..."
    CMD=(uv run gunicorn -c "$SCRIPT_DIR/gunicorn.conf.py" wma.wsgi:application --bind "$BIND_ADDR" --workers "$WORKERS" --timeout "$TIMEOUT")
else
    log_info "Starting ${BOLD}Django Development Server${RESET} on ${GREEN}http://${HOST}:${SERVER_PORT}/${RESET}..."
    CMD=(uv run python manage.py runserver "${HOST}:${SERVER_PORT}")
    if [[ "$NORELOAD" == true ]]; then CMD+=(--noreload); fi
fi

if [[ "$DO_DRY_RUN" == true ]]; then
    log_info "[dry-run] Execution command:"
    echo "  ${CMD[*]}"
    exit 0
fi

# Execute server replacing shell process
exec "${CMD[@]}"
