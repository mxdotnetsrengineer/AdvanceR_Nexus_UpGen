from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
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
    def allocate_banks(self, game_file: bytearray, find_maps: bool = False) -> None:
        banks_id = self.config.get_value("BANK_TABLE_BANKS_POSITION")
        bank_table_offset = self.config.get_value("BANK_TABLE_OFFSET")
        banks_to_print = self.config.get_value("BANKS_TO_PRINT")

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
                get_maps=find_maps,
            )
    # End Public Methods

    # Private Methods
    def _allocate_bank(self, game_file: bytearray, bank_list_offset: int, bank_id: int, get_maps: bool = False) -> None:
        bank_entry_offset = bank_list_offset + (bank_id * 4)
        bank_header_offset = self.memory.gba_pointer_to_file_offset(game_file, bank_entry_offset)

        if bank_header_offset is None or bank_header_offset == 0 or bank_header_offset > 0x1D00000:
            return

        next_bank_entry_offset = bank_list_offset + ((bank_id + 1) * 4)
        next_bank_header_offset = self.memory.gba_pointer_to_file_offset(game_file, next_bank_entry_offset)

        if next_bank_header_offset is None or next_bank_header_offset == 0 or next_bank_header_offset > 0x1D00000:
            next_bank_header_offset = bank_header_offset + 0x2000

        self.log.info(self.translator.translate("messages.banks.bank_entry",bank_id=f"{bank_id:2d}",offset=hex(bank_header_offset)),False)

        if get_maps:
            self.current_bank = CompiledBank(
                bank_id=bank_id,
                header_offset=bank_header_offset,
                maps=[],
            )
            self._allocate_maps(game_file)

    def _allocate_maps(self, game_file: bytearray) -> None:
        for map_id in range(self.config.get_value("MAPS_PER_BANK_TO_PRINT")):
            map_entry_offset = self.current_bank.header_offset + (map_id * 4)
            map_header_offset = self.memory.gba_pointer_to_file_offset(game_file, map_entry_offset)

            if map_header_offset is None or map_header_offset == 0 or map_header_offset > 0x1D00000:
                break

            map_name = self._get_map_name(game_file, map_header_offset)

            layout_pointer = self.memory.gba_pointer_to_file_offset(game_file, map_header_offset)
            width, height = 0, 0
            if layout_pointer and layout_pointer < len(game_file):
                width = int.from_bytes(game_file[layout_pointer : layout_pointer + 4], byteorder="little")
                height = int.from_bytes(game_file[layout_pointer + 4 : layout_pointer + 8], byteorder="little")

            if width > 200 or height > 200 or width == 0 or height == 0:
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

            if self.config.get_value("RANDOMIZE_POKEBALLS_ITEMS") and not self.config.get_value("ONLY_DATABASE"):
                self.events.find_map_events(game_file, current_map)
            self.current_bank.maps.append(current_map)
        self.banks.append(self.current_bank)

    def _get_map_name(self, game_file: bytearray, map_header_offset: int) -> str:
        map_names_table_offset = self.config.get_value("MAP_NAMES_TABLE_OFFSET")
        name_id = game_file[map_header_offset + self.config.get_value("REGION_MAP_BYTE")]

        if name_id < self.config.get_value("GAME_START"):
            return "UNKNOWN"

        adjusted_index = name_id - self.config.get_value("GAME_START")
        pointer_entry = map_names_table_offset + (adjusted_index * 4)
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