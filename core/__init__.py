from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import time
from collections.abc import AsyncGenerator, Iterable
from pathlib import Path
from shutil import which
from typing import Any

import orjson

RGA_FILE_FILTERS: tuple[str, ...] = ("*.doc", "*.docx", "*.json", "*.md")
DIR_CACHE_TTL = 60
MAX_DEPTH = 3

_dir_cache: dict[tuple[Path, int], tuple[float, list[str]]] = {}


def highlight_matches(text: str, submatches: list[dict[str, dict[str, str]]]) -> str:
    for item in submatches:
        text = text.replace(
            item["match"]["text"],
            f'<span class="bg-yellow-200">{item["match"]["text"]}</span>',
        )
    return text.strip()


def build_search_command(
    query: str,
    directory: str,
    file_filter: str,
    data_dir: Path,
    rga_config: Path | None = None,
) -> list[str]:
    tool = "rga" if file_filter in RGA_FILE_FILTERS else "rg"
    binary = which(tool)
    if not binary:
        raise FileNotFoundError(f"{tool} not found on PATH")

    cmd: list[str] = [binary]
    if tool == "rga" and rga_config and rga_config.exists():
        cmd.append(f"--rga-config-file={str(rga_config)}")

    cmd.extend(
        [
            "--json",
            "--max-count",
            "100",
            "-m",
            "500",
            "--no-ignore-vcs",
            "-C",
            "1",
            "--follow",
        ]
    )

    if directory:
        pattern = f"{directory}/**" if directory != "." else "**/"
        cmd.extend(["-g", pattern])

    if file_filter:
        if directory:
            last = cmd.pop()
            cmd.append(f"{last}{'/' if directory != '.' else ''}{file_filter}")
        else:
            cmd.extend(["-g", file_filter])

    cmd.append(query)
    return cmd


class ResultStreamProcessor:
    def __init__(self, command: Iterable[str], data_dir: Path):
        self.command = list(command)
        self.data_dir = data_dir
        self.previous_match: dict[str, Any] | None = None
        self.context_before = ""
        self.proc: asyncio.subprocess.Process | None = None

    async def process(self) -> AsyncGenerator[dict[str, Any], None]:
        try:
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
                    logging.error("JSON decode error: %s", exc)
                    continue
                except Exception as exc:  # noqa: BLE001
                    logging.error("Error decoding search output: %s", exc)
                    continue

                match_type = result.get("type")
                if match_type == "match":
                    payload = self._handle_match(result)
                    if payload:
                        yield payload
                elif match_type == "context":
                    payload = self._handle_context(result)
                    if payload:
                        yield payload

            if self.previous_match:
                yield self.previous_match

            yield {"complete": True}
        except Exception as exc:  # noqa: BLE001
            logging.error("Stream processing error: %s", exc)
            yield {"error": str(exc)}
        finally:
            if self.proc:
                try:
                    await asyncio.wait_for(self.proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    self.proc.terminate()
                    await self.proc.wait()

    def _handle_match(self, result: dict[str, Any]) -> dict[str, Any] | None:
        data = result.get("data", {})
        match_payload = {
            "path": data.get("path", {}).get("text", ""),
            "line_number": data.get("line_number", 0),
            "lines": data.get("lines", {}).get("text", ""),
            "submatches": data.get("submatches", []),
            "context_before": "",
            "context_after": "",
            "highlighted_text": highlight_matches(
                data.get("lines", {}).get("text", ""),
                data.get("submatches", []),
            ),
        }

        if self.context_before:
            match_payload["context_before"] = self.context_before
            self.context_before = ""

        if self.previous_match:
            payload = self.previous_match
            self.previous_match = match_payload
            return payload

        self.previous_match = match_payload
        return None

    def _handle_context(self, result: dict[str, Any]) -> dict[str, Any] | None:
        data = result.get("data", {})
        text = data.get("lines", {}).get("text", "").strip()

        if self.previous_match:
            self.previous_match["context_after"] = text
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

        rel_str = "." if str(rel) == "." else str(rel)
        depth = 0 if rel_str == "." else len(rel.parts)
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


def read_file_lines(path: Path) -> list[str]:
    try:
        ext = path.suffix.lower()
        if ext == ".docx" and which("pandoc"):
            proc = subprocess.run(
                ["pandoc", "-f", "docx", "-t", "plain", str(path)],
                capture_output=True,
                check=False,
            )
            text = proc.stdout.decode("utf-8", errors="replace")
            return text.splitlines()
        if ext == ".doc" and which("antiword"):
            proc = subprocess.run(
                ["antiword", str(path)],
                capture_output=True,
                check=False,
            )
            text = proc.stdout.decode("utf-8", errors="replace")
            return text.splitlines()

        return path.read_text(errors="replace").splitlines()
    except Exception:  # noqa: BLE001
        return path.read_text(errors="replace").splitlines()
