from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from decorators.app_decorators import when_enabled,skip_when_disabled
from helpers.gba.games_helper import GBA_POKEMON_III_CHAR_TABLE
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
    def get_core_banks_position(self, game_file: bytearray) -> None:
        # Rango donde vive la rutina de mapas en todas las versiones de Emerald (USA/EUR/ESP)
        start_scan = 0x084000
        end_scan = 0x086000

        for offset in range(start_scan, end_scan, 4):
            # 1. Leemos el posible puntero a la tabla de bancos (ej. 0x08486578)
            bank_table_ptr = self.memory.gba_pointer_to_file_offset(game_file, offset)
            if not bank_table_ptr:
                continue

            # 2. Validamos que los primeros 5 elementos dentro de esa tabla sean punteros válidos a listas de mapas
            valid_banks = 0
            for bank_id in range(5):
                bank_ptr = self.memory.gba_pointer_to_file_offset(game_file, bank_table_ptr + (bank_id * 4))
                if bank_ptr:
                    # 3. Validamos que el primer mapa dentro de ese banco también sea un puntero válido
                    first_map_ptr = self.memory.gba_pointer_to_file_offset(game_file, bank_ptr)
                    if first_map_ptr:
                        valid_banks += 1

            if valid_banks == 5:
                self.log.info(f"✅ Puntero encontrado en: {hex(offset)} -> Apunta a tabla de bancos en: {hex(bank_table_ptr)}")
                return offset, bank_table_ptr

        self.log.info("❌ No se encontró en el rango estándar (puede ser una ROM hack con rutina movida).")
        return None, None
    
    def inspect_core_banks(self,game_file: bytearray) -> None:
        bank_table_offset = self.config.get("BANK_TABLE_OFFSET")
        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.banks.decryption_start", offset=hex(bank_table_offset)))
        self.log.raw("=" * 80)

        for position in range(100):
            entry_offset = bank_table_offset + (position * 4)
            pointer_offset = self.memory.gba_pointer_to_file_offset(game_file, entry_offset)

            if pointer_offset is None or pointer_offset == 0:
                self.log.info(self.translator.translate("messages.banks.empty_table_position", position=position))
                continue

            # Verificamos si lo que hay dentro de esa posición apunta a una lista de mapas válida
            first_bank_map_list = self.memory.gba_pointer_to_file_offset(game_file, pointer_offset)
            is_banks_array = first_bank_map_list is not None and first_bank_map_list > 0

            self.log.info(
                f"\n {self.translator.translate('messages.banks.table_pointer_found', position=position, offset=hex(pointer_offset))}"
                f" -> ¿Es tabla de bancos?: {'✅ SÍ' if is_banks_array else '❌ No'}"
            )
            self.log.raw("-" * 80)

    def allocate_banks(self, game_file: bytearray) -> None:
        banks_id = self.config.get("BANK_TABLE_BANKS_POSITION")
        bank_table_offset = self.config.get("BANK_TABLE_OFFSET")
        banks_to_print = self.config.get("BANKS_TO_PRINT")

        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.banks.decryption_start", offset=hex(bank_table_offset)))
        self.log.raw("=" * 80)

        bank_entry_offset = bank_table_offset + (banks_id * 4)
        bank_list_offset = self.memory.gba_pointer_to_file_offset(game_file, bank_entry_offset)

        if bank_list_offset is None or bank_list_offset == 0:
            self.log.info(self.translator.translate("messages.banks.empty_table_position", position=banks_id))
            return

        self.log.info(f"\n {self.translator.translate("messages.banks.table_pointer_found",position=banks_id,offset=hex(bank_list_offset))}")
        self.log.raw("-" * 80)

        for bank_id in range(banks_to_print):
            self._allocate_bank(
                game_file=game_file,
                bank_list_offset=bank_list_offset,
                bank_id=bank_id,
            )
    # End Public Methods

    # Private Methods
    @when_enabled("ALLOCATE_BANKS", default=True)
    def _allocate_bank(self, game_file: bytearray, bank_list_offset: int, bank_id: int) -> None:
        bank_entry_offset = bank_list_offset + (bank_id * 4)
        bank_header_offset = self.memory.gba_pointer_to_file_offset(game_file, bank_entry_offset)

        if bank_header_offset is None or bank_header_offset == 0 or bank_header_offset > len(game_file):
            return

        next_bank_entry_offset = bank_list_offset + ((bank_id + 1) * 4)
        next_bank_header_offset = self.memory.gba_pointer_to_file_offset(game_file, next_bank_entry_offset)

        if next_bank_header_offset is None or next_bank_header_offset == 0 or next_bank_header_offset > len(game_file):
            next_bank_header_offset = bank_header_offset + 0x2000

        self.log.info(self.translator.translate("messages.banks.bank_entry",bank_id=f"{bank_id:2d}",offset=hex(bank_header_offset)),False)

        self.current_bank = CompiledBank(
            bank_id=bank_id,
            header_offset=bank_header_offset,
            maps=[],
        )
        self._allocate_maps(game_file, next_bank_header_offset)
            
    
    @when_enabled("ALLOCATE_MAPS", default=True)
    def _allocate_maps(self, game_file: bytearray, next_bank_header_offset: int) -> None:
        max_configured = self.config.get("MAPS_PER_BANK_TO_PRINT") or 256
        calculated_maps = (next_bank_header_offset - self.current_bank.header_offset) // 4

        # Solo usamos calculated_maps si el siguiente banco está adelante y dentro de un rango lógico
        if 0 < calculated_maps <= max_configured:
            total_maps = calculated_maps
        else:
            total_maps = max_configured

        for map_id in range(total_maps):
            map_entry_offset = self.current_bank.header_offset + (map_id * 4)
            map_header_offset = self.memory.gba_pointer_to_file_offset(game_file, map_entry_offset)

            if map_header_offset is None or map_header_offset == 0 or map_header_offset >= len(game_file):
                break

            map_name = self._get_map_name(game_file, map_header_offset)
            if not map_name or not map_name.strip():
                map_name = f"({self.current_bank.bank_id}.{map_id})"

            layout_pointer = self.memory.gba_pointer_to_file_offset(game_file, map_header_offset)
            width, height = 0, 0
            if layout_pointer and layout_pointer < len(game_file):
                width = int.from_bytes(game_file[layout_pointer : layout_pointer + 4], byteorder="little")
                height = int.from_bytes(game_file[layout_pointer + 4 : layout_pointer + 8], byteorder="little")

            if width > 2000 or height > 2000 or width == 0 or height == 0:
                break

            self.log.info(
                self.translator.translate("messages.banks.map_entry",map_id=f"{map_id:2d}",name=f"{map_name:<15s}",header=hex(map_header_offset),
                width=f"{width:3d}", height=f"{height:3d}"), False
            )
            current_map = CompiledMap(
                map_id=map_id,
                header_offset=map_header_offset,
                name=map_name,
                events_count=0,
            )

            self.events.find_map_events(game_file, current_map)
            self.current_bank.maps.append(current_map)
        self.banks.append(self.current_bank)

    def _get_map_name(self, game_file: bytearray, map_header_offset: int) -> str:
        map_names_table_offset = self.config.get("MAP_NAMES_TABLE_OFFSET")
        name_id = game_file[map_header_offset + self.config.get("REGION_MAP_BYTE")]

        if name_id < self.config.get("GAME_START"):
            return "UNKNOWN"

        adjusted_index = name_id - self.config.get("GAME_START")
        
        #Default Fire Red Values 4,0
        entry_size = self.config.get("MAP_NAME_ENTRY_SIZE") or 4
        text_offset = self.config.get("MAP_NAME_TEXT_OFFSET") or 0
        pointer_entry = map_names_table_offset + (adjusted_index * entry_size) + text_offset
        string_pointer = self.memory.gba_pointer_to_file_offset(game_file, pointer_entry)

        if not string_pointer or string_pointer >= len(game_file):
            return "UNKNOWN"

        map_name = ""
        offset = string_pointer
        while offset < len(game_file):
            char_byte = game_file[offset]
            if char_byte == 0xFF:
                break
            map_name += GBA_POKEMON_III_CHAR_TABLE.get(char_byte, "?")
            offset += 1
        return map_name
    # End Private Methods