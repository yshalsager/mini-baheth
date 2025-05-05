#!/bin/sh
set -e

# Default values for environment variables if not set
API_PORT=${API_PORT:-5000}
API_WORKERS=${API_WORKERS:-4}

# Execute the granian command directly
exec granian --interface asginl --host 0.0.0.0 --port "$API_PORT" --workers "$API_WORKERS" app:app "$@" 