from pathlib import Path

import orjson
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from nanodjango import Django

from core import (
    MAX_DEPTH,
    get_directories as core_get_directories,
    read_file_lines,
    stream_search,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
DATA_DIR = ROOT_DIR / "data"
RGA_CONFIG_PATH = ROOT_DIR / "rga.config.json"

app = Django(
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [TEMPLATES_DIR],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        }
    ]
)


def get_directories(max_depth: int = MAX_DEPTH) -> list[str]:
    return core_get_directories(DATA_DIR, max_depth=max_depth)


@app.route("/")
def index(request):
    return render(
        request,
        "index.html",
        {"directories": get_directories(max_depth=1)},
    )


@app.api.get("/search")
async def search(
    request: StreamingHttpResponse, query: str, directory: str, file_filter: str
):
    if not query:
        return ""

    try:
        processor = stream_search(
            query,
            directory,
            file_filter,
            DATA_DIR,
            RGA_CONFIG_PATH if RGA_CONFIG_PATH.exists() else None,
        )
    except FileNotFoundError:

        async def error_stream():
            yield f"data: {orjson.dumps({'error': 'File not found'}).decode()}\n\n"

        return StreamingHttpResponse(error_stream(), content_type="text/event-stream")

    async def event_stream():
        async for payload in processor.process():
            yield f"data: {orjson.dumps(payload).decode()}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


@app.api.get("/file")
def file(
    request: HttpRequest, file: str, line_number: int | None = None
) -> HttpResponse:
    if not file:
        return HttpResponse(status=400)

    path = DATA_DIR / file
    if not path.exists():
        return HttpResponse(status=404)

    lines = read_file_lines(path)

    return render(
        request,
        "file_modal.html",
        {
            "file": path.relative_to(DATA_DIR),
            "lines": lines,
            "line_number": line_number,
        },
    )


@app.api.get("/directories")
def directories(
    request: HttpRequest, q: str = "", limit: int = 200, max_depth: int = MAX_DEPTH
) -> HttpResponse:
    try:
        limit = max(1, min(int(limit or 200), 1000))
    except Exception:  # noqa: BLE001
        limit = 200
    try:
        max_depth = int(max_depth or MAX_DEPTH)
    except Exception:  # noqa: BLE001
        max_depth = MAX_DEPTH

    dirs = get_directories(max_depth=max_depth)
    if q:
        ql = q.lower()
        dirs = [d for d in dirs if ql in d.lower()]

    if "." in dirs:
        dirs = ["."] + [d for d in dirs if d != "."]

    return HttpResponse(
        orjson.dumps({"directories": dirs[:limit]}),
        content_type="application/json",
    )


__all__ = ["app"]
