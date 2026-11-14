from dataclasses import dataclass
from models.gba.pokemon.compiled_map import CompiledMap

@dataclass
class CompiledBank:
    bank_id:int
    header_offset:int
    maps:list[CompiledMap]