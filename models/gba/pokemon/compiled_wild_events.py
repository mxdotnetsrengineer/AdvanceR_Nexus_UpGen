from dataclasses import dataclass
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats

@dataclass
class CompiledWildEvents:
    offsets:list[int]
    events_count:int
    species:list[CompiledBaseStats]