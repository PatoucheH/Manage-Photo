"""Internationalization module for the application"""

from typing import Dict, Callable, List
from enum import Enum


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    FRENCH = "fr"


class Translations:
    """Translation strings for all supported languages"""

    _strings: Dict[str, Dict[str, str]] = {
        # App title and subtitle
        "app_title": {
            "en": "Photo Manager",
            "fr": "Photo Manager"
        },
        "app_subtitle": {
            "en": "Export your photos to Word",
            "fr": "Exportez vos photos en Word"
        },

        # Sidebar sections
        "add_photos": {
            "en": "ADD PHOTOS",
            "fr": "AJOUTER DES PHOTOS"
        },
        "folder": {
            "en": "Folder",
            "fr": "Dossier"
        },
        "files": {
            "en": "Files",
            "fr": "Fichiers"
        },
        "photos": {
            "en": "photos",
            "fr": "photos"
        },
        "photos_per_page": {
            "en": "PHOTOS PER PAGE",
            "fr": "PHOTOS PAR PAGE"
        },
        "photos_layout_4": {
            "en": "4 photos (2x2)",
            "fr": "4 photos (2x2)"
        },
        "photos_layout_6": {
            "en": "6 photos (2x3)",
            "fr": "6 photos (2x3)"
        },
        "photos_layout_9": {
            "en": "9 photos (3x3)",
            "fr": "9 photos (3x3)"
        },
        "export_word": {
            "en": "EXPORT TO WORD",
            "fr": "EXPORTER EN WORD"
        },
        "clear_all": {
            "en": "Clear all",
            "fr": "Tout effacer"
        },
        "supported_formats": {
            "en": "JPG, JPEG, PNG",
            "fr": "JPG, JPEG, PNG"
        },

        # Content area
        "preview": {
            "en": "Preview",
            "fr": "Apercu"
        },

        # Dialogs
        "select_folder": {
            "en": "Select a folder",
            "fr": "Selectionner un dossier"
        },
        "select_photos": {
            "en": "Select photos",
            "fr": "Selectionner des photos"
        },
        "confirm": {
            "en": "Confirm",
            "fr": "Confirmer"
        },
        "confirm_clear": {
            "en": "Do you really want to clear all photos?",
            "fr": "Voulez-vous vraiment effacer toutes les photos ?"
        },
        "warning": {
            "en": "Warning",
            "fr": "Attention"
        },
        "no_photos": {
            "en": "No photos to export.",
            "fr": "Aucune photo a exporter."
        },
        "save_document": {
            "en": "Save document",
            "fr": "Enregistrer le document"
        },
        "word_document": {
            "en": "Word Document (*.docx)",
            "fr": "Document Word (*.docx)"
        },
        "generating_word": {
            "en": "Generating Word document...",
            "fr": "Generation du document Word..."
        },
        "export_success": {
            "en": "Export successful",
            "fr": "Export reussi"
        },
        "export_success_msg": {
            "en": "Document exported successfully:",
            "fr": "Le document a ete exporte avec succes:"
        },
        "export_error": {
            "en": "Export error",
            "fr": "Erreur d'export"
        },
        "close": {
            "en": "Close",
            "fr": "Fermer"
        },
        "press_esc": {
            "en": "Press Esc to close",
            "fr": "Appuyez sur Echap pour fermer"
        },
        "loading_error": {
            "en": "Loading error",
            "fr": "Erreur de chargement"
        },
        "error": {
            "en": "Error",
            "fr": "Erreur"
        },
        "view": {
            "en": "View",
            "fr": "Voir"
        },

        # Language
        "language": {
            "en": "LANGUAGE",
            "fr": "LANGUE"
        },
        "english": {
            "en": "English",
            "fr": "Anglais"
        },
        "french": {
            "en": "French",
            "fr": "Francais"
        }
    }

    _current_language: Language = Language.FRENCH
    _listeners: List[Callable[[], None]] = []

    @classmethod
    def get(cls, key: str) -> str:
        """Get translated string for the current language"""
        if key in cls._strings:
            return cls._strings[key].get(cls._current_language.value, key)
        return key

    @classmethod
    def get_language(cls) -> Language:
        """Get current language"""
        return cls._current_language

    @classmethod
    def set_language(cls, language: Language) -> None:
        """Set the current language and notify listeners"""
        if cls._current_language != language:
            cls._current_language = language
            cls._notify_listeners()

    @classmethod
    def toggle_language(cls) -> None:
        """Toggle between English and French"""
        if cls._current_language == Language.ENGLISH:
            cls.set_language(Language.FRENCH)
        else:
            cls.set_language(Language.ENGLISH)

    @classmethod
    def add_listener(cls, callback: Callable[[], None]) -> None:
        """Add a listener for language changes"""
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def remove_listener(cls, callback: Callable[[], None]) -> None:
        """Remove a language change listener"""
        if callback in cls._listeners:
            cls._listeners.remove(callback)

    @classmethod
    def _notify_listeners(cls) -> None:
        """Notify all listeners of language change"""
        for listener in cls._listeners:
            try:
                listener()
            except Exception:
                pass


# Shortcut function
def tr(key: str) -> str:
    """Shortcut for Translations.get()"""
    return Translations.get(key)
