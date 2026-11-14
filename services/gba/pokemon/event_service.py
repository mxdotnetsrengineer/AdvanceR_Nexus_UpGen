from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_event import CompiledEvent
from decorators.app_decorators import when_enabled,skip_when_disabled,when_any_enabled
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.item_service import ItemService

class EventService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        item_service: ItemService,
        translations_service: TranslationsService,
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.items: ItemService = item_service
        self.translator = translations_service

    # Public Methods
    @skip_when_disabled("ONLY_DATABASE")
    @when_any_enabled("RANDOMIZE_POKEBALLS_ITEMS","MAPS_EVENTS")
    def find_map_events(self, game_file: bytearray, map_data: CompiledMap) -> None:
        events_pointer = self.memory.gba_pointer_to_file_offset(game_file, map_data.header_offset + 4)
        event_list_pointer = None

        if events_pointer and events_pointer < len(game_file):
            map_data.events_count = game_file[events_pointer]
            event_list_pointer = self.memory.gba_pointer_to_file_offset(game_file, events_pointer + 4)

        if not event_list_pointer:
            return

        self.log.info(self.translator.translate("events.total_events", count=map_data.events_count))
        self.memory.free_space = self.config.get("FREE_SPACE_START")
        for event_idx in range(map_data.events_count):
            event_base_offset = event_list_pointer + (event_idx * 24)

            if event_base_offset + 20 < len(game_file):
                sprite_id = game_file[event_base_offset + 1]
                original_event_offset = self.memory.gba_pointer_to_file_offset(game_file, event_base_offset + 16)

                current_event = CompiledEvent(
                    event_id=event_idx,
                    sprite_id=sprite_id,
                    header_offset=original_event_offset,
                )
                if self.config.get("RANDOMIZE_POKEBALLS_ITEMS"):
                    self._process_event_with_items(current_event, game_file, event_base_offset)
    # End Public Methods

    # Private Methods
    def _process_event_with_items(self, event: CompiledEvent, game_file: bytearray, event_base_offset: int) -> None:
        if event.sprite_id == self.config.get("POKEBALL_SPRITE_ID"):
            event_has_item = False
            if event.header_offset is not None and 0 <= event.header_offset < len(game_file):
                original_script_bytes = game_file[event.header_offset : event.header_offset + 20]
                event_has_item = 0x1A in original_script_bytes and b"\x09\x01" in original_script_bytes

            if event_has_item:
                new_script_bytes = self.items.randomize_pokeballs(game_file)
                allocated_offset = self.memory.find_free_space(len(new_script_bytes), self.memory.free_space)

                if allocated_offset:
                    game_file[allocated_offset : allocated_offset + len(new_script_bytes)] = new_script_bytes
                    self.memory.free_space = allocated_offset + len(new_script_bytes)

                    gba_pointer_address = allocated_offset + 0x08000000
                    game_file[event_base_offset + 16 : event_base_offset + 20] = gba_pointer_address.to_bytes(4, byteorder="little")
                    self.log.info( self.translator.translate("events.new_script", offset=hex(allocated_offset)), False)
                else:
                    self.log.warning(self.translator.translate("events.pokeball_failed"))
    # End Private Methods