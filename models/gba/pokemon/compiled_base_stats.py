from dataclasses import dataclass


@dataclass
class CompiledBaseStats:
    id: int
    name: str
    offset: int
    hp: int
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int
    bst: int
    type_1: int
    type_2: int
    catch_rate: int
    base_exp: int
    ev_yield_raw: int
    item_1: int
    item_2: int
    gender_ratio: int
    egg_cycles: int
    base_friendship: int
    growth_rate: int
    egg_group_1: int
    egg_group_2: int
    ability_1: int
    ability_2: int
    safari_zone_flee_rate: int
    body_color_and_flip: int
    evolution_stage:int
    is_mega: bool = False

    @property
    def offset_hex(self) -> str:
        return hex(self.offset)