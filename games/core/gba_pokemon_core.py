from typing import Any
from enums.gba.games_enum import AvailableGames
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.keyboard_service import GBAKeyboardService
from services.gba.pokemon.stats_service import StatsService
from games.core.games_core import GamesCore
from games.base_game import BaseGame

class GBAPokemonCoreFactory(GamesCore):

    def create_memory_service(self) -> GBAMemoryService:
        
        memory_service = GBAMemoryService(self.translations_service)
        memory_service.game_file = self.file_service.open_game(self.config_service.get("ORIGINAL_GAME"))
        return memory_service

    def create_keyboard_service(self) -> GBAKeyboardService:
        return GBAKeyboardService(self.config_service)

    def _create_services_with_domain_services(self, memory_service: GBAMemoryService) -> dict[str, Any]:
        from services.gba.pokemon.bank_service import BankService
        from services.gba.pokemon.event_service import EventService
        from services.gba.pokemon.item_service import ItemService

        common_services = {
            "config_service": self.config_service,
            "memory_service": memory_service,
            "log_service": self.log_service,
            "translations_service": self.translations_service,
        }

        item_service = ItemService(**common_services)
        event_service = EventService(**common_services, item_service=item_service)
        bank_service = BankService(**common_services, event_service=event_service)

        stats_service = StatsService(self.config_service, memory_service, self.log_service)
        return {
            "bank_service": bank_service,
            "stats_service": stats_service,
        }

    def _resolve_game_class(self, game: AvailableGames):
        from games.gba.pokemon.fire_red_game import FireRedGame
        from games.gba.pokemon.emerald_game import EmeraldGame

        mapping = {
            AvailableGames.ORIGINAL_FIRE_RED: FireRedGame,
            AvailableGames.RADICAL_FIRE_RED: FireRedGame,
            AvailableGames.EMERALD: EmeraldGame,
            AvailableGames.EMERALD_KAIZO: EmeraldGame
        }
        return mapping[game]

    def create_game(self, game: AvailableGames) -> BaseGame:
        memory_service = self.create_memory_service()
        keyboard_service = self.create_keyboard_service()
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
            **domain_services,
        )