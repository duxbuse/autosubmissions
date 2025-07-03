#!/bin/sh
# Entrypoint for dev: run Django and Vite with hot reload

# Start Django dev server (with autoreload)
cd /app/backend
uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput
uv run python manage.py runserver 0.0.0.0:8000 &

# Start Vite dev server
cd /app/frontend
npm run dev -- --host 0.0.0.0
