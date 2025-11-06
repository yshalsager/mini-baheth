from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import time
from collections.abc import AsyncGenerator, Iterable
from contextlib import suppress
from pathlib import Path
from shutil import which
from typing import Any

import orjson

from core.schemas import (
    DirectoriesRequest,
    DirectoriesResponse,
    FileRequest,
    FileResponse,
    SearchComplete,
    SearchError,
    SearchEvent,
    SearchMatch,
    SearchRequest,
)

RGA_FILE_FILTERS: tuple[str, ...] = ('*.doc', '*.docx', '*.json', '*.md')
DIR_CACHE_TTL = 60
MAX_DEPTH = 3

_dir_cache: dict[tuple[Path, int], tuple[float, list[str]]] = {}


def highlight_matches(text: str, submatches: list[dict[str, dict[str, str]]]) -> str:
    for item in submatches:
        text = text.replace(
            item['match']['text'],
            f'<span class="bg-yellow-200">{item["match"]["text"]}</span>',
        )
    return text.strip()


def resolve_data_path(data_dir: Path, relative: str) -> Path:
    candidate = (data_dir / relative).resolve()
    data_root = data_dir.resolve()
    if candidate == data_root:
        return candidate
    if data_root not in candidate.parents:
        raise ValueError('path must stay within data directory')
    return candidate


def _normalize_directory(directory: str, data_dir: Path) -> str:
    normalized = (directory or '').strip()
    if not normalized or normalized == '.':
        return '.'

    resolved = resolve_data_path(data_dir, normalized)
    if resolved == data_dir.resolve():
        return '.'

    return str(resolved.relative_to(data_dir))


def _find_tool(tool: str) -> str | None:
    if found := which(tool):
        return found
    with suppress(Exception):
        exe = Path(sys.executable).resolve()
        for p in exe.parents:
            if p.name == 'Resources' and p.is_dir():
                cand = p / 'bin' / tool
                if cand.exists() and os.access(cand, os.X_OK):
                    return str(cand)
                break
    return None


def build_search_command(
    query: str,
    directory: str,
    file_filter: str,
    data_dir: Path,
    rga_config: Path | None = None,
) -> list[str]:
    tool = 'rga' if file_filter in RGA_FILE_FILTERS else 'rg'
    binary = _find_tool(tool)
    if not binary:
        raise FileNotFoundError(f'{tool} not found on PATH')

    cmd: list[str] = [binary]
    if tool == 'rga' and rga_config and rga_config.exists():
        cmd.append(f'--rga-config-file={str(rga_config)}')

    cmd.extend(
        [
            '--json',
            '--max-count',
            '100',
            '-m',
            '500',
            '--no-ignore-vcs',
            '-C',
            '1',
            '--follow',
        ]
    )

    target_dir = _normalize_directory(directory, data_dir)

    if file_filter:
        pattern = f'**/{file_filter}' if target_dir == '.' else f'{target_dir}/**/{file_filter}'
        cmd.extend(['-g', pattern])
    elif target_dir != '.':
        cmd.extend(['-g', f'{target_dir}/**'])

    cmd.append(query)
    cmd.append(target_dir)
    return cmd


