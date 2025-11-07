#!/usr/bin/env python

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / 'src-tauri' / 'bin'


def which(cmd: str) -> str | None:
    try:
        out = subprocess.check_output(['mise', 'which', cmd], text=True).strip()
        return out if out else None
    except Exception:
        return None


def stage(names: list[str]) -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = which(name)
        if not src:
            continue
        dest = BIN_DIR / Path(src).name
        shutil.copy2(src, dest)
        if os.name != 'nt':
            dest.chmod(dest.stat().st_mode | 0o111)
        print(dest)


def main(argv: list[str]) -> int:
    names = argv[1:] or ['rg', 'rga', 'rga-preproc', 'gron', 'pandoc']
    stage(names)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))

