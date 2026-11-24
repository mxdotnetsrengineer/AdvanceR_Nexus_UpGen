from fastapi import File, Form, UploadFile, Cookie
from enums.gba.games_enum import GameSelection
from models.game_api_input import GameAPIInput


async def parse_game_input(
    game: GameSelection | None = Form(default=None),
    game_file: UploadFile | None = File(default=None),
     app_language: str | None = Cookie(default=None),
) -> GameAPIInput:
    """Extract and package form game selection and optional ROM upload into a single DTO."""
    raw_bytes = await game_file.read() if game_file is not None else None
    filename = game_file.filename if game_file is not None else None
    game_id = game.to_domain_enum().value if game is not None else None

    return GameAPIInput(game_id=game_id, raw_file=raw_bytes, filename=filename, language=app_language)