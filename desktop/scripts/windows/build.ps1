Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$PROJECT_NAME = "mini-baheth"

$env:PYTAURI_STANDALONE = "1"
$env:PYO3_PYTHON = (Resolve-Path -LiteralPath "src-tauri\pyembed\python\python.exe").Path

& .\scripts\windows\download-rg.ps1

uv.exe pip install `
    --exact `
    --compile-bytecode `
    --python="$env:PYO3_PYTHON" `
    --reinstall-package="$PROJECT_NAME" `
    .\src-tauri

pnpm -- tauri build --config="src-tauri\tauri.bundle.json" -- --profile bundle-release
