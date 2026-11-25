import pytest
from fastapi.testclient import TestClient
from services.translations_service import TranslationsService
from services.log_service import LogService
from services.error_service import ErrorService
from api.app import create_app


@pytest.fixture(scope="session")
def translations_service() -> TranslationsService:
    """Provide a default English TranslationsService instance."""
    return TranslationsService(default_locale="EN_US")


@pytest.fixture(scope="session")
def error_service(translations_service: TranslationsService) -> ErrorService:
    """Provide an ErrorService instance backed by a silent LogService."""
    logger = LogService(translations_service, level="NONE")
    return ErrorService(logger, translations_service)

@pytest.fixture(scope="module")
def api_client() -> TestClient:
    """Provide a FastAPI TestClient scoped per test module."""
    return TestClient(create_app())

@pytest.fixture
def fake_gba_rom() -> bytearray:
    """Create a 64KB zero-initialized buffer filled with 0xFF free space bytes."""
    return bytearray(b"\xFF" * 0x10000)