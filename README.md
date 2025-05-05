# Mini Baheth

A simple, self-hosted web UI for searching through text files using `ripgrep`.

[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?style=flat&labelColor=00457C&logo=PayPal&logoColor=white&link=https://www.paypal.me/yshalsager)](https://www.paypal.me/yshalsager)
[![Patreon](https://img.shields.io/badge/Patreon-Support-F96854?style=flat&labelColor=F96854&logo=Patreon&logoColor=white&link=https://www.patreon.com/XiaomiFirmwareUpdater)](https://www.patreon.com/XiaomiFirmwareUpdater)
[![Liberapay](https://img.shields.io/badge/Liberapay-Support-F6C915?style=flat&labelColor=F6C915&logo=Liberapay&logoColor=white&link=https://liberapay.com/yshalsager)](https://liberapay.com/yshalsager)

## Features

*   Real-time search results streamed to the UI.
*   Context lines (before/after) displayed for each match.
*   Syntax highlighting for matched terms.
*   Ability to filter searches by directory and file patterns.
*   Clickable file paths/line numbers to view the full file content in a modal.
*   Responsive design using Tailwind CSS.

## Technology Stack

*   **Backend:** Python, NanoDjango, Granian (ASGI Server)
*   **Search:** Ripgrep
*   **Frontend:** HTML, Tailwind CSS (via CDN), htmx
*   **Packaging & Runtime:** Docker, uv

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

# Optional: Override default API port or workers
# API_PORT=5001
# API_WORKERS=8
```

3.  **Place your data:**

Put or symlink the directories and files you want to search inside the `data/` directory.

### Docker

**Build and Run:**

```bash
docker compose up --build -d
```

### Manual

### Without Docker

1. Ensure you have Python 3.13+ and UV.
2. Clone the repository.
3. Install dependencies:
    - Using poetry: `uv sync`
4. Install system dependencies:
    - ripgrep
    - Any other system-level dependencies (refer to the Dockerfile for a complete list)
5. Run the application:

```bash
uv run app.py
```

The application should now be accessible at `http://127.0.0.1:5000` (or the `API_PORT` you configured).

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

*   `app.py`: Main NanoDjango application, defines routes and search logic.
*   `templates/`: HTML templates for the UI.
*   `data/`: Mount point for the files/directories you want to search.
*   `Dockerfile`: Defines the Docker image build process.
*   `docker-compose.yml`: Defines the Docker Compose service for development/basic deployment.
*   `docker-compose.override.yml.example`: Example override for Traefik integration.
*   `pyproject.toml`: Project metadata and Python dependencies (managed by `uv`).

## Acknowledgements

This project relies on several fantastic open-source tools:

*   [Ripgrep](https://github.com/BurntSushi/ripgrep) for its incredibly fast search capabilities.
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
