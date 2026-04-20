#!/bin/sh
set -e

echo "[entrypoint] waiting for database..."
python << 'PY'
import os, time, sys
import psycopg
url = os.environ.get("DATABASE_URL", "")
if not url.startswith("postgres"):
    sys.exit(0)
for i in range(60):
    try:
        with psycopg.connect(url, connect_timeout=2) as _:
            print("[entrypoint] db ready")
            break
    except Exception as e:
        print(f"[entrypoint] db not ready ({e}); retry {i+1}/60")
        time.sleep(2)
else:
    sys.exit("[entrypoint] db never became ready")
PY

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] running migrations"
    python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
    echo "[entrypoint] collectstatic"
    python manage.py collectstatic --noinput
fi

exec "$@"
