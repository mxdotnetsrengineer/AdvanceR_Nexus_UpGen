import struct
from helpers.gba.games_helper import GBA_ROM_BASE, GBA_ROM_END, STRING_TERMINATOR, GBA_PTR_BYTE_SIZE
from helpers.gba.pokemon.gba_pokemon_helper import GBA_POKEMON_III_CHAR_TABLE
from services.translations_service import TranslationsService
class GBAMemoryService:

    def __init__(
            _self,
            translations_service: TranslationsService,
        ):
            _self.game_file: bytearray | None = None
            _self.free_space_offset: int = 0
            _self.translator = translations_service
    
    @staticmethod
    def pointer_to_offset(pointer: int | bytearray) -> int | None:
        """Convert a GBA pointer (0x08XXXXXX integer or 4-byte little-endian bytearray) to a file offset."""
        if isinstance(pointer, bytearray):
            if len(pointer) != GBA_PTR_BYTE_SIZE:
                return None
            pointer = int.from_bytes(pointer, byteorder="little")

        if GBA_ROM_BASE <= pointer < GBA_ROM_END:
            return pointer - GBA_ROM_BASE
        return None

    @staticmethod
    def offset_to_pointer(offset: int) -> int:
        """Convert a file offset to a GBA pointer integer (0x08XXXXXX)."""
        return offset + GBA_ROM_BASE

    @classmethod
    def offset_to_pointer_bytes(cls,offset: int) -> bytearray:
        """Convert a file offset to a 4-byte little-endian bytearray ready to write into the ROM."""
        return bytearray(cls.offset_to_pointer(offset).to_bytes(GBA_PTR_BYTE_SIZE, byteorder="little"))

    @staticmethod
    def read_string(
        game_file: bytearray,
        string_offset: int | None,
        max_length: int | None = None,
        fallback: str = "UNKNOWN",
    ) -> str:
        """Decode GBA text at `string_offset` until `0xFF` terminator or `max_length`."""
        game_size = len(game_file)
        if string_offset is None or string_offset < 0 or string_offset >= game_size:
            return fallback

        end_offset = min(string_offset + max_length, game_size) if max_length else game_size
        terminator_offset = game_file.find(STRING_TERMINATOR, string_offset, end_offset)

        if terminator_offset != -1:
            end_offset = terminator_offset

        raw_bytes = game_file[string_offset:end_offset]
        result = "".join(GBA_POKEMON_III_CHAR_TABLE.get(byte, "?") for byte in raw_bytes).strip()

        return result if result else fallback

    @staticmethod
    def read_u32_array(game_file: bytearray, offset: int, count: int) -> tuple[int, ...]:
        """Read `count` little-endian 32-bit unsigned integers starting at `offset`."""
        end_offset = offset + (count * GBA_PTR_BYTE_SIZE)
        if offset < 0 or end_offset > len(game_file):
            return ()

        return struct.unpack_from(f"<{count}I", game_file, offset)

    @staticmethod
    def read_u16_array(game_file: bytearray, offset: int, count: int) -> tuple[int, ...]:
        """Read `count` little-endian 16-bit unsigned integers starting at `offset`."""
        u16_byte_size = 2
        end_offset = offset + (count * u16_byte_size)
        if offset < 0 or end_offset > len(game_file):
            return ()

        return struct.unpack_from(f"<{count}H", game_file, offset)
    
    def find_free_space_offset(
        _self,
        game_file: bytearray,
        size: int,
        start_offset: int | None = None,
        align_to_word: bool = True,
    ) -> int | None:
        """Find a contiguous block of `0xFF` bytes of length `size` inside `game_file`, optionally 4-byte aligned."""
        if size <= 0:
            return None

        search_start = start_offset if start_offset is not None else _self.free_space_offset
        if search_start < 0 or search_start >= len(game_file):
            return None

        pattern = b"\xFF" * size
        current_search = search_start

        while True:
            offset = game_file.find(pattern, current_search)
            if offset == -1:
                return None

            if not align_to_word or (offset % GBA_PTR_BYTE_SIZE == 0):
                return offset

            # Advance to the next 4-byte aligned boundary and verify if the block still fits
            aligned_offset = (offset + GBA_PTR_BYTE_SIZE - 1) & ~(GBA_PTR_BYTE_SIZE - 1)
            if game_file[aligned_offset : aligned_offset + size] == pattern:
                return aligned_offset

            current_search = aligned_offset