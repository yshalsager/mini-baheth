import asyncio
import importlib
import json

import pytest

from core import SearchComplete, SearchMatch

webapp_module = importlib.import_module('webapp.app')

pytestmark = pytest.mark.django_db


async def _collect(gen):
    return [chunk async for chunk in gen]


def collect_streaming(response):
    return asyncio.run(_collect(response.streaming_content))


class FakeProcessor:
    def __init__(self, payloads):
        self._payloads = payloads

    async def process(self):
        for p in self._payloads:
            yield p


def patch_stream_search(monkeypatch, calls, *, include_pcre=False, payloads=None):
    payloads = payloads or []

    def fake_stream_search(query, directory, file_filters, data_dir, rga_config, use_pcre=False):
        calls.append((query, directory, file_filters, data_dir, use_pcre) if include_pcre else (query, directory, file_filters, data_dir))
        return FakeProcessor(payloads)

    monkeypatch.setattr(webapp_module, 'stream_search', fake_stream_search)


def test_index_lists_first_level_directories(client, temp_data_dir):
    (temp_data_dir / 'alpha').mkdir()
    nested = temp_data_dir / 'nested'
    nested.mkdir()
    (nested / 'deep').mkdir()

    response = client.get('/')
    body = response.content.decode()

    assert response.status_code == 200
    assert '<option value="alpha">' in body
    assert '<option value="nested">' in body
    assert 'nested/deep' not in body


def test_directories_endpoint_honors_limit(client, temp_data_dir):
    for name in ['one', 'two', 'three', 'four']:
        (temp_data_dir / name).mkdir()

    response = client.get('/api/directories', {'limit': 3})
    payload = json.loads(response.content)

    assert response.status_code == 200
    assert payload['directories'][0] == '.'
    assert len(payload['directories']) == 3


def test_file_endpoint_highlights_requested_line(client, temp_data_dir):
    file_path = temp_data_dir / 'notes.txt'
    file_path.write_text('first\nsecond\nthird\n')

    response = client.get('/api/file', {'file': 'notes.txt', 'line_number': 2})
    body = response.content.decode()

    assert response.status_code == 200
    assert 'notes.txt' in body
    assert 'second' in body
    assert 'bg-yellow-100' in body


def test_search_stream_emits_matches_and_completion(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(
        monkeypatch,
        calls,
        payloads=[
            SearchMatch(
                path='notes.txt',
                line_number=5,
                lines='match line',
                submatches=[],
                highlighted_text='match line',
            ),
            SearchComplete(),
        ],
    )

    response = client.get('/api/search', {'query': 'term', 'directory': '.', 'file_filter': '*.txt'})
    chunks = collect_streaming(response)

    assert calls == [('term', '.', ['*.txt'], temp_data_dir)]
    assert chunks[0].startswith(b'data:')
    assert b'"path":"notes.txt"' in chunks[0]
    assert b'"complete":true' in chunks[-1]



def test_search_mode_smart_fast_path(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(monkeypatch, calls, include_pcre=True, payloads=[SearchComplete()])
    response = client.get('/api/search', {'query': 'العربية', 'directory': '.', 'search_mode': 'smart'})
    _ = collect_streaming(response)
    assert calls and calls[0][4] is False
    assert '\\p{M}' not in calls[0][0]


def test_search_mode_ignore_sets_pcre_and_marks(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(monkeypatch, calls, include_pcre=True, payloads=[SearchComplete()])
    response = client.get('/api/search', {'query': 'العربية', 'directory': '.', 'search_mode': 'ignore'})
    _ = collect_streaming(response)
    assert calls and calls[0][4] is True
    assert '\\p{M}' in calls[0][0]


def test_search_mode_require_sets_pcre_and_plus_when_typed(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(monkeypatch, calls, include_pcre=True, payloads=[SearchComplete()])
    # include a fatha after ع
    response = client.get('/api/search', {'query': 'العَر', 'directory': '.', 'search_mode': 'require'})
    _ = collect_streaming(response)
    assert calls and calls[0][4] is True
    assert '\\p{M}' in calls[0][0]
    assert '\\p{M}]+' in calls[0][0] or '\\p{M}+' in calls[0][0]


def test_search_mode_regex_passthrough(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(monkeypatch, calls, include_pcre=True, payloads=[SearchComplete()])
    response = client.get('/api/search', {'query': 'a.*b', 'directory': '.', 'search_mode': 'regex'})
    _ = collect_streaming(response)
    assert calls and calls[0][4] is False
    assert calls[0][0] == 'a.*b'


def test_search_empty_query_returns_empty_body(client):
    response = client.get('/api/search', {'query': '', 'directory': '.'})
    assert response.status_code == 200
    # API endpoints return JSON responses; empty string becomes b'""'
    assert response.content == b'""'


def test_search_multi_filter_parsing_repeated_params(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(monkeypatch, calls, payloads=[SearchComplete()])
    # explicit querystring to ensure repeated params
    response = client.get('/api/search?query=t&directory=.&file_filter=*.txt&file_filter=*.md')
    _ = collect_streaming(response)
    assert calls and calls[0][2] == ['*.txt', '*.md']


def test_search_multi_filter_parsing_comma_separated(client, temp_data_dir, monkeypatch):
    calls = []
    patch_stream_search(monkeypatch, calls, payloads=[SearchComplete()])
    response = client.get('/api/search', {'query': 't', 'directory': '.', 'file_filter': '*.txt,*.md'})
    _ = collect_streaming(response)
    # With a single GET value, server keeps it as one item (no split at this stage)
    assert calls and calls[0][2] == ['*.txt,*.md']


def test_search_file_not_found_streams_error(client, temp_data_dir, monkeypatch):
    def raising_stream_search(*_args, **_kwargs):
        raise FileNotFoundError('missing')

    monkeypatch.setattr(webapp_module, 'stream_search', raising_stream_search)
    response = client.get('/api/search', {'query': 't', 'directory': '.'})
    chunks = collect_streaming(response)
    assert any(b'File not found' in c for c in chunks)
