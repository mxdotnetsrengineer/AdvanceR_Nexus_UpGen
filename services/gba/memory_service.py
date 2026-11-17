from helpers.gba.games_helper import GBA_POKEMON_III_CHAR_TABLE
from services.log_service import LogService
from services.translations_service import TranslationsService
class GBAMemoryService:
    GBA_ROM_BASE = 0x08000000
    GBA_ROM_END = 0x0A000000
    STRING_TERMINATOR = 0xFF

    def __init__(
        self,
        translations_service: TranslationsService,
        log_service: LogService | None = None,
    ):
        self.game_file: bytearray | None = None
        self.free_space_offset: int = 0
        self.translator = translations_service
        self.log = log_service

    def find_free_space_offset(self, size: int, start_offset: int = 0, game_file: bytearray | None = None) -> int | None:
        target = game_file if game_file is not None else self.game_file
        if target is None:
            if self.log:
                self.log.error(self.translator.translate("errors.no_game_loaded"), error_key="runtime")
            return None

        offset = target.find(b"\xFF" * size, start_offset)
        return offset if offset != -1 else None

    def pointer_to_offset(self, game_file: bytearray, ptr_offset: int | str | None) -> int | None:
        """Read (4 bytes little-endian) Offset and return game file offset"""
        if ptr_offset is None:
            return None
            
        if isinstance(ptr_offset, str):
            ptr_offset = int(ptr_offset, 16)

        if ptr_offset < 0 or ptr_offset + 4 > len(game_file):
            return None
            
        gba_addr = self.read_u32(game_file, ptr_offset)
        return self.gba_addr_to_offset(gba_addr)

    def gba_addr_to_offset(self, gba_addr: int) -> int | None:
        """GBA Adress (`0x08XXXXXX`) to game file offset."""
        if self.GBA_ROM_BASE <= gba_addr < self.GBA_ROM_END:
            return gba_addr - self.GBA_ROM_BASE
        return None

    def offset_to_gba_addr(self, offset: int) -> int:
        return offset + self.GBA_ROM_BASE

    def offset_to_pointer_bytes(self, offset: int) -> bytes:
        return self.offset_to_gba_addr(offset).to_bytes(4, byteorder="little")

    def get_struct_offset(self, base_offset: int, index: int, struct_size: int) -> int:
        """`offset` position in game file table"""
        return base_offset + (index * struct_size)

    def read_u16(self, game_file: bytearray, offset: int) -> int:
        return int.from_bytes(game_file[offset : offset + 2], byteorder="little")

    def read_u32(self, game_file: bytearray, offset: int) -> int:
        return int.from_bytes(game_file[offset : offset + 4], byteorder="little")

    def read_u32_array(self, game_file: bytearray, offset: int, count: int) -> list[int]:
        return [
            int.from_bytes(game_file[offset + i * 4 : offset + (i + 1) * 4], byteorder="little")
            for i in range(count)
        ]

    def write_pointer(self, game_file: bytearray, target_ptr_offset: int, destination_offset: int) -> None:
        game_file[target_ptr_offset : target_ptr_offset + 4] = self.offset_to_pointer_bytes(destination_offset)

    # --- Offset values to string
    def read_string(
        self,
        game_file: bytearray,
        string_offset: int | None,
        max_length: int | None = None,
        fallback: str = "UNKNOWN",
    ) -> str:
        """Text from GBA `string_offset` to readble text, text is read until find 0xFF or a max length"""
        if string_offset is None or string_offset <= 0 or string_offset >= len(game_file):
            return fallback

        end_offset = min(string_offset + max_length, len(game_file)) if max_length else len(game_file)
        chars: list[str] = []

        for current_offset in range(string_offset, end_offset):
            char_byte = game_file[current_offset]
            if char_byte == self.STRING_TERMINATOR:
                break
            chars.append(GBA_POKEMON_III_CHAR_TABLE.get(char_byte, "?"))

        result = "".join(chars).strip()
        return result if result else fallback