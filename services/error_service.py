from typing import Any, NoReturn
from exceptions.domain_exceptions import (
    DomainException,
    DomainValidationError,
    ResourceNotFoundError,
    RomPreconditionError,
)
from services.log_service import LogService
from services.translations_service import TranslationsService


class ErrorService:
    _ERROR_MAP: dict[str, type[DomainException]] = {
        "file_not_found": ResourceNotFoundError,
        "runtime": RomPreconditionError,
        "value": DomainValidationError,
        "key": DomainValidationError,
    }

    def __init__(
        self,
        log_service: LogService,
        translations_service: TranslationsService,
    ):
        self.log = log_service
        self.translator = translations_service

    def raise_error(
        self,
        translation_key: str,
        error_type: str = "domain",
        cause: Exception | None = None,
        **variables: Any,
    ) -> NoReturn:
        """Translate the error message, log it, and raise the mapped domain exception."""
        message = self.translator.translate(translation_key, **variables)
        self.log.error(message)

        exception_cls = self._ERROR_MAP.get(error_type, DomainException)
        if cause is not None:
            raise exception_cls(message) from cause
        raise exception_cls(message)