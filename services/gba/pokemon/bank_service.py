import json
from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from decorators.app_decorators import when_enabled, skip_when_enabled, when_any_enabled
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE, HEX_NUM_BASE
from helpers.gba.pokemon.gba_pokemon_helper import MAX_BANK_SCAN_BYTES
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.error_service import ErrorService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.events_service import EventsService


class BankService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        error_service: ErrorService,
        events_service: EventsService,
        translations_service: TranslationsService,
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.events = events_service
        self.translator = translations_service
        self.errors = error_service

        self.banks: list[CompiledBank] = []

    # Public Methods
    def get_core_banks_position(self, game_file: bytearray, start_ptr = 0x055000, end_ptr = 0x056000) -> tuple[int | None, int | None]:
        """Scan the standard game memory range to find the pointer to the core map bank table."""
        #Change the pointers for other games, default firered
        game_size = len(game_file)
        banks_to_find = 5

        for candidate_ptr in range(start_ptr, end_ptr, GBA_PTR_BYTE_SIZE):
            bank_table_offset = self.memory.pointer_to_offset(
                game_file[candidate_ptr : candidate_ptr + GBA_PTR_BYTE_SIZE]
            )
            
            if bank_table_offset is None or bank_table_offset + (GBA_PTR_BYTE_SIZE * banks_to_find) > game_size:
                continue

            valid_banks = 0
            for bank_id in range(banks_to_find):
                bank_ptr = bank_table_offset + (bank_id * GBA_PTR_BYTE_SIZE)
                bank_header_offset = self.memory.pointer_to_offset(
                    game_file[bank_ptr : bank_ptr + GBA_PTR_BYTE_SIZE]
                )
                
                if bank_header_offset is not None and bank_header_offset + GBA_PTR_BYTE_SIZE <= game_size:
                    map_list_offset = self.memory.pointer_to_offset(
                        game_file[bank_header_offset : bank_header_offset + GBA_PTR_BYTE_SIZE]
                    )
                    if map_list_offset is not None and map_list_offset < game_size:
                        valid_banks += 1

            if valid_banks == banks_to_find:
                self.log.info(
                    self.translator.translate(
                        "messages.banks.table_pointer_found",
                        ptr_memory=hex(candidate_ptr),
                        offset=hex(bank_table_offset),
                    )
                )
                return candidate_ptr, bank_table_offset

        self.log.warning(self.translator.translate("warnings.banks.pointer_not_found"))
        return None, None
    
    def inspect_core_banks(self, game_file: bytearray) -> None:
        """Inspect entries inside the core map bank table of the game file."""
        bank_table_offset = self.config.get("BANK_TABLE_OFFSET")
        game_size = len(game_file)

        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.banks.parsing_start", offset=hex(bank_table_offset)))
        self.log.raw("=" * 80)
        
        target_id = 0
        for position in range(self.config.get("MAX_BANKS")):
            entry_offset = bank_table_offset + (position * GBA_PTR_BYTE_SIZE)
            if entry_offset + GBA_PTR_BYTE_SIZE > game_size:
                break

            entry_ptr = self.memory.offset_to_pointer(entry_offset)
            target_ptr = game_file[entry_offset : entry_offset + GBA_PTR_BYTE_SIZE]
            target_offset = self.memory.pointer_to_offset(target_ptr)

            if target_offset is None or target_offset + GBA_PTR_BYTE_SIZE > game_size:
                self.log.warning(
                    self.translator.translate(
                        "warnings.banks.empty_table_position",
                        ptr_memory=hex(entry_ptr),
                    )
                )
                continue

            first_map_list_ptr = game_file[target_offset : target_offset + GBA_PTR_BYTE_SIZE]
            first_map_list_offset = self.memory.pointer_to_offset(first_map_list_ptr)
            is_banks_array = first_map_list_offset is not None and first_map_list_offset < game_size
            if is_banks_array:
                target_id+=1

            self.log.info(self.translator.translate("messages.banks.bank_entry", bank_id=f"{target_id:2d}", 
                        offset=hex(target_offset)), False)
            self.log.raw("-" * 80)

    def allocate_banks(self, game_file: bytearray) -> None:
        """Read and allocate the map banks directly from the bank table file offset."""
        self.banks = []
        bank_table_offset = self.config.get("BANK_TABLE_OFFSET")
        max_banks = self.config.get("MAX_BANKS")

        if bank_table_offset is None or bank_table_offset >= len(game_file):
            return self.banks

        bank_table_ptr = self.memory.offset_to_pointer(bank_table_offset)

        self.log.raw("=" * 80)
        self.log.info(
            self.translator.translate("messages.banks.parsing_start", offset=hex(bank_table_offset))
        )
        self.log.info(
            f"\n {self.translator.translate('messages.banks.table_pointer_found', ptr_memory=hex(bank_table_ptr), 
                offset=hex(bank_table_offset))}"
        )
        self.log.raw("-" * 80)

        for bank_id in range(max_banks):
            compiled_bank = self._allocate_bank(
                game_file=game_file,
                bank_table_offset=bank_table_offset,
                bank_id=bank_id,
            )
            if compiled_bank is not None:
                self.banks.append(compiled_bank)

        return self.banks

    def load_from_json(self, banks_json: str) -> None:
        """Deserialize a JSON string into a list of Bank instances."""
        self.banks = [
            CompiledBank.dict_to_class(bank_data) for bank_data in json.loads(banks_json)
        ]
    # End Public Methods

    # Private Methods
    @when_enabled("ALLOCATE_BANKS", default=True)
    def _allocate_bank(self, game_file: bytearray, bank_table_offset: int, bank_id: int) -> None:
        """Resolve a single bank's map list offset and calculate its boundary using the next bank."""
        game_size = len(game_file)
        bank_entry_offset = bank_table_offset + (bank_id * GBA_PTR_BYTE_SIZE)

        if bank_entry_offset + 4 > game_size:
            return

        bank_header_ptr = game_file[bank_entry_offset : bank_entry_offset + GBA_PTR_BYTE_SIZE]
        bank_header_offset = self.memory.pointer_to_offset(bank_header_ptr)

        if bank_header_offset is None or bank_header_offset >= game_size:
            return

        next_bank_entry_offset = bank_table_offset + ((bank_id + 1) * GBA_PTR_BYTE_SIZE)
        next_bank_header_offset = None

        if next_bank_entry_offset + 4 <= game_size:
            next_bank_header_ptr = game_file[next_bank_entry_offset : next_bank_entry_offset + GBA_PTR_BYTE_SIZE]
            next_bank_header_offset = self.memory.pointer_to_offset(next_bank_header_ptr)

        # For the last bank (42 in FireRed), its map list ends right where the bank table begins
        if next_bank_header_offset is None or next_bank_header_offset <= bank_header_offset or next_bank_header_offset > game_size:
            next_bank_header_offset = bank_table_offset if bank_table_offset > bank_header_offset else bank_header_offset + MAX_BANK_SCAN_BYTES

        current_bank = CompiledBank(bank_id=bank_id, header_offset=bank_header_offset, maps=[])
        self._allocate_maps(game_file, current_bank, next_bank_header_offset)
        return current_bank

    @when_enabled("ALLOCATE_MAPS", default=True)
    def _allocate_maps(self, game_file: bytearray, current_bank: CompiledBank, next_bank_header_offset: int) -> None:
        """Iterate through the current bank's map list, parse map headers, and collect events."""
        game_size = len(game_file)
        max_configured = self.config.get("MAX_MAPS_PER_BANK")
        calculated_maps = (next_bank_header_offset - current_bank.header_offset) // GBA_PTR_BYTE_SIZE
        total_maps = calculated_maps if 0 < calculated_maps <= max_configured else max_configured

        for map_id in range(total_maps):
            map_entry_offset = current_bank.header_offset + (map_id * GBA_PTR_BYTE_SIZE)
            if map_entry_offset + 4 > game_size:
                break

            map_header_ptr = game_file[map_entry_offset : map_entry_offset + GBA_PTR_BYTE_SIZE]
            map_header_offset = self.memory.pointer_to_offset(map_header_ptr)

            if map_header_offset is None or map_header_offset + GBA_PTR_BYTE_SIZE > game_size:
                break

            map_name = self._get_map_name(game_file, map_header_offset)
            if not map_name.strip() or map_name == "UNKNOWN":
                map_name = f"({current_bank.bank_id}.{map_id})"

            layout_ptr = game_file[map_header_offset : map_header_offset + GBA_PTR_BYTE_SIZE]
            layout_offset = self.memory.pointer_to_offset(layout_ptr)

            width, height = 0, 0
            layout_lenght = 2
            if layout_offset is not None:
                data = self.memory.read_u32_array(game_file, layout_offset, layout_lenght)
                if len(data) == layout_lenght:
                    width, height = data[0], data[1]

            if width > 2000 or height > 2000 or width == 0 or height == 0:
                break

            current_map = CompiledMap(
                map_id=map_id,
                header_offset=map_header_offset,
                name=map_name,
                events_count=0,
                width=width,
                height=height,
            )
            self.events.find_map_events(game_file, current_map)
            current_bank.maps.append(current_map)

    def _get_map_name(self, game_file: bytearray, map_header_offset: int) -> str:
        """Resolve the map's region name string from the map names table."""
        game_size = len(game_file)
        region_byte_offset = map_header_offset + self.config.get("REGION_MAP_BYTE")

        if region_byte_offset >= game_size:
            return "UNKNOWN"

        name_id = game_file[region_byte_offset]
        game_start = self.config.get("GAME_START")

        if name_id < game_start:
            return "UNKNOWN"

        adjusted_index = name_id - game_start
        entry_size = self.config.get("MAP_NAME_ENTRY_SIZE")
        text_field_offset = self.config.get("MAP_NAME_TEXT_OFFSET")
        names_table_offset = self.config.get("MAP_NAMES_TABLE_OFFSET")

        name_entry_offset = names_table_offset + (adjusted_index * entry_size) + text_field_offset
        if name_entry_offset + GBA_PTR_BYTE_SIZE > game_size:
            return "UNKNOWN"

        name_string_ptr = game_file[name_entry_offset : name_entry_offset + GBA_PTR_BYTE_SIZE]
        name_string_offset = self.memory.pointer_to_offset(name_string_ptr)

        return self.memory.read_string(game_file, name_string_offset)
    # End Private Methods