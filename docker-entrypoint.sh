#!/bin/sh
set -e

# Set default values for Granian environment variables if not already set
export GRANIAN_HOST=${GRANIAN_HOST:-0.0.0.0}
export GRANIAN_PORT=${GRANIAN_PORT:-5000}
export GRANIAN_WORKERS=${GRANIAN_WORKERS:-2}
export GRANIAN_THREADS=${GRANIAN_THREADS:-1}
export GRANIAN_INTERFACE=${GRANIAN_INTERFACE:-asginl}
export GRANIAN_RELOAD=${GRANIAN_RELOAD:-false}

exec granian app:app.asgi "$@" 