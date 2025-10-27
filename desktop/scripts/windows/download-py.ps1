### Argument ###

$PYTHON_VERSION = "3.13.7"  # update these by yourself
$TAG = "20250828"  # update these by yourself
$TARGET = "x86_64-pc-windows-msvc"

################

Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$url = "https://github.com/astral-sh/python-build-standalone/releases/download/${TAG}/cpython-${PYTHON_VERSION}+${TAG}-${TARGET}-install_only_stripped.tar.gz"

$DEST_DIR = "src-tauri\pyembed"
$TEMP_FILE = ".python-standalone.tar.gz"
try {
    curl.exe -L "$url" -o "$TEMP_FILE"
    mkdir "$DEST_DIR"
    tar.exe -xzf "$TEMP_FILE" -C "$DEST_DIR"
}
finally {
    Remove-Item "$TEMP_FILE"
}
