Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$PROJECT_NAME = "mini-baheth-desktop"

$env:PYTAURI_STANDALONE = "1"
$env:PYO3_PYTHON = (Resolve-Path -LiteralPath "src-tauri\pyembed\python\python.exe").Path

mise.exe x uv -- uv run .\scripts\stage-tools.py

# Stage rga.config.json into src-tauri if present at repo root
if (Test-Path ..\rga.config.json) { Copy-Item ..\rga.config.json src-tauri\rga.config.json -Force }

# 1) Install core (non-editable) from local path while ignoring workspace sources
mise.exe x uv -- uv.exe pip install --no-sources `
    --exact `
    --compile-bytecode `
    --python="$env:PYO3_PYTHON" `
    ..\core

# 2) Install the desktop package with its dependencies; core already satisfied
mise.exe x uv -- uv.exe pip install --no-sources `
    --exact `
    --compile-bytecode `
    --python="$env:PYO3_PYTHON" `
    --reinstall-package="$PROJECT_NAME" `
    .\src-tauri

$arch = $enpnpmOR_ARCHITECTURE
if ($arch -eq 'ARM64') {
  mise.exe x node pnpm -- pnpm dlx @tauri-apps/cli-win32-arm64-msvc tauri build --config="src-tauri\tauri.bundle.json" -- --profile bundle-release
} else {
  mise.exe x node pnpm -- pnpm tauri build --config="src-tauri\tauri.bundle.json" -- --profile bundle-release
}
