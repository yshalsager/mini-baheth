from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    directory: str = '.'
    file_filters: list[str] = Field(default_factory=list)
    request_id: str | None = None


class SearchMatch(BaseModel):
    path: str
    line_number: int
    lines: str
    submatches: list[dict[str, Any]] = Field(default_factory=list)
    context_before: str = ''
    context_after: str = ''
    highlighted_text: str = ''
    request_id: str | None = None


class SearchError(BaseModel):
    error: str
    request_id: str | None = None


class SearchComplete(BaseModel):
    complete: bool = True
    request_id: str | None = None


SearchEvent = SearchMatch | SearchError | SearchComplete


class DirectoriesRequest(BaseModel):
    query: str = ''
    limit: int = 200
    max_depth: int | None = None


class DirectoriesResponse(BaseModel):
    directories: list[str]


class FileRequest(BaseModel):
    path: str
    line_number: int | None = None


class FileResponse(BaseModel):
    file: str
    lines: list[str]
    line_number: int | None = None


__all__ = [
    'DirectoriesRequest',
    'DirectoriesResponse',
    'FileRequest',
    'FileResponse',
    'SearchComplete',
    'SearchError',
    'SearchEvent',
    'SearchMatch',
    'SearchRequest',
]
