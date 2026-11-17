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

    def get_item_name(self, game_file: bytearray, item_id: int, items_table_offset: int | None = None) -> str:
        if items_table_offset is None:
            items_table_offset = self.memory.pointer_to_offset(game_file, self.config.get("ITEMS_POINTER_OFFSET"))

        if not items_table_offset or items_table_offset >= len(game_file):
            return "UNKNOWN"

        item_struct_offset = self.memory.get_struct_offset(items_table_offset, item_id, self.config.get("ITEM_STRUCT_SIZE"))
        return self.memory.read_string(game_file, item_struct_offset, max_length=14)

    def randomize_pokeballs(self, game_file: bytearray, quantity: int = 1) -> bytearray:
        items_table_offset = self.memory.pointer_to_offset(game_file, self.config.get("ITEMS_POINTER_OFFSET"))
        max_item_id = self.config.get("MAX_ITEM_ID")

        while True:
            random_new_item = random.randint(1, max_item_id)
            item_name = self.get_item_name(game_file, random_new_item, items_table_offset)
            if "???" not in item_name and item_name != "UNKNOWN":
                break

        new_script_bytes = bytearray([
            0x1A, 0x00, 0x80, random_new_item & 0xFF, (random_new_item >> 8) & 0xFF,
            0x1A, 0x01, 0x80, quantity & 0xFF, (quantity >> 8) & 0xFF,
            0x09, 0x01,
            0x02,
        ])

        self.log.info(self.translator.translate("items.pokeball_repointed", item_id=random_new_item, item_name=item_name), False)
        return new_script_bytes
    # End Public Methods