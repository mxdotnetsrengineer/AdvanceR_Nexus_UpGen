from dataclasses import dataclass

@dataclass
class CompiledEvent:
    event_id:int
    sprite_id:int
    header_offset:int
    entry_offset:int

    @classmethod
    def dict_to_class(cls, event_data: dict) -> "CompiledEvent":
        return cls(**event_data)