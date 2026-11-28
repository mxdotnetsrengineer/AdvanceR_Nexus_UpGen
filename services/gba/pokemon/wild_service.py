import random
from operator import attrgetter
from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from models.gba.pokemon.compiled_wild_events import CompiledWildEvents
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE, STRING_TERMINATOR, HEX_NUM_BASE, U16_BYTE_SIZE
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.error_service import ErrorService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.difficulty_service import DifficultyService

class WildService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService,
        error_service: ErrorService,
        difficulty_service: DifficultyService
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service  
        self.translator = translations_service
        self.errors = error_service

        self.difficulty = difficulty_service
        self.wild_used_ids = []
        self.wild_used_names = []
        self.wild_header_struct_size = self.config.get("WILD_HEADER_STRUCT_SIZE")
        self.wild_slot_struct_size = self.config.get("WILD_SLOT_STRUCT_SIZE")
        
        self._randomized_slots_offsets: set[int] = set()
        self._slots_offset_cache: dict[tuple[int, int, int], int | None] = {}
                
    # Public Methods
    def get_wild_data(self,game_file: bytearray, species_list: list[CompiledBaseStats]) -> CompiledWildEvents:
        game_size = len(game_file)
        
        raw_wild_offsets: list[int] = self.config.get("WILD_POKEMON_OFFSET") or []
        wild_table_offsets = [
            val for off in raw_wild_offsets
            if 0 <= (val := int(off, HEX_NUM_BASE) if isinstance(off, str) else off) < game_size
        ]
        wild_grass_slot_count = self.config.get("WILD_GRASS_SLOT_COUNT")
        wild_candidates = [sp for sp in species_list if not sp.is_mega]
        return CompiledWildEvents(wild_table_offsets,wild_grass_slot_count,wild_candidates)

    def randomize_wild_encounters(
        self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_grass_slot_count: int,
        wild_table_offset: int,
        selected_species: list[CompiledBaseStats],
        species_by_id: dict[int, CompiledBaseStats],
        game_file: bytearray,
    ) -> None:
        """Locate wild encounter data for a map and replace its grass encounter slots."""
        if not selected_species or wild_table_offset is None or wild_table_offset < 0:
            return

        slots_list_offset = self._resolve_slots_list_offset(
            game_file, wild_table_offset, bank.bank_id, compiled_map.map_id
        )
        if slots_list_offset is None or slots_list_offset in self._randomized_slots_offsets:
            return

        self._save_randomized_wild_slots(
            game_file=game_file,
            slots_list_offset=slots_list_offset,
            wild_grass_slot_count=wild_grass_slot_count,
            bank=bank,
            compiled_map=compiled_map,
            selected_species=selected_species,
            species_by_id=species_by_id,
        )

    def select_wild_species(
        self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_grass_slot_count: int,
        wild_table_offset: int,
        wild_candidates: list[CompiledBaseStats],
        game_file: bytearray,
    ) -> list[CompiledBaseStats]:
        """Select and sort wild Pokémon candidates by BST based on each slot's average encounter level."""
        game_size = len(game_file)
        if wild_table_offset is None or wild_table_offset < 0 or not wild_candidates:
            return []
        
        slots_list_offset = self._resolve_slots_list_offset(
            game_file, wild_table_offset, bank.bank_id, compiled_map.map_id
        )
        if slots_list_offset is None or slots_list_offset < 0 or slots_list_offset >= game_size:
            return []

        if not self.difficulty.get_difficulty_pools(wild_grass_slot_count, wild_candidates):
            return []

        self._reset_used_candidates()
        selected_species: list[CompiledBaseStats] = []

        for slot_idx in range(wild_grass_slot_count):
            slot_offset = slots_list_offset + (slot_idx * self.wild_slot_struct_size)
            if slot_offset + self.wild_slot_struct_size > game_size:
                break

            min_level, max_level = game_file[slot_offset], game_file[slot_offset + 1]
            avg_level = (min_level + max_level) / 2

            chosen_pool = self.difficulty.get_chosen_pool(avg_level)
            available_elements = self._filter_to_unique_candidates(wild_candidates, chosen_pool)
            selected_species.append(self._pick_candidate(available_elements))

        selected_species.sort(key=attrgetter("bst"))
        return selected_species
    # End Public Methods
    
    # Private Methods
    def _find_wild_info_offset(
        self,
        game_file: bytearray,
        wild_table_offset: int,
        bank_id: int,
        map_id: int,
    ) -> int | None:
        """Locate the grass wild encounter info offset for a given bank and map ID."""
        game_size = len(game_file)
        if wild_table_offset < 0 or wild_table_offset + self.wild_header_struct_size > game_size:
            return None

        max_end_offset = game_size - self.wild_header_struct_size + 1

        for header_offset in range(wild_table_offset, max_end_offset, self.wild_header_struct_size):
            entry_bank_id = game_file[header_offset]
            entry_map_id = game_file[header_offset + 1]

            if entry_bank_id == STRING_TERMINATOR and entry_map_id == STRING_TERMINATOR:
                break

            if entry_bank_id == bank_id and entry_map_id == map_id:
                wild_info_entry_offset = header_offset + GBA_PTR_BYTE_SIZE
                wild_info_ptr = game_file[wild_info_entry_offset : wild_info_entry_offset + GBA_PTR_BYTE_SIZE]
                return self.memory.pointer_to_offset(wild_info_ptr)

        return None

    def _resolve_slots_list_offset(
        self,
        game_file: bytearray,
        wild_table_offset: int,
        bank_id: int,
        map_id: int,
    ) -> int | None:
        """Resolve and cache the grass encounter slots offset for a given (table, bank, map)."""
        cache_key = (wild_table_offset, bank_id, map_id)
        if cache_key in self._slots_offset_cache:
            return self._slots_offset_cache[cache_key]

        wild_info_offset = self._find_wild_info_offset(
            game_file=game_file,
            wild_table_offset=wild_table_offset,
            bank_id=bank_id,
            map_id=map_id,
        )
        if wild_info_offset is None:
            self._slots_offset_cache[cache_key] = None
            return None

        # Wild info struct (8 bytes): [encounter_rate: u32, slots_list_ptr: u32]
        slots_entry_offset = wild_info_offset + GBA_PTR_BYTE_SIZE
        if slots_entry_offset + GBA_PTR_BYTE_SIZE > len(game_file):
            self._slots_offset_cache[cache_key] = None
            return None

        slots_list_ptr = game_file[slots_entry_offset : slots_entry_offset + GBA_PTR_BYTE_SIZE]
        slots_list_offset = self.memory.pointer_to_offset(slots_list_ptr)

        if slots_list_offset is None or slots_list_offset < 0 or slots_list_offset >= len(game_file):
            self._slots_offset_cache[cache_key] = None
            return None

        self._slots_offset_cache[cache_key] = slots_list_offset
        return slots_list_offset

    def _reset_used_candidates(self) -> None:
        """Clear used species IDs and names before randomizing a new map's encounter table."""
        self.wild_used_ids.clear()
        self.wild_used_names.clear()

    def _filter_to_unique_candidates(self,fallback_pool: list[CompiledBaseStats], chosen_pool: list[CompiledBaseStats]):
        available_elements = [
            sp for sp in chosen_pool
            if sp.id not in self.wild_used_ids and sp.name.strip().lower() not in self.wild_used_names
        ]
        if not available_elements:
            available_elements = [
                sp for sp in fallback_pool
                if sp.id not in self.wild_used_ids and sp.name.strip().lower() not in self.wild_used_names
            ]
        if not available_elements:
            available_elements = [sp for sp in chosen_pool if sp.id not in self.wild_used_ids]
        if not available_elements:
            available_elements = chosen_pool
        return available_elements

    def _get_previous_wild_specie(
        self,
        slot_idx: int,
        species_field_offset: int,
        old_min_level: int,
        old_max_level: int,
        new_pokemon: CompiledBaseStats,
        new_min_level: int,
        new_max_level: int,
        species_by_id: dict[int, CompiledBaseStats],
        game_file: bytearray,
    ) -> str:
        """Format a comparison log line showing the previous and new wild Pokémon in a slot."""
        species_values = self.memory.read_u16_array(game_file, species_field_offset, 1)
        old_species_id = species_values[0] if species_values else 0

        old_pokemon = species_by_id.get(old_species_id)
        old_name = old_pokemon.name if old_pokemon else f"ID#{old_species_id}"

        return (
            f"Slot {slot_idx + 1:02d}: "
            f"{old_name} (#{old_species_id:03d} Nv.{old_min_level}-{old_max_level}) -> "
            f"{new_pokemon.name} (#{new_pokemon.id:03d} | BST:{new_pokemon.bst} Nv.{new_min_level}-{new_max_level})"
        )

    def _pick_candidate(self, available_elements: list[CompiledBaseStats]):
        chosen_element = random.choice(available_elements)
        self.wild_used_ids.append(chosen_element.id)
        self.wild_used_names.append(chosen_element.name.strip().lower())
        return chosen_element

    def _save_randomized_wild_slots(
        self,
        game_file: bytearray,
        slots_list_offset: int,
        wild_grass_slot_count: int,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        selected_species: list[CompiledBaseStats],
        species_by_id: dict[int, CompiledBaseStats],
    ) -> None:
        """Write randomized species and adjusted levels into each wild encounter slot."""
        game_size = len(game_file)
        # Wild info struct (8 bytes): [encounter_rate: u32, slots_list_ptr: u32]
        if slots_list_offset in self._randomized_slots_offsets:
            return

        self._randomized_slots_offsets.add(slots_list_offset)
        replacements_log: list[str] = []

        # Wild slot struct (4 bytes): [min_level: u8, max_level: u8, species_id: u16]
        for slot_idx, new_pokemon in enumerate(selected_species[:wild_grass_slot_count]):
            slot_offset = slots_list_offset + (slot_idx * self.wild_slot_struct_size)
            if slot_offset + self.wild_slot_struct_size > game_size:
                break

            species_field_offset = slot_offset + U16_BYTE_SIZE
            old_min_level, old_max_level = game_file[slot_offset], game_file[slot_offset + 1]
            new_min_level, new_max_level = old_min_level, old_max_level
            if self.config.get("CURRENT_DIFFICULTY"):
                new_min_level = self.difficulty.calculate_adjusted_level(old_min_level)
                new_max_level = self.difficulty.calculate_adjusted_level(old_max_level)

            replacements_log.append(
                self._get_previous_wild_specie(
                    slot_idx=slot_idx,
                    species_field_offset=species_field_offset,
                    old_min_level=old_min_level,
                    old_max_level=old_max_level,
                    new_pokemon=new_pokemon,
                    new_min_level=new_min_level,
                    new_max_level=new_max_level,
                    species_by_id=species_by_id,
                    game_file=game_file,
                )
            )

            game_file[slot_offset] = new_min_level
            game_file[slot_offset + 1] = new_max_level
            game_file[species_field_offset : species_field_offset + U16_BYTE_SIZE] = new_pokemon.id.to_bytes(
                U16_BYTE_SIZE, byteorder="little"
            )

        bank_label = getattr(bank, "name", f"Bank {bank.bank_id}")
        self.log.info(
            self.translator.translate(
                "messages.wilds.grass_randomized",
                bank_id=bank.bank_id,
                bank_label=bank_label,
                map_id=compiled_map.map_id,
                map_name=compiled_map.name,
                replacements="\n  ".join(replacements_log),
            ),
            False,
        )
    # End Private Methods
    