#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update translation files from source code.

Run this after adding new tr() calls or modifying .ui files.
It will:
1. Scan Python and .ui files with pylupdate6
2. Convert the .ts output to our .json translation format
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(PROJECT_DIR, 'src', 'cfclient')
LOCALE_DIR = os.path.join(SRC_DIR, 'locale')
TS_FILE = os.path.join(LOCALE_DIR, 'cfclient_zh_CN.ts')
JSON_FILE = os.path.join(LOCALE_DIR, 'cfclient_zh_CN.json')


def run_pylupdate():
    """Extract translatable strings from source files."""
    print("Extracting translatable strings with pylupdate6...")

    python_files = []
    for root in ['src/cfclient', 'src/cfloader', 'src/cfzmq']:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith('.py'):
                    python_files.append(os.path.join(dirpath, fn))

    ui_files = []
    for dirpath, _, filenames in os.walk('src/cfclient/ui'):
        for fn in filenames:
            if fn.endswith('.ui'):
                ui_files.append(os.path.join(dirpath, fn))

    cmd = [
        'pylupdate6',
        '-ts', TS_FILE,
        '--no-obsolete',
    ] + python_files + ui_files

    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print("pylupdate6 failed:\n", result.stderr)
        if "An unexpected error occurred" in result.stderr:
            print("Try running on individual file groups.")
        return False
    print(result.stdout)
    return True


def ts_to_json():
    """Convert .ts XML to our JSON translation format."""
    if not os.path.exists(TS_FILE):
        print(f".ts file not found: {TS_FILE}")
        return False

    existing = {}
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    tree = ET.parse(TS_FILE)
    root = tree.getroot()
    new_translations = {}

    for context in root.findall('context'):
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            if source is not None and source.text:
                src_text = source.text.strip()
                if not src_text:
                    continue
                trans_text = ''
                if translation is not None and translation.text:
                    trans_text = translation.text.strip()
                if trans_text:
                    new_translations[src_text] = trans_text
                elif src_text in existing:
                    new_translations[src_text] = existing[src_text]
                else:
                    new_translations[src_text] = src_text

    sorted_translations = dict(sorted(new_translations.items()))

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_translations, f, ensure_ascii=False, indent=2)

    newly = sum(1 for k in sorted_translations if k not in existing)
    updated = sum(1 for k in sorted_translations if k in existing)
    print(f"Written {len(sorted_translations)} translations "
          f"({updated} existing, {newly} new) to {JSON_FILE}")
    return True


if __name__ == "__main__":
    success = True
    try:
        if run_pylupdate():
            print(".ts file updated.")
        else:
            print("Skipping .ts update (pylupdate6 may not be available).")
    except FileNotFoundError:
        print("pylupdate6 not found, skipping .ts generation.")

    ts_to_json()
