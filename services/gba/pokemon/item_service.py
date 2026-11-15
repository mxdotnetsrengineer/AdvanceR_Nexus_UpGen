import random
from helpers.gba.games_helper import GBA_POKEMON_III_CHAR_TABLE
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
        base_items_offset = self.memory.gba_pointer_to_file_offset(
            game_file, self.config.get("ITEMS_POINTER_OFFSET")
        )

        if not base_items_offset or base_items_offset >= len(game_file):
            self.log.warning(self.translator.translate("warnings.invalid_items_pointer"))
            return {}

        items: dict[int, str] = {}
        max_item_id = self.config.get("MAX_ITEM_ID")

        for item_id in range(max_item_id + 1):
            item_name = self.get_item_name(game_file, item_id)
            items[item_id] = item_name
            self.log.info(
                self.translator.translate(
                    "items.item_entry",
                    item_id=item_id,
                    item_name=item_name,
                ), False
            )

        return items
    def get_item_name(self, game_file: bytearray, item_id: int) -> str:
        base_items_offset = self.memory.gba_pointer_to_file_offset(game_file, self.config.get("ITEMS_POINTER_OFFSET"))

        if not base_items_offset or base_items_offset >= len(game_file):
            return "UNKNOWN"

        target_item_offset = base_items_offset + (item_id * self.config.get("ITEM_STRUCT_SIZE"))
        if target_item_offset >= len(game_file):
            return "UNKNOWN"

        item_name = ""
        offset = target_item_offset
        max_string_end = target_item_offset + 14

        while offset < max_string_end and offset < len(game_file):
            char_byte = game_file[offset]
            if char_byte == 0xFF:
                break
            item_name += GBA_POKEMON_III_CHAR_TABLE.get(char_byte, "?")
            offset += 1

        return item_name if item_name.strip() else "UNKNOWN"

    def randomize_pokeballs(self, game_file: bytearray, quantity: int = 1) -> bytearray:
        item_name = ""
        random_new_item = -1

        while True:
            random_new_item = random.randint(1, self.config.get("MAX_ITEM_ID"))
            item_name = self.get_item_name(game_file, random_new_item)
            if "???" in item_name or item_name == "UNKNOWN":
                continue
            break

        new_script_bytes = bytearray([
            0x1A, 0x00, 0x80, random_new_item & 0xFF, (random_new_item >> 8) & 0xFF,
            0x1A, 0x01, 0x80, quantity & 0xFF, (quantity >> 8) & 0xFF,
            0x09, 0x01,
            0x02,
        ])

        self.log.info(
            self.translator.translate(
                "items.pokeball_repointed",
                item_id=random_new_item,
                item_name=item_name,
            ), False
        )
        return new_script_bytes
    # End Public Methods