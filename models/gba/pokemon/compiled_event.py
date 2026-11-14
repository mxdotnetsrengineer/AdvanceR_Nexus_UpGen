from dataclasses import dataclass

@dataclass
class CompiledEvent:
    event_id:int
    sprite_id:int
    header_offset:int