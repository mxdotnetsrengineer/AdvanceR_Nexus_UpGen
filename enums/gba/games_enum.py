from enum import Enum,StrEnum

class AvailableGames(Enum):
    ORIGINAL_FIRE_RED = 0
    RADICAL_FIRE_RED = 1
    LEAF_GREEN = 2
    CUSTOM_LEAF_GREEN = 3
    EMERALD = 4
    EMERALD_KAIZO = 5

class GameSelection(StrEnum):
    ORIGINAL_FIRE_RED = "FIRE_RED"
    RADICAL_FIRE_RED = "RADICAL_RED"
    # Agrega aquí los demás miembros que tengas en AvailableGames

    def to_domain_enum(self) -> AvailableGames:
        return AvailableGames[self.name]