from pathlib import Path
from enums.gba.games_enum import AvailableGames
from models.game_input import GameInput
from services.error_service import ErrorService
from services.config_service import ConfigService
from games.base_game import BaseGame
from games.core.games_provider import GamesProvider

class BaseGameFacade:
    def __init__(
        self,
        global_config: ConfigService,
        error_service: ErrorService,
        default_game: AvailableGames = AvailableGames.ORIGINAL_FIRE_RED,
    ):
        self._global_config = global_config
        self._errors = error_service
        self._default_game = default_game

    def _resolve_game(self, game_input: GameInput) -> BaseGame:
        uploaded_bytes: bytearray | None = None

        if game_input.raw_file is not None:
            if len(game_input.raw_file) == 0:
                self._errors.raise_error("errors.empty_game_file", error_type="value")
            uploaded_bytes = bytearray(game_input.raw_file)

        selected_game = (
            AvailableGames(game_input.game_id)
            if game_input.game_id is not None
            else self._default_game
        )

        resolved_language = game_input.language or self._global_config.get("CURRENT_LANGUAGE")

        target_game = GamesProvider.create(
            game=selected_game,
            language=resolved_language,
            game_file=uploaded_bytes,
            game_filename=game_input.filename,
        )

        if uploaded_bytes is not None:
            configured_path = target_game.config_service.get("ORIGINAL_GAME", "")
            expected_filename = Path(configured_path).name
            provided_filename = Path(game_input.filename).name if game_input.filename else ""

            if expected_filename and provided_filename != expected_filename:
                self._errors.raise_error(
                    "errors.invalid_game_filename",
                    error_type="value",
                    provided_name=provided_filename,
                    expected_name=expected_filename,
                )

        resolved_game_file = target_game.memory_service.game_file
        if not resolved_game_file:
            self._errors.raise_error("errors.no_game_data", error_type="runtime")

        max_rom_size = target_game.config_service.get("MAX_ROM_SIZE")
        if max_rom_size and len(resolved_game_file) > max_rom_size:
            self._errors.raise_error(
                "errors.rom_size_exceeded",
                error_type="value",
                size=len(resolved_game_file),
                max_size=max_rom_size,
            )

        return target_game