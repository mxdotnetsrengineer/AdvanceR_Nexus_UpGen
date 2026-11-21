from dataclasses import dataclass
from models.gba.pokemon.compiled_map import CompiledMap

@dataclass
class CompiledBank:
    bank_id:int
    header_offset:int
    maps:list[CompiledMap]

    @classmethod
    def dict_to_class(cls, bank_data: dict) -> CompiledBank:
        return cls(
            **{
                **bank_data,
                "maps": [CompiledMap.dict_to_class(map_data) for map_data in bank_data.get("maps", [])],
            }
        )