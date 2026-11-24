import json
from enum import Enum
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOCALES_DIR = BASE_DIR / "translations"

class TranslationsService:
    def __init__(
        self,
        default_locale: str | Enum = "EN_US",
        locales_dir: str | Path = DEFAULT_LOCALES_DIR,
    ):
        self._locales_dir = Path(locales_dir)
        normalized_default = self.__normalize_locale(default_locale)
        self._default_locale = normalized_default
        self._active_locale = normalized_default
        self._cache: dict[str, dict[str, Any]] = {}

        self.load_locale(normalized_default)

    @property
    def active_locale(self) -> str:
        return self._active_locale

    def set_locale(self, locale: str) -> None:
        """Set the active default locale used across the app environment."""
        normalized = self.__normalize_locale(locale)
        if normalized not in self._cache:
            self.load_locale(normalized)
        self._active_locale = normalized

    def preload_locales(self, locales: list[str]) -> None:
        """Preload translation files into cache at startup to avoid repeated disk reads at runtime."""

        for locale in locales:
            self.load_locale(locale)

    def load_locale(self, locale: str | Enum) -> None:
        """Load and flatten all JSON translation files for a given locale."""
        normalized = self.__normalize_locale(locale)
        locale_path = self._locales_dir / normalized
        if not locale_path.is_dir():
            raise FileNotFoundError(f"Locale directory not found: {locale_path}")

        flat_translations: dict[str, Any] = {}
        for json_file in sorted(locale_path.glob("*.json")):
            with json_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    self.__flatten_into(data, flat_translations)

        self._cache[normalized] = flat_translations

    def translate(
        self,
        key: str,
        default: str | None = None,
        locale: str | None = None,
        **variables: Any,
    ) -> Any:
        """Resolve and format a localized string by key for the active or requested locale."""
        target_locale = self.__normalize_locale(locale) if locale is not None else self._active_locale
        if target_locale not in self._cache:
            self.load_locale(target_locale)

        value = self._cache[target_locale].get(key)
        if value is None:
            value = default if default is not None else key

        return value.format(**variables) if variables and isinstance(value, str) else value
    
    # Private Methods
    @staticmethod
    def __normalize_locale(locale: str | Enum) -> str:
        """Convert a locale string or Enum member into its normalized string key."""
        return locale.name if isinstance(locale, Enum) else str(locale)

    def __flatten_into(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        prefix: str = "",
    ) -> None:
        """Recursively flatten nested translation dictionaries into dot-separated keys."""
        for key, value in source.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self.__flatten_into(value, target, full_key)
            else:
                target[full_key] = value
    # End Private Methods