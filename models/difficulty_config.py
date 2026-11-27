from dataclasses import dataclass
from typing import Any
from models.difficulty_group import DifficultyGroup

@dataclass(frozen=True)
class DifficultyConfig:
    type: str
    level_mode: str
    level_quantity: int
    min_level: int
    groups: tuple[DifficultyGroup, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DifficultyConfig":
        raw_groups = data.get("groups", [])
        return cls(
            type=str(data["type"]),
            level_mode=str(data["level_mode"]),
            level_quantity=int(data["level_quantity"]),
            min_level=int(data["min_level"]),
            groups=tuple(DifficultyGroup.from_dict(g) for g in raw_groups if isinstance(g, dict)),
        )