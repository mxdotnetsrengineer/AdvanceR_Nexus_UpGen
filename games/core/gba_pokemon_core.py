from typing import Any
from enums.gba.games_enum import AvailableGames
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.bank_service import BankService
from services.gba.pokemon.events_service import EventsService
from services.gba.pokemon.item_service import ItemService
from services.gba.pokemon.wild_service import WildService
from services.gba.pokemon.difficulty_service import DifficultyService
from services.gba.pokemon.keyboard_service import GBAKeyboardService
from services.gba.pokemon.stats_service import StatsService
from games.core.games_core import GamesCore
from games.base_game import BaseGame
from games.gba.pokemon.fire_red_game import FireRedGame
from games.gba.pokemon.emerald_game import EmeraldGame

class GBAPokemonCoreFactory(GamesCore):
    def create_game(self, game: AvailableGames, game_file: bytes | bytearray | None = None, readonly: bool = False) -> BaseGame:
        memory_service = self._create_memory_service(game_file=game_file, readonly=readonly)
        keyboard_service = self._create_keyboard_service()
        domain_services = self._create_services_with_domain_services(memory_service)
        game_cls = self._resolve_game_class(game)
        
        return game_cls(
            game=game,
            file_service=self.file_service,
            log_service=self.log_service,
            memory_service=memory_service,
            config_service=self.config_service,
            keyboard_service=keyboard_service,
            translations_service=self.translations_service,
            redis_client=self.redis_client,
            **domain_services,
        )

    #Protected Methods
    def _create_memory_service(self, game_file: bytes | bytearray | None = None, readonly: bool = False) -> GBAMemoryService:
        memory_service = GBAMemoryService(self.translations_service)
        if game_file is not None:
            memory_service.game_file = game_file
        elif readonly:
            memory_service.game_file = self.file_service.open_game_readonly(
                self.config_service.get("ORIGINAL_GAME")
            )
        else:
            memory_service.game_file = self.file_service.open_game(
                self.config_service.get("ORIGINAL_GAME")
            )
        return memory_service

    def _create_keyboard_service(self) -> GBAKeyboardService:
        return GBAKeyboardService(self.config_service)

    def _create_item_service(self,common_services):
        return ItemService(**common_services)

    def _create_services_with_domain_services(self, memory_service: GBAMemoryService) -> dict[str, Any]:
        common_services = {
            "config_service": self.config_service,
            "memory_service": memory_service,
            "log_service": self.log_service,
            "translations_service": self.translations_service,
            "error_service": self.error_service,
        }

        events_service = EventsService(**common_services)
        bank_service = BankService(**common_services, events_service=events_service)
        difficulty_service = DifficultyService(self.config_service)
        item_service = self._create_item_service(common_services)
        stats_service = StatsService(**common_services)
        wild_service = WildService(**common_services, difficulty_service=difficulty_service)
        return {
            "bank_service": bank_service,
            "stats_service": stats_service,
            "items_service" : item_service,
            "wild_service" : wild_service,
            "events_service" : events_service
        }

    @staticmethod
    def _resolve_game_class(game: AvailableGames):
        from games.gba.pokemon.fire_red_game import FireRedGame
        from games.gba.pokemon.emerald_game import EmeraldGame

        mapping = {
            AvailableGames.ORIGINAL_FIRE_RED: FireRedGame,
            AvailableGames.RADICAL_FIRE_RED: FireRedGame,
            AvailableGames.EMERALD: EmeraldGame,
            AvailableGames.EMERALD_KAIZO: EmeraldGame
        }
        return mapping[game]
    #End Protected Methods

    def create_game(_self, game: AvailableGames) -> BaseGame:
        memory_service = _self._create_memory_service()
        keyboard_service = _self._create_keyboard_service()
        domain_services = _self._create_services_with_domain_services(memory_service)
        game_cls = _self._resolve_game_class(game)
        
        return game_cls(
            game=game,
            file_service=_self.file_service,
            log_service=_self.log_service,
            memory_service=memory_service,
            config_service=_self.config_service,
            keyboard_service=keyboard_service,
            translations_service=_self.translations_service,
            **domain_services,
        )
