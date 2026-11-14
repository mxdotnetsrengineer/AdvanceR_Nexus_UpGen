from dataclasses import dataclass

@dataclass
class GameUIKeyboardLogic:
    default:bytearray
    lower:bytearray
    others:bytearray
    offsets:[int,int,int]