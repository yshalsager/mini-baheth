#!/usr/bin/env python

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

PYTHON_VERSION = '3.13.8'
PY_STANDALONE_TAG = '20251010'


def detect_target() -> str:
    sysname = platform.system().lower()
    machine = platform.machine().lower()

    if sysname == 'darwin':
        if machine in {'x86_64', 'amd64'}:
            return 'x86_64-apple-darwin'
        if machine in {'arm64', 'aarch64'}:
            return 'aarch64-apple-darwin'
    elif sysname == 'linux':
        if machine in {'x86_64', 'amd64'}:
            return 'x86_64-unknown-linux-gnu'
        if machine in {'arm64', 'aarch64'}:
            return 'aarch64-unknown-linux-gnu'
    elif sysname == 'windows':
        if machine in {'x86_64', 'amd64'}:
            return 'x86_64-pc-windows-msvc'
        if machine in {'arm64', 'aarch64'}:
            return 'aarch64-pc-windows-msvc'

    raise SystemError(f'unsupported platform: {sysname} {machine}')


def build_url(version: str, tag: str, target: str) -> str:
    return (
        f'https://github.com/astral-sh/python-build-standalone/releases/download/{tag}/'
        f'cpython-{version}+{tag}-{target}-install_only_stripped.tar.gz'
    )


def download_and_extract(url: str, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tar_path = Path(tmp) / 'python.tar.gz'
        req = Request(url)
        with urlopen(req) as r, open(tar_path, 'wb') as f:
            size = int(r.headers.get('Content-Length', '0') or 0)
            print(f'downloading: {url}')
            if size:
                mb = size / (1024 * 1024)
                print(f'size: {mb:.1f} MB')
            shutil.copyfileobj(r, f)
        with tarfile.open(tar_path, 'r:gz') as tf:
            tf.extractall(dest_dir, filter='data')


def maybe_fix_macos_lib(dest_dir: Path, version: str) -> None:
    if platform.system().lower() != 'darwin':
        return
    major_minor = '.'.join(version.split('.')[:2])
    lib = dest_dir / 'python' / 'lib' / f'libpython{major_minor}.dylib'
    if lib.exists():
        subprocess.run(
            ['install_name_tool', '-id', f'@rpath/libpython{major_minor}.dylib', str(lib)],
            check=False,
        )


def strip_tk(dest_dir: Path, version: str) -> None:
    py = dest_dir / 'python'
    mm = '.'.join(version.split('.')[:2])

    def rm(p: Path) -> None:
        if p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()

    def rm_glob(base: Path, patterns: list[str]) -> None:
        if not base.exists():
            return
        for pat in patterns:
            for x in base.glob(pat):
                rm(x)

    rm(py / 'tcl')
    rm_glob(
        py / 'DLLs', ['_tkinter.pyd', 'tcl*.dll', 'tk*.dll', 'itcl*.dll', 'itk*.dll', 'tix*.dll']
    )
    rm_glob(py / 'Lib', ['tkinter'])
    site = py / 'lib' / f'python{mm}'
    rm_glob(site, ['tkinter', 'lib-dynload/_tkinter*.so', 'lib-dynload/_tkinter*.dylib'])
    rm_glob(
        py / 'lib',
        [
            'tcl*',
            'tk*',
            'itcl*',
            'itk*',
            'iwidgets*',
            'libtcl*.dylib',
            'libtk*.dylib',
            'libtcl*.so*',
            'libtk*.so*',
        ],
    )


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[1]
    dest = root / 'src-tauri' / 'pyembed'

    version = os.environ.get('PYTHON_VERSION') or '3.13.8'
    tag = os.environ.get('PY_STANDALONE_TAG') or '20251010'
    target = detect_target()
    url = build_url(version, tag, target)

    download_and_extract(url, dest)
    maybe_fix_macos_lib(dest, version)
    strip_tk(dest, version)
    print(dest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
