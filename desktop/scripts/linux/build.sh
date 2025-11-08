#!/bin/bash

set -e

cd "$(dirname "$0")/../.."

PROJECT_NAME="mini-baheth-desktop"
PYLIB_DIR="$(realpath src-tauri/pyembed/python/lib)"

export PYTAURI_STANDALONE="1"
export PYO3_PYTHON="$(realpath src-tauri/pyembed/python/bin/python3)"
export RUSTFLAGS=" \
    -C link-arg=-Wl,-rpath,\$ORIGIN/../lib/$PROJECT_NAME/lib \
    -L $PYLIB_DIR"

mise x uv -- uv run ./scripts/stage-tools.py || true

# Stage rga.config.json into src-tauri if present at repo root
[ -f ../rga.config.json ] && cp -f ../rga.config.json src-tauri/rga.config.json || true

# 1) Install core (non-editable) from local path while ignoring workspace sources
UV_PIP_NO_SOURCES=1 mise x uv -- uv pip install --no-sources \
    --exact \
    --compile-bytecode \
    --python="$PYO3_PYTHON" \
    ../core

# 2) Install the desktop package with its dependencies; core already satisfied
UV_PIP_NO_SOURCES=1 mise x uv -- uv pip install --no-sources \
    --exact \
    --compile-bytecode \
    --python="$PYO3_PYTHON" \
    --reinstall-package="$PROJECT_NAME" \
    ./src-tauri

mise x pnpm -- pnpm tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release
