import json
from pathlib import Path
from typing import Any


class TranslationsService:
    def __init__(self, locales_dir: str | Path, default_locale: str = "EN_US"):
        self._locales_dir = Path(locales_dir)
        self._default_locale = default_locale
        self._active_locale = default_locale
        self._cache: dict[str, dict[str, Any]] = {}

        self.load_locale(default_locale)

    @property
    def active_locale(self) -> str:
        return self._active_locale

    # Public Methods
    def set_locale(self, locale: str) -> None:
        if locale not in self._cache:
            self.load_locale(locale)
        self._active_locale = locale

    def load_locale(self, locale: str) -> None:
        locale_path = self._locales_dir / locale
        if not locale_path.is_dir():
            raise FileNotFoundError(f"Locale directory not found: {locale_path}")

        flat_translations: dict[str, Any] = {}
        for json_file in sorted(locale_path.glob("*.json")):
            with json_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    self._flatten_into(data, flat_translations)

        self._cache[locale] = flat_translations

    def translate(
        self,
        key: str,
        default: str | None = None,
        locale: str | None = None,
        **variables: Any,
    ) -> Any:
        target_locale = locale or self._active_locale
        if target_locale not in self._cache:
            self.load_locale(target_locale)

        value = self._cache[target_locale].get(key)
        if value is None:
            value = default if default is not None else key

        return value.format(**variables) if variables and isinstance(value, str) else value
    # End Public Methods

    # Private Methods
    def _flatten_into(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        prefix: str = "",
    ) -> None:
        for key, value in source.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_into(value, target, full_key)
            else:
                target[full_key] = value
    # End Private Methods