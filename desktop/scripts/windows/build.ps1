Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$PROJECT_NAME = "mini-baheth"

$env:PYTAURI_STANDALONE = "1"
$env:PYO3_PYTHON = (Resolve-Path -LiteralPath "src-tauri\pyembed\python\python.exe").Path

mise.exe x uv -- uv run .\scripts\stage-tools.py

mise.exe x uv -- uv.exe pip install `
    --exact `
    --compile-bytecode `
    --python="$env:PYO3_PYTHON" `
    --reinstall-package="$PROJECT_NAME" `
    --reinstall-package="mini-baheth-core" `
    ..\core `
    .\src-tauri

mise.exe x pnpm -- pnpm -- tauri build --config="src-tauri\tauri.bundle.json" -- --profile bundle-release
