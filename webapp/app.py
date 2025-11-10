from pathlib import Path

import orjson
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from nanodjango import Django

from core import directories_response, file_response, stream_search, MAX_DEPTH
from core.schemas import (
    DirectoriesRequest,
    FileRequest,
    SearchComplete,
    SearchError,
    SearchMatch,
)
from core.patterns import build_pattern

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / 'templates'
DATA_DIR = ROOT_DIR / 'data'
RGA_CONFIG_PATH = ROOT_DIR / 'rga.config.json'

app = Django(
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [TEMPLATES_DIR],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ]
            },
        }
    ]
)



def get_directories(max_depth: int = MAX_DEPTH) -> list[str]:
    request = DirectoriesRequest(max_depth=max_depth)
    return directories_response(DATA_DIR, request).directories


@app.route('/')
def index(request):
    return render(
        request,
        'index.html',
        {'directories': get_directories(max_depth=1)},
    )


@app.api.get('/search')
async def search(
    request: StreamingHttpResponse,
    query: str,
    directory: str,
    file_filter: str | None = None,
    search_mode: str | None = None,
):
    if not query:
        return ''

    try:
        # Accept multiple file_filter parameters and/or comma-separated values
        filters = request.GET.getlist('file_filter') if hasattr(request, 'GET') else []
        if not filters and file_filter:
            filters = [p.strip() for p in file_filter.split(',') if p.strip()]
        mode = (search_mode or 'smart').strip().lower()
        pattern, need_pcre = build_pattern(mode, query)

        processor = stream_search(
            pattern,
            directory,
            filters,
            DATA_DIR,
            RGA_CONFIG_PATH if RGA_CONFIG_PATH.exists() else None,
            use_pcre=need_pcre,
        )
    except FileNotFoundError:

        async def error_stream():
            yield f'data: {orjson.dumps(SearchError(error="File not found").model_dump()).decode()}\n\n'

        return StreamingHttpResponse(error_stream(), content_type='text/event-stream')

    async def event_stream():
        async for payload in processor.process():
            if isinstance(payload, (SearchMatch, SearchError, SearchComplete)):
                data = payload.model_dump()
            else:
                data = payload  # fallback for unexpected payloads
            yield f'data: {orjson.dumps(data).decode()}\n\n'

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


@app.api.get('/file')
def file(request: HttpRequest, file: str, line_number: int | None = None) -> HttpResponse:
    if not file:
        return HttpResponse(status=400)

    try:
        response = file_response(DATA_DIR, FileRequest(path=file, line_number=line_number))
    except ValueError:
        return HttpResponse(status=400)
    except FileNotFoundError:
        return HttpResponse(status=404)

    return render(
        request,
        'file_modal.html',
        {
            'file': response.file,
            'lines': response.lines,
            'line_number': response.line_number,
        },
    )


@app.api.get('/directories')
def directories(
    request: HttpRequest, q: str = '', limit: int = 200, max_depth: int = MAX_DEPTH
) -> HttpResponse:
    try:
        limit = max(1, min(int(limit or 200), 1000))
    except Exception:  # noqa: BLE001
        limit = 200
    try:
        max_depth = int(max_depth or MAX_DEPTH)
    except Exception:  # noqa: BLE001
        max_depth = MAX_DEPTH

    response = directories_response(
        DATA_DIR,
        DirectoriesRequest(query=q, limit=limit, max_depth=max_depth),
    )

    return HttpResponse(
        orjson.dumps(response.model_dump()),
        content_type='application/json',
    )


__all__ = ['app']
