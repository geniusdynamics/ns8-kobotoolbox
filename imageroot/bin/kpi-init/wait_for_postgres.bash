#!/bin/bash
#
# Run by the KPI entrypoint (/srv/init): the image does not ship it.
# Adapted from kobotoolbox/kobo-docker scripts/wait_for_postgres.bash:
# it also creates the KPI and KoboCAT databases with their extensions.
#
set -e

echo 'Waiting for container `postgres`.'
wait-for-it -t 120 -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}"
echo 'Container `postgres` up.'

echo 'Waiting for Postgres service.'
export PGPASSWORD="${POSTGRES_PASSWORD}"
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}"; do
    sleep 1
done

source /etc/profile

for POSTGRES_DB in ${KPI_POSTGRES_DB} ${KC_POSTGRES_DB}; do
    echo "Postgres service running; ensuring ${POSTGRES_DB} database exists and has PostGIS extensions..."
    if ! psql -d postgres -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -tAc \
        "SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB}'" | grep -q 1; then
        psql -d postgres -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
            -c "CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\""
    fi
    psql -v ON_ERROR_STOP=1 -d "${POSTGRES_DB}" -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" <<SQL
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
SQL
    echo "Postgres database ${POSTGRES_DB} ready for use!"
done
