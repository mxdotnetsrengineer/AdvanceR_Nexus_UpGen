import asyncio
from enums.gba.games_enum import AvailableGames
from models.gba.pokemon.compiled_item import CompiledItem  
from models.game_api_input import GameAPIInput
from facades.base_facade import BaseGameFacade


class ItemsFacade(BaseGameFacade):
    async def get_all_items_gba(self, game_input: GameAPIInput) -> dict[int, CompiledItem]:
        target_game = self._resolve_game(game_input)
        resolved_game_file = target_game.memory_service.game_file

        return await asyncio.to_thread(
            target_game.items_service.get_all_items,
            resolved_game_file,
        )