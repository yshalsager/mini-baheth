from __future__ import annotations

from pathlib import Path

import sys

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

from core import directories_response, file_response, stream_search  # noqa: E402
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

DATA_DIR = PROJECT_ROOT / 'data'
RGA_CONFIG_PATH = PROJECT_ROOT / 'rga.config.json'

commands: Commands = Commands()


class SearchStarted(BaseModel):
    query: str
    directory: str
    file_filter: str


@commands.command()
async def search(body: SearchRequest, app_handle: AppHandle) -> None:
    if not body.query:
        Emitter.emit(app_handle, 'search_complete', SearchComplete())
        return

    Emitter.emit(app_handle, 'search_started', SearchStarted(**body.model_dump()))

    processor = stream_search(
        body.query,
        body.directory,
        body.file_filter,
        DATA_DIR,
        RGA_CONFIG_PATH if RGA_CONFIG_PATH.exists() else None,
    )

    async for payload in processor.process():
        if isinstance(payload, SearchMatch):
            Emitter.emit(app_handle, 'search_match', payload)
        elif isinstance(payload, SearchError):
            Emitter.emit(app_handle, 'search_error', payload)
        elif isinstance(payload, SearchComplete):
            Emitter.emit(app_handle, 'search_complete', payload)


@commands.command()
async def list_directories(body: DirectoriesRequest | None = None) -> DirectoriesResponse:
    request = body or DirectoriesRequest()
    response = directories_response(DATA_DIR, request)
    return response


@commands.command()
async def fetch_file(body: FileRequest) -> FileResponse:
    response = file_response(DATA_DIR, body)
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
]
