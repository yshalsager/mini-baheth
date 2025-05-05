#!/bin/sh
set -e

API_PORT=${API_PORT:-5000}
API_WORKERS=${API_WORKERS:-4}
API_HOST=${API_HOST:-0.0.0.0}

exec granian --interface asginl --host "$API_HOST" --port "$API_PORT" --workers "$API_WORKERS" app:app "$@" 