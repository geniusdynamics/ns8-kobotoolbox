#!/bin/bash
#
# Run by the KPI entrypoint (/srv/init): the image does not ship it.
# Adapted from kobotoolbox/kobo-docker scripts/wait_for_mongo.bash
#
set -e

echo 'Waiting for container `mongo`.'
wait-for-it -t 120 -h "${KOBO_MONGO_HOST}" -p "${KOBO_MONGO_PORT}"
echo 'Container `mongo` up.'
