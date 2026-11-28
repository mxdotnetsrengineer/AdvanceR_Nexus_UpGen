from enum import StrEnum

class AvailableGames(StrEnum):
    ORIGINAL_FIRE_RED = "fire_red"
    RADICAL_FIRE_RED = "radical_red"
    #LEAF_GREEN = "leaf_green"
    #CUSTOM_LEAF_GREEN = "leaf_green_custom"
    EMERALD = "emerald"
    EMERALD_KAIZO = "emerald_kaizo"

    @property
    def config_key(self) -> str:
        return self.value