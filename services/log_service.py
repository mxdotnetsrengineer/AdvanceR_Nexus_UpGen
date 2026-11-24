from enums.logs_enum import LogLevels
from helpers.logs_helper import ALLOWED_OUTPUTS
from api.exceptions.domain_exceptions import DomainValidationError
from services.translations_service import TranslationsService


class LogService:
    def __init__(self, translations_service: TranslationsService, level: LogLevels | str = LogLevels.ALL):
        self._translator = translations_service
        self.logs: list[str] = []
        self.allowed_channels: set[str] = ALLOWED_OUTPUTS[LogLevels.ALL]
        self.__set_level(level)

    # Public Methods
    def raw(self, message: str = "") -> None:
        self.__record(message, "info")

    def info(self, message: str = "", show_icon: bool = True) -> None:
        if not message:
            formatted = ""
        elif show_icon:
            formatted = f"ℹ️ {message}"
        else:
            formatted = message

        self.__record(formatted, "info")

    def warning(self, message: str) -> None:
        self.__record(f"⚠️ {message}", "warning")

    def error(self, message: str) -> None:
        """Record an error message without raising an exception."""
        self.__record(f"❌ {message}", "error")

    def get_logs(self) -> list[str]:
        return self.logs
    # End Public Methods

    # Private Methods
    def __record(self, formatted_message: str, channel: str) -> None:
        self.logs.append(formatted_message)
        if channel in self.allowed_channels:
            print(formatted_message)

    def __set_level(self, level: LogLevels | str) -> None:
        try:
            parsed_level = LogLevels(level)
            self.allowed_channels = ALLOWED_OUTPUTS[parsed_level]
        except ValueError as exc:
            valid_options = ", ".join(item.value for item in LogLevels)
            invalid = "Invalid log level"
            if self._translator:
                invalid = self._translator.translate("errors.invalid_log")

            msg = f"{invalid} '{level}'. Valid options: {valid_options}"
            self.error(msg)
            raise DomainValidationError(msg) from exc
    # End Private Methods
