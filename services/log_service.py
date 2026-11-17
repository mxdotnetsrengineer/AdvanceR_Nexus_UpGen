from typing import NoReturn
from enums.logs_enum import LogLevel
from helpers.logs_helper import ERROR_TYPES, ALLOWED_OUTPUTS
from services.translations_service import TranslationsService

class LogService:
    def __init__(self,translations_service: TranslationsService, level: LogLevel | str = LogLevel.ALL, **kwargs):
        super().__init__(**kwargs)
        self._translator = translations_service
        self.logs: list[str] = []
        self._allowed_channels: set[str] = ALLOWED_OUTPUTS[LogLevel.ALL]
        self._set_level(level)

    # Public Methods
    def raw(self, message: str = "") -> None:
        self._record(message, "info")

    def info(self, message: str = "", show_icon: bool = True) -> None:
        if not message:
            formatted = ""
        elif show_icon:
            formatted = f"ℹ️ {message}"
        else:
            formatted = message

        self._record(formatted, "info")

    def warning(self, message: str) -> None:
        self._record(f"⚠️ {message}", "warning")

    def error(self, message: str, error_key: str = "runtime") -> NoReturn:
        self._record(f"❌ {message}", "error")
        exception_cls = ERROR_TYPES.get(error_key, RuntimeError)
        raise exception_cls(message)

    def get_logs(self) -> list[str]:
        return self.logs
    # End Public Methods

    # Private Methods
    def _record(self, formatted_message: str, channel: str) -> None:
        self.logs.append(formatted_message)
        if channel in self._allowed_channels:
            print(formatted_message)

    def _set_level(self, level: LogLevel | str) -> None:
        try:
            parsed_level = LogLevel(level)
            self._allowed_channels = ALLOWED_OUTPUTS[parsed_level]
        except ValueError:
            valid_options = ", ".join(item.value for item in LogLevel)
            invalid = "Invalid log level"
            if self._translator:
                invalid = self._translator.translate("errors.invalid_log")

            msg = f"{invalid} '{level}'. Valid options: {valid_options}"
            self.error(msg, error_key="value")
    # End Private Methods