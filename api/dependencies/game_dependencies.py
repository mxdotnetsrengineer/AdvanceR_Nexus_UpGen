from functools import lru_cache
from fastapi import File, Form, UploadFile, Cookie, Request
from enums.app_enums import AvailableLanguages
from enums.gba.games_enum import AvailableGames
from models.game_input import GameInput
from exceptions.domain_exceptions import DomainValidationError
from services.config_service import ConfigService

CHUNK_SIZE = 1024 * 1024
DEFAULT_MAX_UPLOAD_MB = 32

def _resolve_upload_limits(request: Request) -> tuple[int, int]:
    global_config: ConfigService | None = getattr(request.app.state, "global_config", None)
    raw_mb = (
        global_config.get("GLOBAL_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB)
        if global_config is not None
        else DEFAULT_MAX_UPLOAD_MB
    )
    max_mb = int(raw_mb)
    return max_mb, max_mb * 1024 * 1024

async def _read_upload_bounded(upload_file: UploadFile, max_mb: int, max_bytes: int) -> bytes:
    """Read an uploaded file in chunks, aborting immediately if it exceeds max_bytes."""
    buffer = bytearray()
    try:
        while chunk := await upload_file.read(CHUNK_SIZE):
            buffer.extend(chunk)
            if len(buffer) > max_bytes:
                raise DomainValidationError(
                    f"The uploaded file exceeds the server maximum limit of {max_mb}MB."
                )
        return bytes(buffer)
    finally:
        await upload_file.close()

async def parse_game_input(
    request: Request,
    game: AvailableGames | None = Form(default=None),
    game_file: UploadFile | None = File(default=None),
    app_language: str | None = Cookie(default=None),
) -> GameInput:
    """Extract and package form game selection and optional ROM upload into a single DTO."""
    raw_bytes: bytes | None = None
    filename: str | None = None

    if game_file is not None:
        max_mb, max_bytes = _resolve_upload_limits(request)
        raw_bytes = await _read_upload_bounded(game_file, max_mb, max_bytes)
        filename = game_file.filename

    valid_lang = app_language if app_language in AvailableLanguages.__members__ else None
    current_game = game.config_key if game is not None else None

    return GameInput(current_game=current_game, raw_file=raw_bytes, filename=filename, language=valid_lang)
