import random
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from services.config_service import ConfigService

class DifficultyService:
    def __init__(
        _self,
        config_service: ConfigService,
    ):
        _self.config = config_service
        _self._cached_difficulty_pools: list[tuple[int, list[CompiledBaseStats]]] | None = None
        _self.current_difficulty = _self.config.get("CURRENT_DIFFICULTY")
        
    # Public Methods
    def get_difficulty_pools(_self, wild_grass_slot_count: int,wild_candidates: list[CompiledBaseStats]):
        """Return cached difficulty pools or a single fallback tier containing all wild candidates."""
        difficulty_groups = _self.current_difficulty["groups"]
        
        # if not difficulty, random
        if not difficulty_groups or not isinstance(difficulty_groups, list):
            return [random.choice(wild_candidates) for _ in range(wild_grass_slot_count)]

        if _self._cached_difficulty_pools is None:
            _self._cached_difficulty_pools = _self.__build_difficulty_pools(
                difficulty_groups,
                wild_candidates,
                min_pool_size=wild_grass_slot_count,
            )

        return _self._cached_difficulty_pools

    def get_chosen_pool(_self, average_level: float) -> list[CompiledBaseStats]:
        """Return the candidate pool matching the given `average_level`."""
        if not _self._cached_difficulty_pools:
            return []

        for group_max_level, pool_species in _self._cached_difficulty_pools:
            if average_level <= group_max_level:
                return pool_species

        return _self._cached_difficulty_pools[-1][1]

    def calculate_adjusted_level(_self, original_level: int) -> int:
        """Adjust an encounter or trainer Pokémon level according to configured difficulty rules."""
        max_pokemon_level = 100
        level_mode = _self.current_difficulty["level_mode"]
        quantity = _self.current_difficulty["level_quantity"]
        min_allowed = _self.current_difficulty["min_level"]

        match level_mode:
            case "ADD":
                new_level = original_level + quantity
            case "SUBS":
                new_level = original_level - quantity
            case _:
                new_level = original_level

        return max(min_allowed, min(max_pokemon_level, new_level))
    
    # End Public Methods

    # Private Methods
    def __build_difficulty_pools(
        _self,
        difficulty_groups: list[dict],
        wild_candidates: list[CompiledBaseStats],
        min_pool_size: int = 12,
    ) -> list[tuple[int, list[CompiledBaseStats]]]:
        """Group wild Pokémon candidates into difficulty tiers based on BST, level, and evolution stage."""
        pools: list[tuple[int, list[CompiledBaseStats]]] = []
        prev_max_bst = 0
        bst_expansion_step = 50

        for group in difficulty_groups:
            if not isinstance(group, dict):
                continue

            group_max_level = group["max_level"]
            max_bst = group["max_bst"]
            max_stage = group["max_evolution_stage"]

            # Pre-filter candidates eligible for this evolution stage before expanding BST ranges
            stage_eligible = [
                sp for sp in wild_candidates
                if sp.evolution_stage <= max_stage and not sp.is_mega
            ]

            lower_bst = prev_max_bst
            upper_bst = max_bst
            pool = [sp for sp in stage_eligible if lower_bst < sp.bst <= upper_bst]

            while len({sp.name.strip().lower() for sp in pool}) < min_pool_size and lower_bst > 0:
                lower_bst = max(0, lower_bst - bst_expansion_step)
                upper_bst += bst_expansion_step
                pool = [sp for sp in stage_eligible if lower_bst < sp.bst <= upper_bst]

            if not pool:
                pool = wild_candidates

            pools.append((group_max_level, pool))
            prev_max_bst = max_bst

        return pools
    # End Private Methods