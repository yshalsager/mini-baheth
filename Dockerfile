ARG PYTHON_VERSION=3.13
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /usr/local/bin/uv

WORKDIR /code
RUN useradd -m appuser && chown -R appuser:appuser /code

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER appuser

WORKDIR /code
COPY pyproject.toml .
COPY uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-group dev
ENV PATH="/code/.venv/bin:$PATH"

WORKDIR /code/app
EXPOSE ${GRANIAN_PORT:-5000}

ENTRYPOINT ["docker-entrypoint.sh"]