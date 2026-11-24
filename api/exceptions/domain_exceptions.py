class DomainException(Exception):
    """Base exception for all domain and business logic errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DomainValidationError(DomainException):
    """Raised when input data, configuration values, or ROM files fail domain validation."""


class ResourceNotFoundError(DomainException):
    """Raised when a required ROM file or game configuration is missing."""


class RomPreconditionError(DomainException):
    """Raised when the service lacks loaded ROM data or preconditions to execute."""