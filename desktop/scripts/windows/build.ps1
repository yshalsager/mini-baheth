Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$PROJECT_NAME = "mini-baheth-desktop"

$env:PYTAURI_STANDALONE = "1"
$env:PYO3_PYTHON = (Resolve-Path -LiteralPath "src-tauri\pyembed\python\python.exe").Path

mise.exe x uv -- uv run .\scripts\stage-tools.py

# Build a wheel for core to avoid editable installs in the bundle
$env:UV_PIP_NO_SOURCES = "1"
mise.exe x uv -- uv build ..\core
$CORE_WHEEL = (Get-ChildItem -Path "..\core\dist" -Filter "mini_baheth_core-*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName

# 1) Install core wheel (non-editable) while ignoring workspace sources
mise.exe x uv -- uv.exe pip install --no-sources `
    --exact `
    --compile-bytecode `
    --python="$env:PYO3_PYTHON" `
    "$CORE_WHEEL"

# 2) Install the desktop package with its dependencies; core already satisfied
mise.exe x uv -- uv.exe pip install --no-sources `
    --exact `
    --compile-bytecode `
    --python="$env:PYO3_PYTHON" `
    --reinstall-package="$PROJECT_NAME" `
    .\src-tauri

$arch = $env:PROCESSOR_ARCHITECTURE
if ($arch -eq 'ARM64') {
  mise.exe x node pnpm -- pnpm dlx @tauri-apps/cli-win32-arm64-msvc tauri build --config="src-tauri\tauri.bundle.json" -- --profile bundle-release
} else {
  mise.exe x node pnpm -- pnpm tauri build --config="src-tauri\tauri.bundle.json" -- --profile bundle-release
}
