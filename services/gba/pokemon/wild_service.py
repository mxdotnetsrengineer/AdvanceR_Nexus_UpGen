import random
from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE, STRING_TERMINATOR
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService

class WildService:
    def __init__(
        _self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        translations_service: TranslationsService,
    ):
        _self.config = config_service
        _self.memory = memory_service
        _self.log = log_service
        _self.translator = translations_service
        
        _self.wild_used_ids = []
        _self.wild_used_names = []
        _self.wild_header_struct_size = _self.config.get("WILD_HEADER_STRUCT_SIZE")
                
    # Public Methods
    def get_wild_species(
        _self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_table_offset: int,
        game_file: bytearray,
        randomized_offsets: set[int],
    ) -> int | None:
        """Resolve the grass wild encounter slots offset for a map if not already randomized."""
        wild_info_offset = _self.__find_wild_info_offset(
            game_file=game_file,
            wild_table_offset=wild_table_offset,
            bank_id=bank.bank_id,
            map_id=compiled_map.map_id,
        )
        if wild_info_offset is None:
            return None

        slots_ptr_offset = wild_info_offset + GBA_PTR_BYTE_SIZE
        if slots_ptr_offset + GBA_PTR_BYTE_SIZE > len(game_file):
            return None

        slots_list_ptr = game_file[slots_ptr_offset : slots_ptr_offset + GBA_PTR_BYTE_SIZE]
        slots_list_offset = _self.memory.pointer_to_offset(slots_list_ptr)

        if slots_list_offset is None or slots_list_offset in randomized_offsets:
            return None
        
        return slots_list_offset
    
    def filter_to_unique_candidates(_self,fallback_pool: list[CompiledBaseStats], chosen_pool: list[CompiledBaseStats]):
        available_elements = [
            sp for sp in chosen_pool
            if sp.id not in _self.wild_used_ids and sp.name.strip().lower() not in _self.wild_used_names
        ]
        if not available_elements:
            available_elements = [
                sp for sp in fallback_pool
                if sp.id not in _self.wild_used_ids and sp.name.strip().lower() not in _self.wild_used_names
            ]
        if not available_elements:
            available_elements = [sp for sp in chosen_pool if sp.id not in _self.wild_used_ids]
        if not available_elements:
            available_elements = chosen_pool
        return available_elements

    def pick_candidate(_self, available_elements: list[CompiledBaseStats]):
        chosen_element = random.choice(available_elements)
        _self.wild_used_ids.append(chosen_element.id)
        _self.wild_used_names.append(chosen_element.name.strip().lower())
        return chosen_element

    def validate_and_get_wild_offset(
        _self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_table_offset: int,
        game_file: bytearray,
    ) -> int | None:
        """Locate wild encounter info offset for a given map."""
        if wild_table_offset is None or wild_table_offset < 0:
            return None

        return _self.__find_wild_info_offset(
            game_file=game_file,
            wild_table_offset=wild_table_offset,
            bank_id=bank.bank_id,
            map_id=compiled_map.map_id,
        )

    def get_previous_wild_specie(
        _self,
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
        species_values = _self.memory.read_u16_array(game_file, species_field_offset, 1)
        old_species_id = species_values[0] if species_values else 0

        old_pokemon = species_by_id.get(old_species_id)
        old_name = old_pokemon.name if old_pokemon else f"ID#{old_species_id}"

        return (
            f"Slot {slot_idx + 1:02d}: "
            f"{old_name} (#{old_species_id:03d} Nv.{old_min_level}-{old_max_level}) -> "
            f"{new_pokemon.name} (#{new_pokemon.id:03d} | BST:{new_pokemon.bst} Nv.{new_min_level}-{new_max_level})"
        )

    def reset_used_candidates(_self) -> None:
        """Clear used species IDs and names before randomizing a new map's encounter table."""
        _self.wild_used_ids.clear()
        _self.wild_used_names.clear()
    # End Public Methods
    # Private Methods
    def __find_wild_info_offset(
        _self,
        game_file: bytearray,
        wild_table_offset: int,
        bank_id: int,
        map_id: int,
    ) -> int | None:
        """Locate the grass wild encounter info offset for a given bank and map ID."""
        game_size = len(game_file)
        if wild_table_offset < 0 or wild_table_offset + _self.wild_header_struct_size > game_size:
            return None

        max_end_offset = game_size - _self.wild_header_struct_size + 1

        for header_offset in range(wild_table_offset, max_end_offset, _self.wild_header_struct_size):
            entry_bank_id = game_file[header_offset]
            entry_map_id = game_file[header_offset + 1]

            if entry_bank_id == STRING_TERMINATOR and entry_map_id == STRING_TERMINATOR:
                break

            if entry_bank_id == bank_id and entry_map_id == map_id:
                wild_info_entry_offset = header_offset + GBA_PTR_BYTE_SIZE
                wild_info_ptr = game_file[wild_info_entry_offset : wild_info_entry_offset + GBA_PTR_BYTE_SIZE]
                return _self.memory.pointer_to_offset(wild_info_ptr)

        return None
    # End Private Methods
    