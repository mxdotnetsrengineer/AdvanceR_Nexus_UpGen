from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from decorators.app_decorators import when_enabled, skip_when_disabled
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.event_service import EventService


class BankService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        event_service: EventService,
        translations_service: TranslationsService,
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.events = event_service
        self.translator = translations_service

        self.banks: list[CompiledBank] = []
        self.current_bank: CompiledBank | None = None

    # Public Methods
    def get_core_banks_position(self, game_file: bytearray) -> tuple[int | None, int | None]:
        start_scan_offset = 0x084000
        end_scan_offset = 0x086000

        for candidate_ptr_offset in range(start_scan_offset, end_scan_offset, 4):
            bank_table_offset = self.memory.pointer_to_offset(game_file, candidate_ptr_offset)
            if not bank_table_offset:
                continue

            valid_banks = 0
            for bank_id in range(5):
                bank_ptr_offset = self.memory.get_struct_offset(bank_table_offset, bank_id, 4)
                bank_header_offset = self.memory.pointer_to_offset(game_file, bank_ptr_offset)
                if bank_header_offset and self.memory.pointer_to_offset(game_file, bank_header_offset):
                    valid_banks += 1

            if valid_banks == 5:
                self.log.info(
                    f"✅ Puntero encontrado en: {hex(candidate_ptr_offset)} -> Apunta a tabla de bancos en: {hex(bank_table_offset)}"
                )
                return candidate_ptr_offset, bank_table_offset

        self.log.info("❌ No se encontró en el rango estándar (puede ser una ROM hack con rutina movida).")
        return None, None
    
    def inspect_core_banks(self, game_file: bytearray) -> None:
        bank_table_offset = self.config.get("BANK_TABLE_OFFSET")
        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.banks.decryption_start", offset=hex(bank_table_offset)))
        self.log.raw("=" * 80)

        for position in range(100):
            entry_ptr_offset = self.memory.get_struct_offset(bank_table_offset, position, 4)
            target_offset = self.memory.pointer_to_offset(game_file, entry_ptr_offset)

            if not target_offset:
                self.log.info(self.translator.translate("messages.banks.empty_table_position", position=position))
                continue

            first_bank_map_list_offset = self.memory.pointer_to_offset(game_file, target_offset)
            is_banks_array = bool(first_bank_map_list_offset)

            self.log.info(
                f"\n {self.translator.translate('messages.banks.table_pointer_found', position=position, offset=hex(target_offset))}"
                f" -> ¿Es tabla de bancos?: {'✅ SÍ' if is_banks_array else '❌ No'}"
            )
            self.log.raw("-" * 80)

    async def allocate_banks(self, game_file: bytearray) -> None:
        banks_id = self.config.get("BANK_TABLE_BANKS_POSITION")
        bank_table_offset = self.config.get("BANK_TABLE_OFFSET")
        banks_to_print = self.config.get("BANKS_TO_PRINT")

        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.banks.decryption_start", offset=hex(bank_table_offset)))
        self.log.raw("=" * 80)

        bank_entry_ptr_offset = self.memory.get_struct_offset(bank_table_offset, banks_id, 4)
        bank_list_offset = self.memory.pointer_to_offset(game_file, bank_entry_ptr_offset)

        if not bank_list_offset:
            self.log.info(self.translator.translate("messages.banks.empty_table_position", position=banks_id))
            return

        self.log.info(
            f"\n {self.translator.translate('messages.banks.table_pointer_found', position=banks_id, offset=hex(bank_list_offset))}"
        )
        self.log.raw("-" * 80)

        for bank_id in range(banks_to_print):
            self._allocate_bank(game_file=game_file, bank_list_offset=bank_list_offset, bank_id=bank_id)

    @skip_when_disabled("ONLY_DATABASE")
    @when_enabled("RANDOMIZE_WILD_POKEMON")
    def randomize_banks_wild_encounters(
        self,
        game_file: bytearray,
        species_list: list[CompiledBaseStats],
    ) -> None:
        self.current_bank = None

        raw_wild_offsets = self.config.get("WILD_POKEMON_POINTER_OFFSET")
        if isinstance(raw_wild_offsets, (str, int)):
            raw_wild_offsets = [raw_wild_offsets]
        elif not isinstance(raw_wild_offsets, list):
            raw_wild_offsets = []

        wild_table_offsets: list[int] = [
            int(off, 16) if isinstance(off, str) else off
            for off in raw_wild_offsets
            if off is not None
        ]

        if not self.banks or not species_list or not wild_table_offsets:
            return

        wild_grass_slot_count = self.config.get("WILD_GRASS_SLOT_COUNT")
        species_by_id = {pokemon.id: pokemon for pokemon in species_list}
        wild_candidates = [sp for sp in species_list if not sp.is_mega]

        for wild_table_offset in wild_table_offsets:
            for bank in self.banks:
                for compiled_map in bank.maps:

                    selected_species = self.events.select_wild_species(
                        bank=bank,
                        compiled_map=compiled_map,
                        wild_grass_slot_count=wild_grass_slot_count,
                        wild_table_offset=wild_table_offset,
                        wild_candidates=wild_candidates,
                        game_file=game_file,
                    )
                    if not selected_species:
                        continue

                    self.events.randomize_wild_encounters(
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
    def _allocate_bank(self, game_file: bytearray, bank_list_offset: int, bank_id: int) -> None:
        bank_entry_ptr_offset = self.memory.get_struct_offset(bank_list_offset, bank_id, 4)
        bank_header_offset = self.memory.pointer_to_offset(game_file, bank_entry_ptr_offset)

        if not bank_header_offset or bank_header_offset > len(game_file):
            return

        next_bank_entry_ptr_offset = self.memory.get_struct_offset(bank_list_offset, bank_id + 1, 4)
        next_bank_header_offset = self.memory.pointer_to_offset(game_file, next_bank_entry_ptr_offset)

        if not next_bank_header_offset or next_bank_header_offset > len(game_file):
            next_bank_header_offset = bank_header_offset + 0x2000

        self.log.info(self.translator.translate("messages.banks.bank_entry", bank_id=f"{bank_id:2d}", 
            offset=hex(bank_header_offset)), False)

        self.current_bank = CompiledBank(bank_id=bank_id, header_offset=bank_header_offset, maps=[])
        self._allocate_maps(game_file, next_bank_header_offset)

    @when_enabled("ALLOCATE_MAPS", default=True)
    def _allocate_maps(self, game_file: bytearray, next_bank_header_offset: int) -> None:
        max_configured = self.config.get("MAPS_PER_BANK_TO_PRINT") or 256
        calculated_maps = (next_bank_header_offset - self.current_bank.header_offset) // 4
        total_maps = calculated_maps if 0 < calculated_maps <= max_configured else max_configured

        for map_id in range(total_maps):
            map_entry_ptr_offset = self.memory.get_struct_offset(self.current_bank.header_offset, map_id, 4)
            map_header_offset = self.memory.pointer_to_offset(game_file, map_entry_ptr_offset)

            if not map_header_offset or map_header_offset >= len(game_file):
                break

            map_name = self._get_map_name(game_file, map_header_offset)
            if not map_name.strip() or map_name == "UNKNOWN":
                map_name = f"({self.current_bank.bank_id}.{map_id})"

            layout_offset = self.memory.pointer_to_offset(game_file, map_header_offset)
            width, height = 0, 0
            if layout_offset and layout_offset + 8 <= len(game_file):
                data = self.memory.read_u32_array(game_file, layout_offset, 2)
                width = data[0]
                height = data[1]

            if width > 2000 or height > 2000 or width == 0 or height == 0:
                break
            
            # self.log.info(
            #     self.translator.translate(
            #         "messages.banks.map_entry",
            #         map_id=f"{map_id:2d}",
            #         name=f"{map_name:<15s}",
            #         header=hex(map_header_offset),
            #         width=f"{width:3d}",
            #         height=f"{height:3d}",
            #     ),
            #     False,
            # )
            current_map = CompiledMap(map_id=map_id, header_offset=map_header_offset, name=map_name, events_count=0, 
                width=width, height=height)
            self.events.find_map_events(game_file, current_map)
            self.current_bank.maps.append(current_map)

        self.banks.append(self.current_bank)

    def _get_map_name(self, game_file: bytearray, map_header_offset: int) -> str:
        name_id = game_file[map_header_offset + self.config.get("REGION_MAP_BYTE")]
        game_start = self.config.get("GAME_START")

        if name_id < game_start:
            return "UNKNOWN"

        adjusted_index = name_id - game_start
        entry_size = self.config.get("MAP_NAME_ENTRY_SIZE") or 4
        text_field_offset = self.config.get("MAP_NAME_TEXT_OFFSET") or 0

        name_ptr_offset = (
            self.memory.get_struct_offset(self.config.get("MAP_NAMES_TABLE_OFFSET"), adjusted_index, entry_size)
            + text_field_offset
        )
        name_string_offset = self.memory.pointer_to_offset(game_file, name_ptr_offset)

        return self.memory.read_string(game_file, name_string_offset)
    # End Private Methods