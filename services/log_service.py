import logging
import sys
from enums.logs_enum import LogLevels
from helpers.logs_helper import ALLOWED_OUTPUTS
from exceptions.domain_exceptions import DomainValidationError
from services.translations_service import TranslationsService

def _configure_root_logger() -> logging.Logger:
    """Ensure a clean, UTF-8 safe console handler is configured once."""
    logger = logging.getLogger("advancer")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger

class LogService:
    def __init__(self, translations_service: TranslationsService, level: LogLevels | str = LogLevels.ALL,  keep_history: bool = True, logger: logging.Logger | None = None):
        self._translator = translations_service
        self._logger = logger or _configure_root_logger()
        self.logs: list[str] = []
        self.allowed_channels: set[str] = ALLOWED_OUTPUTS[LogLevels.ALL]
        self._keep_history = keep_history
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

    def error(self, message: str) -> None:
        """Record an error message without raising an exception."""
        self._record(f"❌ {message}", "error")

    def get_logs(self) -> list[str]:
        return self.logs
    # End Public Methods

    # Private Methods
    def _record(self, formatted_message: str, channel: str) -> None:
        if self._keep_history:
            self.logs.append(formatted_message)

        if channel not in self.allowed_channels:
            return

        match channel:
            case "warning":
                self._logger.warning(formatted_message)
            case "error":
                self._logger.error(formatted_message)
            case _:
                self._logger.info(formatted_message)

    def _set_level(self, level: LogLevels | str) -> None:
        try:
            parsed_level = LogLevels(level)
            self.allowed_channels = ALLOWED_OUTPUTS[parsed_level]
        except ValueError as exc:
            valid_options = ", ".join(item.value for item in LogLevels)
            invalid = self._translator.translate("errors.invalid_log") if self._translator else "Invalid log level"
            msg = f"{invalid} '{level}'. Valid options: {valid_options}"
            self.error(msg)
            raise DomainValidationError(msg) from exc
    # End Private Methods
