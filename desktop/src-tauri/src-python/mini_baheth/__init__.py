from __future__ import annotations

import asyncio
import sys
from contextlib import suppress
from os import environ, pathsep
from pathlib import Path
from uuid import uuid4

from anyio.from_thread import start_blocking_portal
from pydantic import BaseModel
from pytauri import (
    AppHandle,
    Commands,
    Emitter,
    builder_factory,
    context_factory,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ensure bundled binaries are on PATH when launched from Finder
with suppress(Exception):
    exe = Path(sys.executable).resolve()
    for p in exe.parents:
        if p.name == 'Resources' and p.is_dir():
            bin_dir = p / 'bin'
            if bin_dir.exists():
                current = environ.get('PATH', '')
                environ['PATH'] = str(bin_dir) + (pathsep + current if current else '')
            break

from core import (  # noqa: E402
    ResultStreamProcessor,
    directories_response,
    file_response,
    stream_search,
)
from core.schemas import (  # noqa: E402
    DirectoriesRequest,
    DirectoriesResponse,
    FileRequest,
    FileResponse,
    SearchComplete,
    SearchError,
    SearchMatch,
    SearchRequest,
)

DATA_ROOT = None
RGA_CONFIG_PATH = PROJECT_ROOT / 'rga.config.json'

_search_lock = asyncio.Lock()
_active_processor: ResultStreamProcessor | None = None

commands: Commands = Commands()


class SearchStarted(BaseModel):
    query: str
    directory: str
    file_filter: str
    request_id: str


@commands.command()
async def search(body: SearchRequest, app_handle: AppHandle) -> None:
    global _active_processor

    if not body.query:
        request_id = body.request_id or uuid4().hex
        async with _search_lock:
            if _active_processor:
                await _active_processor.cancel()
                _active_processor = None
        Emitter.emit(app_handle, 'search_complete', SearchComplete(request_id=request_id))
        return

    request_id = body.request_id or uuid4().hex

    async with _search_lock:
        if _active_processor and _active_processor is not None:
            await _active_processor.cancel()
            _active_processor = None

        processor = stream_search(
            body.query,
            body.directory,
            body.file_filter,
            DATA_ROOT,
            RGA_CONFIG_PATH if RGA_CONFIG_PATH.exists() else None,
        )
        _active_processor = processor

    Emitter.emit(
        app_handle,
        'search_started',
        SearchStarted(
            query=body.query,
            directory=body.directory,
            file_filter=body.file_filter,
            request_id=request_id,
        ),
    )

    async for payload in processor.process():
        enriched = payload.model_copy(update={'request_id': request_id})
        if isinstance(payload, SearchMatch):
            Emitter.emit(app_handle, 'search_match', enriched)
        elif isinstance(payload, SearchError):
            Emitter.emit(app_handle, 'search_error', enriched)
        elif isinstance(payload, SearchComplete):
            Emitter.emit(app_handle, 'search_complete', enriched)

    async with _search_lock:
        if _active_processor is processor:
            _active_processor = None


@commands.command()
async def list_directories(body: DirectoriesRequest | None = None) -> DirectoriesResponse:
    if not DATA_ROOT:
        return DirectoriesResponse(directories=[])
    request = body or DirectoriesRequest()
    response = directories_response(DATA_ROOT, request)
    return response


@commands.command()
async def fetch_file(body: FileRequest) -> FileResponse:
    response = file_response(DATA_ROOT, body)
    return response


def main() -> int:
    with start_blocking_portal('asyncio') as portal:
        app = builder_factory().build(
            context=context_factory(),
            invoke_handler=commands.generate_handler(portal),
        )
        return app.run_return()


__all__ = [
    'commands',
    'main',
    'SearchStarted',
    'get_data_root',
    'set_data_root',
]


@commands.command()
async def get_data_root() -> str:
    return str(DATA_ROOT)


@commands.command()
async def set_data_root(body: dict[str, str]) -> str:
    path = body.get('path', '')
    if not path:
        return
    candidate = Path(path).expanduser()
    if not candidate.exists() or not candidate.is_dir():
        raise FileNotFoundError(path)
    global DATA_ROOT
    DATA_ROOT = candidate.resolve()
    return str(DATA_ROOT)
