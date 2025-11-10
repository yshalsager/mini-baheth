from pathlib import Path

from core import build_search_command


def test_build_search_command_adds_pcre_flag(tmp_path: Path):
    cmd = build_search_command('pat', '.', ['*.txt'], tmp_path, None, use_pcre=True)
    assert '-P' in cmd
    assert cmd[-2:] == ['pat', '.']


def test_build_search_command_without_pcre(tmp_path: Path):
    cmd = build_search_command('pat', '.', ['*.txt'], tmp_path, None, use_pcre=False)
    assert '-P' not in cmd
    assert cmd[-2:] == ['pat', '.']

