from typing import Any, NoReturn
from exceptions.domain_exceptions import DomainException
from services.log_service import LogService
from services.translations_service import TranslationsService


class ErrorService:

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
        exception_cls: type[DomainException] = DomainException,
        cause: Exception | None = None,
        **variables: Any,
    ) -> NoReturn:
        """Translate the error message, log it, and raise the specified domain exception."""
        message = self.translator.translate(translation_key, **variables)
        self.log.error(message)

        if cause is not None:
            raise exception_cls(message) from cause
        raise exception_cls(message)
