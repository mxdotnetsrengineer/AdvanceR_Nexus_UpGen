from dataclasses import dataclass
from models.gba.pokemon.game_ui_keyboard_logic import GameUIKeyboardLogic

@dataclass
class GameUIKeyboard:
    default:list[list[tuple[int, int]]]
    lower:list[list[tuple[int, int]]]
    others:list[list[tuple[int, int]]]
    logic:GameUIKeyboardLogic