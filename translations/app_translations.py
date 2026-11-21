import json
from enum import Enum
from pathlib import Path
from typing import Any


class AppsTranslations:
    def __init__(self, locales_dir: str | Path, default_locale: str | Enum = "EN_US"):
        self._locales_dir = Path(locales_dir)
        normalized_default = self.__normalize_locale(default_locale)
        self._default_locale = normalized_default
        self._active_locale = normalized_default
        self._cache: dict[str, dict[str, Any]] = {}

        self.load_locale(normalized_default)

    @property
    def active_locale(self) -> str:
        return self._active_locale

    # Public Methods
    def set_locale(self, locale: str | Enum) -> None:
        normalized = self.__normalize_locale(locale)
        if normalized not in self._cache:
            self.load_locale(normalized)
        self._active_locale = normalized

    def load_locale(self, locale: str | Enum) -> None:
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
        locale: str | Enum | None = None,
        **variables: Any,
    ) -> Any:
        target_locale = self.__normalize_locale(locale) if locale is not None else self._active_locale
        if target_locale not in self._cache:
            self.load_locale(target_locale)

        value = self._cache[target_locale].get(key)
        if value is None:
            value = default if default is not None else key

        return value.format(**variables) if variables and isinstance(value, str) else value
    # End Public Methods

    # Private Methods
    @staticmethod
    def __normalize_locale(locale: str | Enum) -> str:
        return locale.name if isinstance(locale, Enum) else str(locale)

    def __flatten_into(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        prefix: str = "",
    ) -> None:
        for key, value in source.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self.__flatten_into(value, target, full_key)
            else:
                target[full_key] = value
    # End Private Methods
