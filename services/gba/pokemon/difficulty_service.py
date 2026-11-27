import random
from collections.abc import Sequence
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from models.difficulty_config import DifficultyConfig
from models.difficulty_group import DifficultyGroup
from services.config_service import ConfigService

class DifficultyService:
    def __init__(
        self,
        config_service: ConfigService,
    ):
        self.config = config_service
        self._cached_difficulty_pools: list[tuple[int, list[CompiledBaseStats]]] | None = None

        dif_json = self.config.get("CURRENT_DIFFICULTY")
        self.current_difficulty: DifficultyConfig | None = (
            DifficultyConfig.from_dict(dif_json) if isinstance(dif_json, dict) else None
        )
        
    # Public Methods
    def get_difficulty_pools(self, wild_grass_slot_count: int,wild_candidates: list[CompiledBaseStats]):
        """Return cached difficulty pools or a single fallback tier containing all wild candidates."""
        if self._cached_difficulty_pools is not None:
            return self._cached_difficulty_pools
    
        if self.current_difficulty is None or not self.current_difficulty.groups:
            self._cached_difficulty_pools = [(100, list(wild_candidates))]
            return self._cached_difficulty_pools
        
        self._cached_difficulty_pools = self._build_difficulty_pools(
            self.current_difficulty.groups,
            wild_candidates,
            min_pool_size=wild_grass_slot_count,
        )
        return self._cached_difficulty_pools

    def get_chosen_pool(self, average_level: float) -> list[CompiledBaseStats]:
        """Return the candidate pool matching the given `average_level`."""
        if not self._cached_difficulty_pools:
            return []

        for group_max_level, pool_species in self._cached_difficulty_pools:
            if average_level <= group_max_level:
                return pool_species

        return self._cached_difficulty_pools[-1][1]

    def calculate_adjusted_level(self, original_level: int) -> int:
        """Adjust an encounter or trainer Pokémon level according to configured difficulty rules."""
        if self.current_difficulty is None:
            return original_level
        
        max_pokemon_level = 100
        match self.current_difficulty.level_mode:
            case "ADD":
                new_level = original_level + self.current_difficulty.level_quantity
            case "SUBS":
                new_level = original_level - self.current_difficulty.level_quantity
            case _:
                new_level = original_level

        return max(self.current_difficulty.min_level, min(max_pokemon_level, new_level))
    
    # End Public Methods

    # Private Methods
    def _build_difficulty_pools(
        self,
        difficulty_groups: Sequence[DifficultyGroup],
        wild_candidates: list[CompiledBaseStats],
        min_pool_size: int = 12,
    ) -> list[tuple[int, list[CompiledBaseStats]]]:
        """Group wild Pokémon candidates into difficulty tiers based on BST, level, and evolution stage."""
        pools: list[tuple[int, list[CompiledBaseStats]]] = []
        prev_max_bst = 0
        bst_expansion_step = 50

        for group in difficulty_groups:
            if not isinstance(group, DifficultyGroup):
                continue

            group_max_level = group["max_level"]
            max_bst = group["max_bst"]
            max_stage = group["max_evolution_stage"]

            # Pre-filter candidates eligible for this evolution stage before expanding BST ranges
            stage_eligible = [
                sp for sp in wild_candidates
                if sp.evolution_stage <= group.max_evolution_stage and not sp.is_mega
            ]

            lower_bst = prev_max_bst
            upper_bst = group.max_bst
            pool = [sp for sp in stage_eligible if lower_bst < sp.bst <= upper_bst]

            while len({sp.name.strip().lower() for sp in pool}) < min_pool_size and lower_bst > 0:
                lower_bst = max(0, lower_bst - bst_expansion_step)
                upper_bst += bst_expansion_step
                pool = [sp for sp in stage_eligible if lower_bst < sp.bst <= upper_bst]

            if not pool:
                pool = wild_candidates

            pools.append((group.max_level, pool))
            prev_max_bst = group.max_bst

        return pools
    # End Private Methods
