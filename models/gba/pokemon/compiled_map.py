from dataclasses import dataclass

@dataclass
class CompiledMap:
    map_id:int
    header_offset:int
    name:str
    width:int
    height:int
    events_count:int