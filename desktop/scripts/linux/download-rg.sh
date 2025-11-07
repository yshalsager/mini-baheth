#!/bin/bash

set -e

cd "$(dirname "$0")/../.."

BIN_DIR="src-tauri/bin"
mkdir -p "$BIN_DIR"

if [ -x "$BIN_DIR/rg" ]; then
  exit 0
fi

RG_VERSION="14.1.1"
ARCH=$(uname -m)
case "$ARCH" in
  x86_64) TARGET_ARCH="x86_64-unknown-linux-musl" ;;
  aarch64|arm64) TARGET_ARCH="aarch64-unknown-linux-musl" ;;
  *) echo "unsupported arch: $ARCH"; exit 1 ;;
esac

TARBALL="ripgrep-${RG_VERSION}-${TARGET_ARCH}.tar.gz"
URL="https://github.com/BurntSushi/ripgrep/releases/download/${RG_VERSION}/${TARBALL}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

curl -L "$URL" -o "$TMPDIR/$TARBALL"
tar -xzf "$TMPDIR/$TARBALL" -C "$TMPDIR"

SRC_DIR="$TMPDIR/ripgrep-${RG_VERSION}-${TARGET_ARCH}"
cp "$SRC_DIR/rg" "$BIN_DIR/rg"
chmod +x "$BIN_DIR/rg"

echo "rg installed to $BIN_DIR/rg"

