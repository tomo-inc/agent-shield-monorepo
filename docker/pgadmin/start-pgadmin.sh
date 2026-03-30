#!/bin/sh
set -eu

/entrypoint.sh &
pid="$!"

i=0
while [ "$i" -lt 30 ]; do
  if /venv/bin/python /pgadmin4/setup.py get-users 2>/dev/null | grep -q "admin@example.com"; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

/venv/bin/python /pgadmin4/setup.py load-servers /pgadmin4/servers.json --user admin@example.com --replace

wait "$pid"
