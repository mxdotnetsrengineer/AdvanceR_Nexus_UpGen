import random
import json
from collections.abc import Callable
from enums.gba.pokemon.gba_pokemon_enums import ItemPockets, ItemSubCategories
from models.gba.pokemon.compiled_event import CompiledEvent
from models.gba.pokemon.compiled_item import CompiledItem
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE, STRING_TERMINATOR
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService

class ItemService:
    def __init__(
        _self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService,
    ):
        _self.config = config_service
        _self.memory = memory_service
        _self.log = log_service
        _self.translator = translations_service

        _self.items = []

    # Public Methods
    async def get_all_items(_self, game_file: bytearray) -> dict[int, str]:
        """Read and parse all items from the game file item data table up to MAX_ITEM_ID."""
        items_ptr_offset = _self.config.get("ITEMS_POINTER_OFFSET")
        ptr_data = (
            _self.memory.read_u32_array(game_file, items_ptr_offset, count=1)
            if items_ptr_offset is not None
            else ()
        )
        
        items_table_offset = (
            _self.memory.pointer_to_offset(ptr_data[0]) if ptr_data else None
        )

        if items_table_offset is None or items_table_offset >= len(game_file):
            _self.log.warning(_self.translator.translate("warnings.invalid_items_pointer"))
            return {}

        _self.log.raw("=" * 80)
        _self.log.info(
        _self.translator.translate(
            "messages.items.table_header", s1=f"{'':<4}", s2=f"{'':<11}", s3=f"{'':<9}", s4=f"{'':<4}", s5=f"{'':<3}"
        ),False)
        _self.log.raw("=" * 80)

        items: dict[int, CompiledItem] = {}
        for item_id in range(_self.config.get("MAX_ITEM_ID") + 1):
            item = _self.__get_item_data(game_file, item_id, items_table_offset)
            if item:
                items[item_id] = item
                _self.log.info(
                    _self.translator.translate(
                        "messages.items.item_entry",
                        id=f"{item.id:03d}",
                        name=f"{item.name:<14}",
                        pocket=f"{item.pocket.name:<10}",
                        pocket_id=item.pocket.value,
                        item_type=f"0x{item.item_type:02X}",
                        price=f"{item.price:5d}"
                    ),
                    False,
                )

        return items

    def execute_item_function(
    __self,
    game_file: bytearray,
    event: CompiledEvent,
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
            item_handler(game_file, event)

    def randomize_pokeballs(_self, game_file: bytearray, quantity: int = 1) -> bytearray:
        """Generate a randomized giveitem script bytearray for a Poké Ball event."""
        items_ptr = _self.config.get("ITEMS_POINTER_OFFSET")
        items_table_ptr = game_file[items_ptr : items_ptr + GBA_PTR_BYTE_SIZE]
        items_table_offset = _self.memory.pointer_to_offset(items_table_ptr)

        if items_table_offset is None:
            return bytearray()

        max_item_id = _self.config.get("MAX_ITEM_ID")

        while True:
            random_new_item = random.randint(1, max_item_id)
            item_name = _self.get_item_name(game_file, random_new_item, items_table_offset)
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

        _self.log.info(_self.translator.translate("items.pokeball_repointed", item_id=random_new_item, item_name=item_name),False)
        return new_script_bytes

    def load_from_json(self, items_json: str) -> None:
        """Deserialize a JSON string into a list of Item instances."""
        self.items = [
            CompiledItem.dict_to_class(item_data) for item_data in json.loads(items_json)
        ]
    # End Public Methods
    # Private Methods
    def get_item_name(_self, game_file: bytearray, item_id: int, items_table_offset: int | None = None) -> str:
        """Resolve the readable name of an item by its ID from the item data table."""
        item = _self.__get_item_data(game_file, item_id, items_table_offset)
        return item.name if item else "UNKNOWN"

    def __get_item_data(_self, game_file: bytearray, item_id: int, items_table_offset: int | None = None,):
        """Read the 44-byte item structure by its ID from the item table and return a item object."""
        game_size = len(game_file)

        if items_table_offset is None:
            items_ptr = _self.config.get("ITEMS_POINTER_OFFSET")
            if items_ptr is None or items_ptr + GBA_PTR_BYTE_SIZE > game_size:
                return None

            items_table_offset = _self.memory.pointer_to_offset(
                game_file[items_ptr : items_ptr + GBA_PTR_BYTE_SIZE]
            )

        item_struct_size = _self.config.get("ITEM_STRUCT_SIZE")
        if items_table_offset is None or item_struct_size is None:
            return None

        item_struct_offset = items_table_offset + (item_id * item_struct_size)
        if item_struct_offset < 0 or item_struct_offset + item_struct_size > game_size:
            return None

        name = _self.memory.read_string(
            game_file, item_struct_offset, max_length=14
        )

        data = _self.memory.unpack(game_file, item_struct_offset + 0x10, "<H8xBB")
        if not data:
            return None

        price, raw_pocket, raw_type = data

        try:
            pocket = ItemPockets(raw_pocket)
        except ValueError:
            pocket = ItemPockets.UNKNOWN

        if pocket == ItemPockets.POKE_BALLS:
            item_type = ItemSubCategories.NONE
        elif pocket == ItemPockets.BERRIES:
            item_type = ItemSubCategories.PARTY_CONSUMABLE
        elif pocket == ItemPockets.KEY_ITEMS and raw_type == 4:
            item_type = ItemSubCategories.NONE
        else:
            try:
                item_type = ItemSubCategories(raw_type)
            except ValueError:
                item_type = ItemSubCategories.UNKNOWN

        return CompiledItem(
            id=item_id,
            name=name,
            pocket=pocket,
            item_type=item_type,
            price=price,
        )
    # Private Methods