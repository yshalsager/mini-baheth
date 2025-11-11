#!/usr/bin/env python

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
import stat


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print('> ' + ' '.join(cmd))
    subprocess.run(cmd, check=True, env=env)


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    project_name = 'mini-baheth-desktop'

    def mise_which(name: str) -> str | None:
        try:
            out = subprocess.check_output(['mise', 'which', name], text=True).strip()
            return out or None
        except Exception:
            return None

    def stage_tools(names: list[str]) -> None:
        bin_dir = root / 'src-tauri' / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)
        for n in names:
            src = mise_which(n)
            if not src:
                continue
            dest = bin_dir / Path(src).name
            shutil.copy2(src, dest)
            if os.name != 'nt':
                dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(dest)

    stage_tools(['rg', 'rga', 'rga-preproc', 'gron', 'pandoc'])

    # Stage rga config if present at repo root
    repo_root = root.parent
    rga_src = repo_root / 'rga.config.json'
    rga_dst = root / 'src-tauri' / 'rga.config.json'
    if rga_src.exists():
        shutil.copy2(rga_src, rga_dst)

    # Environment for embedding
    env = os.environ.copy()
    env['PYTAURI_STANDALONE'] = '1'

    if platform.system().lower() == 'windows':
        pybin = root / 'src-tauri' / 'pyembed' / 'python' / 'python.exe'
    else:
        pybin = root / 'src-tauri' / 'pyembed' / 'python' / 'bin' / 'python3'
        pylib = root / 'src-tauri' / 'pyembed' / 'python' / 'lib'
        if platform.system().lower() == 'darwin':
            env['RUSTFLAGS'] = (
                f' -C link-arg=-Wl,-rpath,@executable_path/../Resources/lib -L {pylib}'
            )
        elif platform.system().lower() == 'linux':
            env['RUSTFLAGS'] = (
                f' -C link-arg=-Wl,-rpath,$ORIGIN/../lib/{project_name}/lib -L {pylib}'
            )

    env['PYO3_PYTHON'] = str(pybin)

    # Install core (non-editable) and desktop package into embedded Python
    run(
        [
            'mise',
            'x',
            'uv',
            '--',
            'uv',
            'pip',
            'install',
            '--no-sources',
            '--exact',
            '--compile-bytecode',
            f'--python={pybin}',
            '../core',
        ],
        env=env,
    )

    run(
        [
            'mise',
            'x',
            'uv',
            '--',
            'uv',
            'pip',
            'install',
            '--no-sources',
            '--exact',
            '--compile-bytecode',
            f'--python={pybin}',
            f'--reinstall-package={project_name}',
            './src-tauri',
        ],
        env=env,
    )

    # Optionally refresh platform icons from SVG if present
    svg = root / 'src-tauri' / 'icons' / 'source.svg'
    if svg.exists():
        try:
            # Generate platform icons next to tauri.conf.json
            run(['mise', 'x', 'pnpm', '--', 'pnpm', 'tauri', 'icon', str(svg), '-o', 'src-tauri/icons'])
        except Exception:
            pass

    # Build tauri bundle
    verbose_flags = []
    if os.environ.get('DEBUG') or os.environ.get('CI'):
        verbose_flags = ['-v', '-v']

    if platform.system().lower() == 'windows' and platform.machine().lower() in {
        'arm64',
        'aarch64',
    }:
        cmd = [
            'mise',
            'x',
            'pnpm',
            '--',
            'pnpm',
            'dlx',
            '@tauri-apps/cli-win32-arm64-msvc',
            'tauri',
            'build',
            *verbose_flags,
            '--config=src-tauri/tauri.bundle.json',
            '--',
            '--profile',
            'bundle-release',
        ]
    else:
        cmd = [
            'mise',
            'x',
            'pnpm',
            '--',
            'pnpm',
            'tauri',
            'build',
            *verbose_flags,
            '--config=src-tauri/tauri.bundle.json',
            '--',
            '--profile',
            'bundle-release',
        ]
    run(cmd, env=env)

    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
