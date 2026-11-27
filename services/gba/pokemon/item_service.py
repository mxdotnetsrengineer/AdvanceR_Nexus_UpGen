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
from services.error_service import ErrorService
from services.gba.memory_service import GBAMemoryService

class ItemService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService,
        error_service: ErrorService,
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.translator = translations_service
        self.errors = error_service

        self.items: dict[int, CompiledItem] = {}
        self._valid_random_item_ids: list[int] | None = None

    # Public Methods
    def get_all_items(self, game_file: bytearray) -> dict[int, CompiledItem]:
        """Read and parse all items from the game file item data table up to MAX_ITEM_ID."""
        items_ptr_offset = self.config.get("ITEMS_POINTER_OFFSET")
        ptr_data = (
            self.memory.read_u32_array(game_file, items_ptr_offset, count=1)
            if items_ptr_offset is not None
            else ()
        )
        
        items_table_offset = (
            self.memory.pointer_to_offset(ptr_data[0]) if ptr_data else None
        )

        if items_table_offset is None or items_table_offset >= len(game_file):
            self.log.warning(self.translator.translate("warnings.invalid_items_pointer"))
            return {}

        self.log.raw("=" * 80)
        self.log.info(
        self.translator.translate(
            "messages.items.table_header", s1=f"{'':<4}", s2=f"{'':<11}", s3=f"{'':<9}", s4=f"{'':<4}", s5=f"{'':<3}"
        ),False)
        self.log.raw("=" * 80)

        items: dict[int, CompiledItem] = {}
        for item_id in range(self.config.get("MAX_ITEM_ID") + 1):
            item = self._get_item_data(game_file, item_id, items_table_offset)
            if item:
                items[item_id] = item
                self.log.info(
                    self.translator.translate(
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
        self.items = items
        self._valid_random_item_ids = None
        return items

    @staticmethod
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

    def randomize_pokeballs(self, game_file: bytearray, quantity: int = 1) -> bytearray:
        """Generate a randomized giveitem script bytearray for a Poké Ball event."""
        items_ptr = self.config.get("ITEMS_POINTER_OFFSET")
        items_table_ptr = game_file[items_ptr : items_ptr + GBA_PTR_BYTE_SIZE]
        items_table_offset = self.memory.pointer_to_offset(items_table_ptr)

        if items_table_offset is None:
            return bytearray()

        valid_ids = self._get_valid_item_ids(game_file, items_table_offset)
        random_new_item = random.choice(valid_ids) if valid_ids else 1

        if random_new_item in self.items:
            item_name = self.items[random_new_item].name
        else:
            item_name = self._get_item_name(game_file, random_new_item, items_table_offset)

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

        self.log.info(self.translator.translate("items.pokeball_repointed", item_id=random_new_item, item_name=item_name),False)
        return new_script_bytes

    def load_from_json(self, items_json: str) -> None:
        """Deserialize a JSON string into a dictionary of CompiledItem instances keyed by ID."""
        self.items = {
            item_data["id"]: CompiledItem.dict_to_class(item_data)
            for item_data in json.loads(items_json)
        }
        self._valid_random_item_ids = None
        
    # End Public Methods
    # Private Methods
    def _get_valid_item_ids(self, game_file: bytearray, items_table_offset: int) -> list[int]:
        if self._valid_random_item_ids is not None:
            return self._valid_random_item_ids

        if self.items:
            self._valid_random_item_ids = [
                item_id
                for item_id, item in self.items.items()
                if item_id > 0 and "???" not in item.name and item.name != "UNKNOWN"
            ]
            return self._valid_random_item_ids

        max_item_id = self.config.get("MAX_ITEM_ID")
        valid_ids: list[int] = []
        for item_id in range(1, max_item_id + 1):
            name = self._get_item_name(game_file, item_id, items_table_offset)
            if "???" not in name and name != "UNKNOWN":
                valid_ids.append(item_id)

        self._valid_random_item_ids = valid_ids
        return valid_ids
    
    def _get_item_name(self, game_file: bytearray, item_id: int, items_table_offset: int | None = None) -> str:
        """Resolve the readable name of an item by its ID from the item data table."""
        item = self._get_item_data(game_file, item_id, items_table_offset)
        return item.name if item else "UNKNOWN"

    def _get_item_data(self, game_file: bytearray, item_id: int, items_table_offset: int | None = None,):
        """Read the 44-byte item structure by its ID from the item table and return a item object."""
        game_size = len(game_file)

        if items_table_offset is None:
            items_ptr = self.config.get("ITEMS_POINTER_OFFSET")
            if items_ptr is None or items_ptr + GBA_PTR_BYTE_SIZE > game_size:
                return None

            items_table_offset = self.memory.pointer_to_offset(
                game_file[items_ptr : items_ptr + GBA_PTR_BYTE_SIZE]
            )

        item_struct_size = self.config.get("ITEM_STRUCT_SIZE")
        if items_table_offset is None or item_struct_size is None:
            return None

        item_struct_offset = items_table_offset + (item_id * item_struct_size)
        if item_struct_offset < 0 or item_struct_offset + item_struct_size > game_size:
            return None

        name = self.memory.read_string(
            game_file, item_struct_offset, max_length=14
        )

        data = self.memory.unpack(game_file, item_struct_offset + 0x10, "<H8xBB")
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
