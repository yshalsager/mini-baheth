# Mini Baheth

A simple, self-hosted web UI and desktop app for searching through text files using `ripgrep` and `ripgrep-all`.

<img src="desktop/src/lib/assets/logo.svg" alt="logo" width="256" height="256" />

[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)


[![GitHub release](https://img.shields.io/github/release/yshalsager/mini-baheth.svg)](https://github.com/yshalsager/mini-baheth/releases/)
[![GitHub Downloads](https://img.shields.io/github/downloads/yshalsager/mini-baheth/total.svg)](https://github.com/yshalsager/mini-baheth/releases/latest)


[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?style=flat&labelColor=00457C&logo=PayPal&logoColor=white&link=https://www.paypal.me/yshalsager)](https://www.paypal.me/yshalsager)
[![Patreon](https://img.shields.io/badge/Patreon-Support-F96854?style=flat&labelColor=F96854&logo=Patreon&logoColor=white&link=https://www.patreon.com/XiaomiFirmwareUpdater)](https://www.patreon.com/XiaomiFirmwareUpdater)
[![Liberapay](https://img.shields.io/badge/Liberapay-Support-F6C915?style=flat&labelColor=F6C915&logo=Liberapay&logoColor=white&link=https://liberapay.com/yshalsager)](https://liberapay.com/yshalsager)

## Features

- Streaming results realtime to the UI.
- Context lines (before/after) and matching text highlighting.
- Directory and file-pattern filtering.
- Fast first paint: only root-level directories initially; fetch more on demand.
- Modal preview for files; DOCX/DOC are converted to text for readability.
- `rga` adapters for more formats:
  - DOCX: via `pandoc` (built-in `rga` adapter)
  - DOC: via `antiword` ([custom adapter](https://github.com/phiresky/ripgrep-all/discussions/272))
  - JSON: via `gron` ([custom adapter](https://github.com/phiresky/ripgrep-all/discussions/176)) to flatten keys/values
- Responsive design using Tailwind CSS.

### Arabic Diacritics (التشكيل)

Both Desktop and Web expose a single “نمط البحث” control with four modes:

- ذكي (Smart): Fast path. Only expands base letters and turns spaces into gaps; no PCRE and no extra mark handling. If you type diacritics, they are treated literally.
- تجاهل التشكيل (Ignore): Matches with or without diacritics by allowing optional combining marks (and tatweel) after Arabic letters. Enables PCRE2.
- التزام التشكيل (Require): Enforces diacritics only where you typed them in your query (per-letter). Enables PCRE2.
- تعبير اعتيادي (Regex): Uses your regex pattern as-is.

Notes
- PCRE2 is enabled only when needed (Ignore / Require). Expect slower searches in those modes.
- “Smart” is the default for performance and predictable results.

## Technology Stack

- Backend: Python, NanoDjango, Granian (ASGI Server)
- Search: ripgrep (rg), ripgrep-all (rga)
- Frontend: HTML, Tailwind CSS (via CDN), htmx
- Packaging & Runtime: Docker, uv
- Desktop: Tauri + PyTauri + SvelteKit + Shadcn

## Setup

1.  **Clone the repository:**

```bash
git clone https://github.com/yshalsager/mini-baheth.git
cd mini-baheth
```

2.  **Prepare Environment:**

Create a .env and fill in the required information as defined in [mise.toml] env section:

```dotenv
# Hostname for Traefik (if using the override)
# TRAEFIK_HOST=baheth.yourdomain.com

# Optional: Override default Granian settings
# GRANIAN_PORT=5001
# GRANIAN_WORKERS=8
# GRANIAN_THREADS=4
```

3.  **Place your data:**

Put or symlink the directories and files you want to search inside the `data/` directory. Symlinks are followed safely with cycle protection.

### Docker

The image installs:
- ripgrep, ripgrep-all
- pandoc (DOCX), antiword (DOC), gron (JSON)

It ships an rga config at `/etc/rga/config.json` that enables custom adapters for antiword and gron.

Build and run:

```bash
docker compose up --build -d
```

### Manual

### Without Docker

1. Ensure you have Python 3.13+ and uv.
2. Install Python deps: `uv sync`
3. Install system tools:
   - ripgrep, ripgrep-all
   - pandoc (DOCX), antiword (DOC), gron (JSON)
   - Any other system-level dependencies (refer to the Dockerfile for a complete list)
4. Run the application:

```bash
uv run granian webapp.app:app.asgi
```

The application should now be accessible at `http://127.0.0.1:5000` (or the `GRANIAN_PORT` you configured).

### Notes
- The server chooses `rga` when the file filter is `*.doc`, `*.docx`, or `*.json`, otherwise it uses `rg`. When using `rga`, it passes `--rga-config-file=rga.config.json` if present (or `/etc/rga/config.json` in Docker).
- Modal preview: `.docx` uses pandoc; `.doc` uses antiword; other files are read as text.
 - Ignore/Require enable PCRE2 (`-P`) in ripgrep which can be slower; prefer Smart when you don’t need diacritic-awareness.

## Traefik Integration (Optional)

An example override file is provided for integrating with a Traefik reverse proxy setup.

1.  **Copy the example override file:**

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

2.  **Configure Hostname:**
    *   Edit the `.env` file and set `TRAEFIK_HOST` to the public hostname you want to use (e.g., `TRAEFIK_HOST=baheth.yourdomain.com`).
3.  **Prerequisites:** Ensure Traefik is running and connected to an external Docker network named `web`.
4.  **Run:** Start the stack using `docker compose up --build -d`. Traefik will automatically pick up the labels and route traffic.

## Files & Directories

*   `webapp/app.py`: Main NanoDjango application, defines routes and search logic.
*   `templates/`: HTML templates for the UI.
*   `data/`: Mount point for the files/directories you want to search.
*   `Dockerfile`: Defines the Docker image build process.
*   `docker-compose.yml`: Defines the Docker Compose service for development/basic deployment.
*   `docker-compose.override.yml.example`: Example override for Traefik integration.
*   `pyproject.toml`: Project metadata and Python dependencies (managed by `uv`).

## Desktop App

Build a native desktop app with embedded Python.

- Install deps
  - In `desktop/`: `mise x pnpm -- pnpm install`
- Download embedded Python (first time only)
  - In `desktop/`: `mise x uv -- uv run ./scripts/download_python.py`
- Build
  - In `desktop/`: `mise r //desktop:build`

Artifacts
- macOS: `desktop/target/bundle-release/bundle/macos/mini-baheth.app`
- Windows: `.msi`/`.exe` under `desktop/target/**/bundle`
- Linux: `.deb`/`.rpm` under `desktop/target/**/bundle`

Notes
- Bundles include the `core` package and staged tools (`rg`, `rga`, `rga-preproc`, `gron`, `pandoc`).
- If `rga.config.json` exists at repo root, it’s bundled and used automatically for `rga` searches.

## Acknowledgements

This project relies on several fantastic open-source tools:

*   [Ripgrep](https://github.com/BurntSushi/ripgrep) for its incredibly fast search capabilities.
    *   [Ripgrep-all](https://github.com/phiresky/ripgrep-all) for its ability to search through more file types.
    *   [Pandoc](https://github.com/jgm/pandoc) for its ability to convert DOCX to text.
    *   [Antiword](https://repology.org/project/antiword/information) for its ability to convert DOC to text.
    *   [Gron](https://github.com/tomnomnom/gron) for its ability to convert JSON to text.
*   [NanoDjango](https://github.com/radiac/nanodjango) for providing a minimal Django-like web framework.
*   [Granian](https://github.com/emmett-framework/granian) as the high-performance ASGI server.
*   [uv](https://github.com/astral-sh/uv) for fast Python packaging and resolution.
*   [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS framework.
*   [htmx](https://htmx.org/) for simplifying dynamic HTML interactions.


## Development

This project uses several tools to streamline the development process:

### mise

[mise](https://mise.jdx.dev/) is used for managing project-level dependencies and environment variables. mise helps
ensure consistent development environments across different machines.

To get started with mise:

1. Install mise by following the instructions on the [official website](https://mise.jdx.dev/).
2. Run `mise install` in the project root to set up the development environment.

### UV

[UV](https://docs.astral.sh/uv/) is used for dependency management and packaging. It provides a clean,
version-controlled way to manage project dependencies.

To set up the project with UV:

1. Install UV by following the instructions on the [official website](https://docs.astral.sh/uv/getting-started/installation/).
2. Run `uv sync` to install project dependencies.
