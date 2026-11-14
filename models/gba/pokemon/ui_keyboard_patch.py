from dataclasses import dataclass,field


@dataclass
class UIKeyboardPatch:
    visual_keyboard: bytearray
    logic_keyboard: bytearray
    visual_remove_indexes: list[int]
    visual_insert_indexes: list[int]
    logic_remove_indexes: list[int]
    logic_insert_indexes: list[int]
    logic_null_indexes: list[int]
    logic_null_bytes: list[bytearray]
    characters_to_insert: list[int]
    visual_relocate_indexes: list[int] = field(default_factory=list)
    logic_relocate_indexes: list[int] = field(default_factory=list)
    relocated_characters: list[int] = field(default_factory=list)