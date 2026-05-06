# -*- coding: utf-8 -*-
"""
Internationalization manager for the Crazyflie client.

Provides runtime language switching for all tools.
Uses Qt's QTranslator system with .qm (binary) or .json fallback.
"""
import json
import logging
import os
from PyQt6.QtCore import QLocale, QTranslator
from PyQt6.QtWidgets import QApplication

import cfclient

logger = logging.getLogger(__name__)

LANGUAGES = {
    "zh_CN": "中文",
    "en_US": "English",
}


class JsonTranslator(QTranslator):
    """QTranslator subclass that loads translations from a JSON file."""

    def __init__(self, translations, parent=None):
        super().__init__(parent)
        self._translations = translations  # dict: "context\x00text" -> translated

    def translate(self, context, source_text, disambiguation=None, n=-1):
        key = f"{context}\x00{source_text}"
        if key in self._translations:
            return self._translations[key]
        # Try without context (Qt sometimes calls with empty context)
        if source_text in self._translations:
            return self._translations[source_text]
        # Return None so Qt falls back to source text (empty string would suppress it)
        return None


class I18nManager:
    """Singleton manager for internationalization."""

    _instance = None
    _current_lang = "en_US"
    _translators = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._locale_dir = os.path.join(cfclient.module_path, "locale")

    @classmethod
    def available_languages(cls):
        return dict(LANGUAGES)

    @classmethod
    def current_language(cls):
        return cls._current_lang

    @classmethod
    def _load_json_translations(cls, lang_code):
        json_path = os.path.join(cls._instance._locale_dir, f"cfclient_{lang_code}.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    @classmethod
    def load_language(cls, lang_code):
        app = QApplication.instance()
        if app is None:
            logger.warning("No QApplication instance, cannot load language")
            return

        for t in cls._translators:
            app.removeTranslator(t)
        cls._translators.clear()

        if lang_code == "en_US":
            cls._current_lang = "en_US"
            return

        # Try JSON first (no lrelease needed), fall back to .qm
        json_translations = cls._load_json_translations(lang_code)
        if json_translations:
            translator = JsonTranslator(json_translations)
            app.installTranslator(translator)
            cls._translators.append(translator)
            cls._current_lang = lang_code
            logger.info("Loaded language via JSON: %s", lang_code)
            return

        # Try .qm file
        app_translator = QTranslator()
        instance = cls._instance
        if instance and app_translator.load("cfclient_" + lang_code, instance._locale_dir):
            app.installTranslator(app_translator)
            cls._translators.append(app_translator)
            cls._current_lang = lang_code
            logger.info("Loaded language via .qm: %s", lang_code)
        else:
            logger.warning("Could not load translation for: %s", lang_code)
            cls._current_lang = "en_US"

    @classmethod
    def get_language_name(cls, lang_code):
        return LANGUAGES.get(lang_code, lang_code)


def tr(context, text):
    """Translate a string in the given context.
    Convenience function for non-QObject classes.
    """
    app = QApplication.instance()
    if app is None:
        return text
    return app.translate(context, text)