class ResultStreamProcessor:
    def __init__(self, command: Iterable[str], data_dir: Path):
        self.command = list(command)
        self.data_dir = data_dir
        self.previous_match: SearchMatch | None = None
        self.context_before = ''
        self.proc: asyncio.subprocess.Process | None = None
        self.cancelled = False

    async def process(self) -> AsyncGenerator[SearchEvent, None]:
        try:
            self.cancelled = False
            self.proc = await asyncio.create_subprocess_exec(
                *self.command,
                cwd=self.data_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            assert self.proc.stdout is not None
            async for line in self.proc.stdout:
                try:
                    result = orjson.loads(line.decode())
                except orjson.JSONDecodeError as exc:
                    logging.error('JSON decode error: %s', exc)
                    continue
                except Exception as exc:  # noqa: BLE001
                    logging.error('Error decoding search output: %s', exc)
                    continue

                match_type = result.get('type')
                if match_type == 'match':
                    payload = self._handle_match(result)
                    if payload:
                        yield payload
                elif match_type == 'context':
                    payload = self._handle_context(result)
                    if payload:
                        yield payload

            if self.previous_match:
                if not self.cancelled:
                    yield self.previous_match

            if not self.cancelled:
                yield SearchComplete()
        except Exception as exc:  # noqa: BLE001
            logging.error('Stream processing error: %s', exc)
            yield SearchError(error=str(exc))
        finally:
            if self.proc:
                try:
                    await asyncio.wait_for(self.proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    self.proc.terminate()
                    await self.proc.wait()

    async def cancel(self) -> None:
        self.cancelled = True
        if not self.proc:
            return
        if self.proc.returncode is None:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=2)
            except asyncio.TimeoutError:
                self.proc.kill()
                await self.proc.wait()

    def _handle_match(self, result: dict[str, Any]) -> SearchMatch | None:
        data = result.get('data', {})
        match_payload = SearchMatch(
            path=data.get('path', {}).get('text', ''),
            line_number=data.get('line_number', 0),
            lines=data.get('lines', {}).get('text', ''),
            submatches=data.get('submatches', []),
            highlighted_text=highlight_matches(
                data.get('lines', {}).get('text', ''),
                data.get('submatches', []),
            ),
        )

        if self.context_before:
            match_payload.context_before = self.context_before
            self.context_before = ''

        if self.previous_match:
            payload = self.previous_match
            self.previous_match = match_payload
            return payload

        self.previous_match = match_payload
        return None

    def _handle_context(self, result: dict[str, Any]) -> SearchMatch | None:
        data = result.get('data', {})
        text = data.get('lines', {}).get('text', '').strip()

        if self.previous_match:
            self.previous_match.context_after = text
            payload = self.previous_match
            self.previous_match = None
            return payload

        self.context_before = text
        return None


def stream_search(
    query: str,
    directory: str,
    file_filter: str,
    data_dir: Path,
    rga_config: Path | None = None,
) -> ResultStreamProcessor:
    command = build_search_command(query, directory, file_filter, data_dir, rga_config)
    return ResultStreamProcessor(command, data_dir)


def get_directories(
    data_dir: Path,
    max_depth: int = MAX_DEPTH,
    ttl: int = DIR_CACHE_TTL,
) -> list[str]:
    key = (data_dir.resolve(), max_depth)
    now = time.time()
    cached = _dir_cache.get(key)
    if cached and now - cached[0] < ttl:
        return cached[1]

    dirs: list[str] = []
    visited: set[str] = set()

    for current, dirnames, _ in os.walk(data_dir, followlinks=True):
        # TODO: use pathlib.walk instead
        resolved = Path(current).resolve()
        if resolved in visited:
            dirnames[:] = []
            continue
        visited.add(resolved)

        try:
            rel = Path(current).relative_to(data_dir)
        except ValueError:
            dirnames[:] = []
            continue

        rel_str = '.' if str(rel) == '.' else str(rel)
        depth = 0 if rel_str == '.' else len(rel.parts)
        dirs.append(rel_str)

        if depth >= max_depth:
            dirnames[:] = []

    seen: set[str] = set()
    ordered: list[str] = []
    for item in dirs:
        if item not in seen:
            seen.add(item)
            ordered.append(item)

    _dir_cache[key] = (now, ordered)
    return ordered


def directories_response(data_dir: Path, request: DirectoriesRequest) -> DirectoriesResponse:
    try:
        limit = max(1, min(request.limit, 1000))
    except Exception:  # noqa: BLE001
        limit = 200

    max_depth = request.max_depth or MAX_DEPTH

    directories = get_directories(data_dir, max_depth=max_depth)
    if request.query:
        term = request.query.lower()
        directories = [item for item in directories if term in item.lower()]

    if '.' in directories:
        directories = ['.'] + [item for item in directories if item != '.']

    return DirectoriesResponse(directories=directories[:limit])


def read_file_lines(path: Path) -> list[str]:
    try:
        ext = path.suffix.lower()
        if ext == '.docx' and which('pandoc'):
            proc = subprocess.run(
                ['pandoc', '-f', 'docx', '-t', 'plain', str(path)],
                capture_output=True,
                check=False,
            )
            text = proc.stdout.decode('utf-8', errors='replace')
            return text.splitlines()
        if ext == '.doc' and which('antiword'):
            proc = subprocess.run(
                ['antiword', str(path)],
                capture_output=True,
                check=False,
            )
            text = proc.stdout.decode('utf-8', errors='replace')
            return text.splitlines()

        return path.read_text(errors='replace').splitlines()
    except Exception:  # noqa: BLE001
        return path.read_text(errors='replace').splitlines()


def file_response(data_dir: Path, request: FileRequest) -> FileResponse:
    resolved = resolve_data_path(data_dir, request.path)
    if not resolved.exists():
        raise FileNotFoundError(request.path)

    lines = read_file_lines(resolved)

    return FileResponse(
        file=str(resolved.relative_to(data_dir)),
        lines=lines,
        line_number=request.line_number,
    )


__all__ = [
    'DIR_CACHE_TTL',
    'MAX_DEPTH',
    'RGA_FILE_FILTERS',
    'DirectoriesRequest',
    'DirectoriesResponse',
    'FileRequest',
    'FileResponse',
    'ResultStreamProcessor',
    'SearchComplete',
    'SearchError',
    'SearchEvent',
    'SearchMatch',
    'SearchRequest',
    'build_search_command',
    'directories_response',
    'file_response',
    'get_directories',
    'highlight_matches',
    'read_file_lines',
    'resolve_data_path',
    'stream_search',
]
