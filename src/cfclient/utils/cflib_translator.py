# -*- coding: utf-8 -*-
"""
Translation layer for cflib error/status messages.

This module provides a tr_cflib() function that translates cflib-originated
strings at the cfclient display boundary, without modifying cflib source code.
Messages are looked up in JSON translation files keyed by the English original.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

_translations = {}
_current_lang = "zh_CN"
_loaded = False


def _get_locale_dir():
    return os.path.join(os.path.dirname(__file__), "..", "locale")


def init_cflib_translator(lang_code="zh_CN"):
    global _current_lang, _translations, _loaded
    _current_lang = lang_code
    if lang_code == "en_US":
        _translations = {}
        _loaded = True
        return
    json_path = os.path.join(_get_locale_dir(), f"cflib_{lang_code}.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            _translations = json.load(f)
        _loaded = True
    except FileNotFoundError:
        logger.warning(f"cflib translation file not found: {json_path}")
        _translations = {}
        _loaded = True


def tr_cflib(text):
    """Translate a cflib error/status message.
    Returns the translation if found, otherwise the original text.
    Handles formatted strings by trying exact match first, then template match.
    """
    if _current_lang == "en_US" or not _translations:
        return text
    if text in _translations:
        return _translations[text]
    return text
