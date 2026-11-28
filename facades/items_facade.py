import redis.asyncio as redis
import hashlib
import json
from dataclasses import asdict
from models.gba.pokemon.compiled_item import CompiledItem  
from models.game_input import GameInput
from facades.base_facade import BaseGameFacade


class ItemsFacade(BaseGameFacade):
    async def get_all_items_gba(self, game_input: GameInput) -> dict[int, CompiledItem]:
        cache_key = self._build_cache_key(game_input) if self._redis is not None else None

        if self._redis is not None and cache_key is not None:
            try:
                cached = await self._redis.get(cache_key)
                if cached:
                    return {
                        item_data["id"]: CompiledItem.dict_to_class(item_data)
                        for item_data in json.loads(cached)
                    }
            except redis.RedisError:
                pass

        items = await self._run_in_thread(
            game_input,
            lambda game: game.items_service.get_all_items(game.memory_service.game_file),
            readonly=True,
        )

        if self._redis is not None and cache_key is not None and items:
            try:
                payload = json.dumps([asdict(item) for item in items.values()])
                await self._redis.set(cache_key, payload, ex=3600)
            except redis.RedisError:
                pass

        return items

    def _build_cache_key(self, game_input: GameInput) -> str | None:
        if game_input.raw_file is not None and len(game_input.raw_file) == 0:
            return None

        selected_game = self._resolve_selected_game(game_input)
        lang = game_input.language or self._global_config.get("CURRENT_LANGUAGE", "EN_US")

        if game_input.raw_file is not None:
            rom_id = hashlib.sha256(game_input.raw_file).hexdigest()[:16]
        else:
            rom_id = "server_default"

        return f"game:{selected_game.name}:{rom_id}:{lang}:items"