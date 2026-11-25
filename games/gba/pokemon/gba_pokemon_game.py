
import redis.asyncio as redis
import copy
import asyncio
import json
from dataclasses import asdict
from enums.gba.games_enum import AvailableGames
from helpers.gba.pokemon.gba_pokemon_helper import (GBA_POKEMON_NAMING_UPPER_KEYBOARD, GBA_POKEMON_NAMING_UPPER_LOGIC, 
    GBA_POKEMON_NAMING_LOWER_KEYBOARD, GBA_POKEMON_NAMING_LOWER_LOGIC, GBA_POKEMON_NAMING_OTHERS_KEYBOARD,GBA_POKEMON_NAMING_OTHERS_LOGIC)
from models.gba.pokemon.game_ui_keyboard import GameUIKeyboard
from models.gba.pokemon.game_ui_keyboard_logic import GameUIKeyboardLogic
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.bank_service import BankService
from services.gba.pokemon.item_service import ItemService
from services.gba.pokemon.events_service import EventsService
from services.gba.pokemon.wild_service import WildService
from services.gba.pokemon.keyboard_service import GBAKeyboardService
from services.gba.pokemon.stats_service import StatsService
from games.gba.gba_game import GBAGame
class GBAPokemonGame(GBAGame):
    def __init__(
        self,
        game: AvailableGames,
        file_service: FileService,
        log_service: LogService,
        memory_service: GBAMemoryService,
        config_service: ConfigService,
        bank_service: BankService,
        keyboard_service: GBAKeyboardService,
        translations_service: TranslationsService,
        stats_service: StatsService,
        events_service: EventsService,
        items_service: ItemService,
        wild_service: WildService,
        redis_client: redis.Redis | None = None,
    ):
        super().__init__(
            game=game,
            file_service=file_service,
            log_service=log_service,
            memory_service=memory_service,
            config_service=config_service,
            translations_service=translations_service,
            redis_client=redis_client,
        )
        self.bank_service = bank_service
        self.keyboard_service = keyboard_service
        self.stats_service = stats_service
        self.items_service= items_service
        self.wild_service = wild_service
        self.events_service = events_service

    # Public Methods
    async def process_game(self) -> None:
        self.log_service.info(
            self.translations_service.translate(
                "messages.games.starting_modification",
                game_name=self._get("GAME_NAME"),
            )
        )
        try:
            cache_hit = await self.__load_from_cache()
            if not cache_hit:
                await asyncio.gather(
                    asyncio.to_thread(self.bank_service.allocate_banks, self.memory_service.game_file),
                    asyncio.to_thread(self.stats_service.get_all_species_data, self.memory_service.game_file),
                    asyncio.to_thread(self.items_service.get_all_items, self.memory_service.game_file),
                )

            await self.__process_banks_modifications(self.memory_service.game_file)

            if not cache_hit:
                await self.__save_to_cache()
        finally:
            if self.client is not None:
                await self.client.aclose()

        self.__configure_spanish_keyboard()
        self.file_service.save_new_game_file(
            self.memory_service.game_file,
            self._get("MODIFIED_GAME"),
        )
    # End Public Methods

    # Protected Methods
    def _apply_game_specific_changes(self) -> None:
        pass
    # End Protected Methods

    # Private Methods
    async def __load_from_cache(self) -> bool:
        """Attempt to hydrate banks, stats, and items from Redis; return False if unavailable or missed."""
        if self.client is None:
            return False

        keys = [
            f"game:{self.game.name}:banks",
            f"game:{self.game.name}:stats",
            f"game:{self.game.name}:items",
        ]
        try:
            banks_json, stats_json, items_json = await self.client.mget(keys)
            if not all([banks_json, stats_json, items_json]):
                return False

            self.bank_service.load_from_json(banks_json)
            self.stats_service.load_from_json(stats_json)
            self.items_service.load_from_json(items_json)
            return True
        except redis.RedisError:
            return False

    async def __save_to_cache(self) -> None:
        """Persist compiled banks, stats, and items into Redis if available."""
        if self.client is None:
            return

        try:
            async with self.client.pipeline() as pipe:
                pipe.set(f"game:{self.game.name}:banks", json.dumps([asdict(bank) for bank in self.bank_service.banks]), ex=3600)
                pipe.set(f"game:{self.game.name}:stats", json.dumps([asdict(stat) for stat in self.stats_service.stats]), ex=3600)
                pipe.set(f"game:{self.game.name}:items", json.dumps([asdict(item) for item in self.items_service.items.values()]), ex=3600)
                await pipe.execute()
        except redis.RedisError:
            pass

    async def __process_banks_modifications(self, game_file: bytearray):
        
        species_by_id = {pokemon.id: pokemon for pokemon in self.stats_service.stats}
        wild_events = self.wild_service.get_wild_data(game_file, self.stats_service.stats)

        for bank in self.bank_service.banks:
            self.log_service.info(
                    self.translations_service.translate(
                        "messages.banks.bank_entry",
                        bank_id=f"{bank.bank_id:2d}",
                        offset=hex(bank.header_offset),
                    ), False)
            for map in bank.maps:
                self.log_service.info(
                    self.translations_service.translate(
                        "messages.banks.map_entry",
                        map_id=f"{map.map_id:2d}",
                        name=f"{map.name:<15s}",
                        header=hex(map.header_offset),
                        width=f"{map.width:3d}",
                        height=f"{map.height:3d}",
                    ), False)
                self.events_service.find_map_events(game_file, map)
                
                for event in map.events:
                    self.events_service.process_event_by_id(event,[
                        [
                            self._get("POKEBALL_SPRITE_ID"),
                            lambda ev: self.items_service.execute_item_function(
                                game_file,
                                ev,
                                lambda gf, ev : (
                                    (new_script_bytes := self.items_service.randomize_pokeballs(gf)) and
                                    self.events_service.change_event_item_with_random(gf,ev, new_script_bytes) 
                                )
                            )
                        ]   
                    ] )
                    
                for wild_table_offset in wild_events.offsets:
                    selected_species = self.wild_service.select_wild_species(
                        bank=bank,
                        compiled_map=map,
                        wild_grass_slot_count=wild_events.events_count,
                        wild_table_offset=wild_table_offset,
                        wild_candidates=wild_events.species,
                        game_file=game_file,
                    )
                    
                    if not selected_species:
                        continue
                    self.wild_service.randomize_wild_encounters(
                        bank=bank,
                        compiled_map=map,
                        wild_grass_slot_count=wild_events.events_count,
                        wild_table_offset=wild_table_offset,
                        selected_species=selected_species,
                        species_by_id=species_by_id,
                        game_file=game_file,
                    )
                    
    def __configure_spanish_keyboard(self) -> None:
        keyboard_layout = GameUIKeyboard(
            default=copy.deepcopy(GBA_POKEMON_NAMING_UPPER_KEYBOARD),
            lower=copy.deepcopy(GBA_POKEMON_NAMING_LOWER_KEYBOARD),
            others=copy.deepcopy(GBA_POKEMON_NAMING_OTHERS_KEYBOARD),
            logic=GameUIKeyboardLogic(
                default=GBA_POKEMON_NAMING_UPPER_LOGIC,
                lower=GBA_POKEMON_NAMING_LOWER_LOGIC,
                others=GBA_POKEMON_NAMING_OTHERS_LOGIC,
                offsets=[
                    self._get("UPPER_KEYBOARD_CHARS_OFFSET"),
                    self._get("LOWER_KEYBOARD_CHARS_OFFSET"),
                    self._get("OTHERS_KEYBOARD_CHARS_OFFSET"),
                ],
            ),
        )
        self.keyboard_service.set_spanish_chars(
            self.memory_service.game_file,
            self.game,
            keyboard_layout,
            self._get("DEFAULT_UI_KEYBOARD_SEPARATORS"),
        )
    # End Private Methods