from enums.gba.games_enum import AvailableGames
from enums.gba.pokemon.gba_pokemon_enums import GBAPokemonKeyIndex, GBAPokemonLogicKeyIndex, GBAPokemonOthersKeyIndex, GBAPokemonOthersLogicKeyIndex
from models.gba.pokemon.game_ui_keyboard import GameUIKeyboard
from models.gba.pokemon.game_ui_keyboard_logic import GameUIKeyboardLogic
from models.gba.pokemon.ui_keyboard_patch import UIKeyboardPatch
from decorators.app_decorators import when_enabled,skip_when_enabled
from helpers.gba.games_helper import STRING_TERMINATOR
from helpers.gba.pokemon.gba_pokemon_helper import GBA_POKEMON_III_CHAR_TABLE
from services.config_service import ConfigService

class GBAKeyboardService:
    def __init__(self, config_service: ConfigService):
        self.allowed_chars = {char: byte for byte, char in GBA_POKEMON_III_CHAR_TABLE.items()}
        self.keyboards: GameUIKeyboard | None = None
        self.keyboards_logic: GameUIKeyboardLogic | None = None 
        self.config = config_service

    # Public Methods
    @skip_when_enabled("ONLY_DATABASE")
    @when_enabled("ADD_SPANISH_CHARS")
    def set_spanish_chars(
        self,
        game_file: bytearray,
        game: AvailableGames,
        game_keyboards: GameUIKeyboard,
        keyboard_separators: list[str],
    ) -> None:
        """Replace and write Spanish character mappings across all UI keyboard layouts."""
        self.keyboards = game_keyboards
        self.keyboards_logic = game_keyboards.logic

        #UI Sprites & Logic  True for more than one ocurrence, For example some games has 2 UPPER Keyboards in Memory
        keyboards_occurrences = [2, 1, 1]
        match game:
            case AvailableGames.ORIGINAL_FIRE_RED | AvailableGames.RADICAL_FIRE_RED | AvailableGames.EMERALD | AvailableGames.EMERALD_KAIZO:
                self._spanish_replace_pokemon_gba()

        keyboard_layers = [
            (self.keyboards.default, self.keyboards.logic.default, game_keyboards.logic.offsets[0], keyboards_occurrences[0]),
            (self.keyboards.lower, self.keyboards.logic.lower, game_keyboards.logic.offsets[1], keyboards_occurrences[1]),
            (self.keyboards.others, self.keyboards.logic.others, game_keyboards.logic.offsets[2], keyboards_occurrences[2]),
        ]

        for visual_layout, logic_layout, target_offset, occurrences in keyboard_layers:
            self._write_keyboard_to_game_file(
                game_file=game_file,
                visual_keyboard=visual_layout,
                logic_keyboard=logic_layout,
                target_offset=target_offset,
                keyboard_separators=keyboard_separators,
                keyboards_occurrences=occurrences,
            )
    # End Public Methods

    # Private Methods
    def _spanish_replace_pokemon_gba(self) -> None:
        """Configure and apply Spanish character layout patches for GBA UI keyboards."""
        shared_main_indexes = {
            "visual_remove_indexes": (GBAPokemonKeyIndex.M,),
            "visual_insert_indexes": (GBAPokemonKeyIndex.N,),
            "visual_relocate_indexes": (GBAPokemonKeyIndex.SPACE_2,),
            "logic_remove_indexes": (GBAPokemonLogicKeyIndex.M,),
            "logic_insert_indexes": (GBAPokemonLogicKeyIndex.N + 1,),
            "logic_relocate_indexes": (GBAPokemonLogicKeyIndex.L + 2,),  # Space after L + 1 + removed char
            "logic_null_indexes": (
                GBAPokemonLogicKeyIndex.F + 1,
                GBAPokemonLogicKeyIndex.L + 1,
                GBAPokemonLogicKeyIndex.S + 1,
                GBAPokemonLogicKeyIndex.Z + 1,
            ),
        }

        upper_patch = UIKeyboardPatch(
            visual_keyboard=self.keyboards.default,
            logic_keyboard=self.keyboards.logic.default,
            characters_to_insert=[self.allowed_chars["Ñ"]],
            relocated_characters=[self.allowed_chars["M"]],
            logic_null_bytes=[bytearray(1) for _ in range(4)],
            **shared_main_indexes,
        )

        lower_patch = UIKeyboardPatch(
            visual_keyboard=self.keyboards.lower,
            logic_keyboard=self.keyboards.logic.lower,
            characters_to_insert=[self.allowed_chars["ñ"]],
            relocated_characters=[self.allowed_chars["m"]],
            logic_null_bytes=[bytearray(1) for _ in range(4)],
            **shared_main_indexes,
        )

        # Offsets account for removed spaces in the unmodified 'others' keyboard layout
        pre_space_shift = 2
        post_space_shift = 3

        others_patch = UIKeyboardPatch(
            visual_keyboard=self.keyboards.others,
            logic_keyboard=self.keyboards.logic.others,
            visual_remove_indexes=(
                GBAPokemonOthersKeyIndex.SPACE_1,
                GBAPokemonOthersKeyIndex.SPACE_2,
            ),
            visual_insert_indexes=(
                GBAPokemonOthersKeyIndex.EXCLAMATION - pre_space_shift,
                GBAPokemonOthersKeyIndex.QUESTION - 1,
            ),
            logic_remove_indexes=(),
            logic_insert_indexes=(
                GBAPokemonOthersLogicKeyIndex.EXCLAMATION,
                GBAPokemonOthersLogicKeyIndex.QUESTION,
            ),
            characters_to_insert=[
                self.allowed_chars["¡"],
                self.allowed_chars["¿"],
            ],
            logic_null_indexes=(
                GBAPokemonOthersLogicKeyIndex.NUM_4 + pre_space_shift,
                GBAPokemonOthersLogicKeyIndex.NUM_9 + post_space_shift,
                GBAPokemonOthersLogicKeyIndex.HYPHEN + post_space_shift,
                GBAPokemonOthersLogicKeyIndex.QUOTE_SINGLE_CLOSE + post_space_shift,
            ),
            logic_null_bytes=[bytearray(2), bytearray(2), bytearray(2), bytearray(3)],
        )

        self._apply_main_keyboards_patch(upper_patch)
        self._apply_main_keyboards_patch(lower_patch)
        self._apply_others_keyboard_patch(others_patch)

    def _write_keyboard_to_game_file(
        self,
        game_file: bytearray,
        visual_keyboard: list[list[tuple[int, int]]],
        logic_keyboard: bytearray,
        target_offset: int,
        keyboard_separators: list[str],
        keyboards_occurrences: int = 1,
    ) -> None:
        """Write the patched visual tilemap and logic bytes into their target offsets in `game_file`."""
        game_size = len(game_file)
        keyboard_offset, keyboard_bytes = self._get_total_keyboard_bytes(
            game_file, visual_keyboard, keyboard_separators, keyboards_occurrences
        )

        if keyboard_offset is not None and 0 <= keyboard_offset and keyboard_offset + len(keyboard_bytes) <= game_size:
            game_file[keyboard_offset : keyboard_offset + len(keyboard_bytes)] = keyboard_bytes

        if 0 <= target_offset and target_offset + len(logic_keyboard) <= game_size:
            game_file[target_offset : target_offset + len(logic_keyboard)] = logic_keyboard

    def _apply_main_keyboards_patch(self, patch: UIKeyboardPatch) -> None:
        """Apply base patch plus character relocation for upper and lower keyboards."""
        self._apply_keyboard_base_patch(patch)

        for index, character in zip(patch.visual_relocate_indexes, patch.relocated_characters):
            self._replace_char(patch.visual_keyboard, index, character)

        for index, character in zip(patch.logic_relocate_indexes, patch.relocated_characters):
            patch.logic_keyboard[index] = character


    def _apply_others_keyboard_patch(self, patch: UIKeyboardPatch) -> None:
        """Apply base patch to the symbols/others keyboard layout."""
        self._apply_keyboard_base_patch(patch)

    def _apply_keyboard_base_patch(self, patch: UIKeyboardPatch) -> None:
        """Apply shared visual, logical, and null-byte modifications to a UI keyboard patch."""
        self._insert_char_and_shift_forward(
            patch.visual_keyboard,
            patch.visual_remove_indexes,
            patch.visual_insert_indexes,
            patch.characters_to_insert,
        )
        self._insert_char_logic_and_shift_forward_bytes(
            patch.logic_keyboard,
            patch.logic_remove_indexes,
            patch.logic_insert_indexes,
            patch.characters_to_insert,
        )
        self._replace_logic_char(
            patch.logic_keyboard,
            indexes=patch.logic_null_indexes,
            new_bytes_list=patch.logic_null_bytes,
        )

    def _get_total_keyboard_bytes(
        self,
        game_file: bytearray,
        ui_keyboard: list[list[tuple[int, int]]],
        hex_separators: list[str],
        keyboards_occurrences: int = 1,
    ) -> tuple[int | None, bytearray]:
        """Locate the Nth keyboard occurrence offset in `game_file` and build its full byte sequence."""
        separators = [int(hex_str, 16) for hex_str in hex_separators]
        preview_chars_count = 5

        first_keyboard_row = bytearray(
            byte
            for spacing, char in ui_keyboard[0][:preview_chars_count]
            for byte in (*separators, spacing, char)
        )

        keyboard_offset: int | None = None
        search_start = 0

        for _ in range(keyboards_occurrences):
            found_offset = game_file.find(first_keyboard_row, search_start)
            
            if found_offset == -1:
                keyboard_offset = None
                break
            keyboard_offset = found_offset
            search_start = found_offset + len(first_keyboard_row)

        final_keyboard = bytearray()
        for row in ui_keyboard:
            for spacing, char in row:
                final_keyboard.extend((*separators, spacing, char))
            final_keyboard.append(STRING_TERMINATOR)

        return keyboard_offset, final_keyboard


    def _insert_char_logic_and_shift_forward_bytes(
        self,
        logic_bytes: bytearray,
        remove_indexes: list[int] | tuple[int, ...],
        insert_indexes: list[int] | tuple[int, ...],
        new_char_bytes: list[int],
        space_byte: int = 0x00,
    ) -> None:
        """Remove target characters, insert new ones, and shift remaining logic bytes forward."""
        chars: list[int | None] = [b for b in logic_bytes if b != space_byte]

        for r_idx in remove_indexes:
            chars[r_idx] = None

        for i_idx, char_byte in sorted(zip(insert_indexes, new_char_bytes), key=lambda x: x[0], reverse=True):
            chars.insert(i_idx, char_byte)

        clean_chars = bytearray(c for c in chars if c is not None)
        logic_bytes[:] = clean_chars


    def _insert_char_and_shift_forward(
        self,
        ui_keyboard: list[list[tuple[int, int]]],
        remove_indexes: list[int] | tuple[int, ...],
        insert_indexes: list[int] | tuple[int, ...],
        new_char_bytes: list[int],
    ) -> None:
        """Remove and insert visual character bytes while preserving each slot's original spacing."""
        chars = [char for row in ui_keyboard for _, char in row]

        for r_idx in sorted(remove_indexes, reverse=True):
            chars.pop(r_idx)

        for i_idx, char_byte in sorted(zip(insert_indexes, new_char_bytes), key=lambda x: x[0]):
            chars.insert(i_idx, char_byte)

        char_iter = iter(chars)
        for row in ui_keyboard:
            for col, (spacing, _) in enumerate(row):
                row[col] = (spacing, next(char_iter))


    def _replace_logic_char(
        self,
        target_bytes: bytearray,
        indexes: int | list[int] | tuple[int, ...],
        new_bytes_list: bytearray | bytes | list[bytearray | bytes],
    ) -> bytearray:
        """Insert null or replacement byte chunks into `target_bytes` from right to left."""
        if isinstance(indexes, int):
            indexes = [indexes]
            new_bytes_list = [new_bytes_list]  

        for idx, chunk in sorted(zip(indexes, new_bytes_list), key=lambda x: x[0], reverse=True):
            target_bytes[idx:idx] = chunk

        return target_bytes


    def _replace_char(self, ui_keyboard: list[list[tuple[int, int]]], character_idx: int, new_byte: int) -> None:
        """Replace a single character byte inside the 8-column visual keyboard grid."""
        keyboard_columns = 8
        row, col = divmod(character_idx, keyboard_columns)
        spacing, _ = ui_keyboard[row][col]
        ui_keyboard[row][col] = (spacing, new_byte)
    # End Private Methods
            
    