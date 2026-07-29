#!/usr/bin/env bash
# Start/stop a local Postgres instance for backend development, using the
# system's installed Postgres (via Homebrew, apt, etc.) rather than Docker.
#
# This exists for developers who want to run the backend's test suite
# (`make backend-test`) without Docker Compose. If Docker is available,
# `infra/docker-compose.yml` is the simpler path — see infra/README.md.
#
# Usage:
#   scripts/local_postgres.sh start   # init (if needed) + start on 127.0.0.1:5432
#   scripts/local_postgres.sh stop
#   scripts/local_postgres.sh status
#
# Expects `initdb`, `pg_ctl`, `psql`, and `createuser`/`createdb` (or `psql`
# with superuser rights) to be on PATH. Data lives in $PGDATA_DIR, a
# directory this script owns entirely and is safe to delete to start fresh.

set -euo pipefail

PGDATA_DIR="${GYM_PGDATA_DIR:-$HOME/.gym-companion/pgdata}"
PGSOCKET_DIR="${GYM_PGSOCKET_DIR:-$HOME/.gym-companion/pgsocket}"
PGPORT="${GYM_PGPORT:-5432}"
DB_NAME="gymcompanion"
DB_USER="gymcompanion"
DB_PASSWORD="gymcompanion"

usage() {
    echo "Usage: $0 {start|stop|status}" >&2
    exit 1
}

ensure_initialized() {
    if [ ! -s "${PGDATA_DIR}/PG_VERSION" ]; then
        echo "Initializing Postgres data directory at ${PGDATA_DIR}..."
        mkdir -p "${PGDATA_DIR}" "${PGSOCKET_DIR}"
        initdb --auth=trust --username=postgres -D "${PGDATA_DIR}" >/dev/null
    fi
}

start() {
    ensure_initialized
    mkdir -p "${PGSOCKET_DIR}"
    pg_ctl -D "${PGDATA_DIR}" -l "${PGDATA_DIR}/server.log" \
        -o "-p ${PGPORT} -k ${PGSOCKET_DIR} -c listen_addresses=127.0.0.1" \
        start

    # Idempotent role/database creation: ignore "already exists" failures.
    psql -h "${PGSOCKET_DIR}" -p "${PGPORT}" -U postgres -d postgres \
        -c "CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
    psql -h "${PGSOCKET_DIR}" -p "${PGPORT}" -U postgres -d postgres \
        -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || true

    echo "Postgres is up: postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${PGPORT}/${DB_NAME}"
    echo "Set this as GYM_DATABASE_URL / GYM_TEST_DATABASE_URL before running the backend or its tests."
}

stop() {
    pg_ctl -D "${PGDATA_DIR}" stop -m fast
}

status() {
    pg_ctl -D "${PGDATA_DIR}" status
}

case "${1:-}" in
    start) start ;;
    stop) stop ;;
    status) status ;;
    *) usage ;;
esac
