import pytest
from services.gba.memory_service import GBAMemoryService


@pytest.mark.parametrize(
    "pointer, expected_offset",
    [
        (0x08000000, 0x000000),
        (0x083526A8, 0x3526A8),
        (bytearray(b"\xA8\x26\x35\x08"), 0x3526A8),  # Little-endian pointer bytes
        (0x07FFFFFF, None),  # Below valid GBA ROM range
        (0x0A000000, None),  # Above valid GBA ROM range
        (bytearray(b"\x01\x02"), None),  # Invalid pointer byte length
    ],
)
def test_pointer_to_offset(pointer, expected_offset):
    assert GBAMemoryService.pointer_to_offset(pointer) == expected_offset


def test_read_string_decodes_until_terminator(fake_gba_rom: bytearray):
    # "ASH" encoded in Gen III character table: A=0xBB, S=0xCD, H=0xC2, terminator=0xFF
    fake_gba_rom[0x100:0x104] = bytearray([0xBB, 0xCD, 0xC2, 0xFF])
    result = GBAMemoryService.read_string(fake_gba_rom, 0x100)
    assert result == "ASH"


def test_find_free_space_offset_word_aligned(translations_service):
    memory = GBAMemoryService(translations_service)
    rom = bytearray(b"\x00" * 0x100)
    # Place 0xFF free space starting at an unaligned offset (0x11)
    rom[0x11:0x30] = b"\xFF" * (0x30 - 0x11)

    offset = memory.find_free_space_offset(rom, size=8, start_offset=0x10, align_to_word=True)
    assert offset == 0x14  # Next 4-byte aligned boundary