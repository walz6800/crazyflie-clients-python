# -*- coding: utf-8 -*-
"""
Lightweight translation function for CLI tools (headless, loader, zmq).

Uses JSON-based translation files that work without Qt.
"""
import json
import os

import cfclient

_translations = {}
_current_lang = "en_US"


def _load_translations(lang_code):
    """Load translation JSON for a language."""
    global _translations
    path = os.path.join(cfclient.module_path, "locale", f"cli_{lang_code}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _translations = json.load(f)
    except (IOError, OSError, json.JSONDecodeError):
        _translations = {}


def init_language(lang_code="zh_CN"):
    """Initialize translations for CLI tools."""
    global _current_lang
    _current_lang = lang_code
    if lang_code != "en_US":
        _load_translations(lang_code)


def tr(text):
    """Translate a string. Returns original if no translation found."""
    if _current_lang == "en_US":
        return text
    return _translations.get(text, text)


def current_language():
    return _current_lang
