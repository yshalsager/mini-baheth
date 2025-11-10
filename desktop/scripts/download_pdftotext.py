#!/usr/bin/env python
from __future__ import annotations

import argparse
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


def download(url: str, dest: Path) -> None:
    req = Request(url, headers={'User-Agent': 'curl/8'})
    with urlopen(req) as r, open(dest, 'wb') as f:  # noqa: S310
        shutil.copyfileobj(r, f)


def find_pdftotext(root: Path, sysname: str, machine: str) -> Path | None:
    prefer: list[str] = []
    if sysname.startswith('win'):
        prefer = ['bin64/pdftotext.exe', 'bin32/pdftotext.exe']
    elif sysname == 'darwin':
        if machine in {'arm64', 'aarch64', 'armv8'}:
            prefer = ['binARM/pdftotext']
        else:
            prefer = ['bin64/pdftotext']
    elif sysname == 'linux':
        # Xpdf publishes bin64 and bin32 for Linux x86; binARM may be absent
        if machine in {'x86_64', 'amd64'}:
            prefer = ['bin64/pdftotext']
        elif machine in {'i386', 'i686'}:
            prefer = ['bin32/pdftotext']

    for pattern in prefer:
        for p in root.glob(f"**/{pattern}"):
            if p.is_file():
                return p

    for name in ['pdftotext.exe', 'pdftotext']:
        for p in root.rglob(name):
            if p.is_file():
                return p
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Fetch Xpdf pdftotext into src-tauri/bin')
    parser.add_argument('--version', default='4.05')
    parser.add_argument('--dest', default='src-tauri/bin')
    parser.add_argument('--require', action='store_true', help='exit non-zero if bundling fails')
    parser.add_argument('--fallback-poppler', action='store_true', help='on Linux ARM, copy /usr/bin/pdftotext if present')
    args = parser.parse_args(argv)

    desktop_root = Path(__file__).resolve().parents[1]
    dest_dir = (desktop_root / args.dest).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    sysname = sys.platform
    machine = platform.machine().lower()

    if sysname.startswith('win'):
        url = f'https://dl.xpdfreader.com/xpdf-tools-win-{args.version}.zip'
        kind = 'zip'
    elif sysname == 'darwin':
        url = f'https://dl.xpdfreader.com/xpdf-tools-mac-{args.version}.tar.gz'
        kind = 'targz'
    elif sysname == 'linux':
        if machine in {'aarch64', 'arm64', 'armv8'}:
            if args.fallback_poppler and Path('/usr/bin/pdftotext').exists():
                target = dest_dir / 'pdftotext'
                shutil.copy2('/usr/bin/pdftotext', target)
                target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                print(f'copied /usr/bin/pdftotext -> {target}')
                return 0
            print('No Xpdf Linux ARM build; skipping bundling on ARM')
            return 1 if args.require else 0
        url = f'https://dl.xpdfreader.com/xpdf-tools-linux-{args.version}.tar.gz'
        kind = 'targz'
    else:
        print(f'Unsupported platform: {sysname}')
        return 1 if args.require else 0

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        archive = tmp / ('pkg.zip' if kind == 'zip' else 'pkg.tar.gz')
        try:
            print(f'Downloading {url}')
            download(url, archive)
        except Exception as e:  # noqa: BLE001
            print(f'Failed to download: {e}')
            return 1 if args.require else 0

        out = tmp / 'xpdf'
        out.mkdir(parents=True, exist_ok=True)
        try:
            if kind == 'zip':
                with zipfile.ZipFile(archive) as z:
                    z.extractall(out)
            else:
                with tarfile.open(archive, 'r:gz') as t:
                    t.extractall(out)
        except Exception as e:  # noqa: BLE001
            print(f'Failed to extract: {e}')
            return 1 if args.require else 0

        exe = find_pdftotext(out, sysname, machine)
        if not exe:
            print('pdftotext not found inside the archive')
            return 1 if args.require else 0

        target = dest_dir / ('pdftotext.exe' if sysname.startswith('win') else 'pdftotext')
        shutil.copy2(exe, target)
        if not sysname.startswith('win'):
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        print(f'Bundled {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
