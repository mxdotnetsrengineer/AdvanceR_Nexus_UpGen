
import random
from operator import attrgetter
from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_event import CompiledEvent
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from decorators.app_decorators import when_enabled,skip_when_enabled
from helpers.gba.games_helper import U16_BYTE_SIZE, GBA_PTR_BYTE_SIZE
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.item_service import ItemService
from services.gba.pokemon.wild_service import WildService
from services.gba.pokemon.difficulty_service import DifficultyService

class EventService:
    def __init__(
        _self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService,
        item_service: ItemService,
        wild_services: WildService,
        difficulty_service: DifficultyService,
    ):
        _self.config = config_service
        _self.memory = memory_service
        _self.log = log_service
        _self.items = item_service
        _self.wilds = wild_services 
        _self.difficulty = difficulty_service
        _self.translator = translations_service

        _self.wild_slot_struct_size = _self.config.get("WILD_SLOT_STRUCT_SIZE")

        _self._randomized_slots_offsets: set[int] = set()

    # Public Methods
    @skip_when_enabled("ONLY_DATABASE")
    @when_enabled("MAPS_EVENTS")
    def find_map_events(_self, game_file: bytearray, map_data: CompiledMap) -> None:
        """Parse the map's event header and iterate through its object events."""
        game_size = len(game_file)

        # Map Header: [0..3] Layout Ptr | [4..7] Events Header Ptr
        events_entry_offset = map_data.header_offset + GBA_PTR_BYTE_SIZE
        if events_entry_offset + GBA_PTR_BYTE_SIZE > game_size:
            return

        events_header_ptr = game_file[events_entry_offset : events_entry_offset + GBA_PTR_BYTE_SIZE]
        events_header_offset = _self.memory.pointer_to_offset(events_header_ptr)

        # Events Header first 8 bytes: [0..3] 4 Event Counts | [4..7] Object Events List Ptr
        if events_header_offset is None or events_header_offset + (2 * GBA_PTR_BYTE_SIZE) > game_size:
            return

        map_data.events_count = game_file[events_header_offset]
        event_list_entry_offset = events_header_offset + GBA_PTR_BYTE_SIZE
        event_list_ptr = game_file[event_list_entry_offset : event_list_entry_offset + GBA_PTR_BYTE_SIZE]
        event_list_offset = _self.memory.pointer_to_offset(event_list_ptr)

        if event_list_offset is None or event_list_offset >= game_size:
            return

        _self.log.info(_self.translator.translate("events.total_events", count=map_data.events_count))
        _self.memory.free_space_offset = _self.config.get("FREE_SPACE_START")

        # Object Event Struct = 24 bytes (6 words of 4 bytes)
        # Script Ptr is at byte 16 (4 * GBA_PTR_BYTE_SIZE) and ends at byte 20 (5 * GBA_PTR_BYTE_SIZE)
        event_struct_size = 6 * GBA_PTR_BYTE_SIZE
        script_field_offset = 4 * GBA_PTR_BYTE_SIZE
        script_field_end = 5 * GBA_PTR_BYTE_SIZE
        sprite_byte_index = 1

        for event_idx in range(map_data.events_count):
            event_struct_offset = event_list_offset + (event_idx * event_struct_size)

            if event_struct_offset + script_field_end > game_size:
                break

            sprite_id = game_file[event_struct_offset + sprite_byte_index]
            script_entry_offset = event_struct_offset + script_field_offset
            script_ptr = game_file[script_entry_offset : script_entry_offset + GBA_PTR_BYTE_SIZE]
            script_offset = _self.memory.pointer_to_offset(script_ptr)

            current_event = CompiledEvent(
                event_id=event_idx,
                sprite_id=sprite_id,
                header_offset=script_offset,
            )

            _self.__process_event_with_items(current_event, game_file, script_entry_offset)

    def select_wild_species(
        _self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_grass_slot_count: int,
        wild_table_offset: int,
        wild_candidates: list[CompiledBaseStats],
        game_file: bytearray,
    ) -> list[CompiledBaseStats]:
        """Select and sort wild Pokémon candidates by BST based on each slot's average encounter level."""
        game_size = len(game_file)
        if wild_table_offset is None or wild_table_offset < 0 or not wild_candidates:
            return []
        slots_list_offset = _self.wilds.get_wild_species(
            bank, compiled_map, wild_table_offset, game_file, _self._randomized_slots_offsets
        )
        if slots_list_offset is None or slots_list_offset < 0 or slots_list_offset >= game_size:
            return []

        if _self.config.get("CURRENT_DIFFICULTY"):
            if not _self.difficulty.get_difficulty_pools(wild_grass_slot_count, wild_candidates):
                return []

        _self.wilds.reset_used_candidates()
        selected_species: list[CompiledBaseStats] = []

        for slot_idx in range(wild_grass_slot_count):
            slot_offset = slots_list_offset + (slot_idx * _self.wild_slot_struct_size)
            if slot_offset + _self.wild_slot_struct_size > game_size:
                break

            min_level, max_level = game_file[slot_offset], game_file[slot_offset + 1]
            avg_level = (min_level + max_level) / 2

            chosen_pool = _self.difficulty.get_chosen_pool(avg_level)
            available_elements = _self.wilds.filter_to_unique_candidates(wild_candidates, chosen_pool)
            selected_species.append(_self.wilds.pick_candidate(available_elements))

        selected_species.sort(key=attrgetter("bst"))
        return selected_species

    def randomize_wild_encounters(
        _self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_grass_slot_count: int,
        wild_table_offset: int,
        selected_species: list[CompiledBaseStats],
        species_by_id: dict[int, CompiledBaseStats],
        game_file: bytearray,
    ) -> None:
        """Locate wild encounter data for a map and replace its grass encounter slots."""
        if not selected_species:
            return

        wild_info_offset = _self.wilds.validate_and_get_wild_offset(bank,compiled_map, wild_table_offset,game_file)

        if wild_info_offset is not None:
            _self.__save_randomized_wild_slots(
                game_file=game_file,
                wild_info_offset=wild_info_offset,
                wild_grass_slot_count=wild_grass_slot_count,
                bank=bank,
                compiled_map=compiled_map,
                selected_species=selected_species,
                species_by_id=species_by_id,
            )
    
    # End Public Methods

    # Private Methods
    @when_enabled("RANDOMIZE_POKEBALLS_ITEMS")
    def __process_event_with_items(_self, event: CompiledEvent, game_file: bytearray, script_entry_offset: int) -> None:
        """Check if a Poké Ball event grants an item and repoint it to a randomized item script."""
        
        if event.sprite_id == _self.config.get("POKEBALL_SPRITE_ID"):
            _self.items.execute_item_function(
                game_file,
                event,
                script_entry_offset,
                _self.__randomize_event_item,
            )
                
    def __randomize_event_item(_self, game_file: bytearray, script_entry_offset: int):
        """Generate a randomized item script, write it to free space, and repoint the event entry."""
        new_script_bytes = _self.items.randomize_pokeballs(game_file)
        if not new_script_bytes:
            return

        script_size = len(new_script_bytes)
        new_script_offset = _self.memory.find_free_space_offset(
            game_file=game_file,
            size=script_size,
            start_offset=_self.memory.free_space_offset,
        )

        if new_script_offset is None:
            _self.log.warning(_self.translator.translate("events.pokeball_failed"))
            return

        if script_entry_offset < 0 or script_entry_offset + GBA_PTR_BYTE_SIZE > len(game_file):
            return

        game_file[new_script_offset : new_script_offset + script_size] = new_script_bytes
        _self.memory.free_space_offset = new_script_offset + script_size

        new_script_ptr_bytes = _self.memory.offset_to_pointer_bytes(new_script_offset)
        game_file[script_entry_offset : script_entry_offset + GBA_PTR_BYTE_SIZE] = new_script_ptr_bytes

        _self.log.info(
            _self.translator.translate("events.new_script", offset=hex(new_script_offset)),
            False,
        )

    def __save_randomized_wild_slots(
       _self,
        game_file: bytearray,
        wild_info_offset: int,
        wild_grass_slot_count: int,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        selected_species: list[CompiledBaseStats],
        species_by_id: dict[int, CompiledBaseStats],
    ) -> None:
        """Write randomized species and adjusted levels into each wild encounter slot."""
        game_size = len(game_file)
        # Wild info struct (8 bytes): [encounter_rate: u32, slots_list_ptr: u32]
        slots_entry_offset = wild_info_offset + GBA_PTR_BYTE_SIZE
        if slots_entry_offset + GBA_PTR_BYTE_SIZE > game_size:
            return

        slots_list_ptr = game_file[slots_entry_offset : slots_entry_offset + GBA_PTR_BYTE_SIZE]
        slots_list_offset = _self.memory.pointer_to_offset(slots_list_ptr)

        if slots_list_offset is None or slots_list_offset in _self._randomized_slots_offsets:
            return

        _self._randomized_slots_offsets.add(slots_list_offset)
        replacements_log: list[str] = []

        # Wild slot struct (4 bytes): [min_level: u8, max_level: u8, species_id: u16]

        for slot_idx, new_pokemon in enumerate(selected_species[:wild_grass_slot_count]):
            slot_offset = slots_list_offset + (slot_idx * _self.wild_slot_struct_size)
            if slot_offset + _self.wild_slot_struct_size > game_size:
                break

            species_field_offset = slot_offset + U16_BYTE_SIZE
            old_min_level, old_max_level = game_file[slot_offset], game_file[slot_offset + 1]
            new_min_level, new_max_level = old_min_level, old_max_level
            if _self.config.get("CURRENT_DIFFICULTY"):
                new_min_level = _self.difficulty.calculate_adjusted_level(old_min_level)
                new_max_level = _self.difficulty.calculate_adjusted_level(old_max_level)

            replacements_log.append(
                _self.wilds.get_previous_wild_specie(
                    slot_idx=slot_idx,
                    species_field_offset=species_field_offset,
                    old_min_level=old_min_level,
                    old_max_level=old_max_level,
                    new_pokemon=new_pokemon,
                    new_min_level=new_min_level,
                    new_max_level=new_max_level,
                    species_by_id=species_by_id,
                    game_file=game_file,
                )
            )

            game_file[slot_offset] = new_min_level
            game_file[slot_offset + 1] = new_max_level
            game_file[species_field_offset : species_field_offset + U16_BYTE_SIZE] = new_pokemon.id.to_bytes(
                U16_BYTE_SIZE, byteorder="little"
            )

        bank_label = getattr(bank, "name", f"Bank {bank.bank_id}")
        _self.log.info(
            f"Pasto randomizado en [{bank.bank_id} - {bank_label}] | Mapa [{compiled_map.map_id} - {compiled_map.name}]:\n  "
            + "\n  ".join(replacements_log),
            False,
        )
    # End Private Methods