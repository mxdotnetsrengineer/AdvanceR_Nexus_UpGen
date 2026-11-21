import json
from pathlib import Path
from typing import Any
from translations.app_translations import AppsTranslations


class TranslationsService:
    def __init__(self, locales_dir: str | Path, default_locale: str = "EN_US"):
        self._engine = AppsTranslations(
            locales_dir=locales_dir,
            default_locale=default_locale,
        )

    @property
    def active_locale(self) -> str:
        return self._engine.active_locale

    def set_locale(self, locale: str) -> None:
        """Set the active default locale used across the app environment."""
        self._engine.set_locale(locale)

    def preload_locales(self, locales: list[str]) -> None:
        """Preload translation files into cache at startup to avoid repeated disk reads at runtime."""
        for locale in locales:
            self._engine.load_locale(locale)

    def translate(
        self,
        key: str,
        default: str | None = None,
        locale: str | None = None,
        **variables: Any,
    ) -> Any:
        """Resolve and format a localized string by key for the active or requested locale."""
        return self._engine.translate(
            key=key,
            default=default,
            locale=locale,
            **variables,
        )