#!/bin/bash

set -e

cd "$(dirname "$0")/../.."

BIN_DIR="src-tauri/bin"
mkdir -p "$BIN_DIR"

if [ -x "$BIN_DIR/rg" ]; then
  exit 0
fi

RG_VERSION="14.1.1"
TARBALL="ripgrep-${RG_VERSION}-aarch64-apple-darwin.tar.gz"
URL="https://github.com/BurntSushi/ripgrep/releases/download/${RG_VERSION}/${TARBALL}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

curl -L "$URL" -o "$TMPDIR/$TARBALL"
tar -xzf "$TMPDIR/$TARBALL" -C "$TMPDIR"

SRC_DIR="$TMPDIR/ripgrep-${RG_VERSION}-aarch64-apple-darwin"
cp "$SRC_DIR/rg" "$BIN_DIR/rg"
chmod +x "$BIN_DIR/rg"

echo "rg installed to $BIN_DIR/rg"

