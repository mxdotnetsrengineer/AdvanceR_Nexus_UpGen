from typing import Any
from pathlib import Path
from enums.gba.games_enum import AvailableGames
from services.file_service import FileService
from services.log_service import LogService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.keyboard_service import GBAKeyboardService
from games.gba.gba_game import GBAGame

class CurrentGameFactory:
    @staticmethod
    def create(
        game: AvailableGames, 
        game_config: dict[str, Any]
    ) -> GBAGame:
        # Service Configuration
        config_service = ConfigService(game_config)

        base_path = Path(__file__).resolve().parent.parent
        translations_path = base_path / "translations"
        translations_service = TranslationsService(translations_path, config_service.get_value("CURRENT_LANGUAGE"))

        log_service = LogService(translations_service, config_service.get_value("LOG_TYPE"))
        file_service = FileService(log_service, translations_service)
        memory_service = GBAMemoryService(translations_service)
        
        # Game
        match game:
            case AvailableGames.ORIGINAL_FIRE_RED | AvailableGames.RADICAL_FIRE_RED:
                from games.gba.pokemon.fire_red_game import FireRedGame
                from services.gba.pokemon.bank_service import BankService
                from services.gba.pokemon.event_service import EventService
                from services.gba.pokemon.item_service import ItemService
                
                item_service = ItemService(config_service=config_service,memory_service=memory_service,log_service=log_service,
                    translations_service=translations_service,
                )
                event_service = EventService(
                    config_service=config_service,memory_service=memory_service,log_service=log_service,translations_service=translations_service,
                        item_service=item_service,
                )
                bank_service = BankService(
                    config_service=config_service,memory_service=memory_service,log_service=log_service,translations_service=translations_service,
                        event_service=event_service,
                )
                keyboard_service = GBAKeyboardService(config_service)

                return FireRedGame(
                    game=game,
                    file_service=file_service,
                    log_service=log_service,
                    memory_service=memory_service,
                    config_service=config_service,
                    bank_service=bank_service,
                    keyboard_service=keyboard_service,
                    translations_service=translations_service
                )
            case _:
                log_service.error(f"{translations_service.translate("errors.no_game")} {game}")
