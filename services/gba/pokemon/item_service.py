import random
from collections.abc import Callable
from models.gba.pokemon.compiled_event import CompiledEvent
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE, STRING_TERMINATOR
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService

class ItemService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService,
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.translator = translations_service

    # Public Methods
    def get_all_items(self, game_file: bytearray) -> dict[int, str]:
        items_table_offset = self.memory.pointer_to_offset(game_file, self.config.get("ITEMS_POINTER_OFFSET"))

        if not items_table_offset or items_table_offset >= len(game_file):
            self.log.warning(self.translator.translate("warnings.invalid_items_pointer"))
            return {}

        items: dict[int, str] = {}
        for item_id in range(self.config.get("MAX_ITEM_ID") + 1):
            item_name = self.get_item_name(game_file, item_id, items_table_offset)
            items[item_id] = item_name
            self.log.info(self.translator.translate("items.item_entry", item_id=item_id, item_name=item_name), False)

        return items

    def execute_item_function(
    _self,
    game_file: bytearray,
    event: CompiledEvent,
    script_entry_offset: int,
    item_handler: Callable[[bytearray], bytes | bytearray],
    ) -> None:
        """If is item execute function."""
        
        game_size = len(game_file)
        script_scan_window = 5 * GBA_PTR_BYTE_SIZE  # 20 bytes covers standard giveitem script (~13-15 bytes)
        copyvar_opcode = 0x1A
        std_obtain_item_bytes = b"\x09\x01"

        event_has_item = False
        if event.header_offset is not None and 0 <= event.header_offset < game_size:
            scan_end = min(event.header_offset + script_scan_window, game_size)
            original_script_bytes = game_file[event.header_offset : scan_end]
            event_has_item = copyvar_opcode in original_script_bytes and std_obtain_item_bytes in original_script_bytes
        
        if event_has_item:
            item_handler(game_file, script_entry_offset)

    def randomize_pokeballs(self, game_file: bytearray, quantity: int = 1) -> bytearray:
        """Generate a randomized giveitem script bytearray for a Poké Ball event."""
        items_ptr = self.config.get("ITEMS_POINTER_OFFSET")
        items_table_ptr = game_file[items_ptr : items_ptr + GBA_PTR_BYTE_SIZE]
        items_table_offset = self.memory.pointer_to_offset(items_table_ptr)

        if items_table_offset is None:
            return bytearray()

        max_item_id = self.config.get("MAX_ITEM_ID")

        while True:
            random_new_item = random.randint(1, max_item_id)
            item_name = self.get_item_name(game_file, random_new_item, items_table_offset)
            if "???" not in item_name and item_name != "UNKNOWN":
                break

        # Gen III XSE Script opcodes for obtaining an item:
        # copyvarifnotzero (0x1A) + var 0x8000 (item) / 0x8001 (qty) + callstd 1 (0x09 0x01) + end (0x02)
        copyvar_opcode = 0x1A
        var_item_low, var_item_high = 0x00, 0x80
        var_qty_low, var_qty_high = 0x01, 0x80
        callstd_opcode, std_obtain_item = 0x09, 0x01
        end_opcode = 0x02

        new_script_bytes = bytearray([
            copyvar_opcode, var_item_low, var_item_high, random_new_item & STRING_TERMINATOR, (random_new_item >> 8) & STRING_TERMINATOR,
            copyvar_opcode, var_qty_low, var_qty_high, quantity & STRING_TERMINATOR, (quantity >> 8) & STRING_TERMINATOR,
            callstd_opcode, std_obtain_item,
            end_opcode,
        ])

        self.log.info(
            self.translator.translate("items.pokeball_repointed", item_id=random_new_item, item_name=item_name),
            False,
        )
        return new_script_bytes
    # End Public Methods
    # Private Methods
    def get_item_name(self, game_file: bytearray, item_id: int, items_table_offset: int | None = None) -> str:
        """Resolve the readable name of an item by its ID from the item data table."""
        game_size = len(game_file)
        item_name_max_length = 14 # In Gen III, item structs allocate 14 bytes for the name (13 characters + 1 terminator byte 0xFF)

        if items_table_offset is None:
            items_ptr = self.config.get("ITEMS_POINTER_OFFSET")
            if items_ptr is None or items_ptr + GBA_PTR_BYTE_SIZE > game_size:
                return "UNKNOWN"

            items_table_ptr = game_file[items_ptr : items_ptr + GBA_PTR_BYTE_SIZE]
            items_table_offset = self.memory.pointer_to_offset(items_table_ptr)

        if items_table_offset is None or items_table_offset >= game_size:
            return "UNKNOWN"

        item_struct_size = self.config.get("ITEM_STRUCT_SIZE")
        item_struct_offset = items_table_offset + (item_id * item_struct_size)

        if item_struct_offset + item_name_max_length > game_size:
            return "UNKNOWN"

        return self.memory.read_string(game_file, item_struct_offset, max_length=item_name_max_length)
    # Private Methods