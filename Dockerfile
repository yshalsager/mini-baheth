ARG PYTHON_VERSION=3.13
ARG RGA_VERSION=0.10.9
ARG UV_VERSION=0.8.19
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim-trixie

# ripgrep + ripgrep-all (rga) with minimal deps for doc/docx only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    ripgrep \
    antiword \
    pandoc \
    gron \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
    amd64) target="x86_64-unknown-linux-musl" ;; \
    arm64) target="aarch64-unknown-linux-musl" ;; \
    *) echo "unsupported arch: $arch"; exit 1 ;; \
    esac; \
    tmpdir="$(mktemp -d)"; cd "$tmpdir"; \
    url1="https://github.com/phiresky/ripgrep-all/releases/download/v${RGA_VERSION}/rga-v${RGA_VERSION}-${target}.tar.gz"; \
    url2="https://github.com/phiresky/ripgrep-all/releases/download/v${RGA_VERSION}/rga-v${RGA_VERSION}-${target}.tar.xz"; \
    if ! curl -fsSL -o rga.tar "$url1"; then curl -fsSL -o rga.tar "$url2"; fi; \
    tar -xf rga.tar; \
    binpath="$(find . -maxdepth 2 -type f -name rga | head -n1)"; \
    preprocpath="$(find . -maxdepth 2 -type f -name rga-preproc | head -n1 || true)"; \
    install -m 0755 "$binpath" /usr/local/bin/rga; \
    if [ -n "$preprocpath" ]; then install -m 0755 "$preprocpath" /usr/local/bin/rga-preproc; fi; \
    cd /; rm -rf "$tmpdir"; \
    rga --version

# Configure rga config with custom DOC adapter (antiword). Pandoc covers DOCX by default.
RUN set -eux; \
    mkdir -p /etc/rga; \
    cat > /etc/rga/config.json <<'JSON'
{
  "custom_adapters": [
    {
      "name": "antiword",
      "version": 1,
      "description": "Uses antiword to extract text from DOC files",
      "extensions": ["doc"],
      "mimetypes": ["application/msword"],
      "binary": "antiword",
      "args": ["-"],
      "disabled_by_default": false,
      "match_only_by_mime": false,
      "output_path_hint": "${input_virtual_path}.txt"
    },
    {
      "name": "gron",
      "version": 1,
      "description": "Transform JSON into discrete JS assignments",
      "extensions": ["json"],
      "mimetypes": ["application/json"],
      "binary": "gron",
      "args": [],
      "disabled_by_default": false,
      "match_only_by_mime": false
    }
  ]
}
JSON

COPY --from=ghcr.io/astral-sh/uv:${UV_VERSION} /uv /usr/local/bin/uv

WORKDIR /code
RUN useradd -m appuser && chown -R appuser:appuser /code

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER appuser

WORKDIR /code
COPY pyproject.toml .
COPY uv.lock .

ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=none
RUN --mount=type=cache,target=/home/appuser/.cache/uv uv sync --frozen --no-group dev
ENV PATH="/code/.venv/bin:$PATH"

WORKDIR /code/app
EXPOSE ${GRANIAN_PORT:-5000}

ENTRYPOINT ["docker-entrypoint.sh"]
