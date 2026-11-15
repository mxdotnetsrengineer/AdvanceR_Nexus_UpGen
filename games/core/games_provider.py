from typing import Any
from pathlib import Path
from enums.gba.games_enum import AvailableGames
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from games.base_game import BaseGame
from games.core.games_core import GamesCore
from games.core.gba_pokemon_core import GBAPokemonCoreFactory 

class GamesProvider:
    _FACTORY_REGISTRY: dict[AvailableGames, type[GamesCore]] = {
        AvailableGames.ORIGINAL_FIRE_RED: GBAPokemonCoreFactory,
        AvailableGames.RADICAL_FIRE_RED: GBAPokemonCoreFactory,
        AvailableGames.EMERALD: GBAPokemonCoreFactory,
        AvailableGames.EMERALD_KAIZO: GBAPokemonCoreFactory,
        # AvailableGames.PLATINUM: NDSPokemonFactory,
    }

    @staticmethod
    def create(game: AvailableGames, game_config: dict[str, Any]) -> BaseGame:
        # 1. Common Services
        config_service = ConfigService(game_config)

        base_path = Path(__file__).resolve().parent.parent.parent
        translations_path = base_path / "translations"
        translations_service = TranslationsService(
            translations_path, config_service.get("CURRENT_LANGUAGE")
        )

        log_service = LogService(
            translations_service, config_service.get("LOG_TYPE")
        )
        file_service = FileService(log_service, translations_service, config_service)

        # 2. Factory
        factory_cls = GamesProvider._FACTORY_REGISTRY.get(game)
        if not factory_cls:
            error_msg = f"{translations_service.translate('errors.no_game')} {game}"
            log_service.error(error_msg)
            raise ValueError(error_msg)

        # 3. Family Build
        factory = factory_cls(
            config_service=config_service,
            log_service=log_service,
            file_service=file_service,
            translations_service=translations_service,
        )
        return factory.create_game(game)