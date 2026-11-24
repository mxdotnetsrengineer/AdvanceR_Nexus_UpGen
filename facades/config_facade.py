from enums.app_enums import AvailableLanguages
from services.config_service import ConfigService
from services.translations_service import TranslationsService


class ConfigFacade:
    def __init__(self, config_service: ConfigService, translations_service: TranslationsService):
        self._config = config_service
        self._translator = translations_service

    def get_language_confirmation(self, language: AvailableLanguages) -> tuple[str, str]:
        message = self._translator.translate(
            "menu.messages.language_updated",
            locale=language.name,
            language=language.name,
        )
        return language.name, message

    def get_language_cookie_data(self, language: AvailableLanguages) -> tuple[str, str, int]:
        message = self._translator.translate(
            "menu.messages.language_updated",
            locale=language.name,
            language=language.name,
        )
        max_age = int(self._config.get("LANGUAGE_COOKIE_MAX_AGE"))
        return language.name, message, max_age