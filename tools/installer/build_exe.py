#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build cfclient.exe with PyInstaller.
Usage: python build_exe.py
"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
SPEC_FILE = os.path.join(SCRIPT_DIR, 'cfclient.spec')


def main():
    print("=" * 60)
    print(" Building cfclient.exe with PyInstaller")
    print("=" * 60)
    print(f" Spec:   {SPEC_FILE}")
    print(f" Output: {os.path.join(PROJECT_DIR, 'dist', 'cfclient.exe')}")
    print()

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        SPEC_FILE,
    ]
    print(f"Running: {' '.join(cmd)}")
    sys.stdout.flush()

    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("\nPyInstaller build failed!")
        sys.exit(result.returncode)

    exe_path = os.path.join(PROJECT_DIR, 'dist', 'cfclient.exe')
    print(f"\nBuild complete! -> {exe_path}")


if __name__ == '__main__':
    main()
