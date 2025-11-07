#!/bin/bash

### Argument ###

PYTHON_VERSION="3.13.8"  # update these by yourself
TAG="20251010"  # update these by yourself

ARCH=$(uname -m)
case "$ARCH" in
  x86_64) TARGET="x86_64-apple-darwin" ;;
  arm64|aarch64) TARGET="aarch64-apple-darwin" ;;
  *) echo "unsupported arch: $ARCH"; exit 1 ;;
esac

################

set -e

cd "$(dirname "$0")/../.."

url="https://github.com/astral-sh/python-build-standalone/releases/download/${TAG}/cpython-${PYTHON_VERSION}+${TAG}-${TARGET}-install_only_stripped.tar.gz"

DEST_DIR="src-tauri/pyembed"
mkdir -p "$DEST_DIR"
curl -L "$url" | tar -xz -C "$DEST_DIR"

# ref: <https://github.com/pytauri/pytauri/issues/99#issuecomment-2704556726>
python_major_minor="${PYTHON_VERSION%.*}"  # "3.13.7" -> "3.13"
install_name_tool -id "@rpath/libpython$python_major_minor.dylib" "$DEST_DIR/python/lib/libpython$python_major_minor.dylib"
