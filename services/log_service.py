from typing import NoReturn
from enums.logs_enum import LogLevels
from helpers.logs_helper import ERROR_TYPES, ALLOWED_OUTPUTS
from services.translations_service import TranslationsService

class LogService:
    def __init__(_self,translations_service: TranslationsService, level: LogLevels | str = LogLevels.ALL, **kwargs):
        super().__init__(**kwargs)
        _self._translator = translations_service
        _self.logs: list[str] = []
        _self.allowed_channels: set[str] = ALLOWED_OUTPUTS[LogLevels.ALL]
        _self.__set_level(level)

    # Public Methods
    def raw(_self, message: str = "") -> None:
        _self.__record(message, "info")

    def info(_self, message: str = "", show_icon: bool = True) -> None:
        if not message:
            formatted = ""
        elif show_icon:
            formatted = f"ℹ️ {message}"
        else:
            formatted = message

        _self.__record(formatted, "info")

    def warning(_self, message: str) -> None:
        _self.__record(f"⚠️ {message}", "warning")

    def error(_self, message: str, error_key: str = "runtime") -> NoReturn:
        _self.__record(f"❌ {message}", "error")
        exception_cls = ERROR_TYPES.get(error_key, RuntimeError)
        raise exception_cls(message)

    def get_logs(_self) -> list[str]:
        return _self.logs
    # End Public Methods

    # Private Methods
    def __record(_self, formatted_message: str, channel: str) -> None:
        _self.logs.append(formatted_message)
        if channel in _self.allowed_channels:
            print(formatted_message)

    def __set_level(_self, level: LogLevels | str) -> None:
        try:
            parsed_level = LogLevels(level)
            _self.allowed_channels = ALLOWED_OUTPUTS[parsed_level]
        except ValueError:
            valid_options = ", ".join(item.value for item in LogLevels)
            invalid = "Invalid log level"
            if _self._translator:
                invalid = _self._translator.translate("errors.invalid_log")

            msg = f"{invalid} '{level}'. Valid options: {valid_options}"
            _self.error(msg, error_key="value")
    # End Private Methods