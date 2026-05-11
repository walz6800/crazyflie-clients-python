#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full build: cfclient.exe + Inno Setup installer.
Usage: python build_installer.py
"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
SPEC_FILE = os.path.join(SCRIPT_DIR, 'cfclient.spec')
SETUP_FILE = os.path.join(SCRIPT_DIR, 'setup.iss')
INNO_SETUP = r'C:\Users\Administrator\AppData\Local\Programs\Inno Setup 6\ISCC.exe'


def step1_build_exe():
    print("=" * 60)
    print(" [1/2] Building FormflieHub.exe with PyInstaller")
    print("=" * 60)
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', SPEC_FILE]
    print(f"Running: {' '.join(cmd)}")
    sys.stdout.flush()
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("\nPyInstaller build failed!")
        sys.exit(result.returncode)
    print("OK: FormflieHub.exe built.\n")


def step2_build_installer():
    print("=" * 60)
    print(" [2/2] Building installer with Inno Setup")
    print("=" * 60)
    if not os.path.exists(INNO_SETUP):
        print(f"WARNING: Inno Setup not found at {INNO_SETUP}")
        print("Please install Inno Setup 6 (https://jrsoftware.org/isinfo.php)")
        print(f"Then manually compile: {SETUP_FILE}")
        return
    cmd = [INNO_SETUP, SETUP_FILE]
    print(f"Running: {' '.join(cmd)}")
    sys.stdout.flush()
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print("\nInno Setup build failed!")
        sys.exit(result.returncode)
    installer_path = os.path.join(PROJECT_DIR, 'dist', 'installer', 'FormflieHub_Setup.exe')
    print(f"\nOK: Installer built -> {installer_path}")


def main():
    step1_build_exe()
    step2_build_installer()
    print("\nAll done!")


if __name__ == '__main__':
    main()
