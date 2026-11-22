#!/usr/bin/env bash
set -euo pipefail
umask 077
# Resolve explicit relative environment paths from the caller's directory.
action=${1:?Docker action required}
selected=${2:-}
if [[ -n "$selected" ]]; then selected="$(cd "$(dirname "$selected")" && pwd)/$(basename "$selected")"; fi
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
source scripts/docker-common.sh
configure_stack "${selected:-$repo/.env}" "${3:-}"
case "$action" in
    --docker-build) exec "${compose[@]}" build web ;;
    --docker-logs) exec "${compose[@]}" logs --follow --tail=100 ;;
    --docker-down) exec "${compose[@]}" down ;;
    --docker-up) ;;
    *) fail 'Unknown Docker action' ;;
esac
validate_release_settings
# Migration files are required: they define the schema for both fresh and existing databases.
[[ -f wmaApp/migrations/0001_initial.py ]] || fail 'Missing wmaApp migration history; restore the reviewed migrations before deployment'
# Host-wide lock serializes all checkouts targeting this stack on this machine.
lock="/tmp/wma-deploy-$COMPOSE_PROJECT_NAME.lock"
mkdir "$lock" 2>/dev/null || fail "Deployment lock exists: $lock; investigate before removing"
paused=false
cleanup() {
    status=$?
    trap - EXIT
    if ((status != 0)) && [[ "$paused" == true ]]; then
        "${compose[@]}" stop web >/dev/null 2>&1 || true
        printf 'Release failed after downtime; web remains stopped. Inspect schema before retrying.\n' >&2
    fi
    rmdir "$lock" || true
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git_revision=$(git rev-parse --verify --short=12 HEAD)
source_state=''
[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || source_state=-dirty
build_id=$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')
export APP_IMAGE_TAG="release-$(date -u +%Y%m%dT%H%M%SZ)-$git_revision$source_state-$build_id"
export APP_IMAGE="$IMAGE_NAME:$APP_IMAGE_TAG"
printf 'Release: %s\nStorage: %s\n' "$APP_IMAGE" "$APP_DATA_ROOT"
"${compose[@]}" build web
"${compose[@]}" run --pull never --rm --no-deps -T storage-init
if [[ "$DATABASE_ENGINE" == mysql ]]; then
    "${compose[@]}" up -d --no-deps --wait --wait-timeout 240 mysql
fi
# Validate before downtime, then stop every application writer before schema changes.
"${compose[@]}" run --pull never --rm --no-deps -T migrate check
"${compose[@]}" run --pull never --rm --no-deps -T migrate makemigrations --check --dry-run
paused=true
"${compose[@]}" stop web
"${compose[@]}" run --pull never --rm --no-deps -T migrate migrate --noinput
"${compose[@]}" up -d --wait --wait-timeout 240 redis
"${compose[@]}" up -d --no-deps --no-build --force-recreate --pull never --wait --wait-timeout 240 web
paused=false
printf 'Healthy release: %s\nUse this exact image for management and rollback.\n' "$APP_IMAGE"
"${compose[@]}" ps -a
