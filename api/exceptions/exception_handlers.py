import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from api.exceptions.domain_exceptions import (
    DomainValidationError,
    ResourceNotFoundError,
    RomPreconditionError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI, internal_error_message: str = "An unexpected internal server error occurred.") -> None:
    """Attach centralized domain-to-HTTP exception translators to the FastAPI app."""

    @app.exception_handler(DomainValidationError)
    @app.exception_handler(ValueError)
    async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ResourceNotFoundError)
    @app.exception_handler(FileNotFoundError)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(RomPreconditionError)
    @app.exception_handler(RuntimeError)
    async def precondition_failed_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": internal_error_message}
        )