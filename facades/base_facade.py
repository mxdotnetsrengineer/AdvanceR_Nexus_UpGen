import asyncio
import redis.asyncio as redis
from collections.abc import Callable
from typing import TypeVar
from enums.gba.games_enum import AvailableGames
from models.game_input import GameInput
from exceptions.domain_exceptions import DomainValidationError, RomPreconditionError
from services.error_service import ErrorService
from services.config_service import ConfigService
from games.base_game import BaseGame
from games.core.games_provider import GamesProvider

T = TypeVar("T")

class BaseGameFacade:
    def __init__(
        self,
        global_config: ConfigService,
        error_service: ErrorService,
        default_game: AvailableGames | None = None,
        redis_client: redis.Redis | None = None,
    ):
        self._global_config = global_config
        self._errors = error_service
        self._default_game = default_game or AvailableGames.ORIGINAL_FIRE_RED
        self._redis = redis_client

    def _resolve_selected_game(self, game_input: GameInput) -> AvailableGames:
        try:
            return (
                AvailableGames(game_input.current_game)
                if game_input.current_game is not None
                else self._default_game
            )
        except ValueError:
            self._errors.raise_error(
                "errors.no_game",
                DomainValidationError,
                game=game_input.current_game,
            )

    def _resolve_game(self, game_input: GameInput, readonly: bool = True) -> BaseGame:
        if game_input.raw_file is not None:
            if len(game_input.raw_file) == 0:
                self._errors.raise_error("errors.empty_game_file", DomainValidationError)

        selected_game = self._resolve_selected_game(game_input)
        resolved_language = game_input.language or self._global_config.get("CURRENT_LANGUAGE")

        rom_buffer = (
            game_input.raw_file
            if (readonly or game_input.raw_file is None)
            else bytearray(game_input.raw_file)
        )

        target_game = GamesProvider.create(
            game=selected_game,
            language=resolved_language,
            game_file=rom_buffer,
            game_filename=game_input.filename,
            readonly=readonly
        )

        resolved_game_file = target_game.memory_service.game_file
        if not resolved_game_file:
            self._errors.raise_error("errors.no_game_data", RomPreconditionError)

        max_rom_size = target_game.config_service.get("MAX_ROM_SIZE")
        if max_rom_size and len(resolved_game_file) > max_rom_size:
            self._errors.raise_error(
                "errors.rom_size_exceeded",
                DomainValidationError,
                size=len(resolved_game_file),
                max_size=max_rom_size,
            )

        return target_game

    async def _run_in_thread(
        self,
        game_input: GameInput,
        action: Callable[[BaseGame], T],
        readonly: bool = True,
    ) -> T:
        """Resolve the game and run any synchronous domain action in a worker thread."""
        return await asyncio.to_thread(self._execute_sync, game_input, action, readonly)

    def _execute_sync(
        self,
        game_input: GameInput,
        action: Callable[[BaseGame], T],
        readonly: bool = True,
    ) -> T:
        target_game = self._resolve_game(game_input, readonly=readonly)
        return action(target_game)