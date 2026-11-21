from dataclasses import dataclass, field
from models.gba.pokemon.compiled_event import CompiledEvent

@dataclass
class CompiledMap:
    map_id:int
    header_offset:int
    name:str
    width:int
    height:int
    events_count:int
    events: CompiledEvent[list] = field(default_factory=list)

    @classmethod
    def dict_to_class(cls, map_data: dict) -> "CompiledMap":
        """Create a CompiledMap instance along with its nested CompiledEvent objects."""
        return cls(
            **{
                **map_data,
                "events": [
                    CompiledEvent.dict_to_class(event_data)
                    for event_data in map_data.get("events", [])
                ],
            }
        )