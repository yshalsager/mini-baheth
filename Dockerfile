ARG PYTHON_VERSION=3.13
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /usr/local/bin/uv

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
    
WORKDIR /code
COPY pyproject.toml .
COPY uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen
ENV PATH="/code/.venv/bin:$PATH"

WORKDIR /code/app
EXPOSE ${API_PORT:-5000}
CMD ["granian", "--interface", "asginl", "--host", "0.0.0.0", "--port", "${API_PORT:-5000}", "--workers", "${API_WORKERS:-4}", "app:app"]
