Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

### Arguments ###
$PYTHON_VERSION = "3.13.8"  # update these by yourself
$TAG = "20251010"         # update these by yourself

# Detect arch and map to python-build-standalone target
switch -Regex ($env:PROCESSOR_ARCHITECTURE) {
  'ARM64' { $TARGET = 'aarch64-pc-windows-msvc' }
  'AMD64' { $TARGET = 'x86_64-pc-windows-msvc' }
  default { throw "unsupported arch: $env:PROCESSOR_ARCHITECTURE" }
}

Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$url = "https://github.com/astral-sh/python-build-standalone/releases/download/${TAG}/cpython-${PYTHON_VERSION}+${TAG}-${TARGET}-install_only_stripped.tar.gz"

$DEST_DIR = "src-tauri\pyembed"
$TEMP_FILE = ".python-standalone.tar.gz"
try {
    curl.exe -L "$url" -o "$TEMP_FILE"
    New-Item -ItemType Directory -Force -Path $DEST_DIR | Out-Null
    tar.exe -xzf "$TEMP_FILE" -C "$DEST_DIR"
}
finally {
    if (Test-Path $TEMP_FILE) { Remove-Item "$TEMP_FILE" -Force }
}
