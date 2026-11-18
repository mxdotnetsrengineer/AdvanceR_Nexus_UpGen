from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from decorators.app_decorators import when_enabled, skip_when_enabled, when_any_enabled
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE, HEX_NUM_BASE
from helpers.gba.pokemon.gba_pokemon_helper import MAX_BANK_SCAN_BYTES
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.event_service import EventService


class BankService:
    def __init__(
        _self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        event_service: EventService,
        translations_service: TranslationsService,
    ):
        _self.config = config_service
        _self.memory = memory_service
        _self.log = log_service
        _self.events = event_service
        _self.translator = translations_service

        _self.banks: list[CompiledBank] = []
        _self.current_bank: CompiledBank | None = None

    # Public Methods
    def get_core_banks_position(_self, game_file: bytearray) -> tuple[int | None, int | None]:
        """Scan the standard game memory range to find the pointer to the core map bank table."""
        start_scan_ptr = 0x055000 #Change the pointers for other games, default firered
        end_scan_ptr = 0x056000   
        game_size = len(game_file)
        banks_to_find = 5

        for candidate_ptr in range(start_scan_ptr, end_scan_ptr, GBA_PTR_BYTE_SIZE):
            bank_table_offset = GBAMemoryService.pointer_to_offset(
                game_file[candidate_ptr : candidate_ptr + GBA_PTR_BYTE_SIZE]
            )
            
            if bank_table_offset is None or bank_table_offset + (GBA_PTR_BYTE_SIZE * banks_to_find) > game_size:
                continue

            valid_banks = 0
            for bank_id in range(banks_to_find):
                bank_ptr = bank_table_offset + (bank_id * GBA_PTR_BYTE_SIZE)
                bank_header_offset = GBAMemoryService.pointer_to_offset(
                    game_file[bank_ptr : bank_ptr + GBA_PTR_BYTE_SIZE]
                )
                
                if bank_header_offset is not None and bank_header_offset + GBA_PTR_BYTE_SIZE <= game_size:
                    map_list_offset = GBAMemoryService.pointer_to_offset(
                        game_file[bank_header_offset : bank_header_offset + GBA_PTR_BYTE_SIZE]
                    )
                    if map_list_offset is not None and map_list_offset < game_size:
                        valid_banks += 1

            if valid_banks == banks_to_find:
                _self.log.info(
                    _self.translator.translate(
                        "messages.banks.table_pointer_found",
                        ptr_memory=hex(candidate_ptr),
                        offset=hex(bank_table_offset),
                    )
                )
                return candidate_ptr, bank_table_offset

        _self.log.info(_self.translator.translate("warnings.banks.pointer_not_found"))
        return None, None
    
    def inspect_core_banks(_self, game_file: bytearray) -> None:
        """Inspect entries inside the core map bank table of the game file."""
        bank_table_offset = _self.config.get("BANK_TABLE_OFFSET")
        game_size = len(game_file)

        _self.log.raw("=" * 80)
        _self.log.info(
            _self.translator.translate("messages.banks.decryption_start", offset=hex(bank_table_offset))
        )
        _self.log.raw("=" * 80)
        
        target_id = 0
        for position in range(_self.config.get("BANKS_TO_PRINT")):
            entry_offset = bank_table_offset + (position * GBA_PTR_BYTE_SIZE)
            if entry_offset + GBA_PTR_BYTE_SIZE > game_size:
                break

            entry_ptr = GBAMemoryService.offset_to_pointer(entry_offset)
            target_ptr = game_file[entry_offset : entry_offset + GBA_PTR_BYTE_SIZE]
            target_offset = GBAMemoryService.pointer_to_offset(target_ptr)

            if target_offset is None or target_offset + GBA_PTR_BYTE_SIZE > game_size:
                _self.log.info(
                    _self.translator.translate(
                        "warnings.banks.empty_table_position",
                        ptr_memory=hex(entry_ptr),
                    )
                )
                continue

            first_map_list_ptr = game_file[target_offset : target_offset + GBA_PTR_BYTE_SIZE]
            first_map_list_offset = GBAMemoryService.pointer_to_offset(first_map_list_ptr)
            is_banks_array = first_map_list_offset is not None and first_map_list_offset < game_size
            if is_banks_array:
                target_id+=1

            _self.log.info(_self.translator.translate("messages.banks.bank_entry", bank_id=f"{target_id:2d}", 
                        offset=hex(target_offset)), False)
            _self.log.raw("-" * 80)

    async def allocate_banks(_self, game_file: bytearray) -> None:
        """Read and allocate the map banks directly from the bank table file offset."""
        bank_table_offset = _self.config.get("BANK_TABLE_OFFSET")
        banks_to_print = _self.config.get("BANKS_TO_PRINT")

        if bank_table_offset is None or bank_table_offset >= len(game_file):
            return

        bank_table_ptr = GBAMemoryService.offset_to_pointer(bank_table_offset)

        _self.log.raw("=" * 80)
        _self.log.info(
            _self.translator.translate("messages.banks.decryption_start", offset=hex(bank_table_offset))
        )
        _self.log.info(
            f"\n {_self.translator.translate('messages.banks.table_pointer_found', ptr_memory=hex(bank_table_ptr), 
                offset=hex(bank_table_offset))}"
        )
        _self.log.raw("-" * 80)

        for bank_id in range(banks_to_print):
            _self.__allocate_bank(
                game_file=game_file,
                bank_table_offset=bank_table_offset,
                bank_id=bank_id,
        )

    @skip_when_enabled("ONLY_DATABASE")
    @when_any_enabled("WILD_EVENTS" , "RANDOMIZE_WILD_POKEMON")
    def randomize_banks_wild_encounters(
        _self,
        game_file: bytearray,
        species_list: list[CompiledBaseStats],
    ) -> None:
        """Iterate through all compiled banks and maps to randomize wild Pokémon encounters."""
        
        _self.current_bank = None
        game_size = len(game_file)

        raw_wild_offsets: list[int] = _self.config.get("WILD_POKEMON_OFFSET") or []
        wild_table_offsets = [
            val for off in raw_wild_offsets
            if 0 <= (val := int(off, HEX_NUM_BASE) if isinstance(off, str) else off) < game_size
        ]

        if not _self.banks or not species_list or not wild_table_offsets:
            return
        
        wild_grass_slot_count = _self.config.get("WILD_GRASS_SLOT_COUNT")
        species_by_id = {pokemon.id: pokemon for pokemon in species_list}
        wild_candidates = [sp for sp in species_list if not sp.is_mega]
        bank_map_pairs = [(bank, compiled_map) for bank in _self.banks for compiled_map in bank.maps]
        
        for wild_table_offset in wild_table_offsets:
            for bank, compiled_map in bank_map_pairs:
                selected_species = _self.events.select_wild_species(
                    bank=bank,
                    compiled_map=compiled_map,
                    wild_grass_slot_count=wild_grass_slot_count,
                    wild_table_offset=wild_table_offset,
                    wild_candidates=wild_candidates,
                    game_file=game_file,
                )
                
                if not selected_species:
                    continue
                _self.events.randomize_wild_encounters(
                    bank=bank,
                    compiled_map=compiled_map,
                    wild_grass_slot_count=wild_grass_slot_count,
                    wild_table_offset=wild_table_offset,
                    selected_species=selected_species,
                    species_by_id=species_by_id,
                    game_file=game_file,
                )

    # End Public Methods

    # Private Methods
    @when_enabled("ALLOCATE_BANKS", default=True)
    def __allocate_bank(_self, game_file: bytearray, bank_table_offset: int, bank_id: int) -> None:
        """Resolve a single bank's map list offset and calculate its boundary using the next bank."""
        game_size = len(game_file)
        bank_entry_offset = bank_table_offset + (bank_id * GBA_PTR_BYTE_SIZE)

        if bank_entry_offset + 4 > game_size:
            return

        bank_header_ptr = game_file[bank_entry_offset : bank_entry_offset + GBA_PTR_BYTE_SIZE]
        bank_header_offset = GBAMemoryService.pointer_to_offset(bank_header_ptr)

        if bank_header_offset is None or bank_header_offset >= game_size:
            return

        next_bank_entry_offset = bank_table_offset + ((bank_id + 1) * GBA_PTR_BYTE_SIZE)
        next_bank_header_offset = None

        if next_bank_entry_offset + 4 <= game_size:
            next_bank_header_ptr = game_file[next_bank_entry_offset : next_bank_entry_offset + GBA_PTR_BYTE_SIZE]
            next_bank_header_offset = GBAMemoryService.pointer_to_offset(next_bank_header_ptr)

        # For the last bank (42 in FireRed), its map list ends right where the bank table begins
        if next_bank_header_offset is None or next_bank_header_offset <= bank_header_offset or next_bank_header_offset > game_size:
            next_bank_header_offset = bank_table_offset if bank_table_offset > bank_header_offset else bank_header_offset + MAX_BANK_SCAN_BYTES

        _self.log.info(
            _self.translator.translate(
                "messages.banks.bank_entry",
                bank_id=f"{bank_id:2d}",
                offset=hex(bank_header_offset),
            ),
            False,
        )

        _self.current_bank = CompiledBank(bank_id=bank_id, header_offset=bank_header_offset, maps=[])
        _self.__allocate_maps(game_file, next_bank_header_offset)

    @when_enabled("ALLOCATE_MAPS", default=True)
    def __allocate_maps(_self, game_file: bytearray, next_bank_header_offset: int) -> None:
        """Iterate through the current bank's map list, parse map headers, and collect events."""
        game_size = len(game_file)
        max_configured = _self.config.get("MAPS_PER_BANK_TO_PRINT")
        calculated_maps = (next_bank_header_offset - _self.current_bank.header_offset) // GBA_PTR_BYTE_SIZE
        total_maps = calculated_maps if 0 < calculated_maps <= max_configured else max_configured

        for map_id in range(total_maps):
            map_entry_offset = _self.current_bank.header_offset + (map_id * GBA_PTR_BYTE_SIZE)
            if map_entry_offset + 4 > game_size:
                break

            map_header_ptr = game_file[map_entry_offset : map_entry_offset + GBA_PTR_BYTE_SIZE]
            map_header_offset = GBAMemoryService.pointer_to_offset(map_header_ptr)

            if map_header_offset is None or map_header_offset + GBA_PTR_BYTE_SIZE > game_size:
                break

            map_name = _self.__get_map_name(game_file, map_header_offset)
            if not map_name.strip() or map_name == "UNKNOWN":
                map_name = f"({_self.current_bank.bank_id}.{map_id})"

            layout_ptr = game_file[map_header_offset : map_header_offset + GBA_PTR_BYTE_SIZE]
            layout_offset = GBAMemoryService.pointer_to_offset(layout_ptr)

            width, height = 0, 0
            layout_lenght = 2
            if layout_offset is not None:
                data = GBAMemoryService.read_u32_array(game_file, layout_offset, layout_lenght)
                if len(data) == layout_lenght:
                    width, height = data[0], data[1]

            if width > 2000 or height > 2000 or width == 0 or height == 0:
                break

            _self.log.info(
                _self.translator.translate(
                    "messages.banks.map_entry",
                    map_id=f"{map_id:2d}",
                    name=f"{map_name:<15s}",
                    header=hex(map_header_offset),
                    width=f"{width:3d}",
                    height=f"{height:3d}",
                ),
                False,
            )

            current_map = CompiledMap(
                map_id=map_id,
                header_offset=map_header_offset,
                name=map_name,
                events_count=0,
                width=width,
                height=height,
            )
            _self.events.find_map_events(game_file, current_map)
            _self.current_bank.maps.append(current_map)

        _self.banks.append(_self.current_bank)

    def __get_map_name(_self, game_file: bytearray, map_header_offset: int) -> str:
        """Resolve the map's region name string from the map names table."""
        game_size = len(game_file)
        region_byte_offset = map_header_offset + _self.config.get("REGION_MAP_BYTE")

        if region_byte_offset >= game_size:
            return "UNKNOWN"

        name_id = game_file[region_byte_offset]
        game_start = _self.config.get("GAME_START")

        if name_id < game_start:
            return "UNKNOWN"

        adjusted_index = name_id - game_start
        entry_size = _self.config.get("MAP_NAME_ENTRY_SIZE")
        text_field_offset = _self.config.get("MAP_NAME_TEXT_OFFSET")
        names_table_offset = _self.config.get("MAP_NAMES_TABLE_OFFSET")

        name_entry_offset = names_table_offset + (adjusted_index * entry_size) + text_field_offset
        if name_entry_offset + GBA_PTR_BYTE_SIZE > game_size:
            return "UNKNOWN"

        name_string_ptr = game_file[name_entry_offset : name_entry_offset + GBA_PTR_BYTE_SIZE]
        name_string_offset = GBAMemoryService.pointer_to_offset(name_string_ptr)

        return GBAMemoryService.read_string(game_file, name_string_offset)
    # End Private Methods