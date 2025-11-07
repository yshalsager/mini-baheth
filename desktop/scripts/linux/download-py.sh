#!/bin/bash

### Argument ###

PYTHON_VERSION="3.13.8"  # update these by yourself
TAG="20251010"  # update these by yourself

ARCH=$(uname -m)
case "$ARCH" in
  x86_64) TARGET="x86_64-unknown-linux-gnu" ;;
  aarch64|arm64) TARGET="aarch64-unknown-linux-gnu" ;;
  *) echo "unsupported arch: $ARCH"; exit 1 ;;
esac

################

set -e

cd "$(dirname "$0")/../.."

url="https://github.com/astral-sh/python-build-standalone/releases/download/${TAG}/cpython-${PYTHON_VERSION}+${TAG}-${TARGET}-install_only_stripped.tar.gz"

DEST_DIR="src-tauri/pyembed"
mkdir -p "$DEST_DIR"
curl -L "$url" | tar -xz -C "$DEST_DIR"
