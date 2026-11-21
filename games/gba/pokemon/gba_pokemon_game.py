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
        _self,
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
        wild_service: WildService
    ):
        super().__init__(
            game=game,
            file_service=file_service,
            log_service=log_service,
            memory_service=memory_service,
            config_service=config_service,
            translations_service=translations_service,
        )
        _self.bank_service = bank_service
        _self.keyboard_service = keyboard_service
        _self.stats_service = stats_service
        _self.items_service= items_service
        _self.wild_service = wild_service
        _self.events_service = events_service

    # Public Methods
    async def process_game(_self) -> None:
        _self.log_service.info(
            _self.translations_service.translate(
                "messages.games.starting_modification",
                game_name=_self._get("GAME_NAME"),
            )
        )

        bank_cont = f"rom:{_self.game.name}:banks"
        stats_cont = f"rom:{_self.game.name}:stats"
        items_cont = f"rom:{_self.game.name}:items"

        banks_json, stats_json, items_json = await _self.client.mget( [bank_cont, stats_cont, items_cont])
        if not all([banks_json, stats_json, items_json]):
            await asyncio.gather(
                _self.bank_service.allocate_banks(_self.memory_service.game_file),
                _self.stats_service.get_all_species_data(_self.memory_service.game_file),
                _self.items_service.get_all_items(_self.memory_service.game_file)
            )

            async with _self.client.pipeline() as pipe:
                pipe.set(stats_cont, json.dumps([asdict(stat) for stat in _self.stats_service.stats]), ex=3600)
                pipe.set(items_cont, json.dumps([asdict(item) for item in _self.items_service.items]), ex=3600)
                await pipe.execute()
        else:
            _self.bank_service.load_from_json(banks_json)
            _self.stats_service.load_from_json(stats_json)
            _self.items_service.load_from_json(items_json)

        await _self.__process_banks_modifications(_self.memory_service.game_file)
        if not banks_json:
            await _self.client.set(
                bank_cont,
                json.dumps([asdict(bank) for bank in _self.bank_service.banks]),
                ex=3600
            )

        await _self.__configure_spanish_keyboard()
        _self.file_service.save_new_game_file(
            _self.memory_service.game_file,
            _self._get("MODIFIED_GAME"),
        )
    # End Public Methods

    # Protected Methods
    def _apply_game_specific_changes() -> None:
        pass
    # End Protected Methods

    # Private Methods
    async def __process_banks_modifications(_self, game_file: bytearray):
        
        species_by_id = {pokemon.id: pokemon for pokemon in _self.stats_service.stats}
        wild_events = _self.wild_service.get_wild_data(game_file, _self.stats_service.stats)

        for bank in _self.bank_service.banks:
            _self.log_service.info(
                    _self.translations_service.translate(
                        "messages.banks.bank_entry",
                        bank_id=f"{bank.bank_id:2d}",
                        offset=hex(bank.header_offset),
                    ), False)
            for map in bank.maps:
                _self.log_service.info(
                    _self.translations_service.translate(
                        "messages.banks.map_entry",
                        map_id=f"{map.map_id:2d}",
                        name=f"{map.name:<15s}",
                        header=hex(map.header_offset),
                        width=f"{map.width:3d}",
                        height=f"{map.height:3d}",
                    ), False)
                _self.events_service.find_map_events(game_file, map)
                
                for event in map.events:
                    _self.events_service.process_event_by_id(event,[
                        [
                            _self._get("POKEBALL_SPRITE_ID"),
                            lambda ev: _self.items_service.execute_item_function(
                                game_file,
                                ev,
                                lambda gf, ev : (
                                    (new_script_bytes := _self.items_service.randomize_pokeballs(gf)) and
                                    _self.events_service.change_event_item_with_random(gf,ev, new_script_bytes) 
                                )
                            )
                        ]   
                    ] )
                    
                for wild_table_offset in wild_events.offsets:
                    selected_species = _self.wild_service.select_wild_species(
                        bank=bank,
                        compiled_map=map,
                        wild_grass_slot_count=wild_events.events_count,
                        wild_table_offset=wild_table_offset,
                        wild_candidates=wild_events.species,
                        game_file=game_file,
                    )
                    
                    if not selected_species:
                        continue
                    _self.wild_service.randomize_wild_encounters(
                        bank=bank,
                        compiled_map=map,
                        wild_grass_slot_count=wild_events.events_count,
                        wild_table_offset=wild_table_offset,
                        selected_species=selected_species,
                        species_by_id=species_by_id,
                        game_file=game_file,
                    )
                    
    async def __configure_spanish_keyboard(_self) -> None:
        keyboard_layout = GameUIKeyboard(
            default=copy.deepcopy(GBA_POKEMON_NAMING_UPPER_KEYBOARD),
            lower=copy.deepcopy(GBA_POKEMON_NAMING_LOWER_KEYBOARD),
            others=copy.deepcopy(GBA_POKEMON_NAMING_OTHERS_KEYBOARD),
            logic=GameUIKeyboardLogic(
                default=GBA_POKEMON_NAMING_UPPER_LOGIC,
                lower=GBA_POKEMON_NAMING_LOWER_LOGIC,
                others=GBA_POKEMON_NAMING_OTHERS_LOGIC,
                offsets=[
                    _self._get("UPPER_KEYBOARD_CHARS_OFFSET"),
                    _self._get("LOWER_KEYBOARD_CHARS_OFFSET"),
                    _self._get("OTHERS_KEYBOARD_CHARS_OFFSET"),
                ],
            ),
        )
        await _self.keyboard_service.set_spanish_chars(
            _self.memory_service.game_file,
            _self.game,
            keyboard_layout,
            _self._get("DEFAULT_UI_KEYBOARD_SEPARATORS"),
        )
    # End Private Methods