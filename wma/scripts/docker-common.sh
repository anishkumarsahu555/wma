#!/usr/bin/env bash
# Shared safe Compose configuration. Never source dotenv files as shell code.
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
configure_stack() {
    command -v docker >/dev/null || fail 'Docker with Compose v2.24+ is required'
    local selected=${1:-.env} requested_db=${2:-} resolved key value
    [[ -f "$selected" ]] || fail 'Selected environment file does not exist'
    export APP_ENV_FILE="$(cd "$(dirname "$selected")" && pwd)/$(basename "$selected")"
    compose=(docker compose --env-file "$APP_ENV_FILE" -f "$repo/docker-compose.yml")
    # Compose parses interpolation, quotes and comments. Capture privately; never print it.
    # A fixed probe name distinguishes Compose's implicit project-name export
    # from an operator-supplied COMPOSE_PROJECT_NAME before choosing legacy paths.
    resolved=$(docker compose --env-file "$APP_ENV_FILE" -f - config --environment <<'COMPOSE'
name: wma-configuration-probe
services:
  probe:
    image: scratch
COMPOSE
    ) || fail 'Invalid Compose configuration'
    while IFS='=' read -r key value; do
        case "$key" in
            COMPOSE_PROJECT_NAME)
                [[ "$value" == wma-configuration-probe ]] || export "$key=$value" ;;
            PROJECT_NAME|DEPLOY_ENV|IMAGE_NAME|APP_IMAGE_TAG|VPS_STORAGE_ROOT|APP_DATA_ROOT|PORT|APP_PORT|DATABASE_ENGINE|DB_ENGINE|DB_NAME|DB_USER|DB_PASSWORD|MYSQL_ROOT_PASSWORD|SECRET_KEY|ALLOWED_HOSTS)
                export "$key=$value" ;;
        esac
    done <<< "$resolved"
    export PROJECT_NAME=${PROJECT_NAME:-watermanagement} DEPLOY_ENV=${DEPLOY_ENV:-production}
    if [[ -n "${APP_DATA_ROOT:-}" ]]; then
        export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-watermanagement}
    else
        export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-$PROJECT_NAME-$DEPLOY_ENV}
    fi
    [[ "$COMPOSE_PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || fail 'Invalid Compose project identity'
    [[ "$PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ && "$DEPLOY_ENV" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || fail 'Invalid project/environment slug'
    export IMAGE_NAME=${IMAGE_NAME:-$PROJECT_NAME}
    export DATABASE_ENGINE=${requested_db:-${DATABASE_ENGINE:-${DB_ENGINE:-mysql}}}
    export PORT=${PORT:-${APP_PORT:-8005}}
    [[ "$PORT" =~ ^[0-9]+$ && ${#PORT} -le 5 ]] && ((10#$PORT > 0 && 10#$PORT < 65536)) || fail 'PORT must be 1-65535'
    if [[ -n "${APP_DATA_ROOT:-}" ]]; then
        # Existing installations retain their exact bind mount paths and stack name.
        export MYSQL_DATA_DIR="$APP_DATA_ROOT/mysql_data" MEDIA_DATA_DIR="$APP_DATA_ROOT/media_data"
        printf 'Using legacy APP_DATA_ROOT storage; preserve its existing stack identity.\n'
    else
        export APP_DATA_ROOT="${VPS_STORAGE_ROOT:-/srv/apps}/$PROJECT_NAME/$DEPLOY_ENV"
        export MYSQL_DATA_DIR="$APP_DATA_ROOT/mysql" MEDIA_DATA_DIR="$APP_DATA_ROOT/media"
    fi
    [[ "$APP_DATA_ROOT" == /* && "$APP_DATA_ROOT" != / ]] || fail 'Storage root must be an absolute project directory'
    case "$DATABASE_ENGINE" in
        mysql)
            export COMPOSE_PROFILES=mysql DEPLOY_DB_NAME=${DB_NAME:-wma}
            ;;
        sqlite3)
            export COMPOSE_PROFILES='' DEPLOY_DB_NAME=/data/db.sqlite3
            ;;
        *) fail 'Docker supports mysql and sqlite3 only; PostgreSQL has no installed driver' ;;
    esac
    # Do not pass a host ENV_FILE path into Django inside the image.
    "${compose[@]}" config --quiet
}
validate_release_settings() {
    [[ -n "${SECRET_KEY:-}" && "$SECRET_KEY" != change-me-to-a-secure-random-secret-key && "$SECRET_KEY" != django-insecure-local-development-only ]] || fail 'Set a private SECRET_KEY'
    [[ -n "${ALLOWED_HOSTS:-}" ]] || fail 'Set ALLOWED_HOSTS'
    if [[ "$DATABASE_ENGINE" == mysql ]]; then
        [[ -n "${DB_PASSWORD:-}" && -n "${MYSQL_ROOT_PASSWORD:-}" ]] || fail 'Set DB_PASSWORD and MYSQL_ROOT_PASSWORD'
        [[ "${DB_USER:-wma}" != root ]] || fail 'DB_USER must be a non-root application account'
        [[ "$DEPLOY_DB_NAME" != *.sqlite3 ]] || fail 'Set DB_NAME to the MySQL database name'
    fi
}
