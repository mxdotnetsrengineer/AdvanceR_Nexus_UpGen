from dataclasses import dataclass

@dataclass
class GameUIKeyboardLogic:
    default:bytearray
    lower:bytearray
    others:bytearray
    offsets:tuple[int,int,int]