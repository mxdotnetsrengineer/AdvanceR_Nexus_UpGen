import json
from enum import Enum
from pathlib import Path
from typing import Any
from enums.app_enums import AvailableLanguages

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOCALES_DIR = BASE_DIR / "translations"

class TranslationsService:
    _SHARED_CACHE: dict[tuple[Path, str], dict[str, Any]] = {}
    _FALLBACK_LOCALE: str = AvailableLanguages.EN_US.name
    def __init__(
        self,
        default_locale: str | Enum = "EN_US",
        locales_dir: str | Path = DEFAULT_LOCALES_DIR,
    ):
        self._locales_dir = Path(locales_dir).resolve()
        normalized_default = self._normalize_locale(default_locale)
        self._default_locale = normalized_default
        self._active_locale = normalized_default

        if (self._locales_dir, normalized_default) not in self._SHARED_CACHE:
            self.load_locale(normalized_default)

    @property
    def active_locale(self) -> str:
        return self._active_locale

    def set_locale(self, locale: str) -> None:
        """Set the active default locale used across the app environment."""
        normalized = self._normalize_locale(locale)
        if (self._locales_dir, normalized) not in self._SHARED_CACHE:
            self.load_locale(normalized)
        self._active_locale = normalized

    def preload_locales(self, locales: list[str]) -> None:
        """Preload translation files into cache at startup to avoid repeated disk reads at runtime."""
        for locale in locales:
            normalized = self._normalize_locale(locale)
            if (self._locales_dir, normalized) not in self._SHARED_CACHE:
                self.load_locale(normalized)

    def load_locale(self, locale: str | Enum) -> None:
        """Load and flatten all JSON translation files for a given locale."""
        normalized = self._normalize_locale(locale)
        locale_path = self._locales_dir / normalized
        if not locale_path.is_dir():
            raise FileNotFoundError(f"Locale directory not found: {locale_path}")

        flat_translations: dict[str, Any] = {}
        for json_file in sorted(locale_path.glob("*.json")):
            with json_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    self._flatten_into(data, flat_translations)

        self._SHARED_CACHE[(self._locales_dir, normalized)] = flat_translations

    def translate(
        self,
        key: str,
        default: str | None = None,
        locale: str | None = None,
        **variables: Any,
    ) -> Any:
        """Resolve and format a localized string by key for the active or requested locale."""
        target_locale = self._normalize_locale(locale) if locale is not None else self._active_locale
        cache_key = (self._locales_dir, target_locale)

        if cache_key not in self._SHARED_CACHE:
            self.load_locale(target_locale)

        value = self._SHARED_CACHE[cache_key].get(key)
        if value is None:
            value = default if default is not None else key

        if variables and isinstance(value, str):
            try:
                return value.format(**variables)
            except KeyError:
                return value
        return value
    
    # Private Methods
    @classmethod
    def _normalize_locale(cls, locale: str | Enum | None) -> str:
        """Resolve a valid AvailableLanguages key, falling back to EN_US if missing or unsupported."""
        if isinstance(locale, Enum):
            candidate = locale.name
        elif isinstance(locale, str):
            candidate = locale.strip()
        else:
            return cls._FALLBACK_LOCALE

        return candidate if candidate in AvailableLanguages.__members__ else cls._FALLBACK_LOCALE

    def _flatten_into(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        prefix: str = "",
    ) -> None:
        """Recursively flatten nested translation dictionaries into dot-separated keys."""
        for key, value in source.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_into(value, target, full_key)
            else:
                target[full_key] = value
    # End Private Methods
