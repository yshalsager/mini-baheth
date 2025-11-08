#!/bin/bash

set -e

cd "$(dirname "$0")/../.."

PROJECT_NAME="mini-baheth-desktop"
PYLIB_DIR="$(realpath src-tauri/pyembed/python/lib)"

export PYTAURI_STANDALONE="1"
export PYO3_PYTHON="$(realpath src-tauri/pyembed/python/bin/python3)"
export RUSTFLAGS=" \
    -C link-arg=-Wl,-rpath,@executable_path/../Resources/lib \
    -L $PYLIB_DIR"

mise x uv -- uv run ./scripts/stage-tools.py || true

# Build a wheel for core to avoid editable installs in the bundle
mise x uv -- uv build ../core
CORE_WHEEL="$(ls -t ../core/dist/mini_baheth_core-*.whl | head -n1)"

UV_PIP_NO_SOURCES=1 mise x uv -- uv pip install \
    --exact \
    --compile-bytecode \
    --python="$PYO3_PYTHON" \
    --reinstall-package="$PROJECT_NAME" \
    "$CORE_WHEEL" \
    ./src-tauri

mise x node pnpm -- pnpm tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release
