import asyncio
import importlib
import json

import pytest

from core import SearchComplete, SearchMatch

webapp_module = importlib.import_module('webapp.app')

pytestmark = pytest.mark.django_db


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

    class FakeProcessor:
        async def process(self):
            yield SearchMatch(
                path='notes.txt',
                line_number=5,
                lines='match line',
                submatches=[],
                highlighted_text='match line',
            )
            yield SearchComplete()

    def fake_stream_search(query, directory, file_filter, data_dir, rga_config):
        calls.append((query, directory, file_filter, data_dir))
        return FakeProcessor()

    monkeypatch.setattr(webapp_module, 'stream_search', fake_stream_search)

    response = client.get(
        '/api/search',
        {'query': 'term', 'directory': '.', 'file_filter': '*.txt'},
    )

    async def collect(gen):
        return [chunk async for chunk in gen]

    chunks = asyncio.run(collect(response.streaming_content))

    assert calls == [('term', '.', '*.txt', temp_data_dir)]
    assert chunks[0].startswith(b'data:')
    assert b'"path":"notes.txt"' in chunks[0]
    assert b'"complete":true' in chunks[-1]
