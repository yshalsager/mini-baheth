#!/bin/bash

set -e

cd "$(dirname "$0")/../.."

PROJECT_NAME="mini-baheth"
PYLIB_DIR="$(realpath src-tauri/pyembed/python/lib)"

export PYTAURI_STANDALONE="1"
export PYO3_PYTHON="$(realpath src-tauri/pyembed/python/bin/python3)"
export RUSTFLAGS=" \
    -C link-arg=-Wl,-rpath,\$ORIGIN/../lib/$PROJECT_NAME/lib \
    -L $PYLIB_DIR"

bash ./scripts/linux/download-rg.sh || true

uv pip install \
    --exact \
    --compile-bytecode \
    --python="$PYO3_PYTHON" \
    --reinstall-package="$PROJECT_NAME" \
    --reinstall-package="mini-baheth-core" \
    ./src-tauri

pnpm tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release
