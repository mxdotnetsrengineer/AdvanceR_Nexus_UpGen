from typing import Any
from enums.gba.games_enum import AvailableGames
from enums.gba.pokemon.gba_pokemon_enums import GBAPokemonKeyIndex, GBAPokemonLogicKeyIndex, GBAPokemonOthersKeyIndex, GBAPokemonOthersLogicKeyIndex
from models.gba.pokemon.game_ui_keyboard import GameUIKeyboard
from models.gba.pokemon.ui_keyboard_patch import UIKeyboardPatch
from decorators.app_decorators import when_enabled,skip_when_disabled
from helpers.gba.games_helper import GBA_POKEMON_III_CHAR_TABLE
from services.config_service import ConfigService

class GBAKeyboardService:
    def __init__(self, config_service: ConfigService):
        self.allowed_chars = {char: byte for byte, char in GBA_POKEMON_III_CHAR_TABLE.items()}
        self.keyboards: Any = []
        self.keyboards_logic: Any = []
        self.config = config_service

    # Public Methods
    @when_enabled("ADD_SPANISH_CHARS")
    @skip_when_disabled("ONLY_DATABASE")
    async def set_spanish_chars(
        self,
        game_file: bytearray,
        game: AvailableGames,
        game_keyboards: GameUIKeyboard,
        keyboard_separators: list[str],
    ) -> None:
        self.keyboards = game_keyboards
        self.keyboards_logic = game_keyboards.logic

        #UI Sprites & Logic  True for more than one ocurrence, For example some games has 2 UPPER Keyboards in Memory
        keyboards_ocurrences = [2, 1, 1]
        match game:
            case AvailableGames.ORIGINAL_FIRE_RED | AvailableGames.RADICAL_FIRE_RED | AvailableGames.EMERALD:
                self._spanish_replace_pokemon_gba()

        await self._write_keyboard_to_game_file(
            game_file, game, self.keyboards.default, self.keyboards.logic.default, game_keyboards.logic.offsets[0], keyboard_separators, 
            keyboards_ocurrences[0]
        )
        await self._write_keyboard_to_game_file(
            game_file, game, self.keyboards.lower, self.keyboards.logic.lower, game_keyboards.logic.offsets[1], keyboard_separators, 
            keyboards_ocurrences[1]
        )
        await self._write_keyboard_to_game_file(
            game_file, game, self.keyboards.others, self.keyboards.logic.others, game_keyboards.logic.offsets[2], keyboard_separators,
            keyboards_ocurrences[2]
        )
    # End Public Methods

    # Private Methods
    def _spanish_replace_pokemon_gba(self) -> None:

        main_keyboards_shared_indexes = dict(
            visual_remove_indexes=[GBAPokemonKeyIndex.M],
            visual_insert_indexes=[GBAPokemonKeyIndex.N],
            visual_relocate_indexes=[GBAPokemonKeyIndex.SPACE_2],
            logic_remove_indexes=[GBAPokemonLogicKeyIndex.M],
            logic_insert_indexes=[GBAPokemonLogicKeyIndex.N + 1],
            # Space after L + 1 + Removed Character
            logic_relocate_indexes=[GBAPokemonLogicKeyIndex.L + 2],
            logic_null_indexes=[
                GBAPokemonLogicKeyIndex.F + 1,
                GBAPokemonLogicKeyIndex.L + 1,
                GBAPokemonLogicKeyIndex.S + 1,
                GBAPokemonLogicKeyIndex.Z + 1,
            ],
            logic_null_bytes=[bytearray(b"\x00") for _ in range(4)],
        )

        upper_patch = UIKeyboardPatch(
            visual_keyboard=self.keyboards.default,
            logic_keyboard=self.keyboards.logic.default,
            characters_to_insert=[self.allowed_chars["Ñ"]],
            relocated_characters=[self.allowed_chars["M"]],
            **main_keyboards_shared_indexes,
        )
        lower_patch = UIKeyboardPatch(
            visual_keyboard=self.keyboards.lower,
            logic_keyboard=self.keyboards.logic.lower,
            characters_to_insert=[self.allowed_chars["ñ"]],
            relocated_characters=[self.allowed_chars["m"]],
            **main_keyboards_shared_indexes,
        )
        others_patch = UIKeyboardPatch(
            visual_keyboard=self.keyboards.others,
            logic_keyboard=self.keyboards.logic.others,
            visual_remove_indexes=[
                GBAPokemonOthersKeyIndex.SPACE_1,
                GBAPokemonOthersKeyIndex.SPACE_2,
            ],
            visual_insert_indexes=[
                # Removed Space - 1
                GBAPokemonOthersKeyIndex.EXCLAMATION - 2,
                GBAPokemonOthersKeyIndex.QUESTION - 1,
            ],
            logic_remove_indexes=[],
            logic_insert_indexes=[
                GBAPokemonOthersLogicKeyIndex.EXCLAMATION,
                GBAPokemonOthersLogicKeyIndex.QUESTION,
            ],
            characters_to_insert=[
                self.allowed_chars["¡"],
                self.allowed_chars["¿"],
            ],
            # 0s after 5, after !, after - , after last char , 2 is because (4 + 1 + Space) ,
            # 3 is because (9 + 1 + Space + Removed Space) or for total removed spaces + 1. Indexes are for unmodified keyboard.
            logic_null_indexes=[
                GBAPokemonOthersLogicKeyIndex.NUM_4 + 2,
                GBAPokemonOthersLogicKeyIndex.NUM_9 + 3,
                GBAPokemonOthersLogicKeyIndex.HYPHEN + 3,
                GBAPokemonOthersLogicKeyIndex.QUOTE_SINGLE_CLOSE + 3,
            ],
            logic_null_bytes=[
                bytearray([0x00, 0x00]),
                bytearray([0x00, 0x00]),
                bytearray([0x00, 0x00]),
                bytearray([0x00, 0x00, 0x00]),
            ],
        )

        self._apply_main_keyboards_patch(upper_patch)
        self._apply_main_keyboards_patch(lower_patch)
        self._apply_others_keyboard_patch(others_patch)

    async def _write_keyboard_to_game_file(
        self,
        game_file: bytearray,
        game: AvailableGames,
        visual_keyboard: list[list[tuple[int, int]]],
        logic_keyboard: bytearray,
        logic_offset: int,
        keyboard_separators: list[str],
        keyboards_ocurrences: int = 1,
    ) -> None:
        keyboard_offset, keyboard_bytes = self._get_total_keyboard_bytes(
            game_file, game, visual_keyboard, keyboard_separators, keyboards_ocurrences
        )
        game_file[keyboard_offset : keyboard_offset + len(keyboard_bytes)] = keyboard_bytes
        game_file[logic_offset : logic_offset + len(logic_keyboard)] = logic_keyboard

    def _apply_main_keyboards_patch(self, patch: UIKeyboardPatch) -> None:
        self._insert_char_and_shift_forward(
            patch.visual_keyboard,
            patch.visual_remove_indexes,
            patch.visual_insert_indexes,
            patch.characters_to_insert,
        )
        for index, character in zip(patch.visual_relocate_indexes, patch.relocated_characters):
            self._replace_char(patch.visual_keyboard, index, character)

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
        for index, character in zip(patch.logic_relocate_indexes, patch.relocated_characters):
            patch.logic_keyboard[index] = character

    def _apply_others_keyboard_patch(self, patch: UIKeyboardPatch) -> None:
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

    def _insert_char_logic_and_shift_forward_bytes(
        self,
        logic_bytes: bytearray,
        remove_indexes: list[int],
        insert_indexes: list[int],
        new_char_bytes: list[int],
        space_byte: int = 0x00,
    ) -> None:
        chars = [b for b in logic_bytes if b != space_byte]

        for r_idx in remove_indexes:
            chars[r_idx] = None

        for i_idx, char_byte in sorted(zip(insert_indexes, new_char_bytes), key=lambda x: x[0], reverse=True):
            chars.insert(i_idx, char_byte)

        clean_chars = bytearray(c for c in chars if c is not None)
        logic_bytes.clear()
        logic_bytes.extend(clean_chars)

    def _insert_char_and_shift_forward(
        self,
        ui_keyboard: list[list[tuple[int, int]]],
        remove_indexes: list[int],
        insert_indexes: list[int],
        new_char_bytes: list[int],
    ) -> None:
        chars = [char for row in ui_keyboard for _, char in row]
        for r_idx in sorted(remove_indexes, reverse=True):
            chars.pop(r_idx)

        for i_idx, char_byte in sorted(zip(insert_indexes, new_char_bytes), key=lambda x: x[0]):
            chars.insert(i_idx, char_byte)

        idx = 0
        for row in ui_keyboard:
            for col, (spacing, _) in enumerate(row):
                row[col] = (spacing, chars[idx])
                idx += 1

    def _replace_logic_char(
        self,
        target_bytes: bytearray,
        indexes: int | list[int],
        new_bytes_list: bytearray | bytes | list[bytearray | bytes],
    ) -> bytearray:
        if isinstance(indexes, int):
            indexes = [indexes]
            new_bytes_list = [new_bytes_list]

        for idx, chunk in sorted(zip(indexes, new_bytes_list), key=lambda x: x[0], reverse=True):
            target_bytes[idx:idx] = chunk

        return target_bytes

    def _replace_char(self, ui_keyboard: list[list[tuple[int, int]]], character_idx: int, new_byte: int) -> None:
        row, col = divmod(character_idx, 8)
        spacing, _ = ui_keyboard[row][col]
        ui_keyboard[row][col] = (spacing, new_byte)

    def _get_total_keyboard_bytes(
        self, game_file: bytearray, game: AvailableGames, ui_keyboard: list[list[tuple[int, int]]], hex_separators: list[str],
        keyboards_ocurrences: int = 1,
    ) -> list[Any]:
        separators = [
            int(hex_str, 16)
            for hex_str in hex_separators
        ]

        first_keyboard_row = bytearray(
            byte
            for spacing, char in ui_keyboard[0][:3]
            for byte in (*separators, spacing, char)
        )

        keyboard_offset = (data := game_file).index(first_keyboard_row, data.index(first_keyboard_row) + (keyboards_ocurrences - 1))
        
        final_keyboard = bytearray();
        character_index = 0
        for row in ui_keyboard:
            for spacing, char in row:
                final_keyboard.extend([*separators, spacing, char])
                character_index+= 1
            final_keyboard.append(0xFF)
            
        return [keyboard_offset,final_keyboard]
    # End Private Methods
        
    