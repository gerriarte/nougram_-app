"""
Translation service for backend error messages
Provides fallback translations for backend logging and default responses
"""

import json
from pathlib import Path

from app.core.error_codes import ErrorCode

# Default locale
DEFAULT_LOCALE = "es"

# Translation cache
_translations_cache: dict[str, dict[str, str]] = {}


def load_translations(locale: str = DEFAULT_LOCALE) -> dict[str, str]:
    """
    Load translations for a given locale

    Args:
        locale: Locale code (e.g., 'es', 'en')

    Returns:
        Dictionary of error code to translated message
    """
    if locale in _translations_cache:
        return _translations_cache[locale]

    # Path to locales directory
    locales_dir = Path(__file__).parent.parent / "locales"
    locale_file = locales_dir / f"{locale}.json"

    if not locale_file.exists():
        # Fallback to default locale if file doesn't exist
        if locale != DEFAULT_LOCALE:
            return load_translations(DEFAULT_LOCALE)
        # If default locale file doesn't exist, return empty dict
        return {}

    try:
        with open(locale_file, encoding="utf-8") as f:
            translations = json.load(f)
            _translations_cache[locale] = translations.get("errors", {})
            return _translations_cache[locale]
    except Exception:
        # If loading fails, return empty dict
        return {}


def translate_error(
    error_code: ErrorCode, locale: str = DEFAULT_LOCALE, params: dict[str, any] | None = None
) -> str:
    """
    Translate an error code to a human-readable message

    Args:
        error_code: ErrorCode enum value
        locale: Locale code (e.g., 'es', 'en')
        params: Optional parameters for message interpolation

    Returns:
        Translated error message
    """
    translations = load_translations(locale)
    message = translations.get(error_code.value, error_code.value)

    # Simple parameter interpolation
    if params:
        try:
            message = message.format(**params)
        except (KeyError, ValueError):
            # If interpolation fails, return message as-is
            pass

    return message


def get_locale_from_request(request) -> str:
    """
    Extract locale from request headers

    Args:
        request: FastAPI Request object

    Returns:
        Locale code (defaults to 'es')
    """
    accept_language = request.headers.get("Accept-Language", "")

    # Parse Accept-Language header (e.g., "es-ES,es;q=0.9,en;q=0.8")
    if accept_language:
        # Get first language preference
        first_lang = accept_language.split(",")[0].split(";")[0].strip()
        # Extract base language (e.g., "es" from "es-ES")
        base_lang = first_lang.split("-")[0].lower()

        # Support only 'es' and 'en' for now
        if base_lang in ["es", "en"]:
            return base_lang

    return DEFAULT_LOCALE
