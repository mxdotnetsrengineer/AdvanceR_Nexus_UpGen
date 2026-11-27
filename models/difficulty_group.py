from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DifficultyGroup:
    group: int
    max_level: int
    max_bst: int
    max_evolution_stage: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DifficultyGroup":
        return cls(
            group=int(data["group"]),
            max_level=int(data["max_level"]),
            max_bst=int(data["max_bst"]),
            max_evolution_stage=int(data["max_evolution_stage"]),
        )