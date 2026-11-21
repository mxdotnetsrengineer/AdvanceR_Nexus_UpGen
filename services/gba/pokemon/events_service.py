
from typing import Callable
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

class EventsService:
    def __init__(
        _self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService
    ):
        _self.config = config_service
        _self.memory = memory_service
        _self.log = log_service
        _self.translator = translations_service

    # Public Methods
    @skip_when_enabled("ONLY_DATABASE")
    @when_enabled("MAPS_EVENTS")
    def find_map_events(_self, game_file: bytearray, map_data: CompiledMap) -> None:
        """Parse the map's event header and iterate through its object events."""
        game_size = len(game_file)
        map_data.events = []

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
                entry_offset=script_entry_offset
            )
            map_data.events.append(current_event)

    @when_enabled("RANDOMIZE_POKEBALLS_ITEMS")
    def process_event_by_id(_self, event: CompiledEvent, sprite_handlers: list[tuple[int, Callable[[], None]]]) -> None:
        """Execute the matching function for an event with the specified sprite ID (e.g., a Poké Ball to randomize items)."""
        for target_sprite_id, action in sprite_handlers:
            if event.sprite_id == target_sprite_id:
                action(event)
                break

    def change_event_item_with_random(_self, game_file: bytearray, event: CompiledEvent, new_script_bytes:bytearray):
        """write randomized item script to free space, and repoint the event entry."""
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

        if event.entry_offset < 0 or event.entry_offset + GBA_PTR_BYTE_SIZE > len(game_file):
            return

        game_file[new_script_offset : new_script_offset + script_size] = new_script_bytes
        _self.memory.free_space_offset = new_script_offset + script_size

        new_script_ptr_bytes = _self.memory.offset_to_pointer_bytes(new_script_offset)
        game_file[event.entry_offset : event.entry_offset + GBA_PTR_BYTE_SIZE] = new_script_ptr_bytes

        _self.log.info(
            _self.translator.translate("events.new_script", offset=hex(new_script_offset)),
        False) 
    # End Public Methods