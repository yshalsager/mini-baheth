ARG PYTHON_VERSION=3.13
ARG RGA_VERSION=0.10.9
ARG UV_VERSION=0.9.5

# ===== STAGE 1: Build system dependencies =====
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim-trixie AS builder
ARG RGA_VERSION

# Install system dependencies (ripgrep, antiword, pandoc, gron, curl for downloads)
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  ca-certificates \
  ripgrep \
  antiword \
  pandoc \
  gron \
  xz-utils \
  && rm -rf /var/lib/apt/lists/*

# Install ripgrep-all (rga) with architecture detection
RUN set -eux; \
  arch="$(dpkg --print-architecture)"; \
  case "$arch" in \
  amd64) target="x86_64-unknown-linux-musl" ;; \
  arm64) target="arm-unknown-linux-gnueabihf" ;; \
  *) echo "unsupported arch: $arch"; exit 1 ;; \
  esac; \
  tmpdir="$(mktemp -d)"; cd "$tmpdir"; \
  url="https://github.com/phiresky/ripgrep-all/releases/download/v${RGA_VERSION}/ripgrep_all-v${RGA_VERSION}-${target}.tar.gz"; \
  curl -fsSL -o rga.tar "$url"; \
  tar -xf rga.tar; \
  binpath="$(find . -maxdepth 2 -type f -name rga | head -n1)"; \
  preprocpath="$(find . -maxdepth 2 -type f -name rga-preproc | head -n1 || true)"; \
  install -m 0755 "$binpath" /usr/local/bin/rga; \
  if [ -n "$preprocpath" ]; then install -m 0755 "$preprocpath" /usr/local/bin/rga-preproc; fi; \
  cd /; rm -rf "$tmpdir"; \
  rga --version

# ===== STAGE 2: UV installation =====
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-stage

# ===== STAGE 3: Final application image =====
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim-trixie

# Copy system dependencies and tools from builder stage
COPY --from=builder /usr/local/bin/rga /usr/local/bin/rga
COPY --from=builder /usr/local/bin/rga-preproc /usr/local/bin/rga-preproc
COPY --from=builder /usr/bin/rg /usr/bin/rg
COPY --from=builder /usr/bin/antiword /usr/bin/antiword
COPY --from=builder /usr/bin/pandoc /usr/bin/pandoc
COPY --from=builder /usr/bin/gron /usr/bin/gron

# Install runtime deps for PDF support
RUN apt-get update && apt-get install -y --no-install-recommends \
  poppler-utils \
  && rm -rf /var/lib/apt/lists/*

# Copy UV from uv-stage
COPY --from=uv-stage /uv /usr/local/bin/uv

# Create non-root user
WORKDIR /code
RUN useradd -m appuser && chown -R appuser:appuser /code

# Copy application files
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER appuser

# Copy Python project files
COPY pyproject.toml .
COPY uv.lock .

# Install Python dependencies
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-group dev
ENV PATH="/code/.venv/bin:$PATH"

WORKDIR /code/app
EXPOSE ${GRANIAN_PORT:-5000}

ENTRYPOINT ["docker-entrypoint.sh"]
