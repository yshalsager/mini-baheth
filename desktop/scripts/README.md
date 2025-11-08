# Build Standalone App

ref: https://pytauri.github.io/pytauri/latest/usage/tutorial/build-standalone/

- Download embedded Python
  - macOS/Linux: `mise x uv -- uv run ./scripts/download_python.py`
  - Windows: `mise.exe x uv -- uv.exe run .\scripts\download_python.py`

- Build the app
  - `mise r //desktop:build`

Notes
- The build script stages helper tools (rg, rga, rga-preproc, gron, pandoc) into `src-tauri/bin`
- If `../rga.config.json` exists, it is copied into the bundle
