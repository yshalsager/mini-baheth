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

# Build a wheel for core to avoid editable installs in the bundle
mise x uv -- uv build ../core
CORE_WHEEL="$(ls -t ../core/dist/mini_baheth_core-*.whl | head -n1)"

# 1) Install core wheel (non-editable) while ignoring workspace sources
UV_PIP_NO_SOURCES=1 mise x uv -- uv pip install --no-sources \
    --exact \
    --compile-bytecode \
    --python="$PYO3_PYTHON" \
    "$CORE_WHEEL"

# 2) Install the desktop package with its dependencies; core already satisfied
UV_PIP_NO_SOURCES=1 mise x uv -- uv pip install --no-sources \
    --exact \
    --compile-bytecode \
    --python="$PYO3_PYTHON" \
    --reinstall-package="$PROJECT_NAME" \
    ./src-tauri

mise x pnpm -- pnpm tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release
