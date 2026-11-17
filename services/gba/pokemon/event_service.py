
import random
from operator import attrgetter
from models.gba.pokemon.compiled_bank import CompiledBank
from models.gba.pokemon.compiled_map import CompiledMap
from models.gba.pokemon.compiled_event import CompiledEvent
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from decorators.app_decorators import when_enabled,skip_when_disabled,when_any_enabled
from services.config_service import ConfigService
from services.log_service import LogService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.item_service import ItemService

class EventService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,
        item_service: ItemService,
        translations_service: TranslationsService,
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.items: ItemService = item_service
        self.translator = translations_service

        self.wild_header_struct_size = self.config.get("WILD_HEADER_STRUCT_SIZE")
        self.wild_slot_struct_size = self.config.get("WILD_SLOT_STRUCT_SIZE")
        self.difficulty = self.config.get("CURRENT_DIFFICULTY")

        self._cached_difficulty_pools: list[tuple[int, list[CompiledBaseStats]]] | None = None
        self._randomized_slots_offsets: set[int] = set()

    # Public Methods
    @skip_when_disabled("ONLY_DATABASE")
    @when_any_enabled("RANDOMIZE_POKEBALLS_ITEMS", "MAPS_EVENTS")
    def find_map_events(self, game_file: bytearray, map_data: CompiledMap) -> None:
        events_header_offset = self.memory.pointer_to_offset(game_file, map_data.header_offset + 4)
        event_list_offset = None

        if events_header_offset and events_header_offset < len(game_file):
            map_data.events_count = game_file[events_header_offset]
            event_list_offset = self.memory.pointer_to_offset(game_file, events_header_offset + 4)

        if not event_list_offset:
            return

        self.log.info(self.translator.translate("events.total_events", count=map_data.events_count))
        self.memory.free_space_offset = self.config.get("FREE_SPACE_START")

        for event_idx in range(map_data.events_count):
            event_struct_offset = self.memory.get_struct_offset(event_list_offset, event_idx, 24)

            if event_struct_offset + 20 < len(game_file):
                sprite_id = game_file[event_struct_offset + 1]
                script_ptr_offset = event_struct_offset + 16
                script_offset = self.memory.pointer_to_offset(game_file, script_ptr_offset)

                current_event = CompiledEvent(event_id=event_idx, sprite_id=sprite_id, header_offset=script_offset)
                if self.config.get("RANDOMIZE_POKEBALLS_ITEMS"):
                    self._process_event_with_items(current_event, game_file, script_ptr_offset)

    def select_wild_species(
        self,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        wild_grass_slot_count: int,
        wild_table_offset: int,
        wild_candidates: list[CompiledBaseStats],
        game_file: bytearray,
    ) -> list[CompiledBaseStats]:
        if not wild_table_offset or not wild_candidates:
            return []

        wild_info_offset = self._find_wild_info_offset(
            game_file=game_file,
            wild_table_offset=wild_table_offset,
            bank_id=bank.bank_id,
            map_id=compiled_map.map_id,
        )

        if not wild_info_offset:
            return []

        slots_ptr_offset = wild_info_offset + 4
        slots_list_offset = self.memory.pointer_to_offset(game_file, slots_ptr_offset)
        if not slots_list_offset or slots_list_offset in self._randomized_slots_offsets:
            return []
        
        difficulty_groups = self.difficulty["groups"]

        # if not difficulty, random
        if not difficulty_groups or not isinstance(difficulty_groups, list):
            return [random.choice(wild_candidates) for _ in range(wild_grass_slot_count)]

        # cached difficulty groups
        if self._cached_difficulty_pools is None:
            self._cached_difficulty_pools = self._build_difficulty_pools(difficulty_groups, 
                wild_candidates,min_pool_size=wild_grass_slot_count)

        difficulty_pools = self._cached_difficulty_pools
        selected_species: list[CompiledBaseStats] = []
        used_ids: set[int] = set()
        used_names: set[str] = set()

        for slot_idx in range(wild_grass_slot_count):
            slot_offset = self.memory.get_struct_offset(
                slots_list_offset, slot_idx, self.wild_slot_struct_size
            )
            avg_level = (game_file[slot_offset] + game_file[slot_offset + 1]) / 2

            chosen_pool = difficulty_pools[-1][1]
            for group_max_level, element in difficulty_pools:
                if avg_level <= group_max_level:
                    chosen_pool = element
                    break

            available_elements = [
                sp for sp in chosen_pool
                if sp.id not in used_ids
                and sp.name.strip().lower() not in used_names
            ]
            if not available_elements:
                available_elements = [
                    sp for sp in wild_candidates
                    if sp.id not in used_ids
                    and sp.name.strip().lower() not in used_names
                ]
            if not available_elements:
                available_elements = [sp for sp in chosen_pool if sp.id not in used_ids]
            if not available_elements:
                available_elements = chosen_pool

            chosen_element  = random.choice(available_elements)
            used_ids.add(chosen_element.id)
            used_names.add(chosen_element.name.strip().lower())
            selected_species.append(chosen_element)

        # Ordenar de menor a mayor BST para que los más fuertes caigan en los últimos slots (menor probabilidad)
        selected_species.sort(key=attrgetter("bst"))
        return selected_species

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
        if not wild_table_offset or not selected_species:
            return

        wild_info_offset = self._find_wild_info_offset(
            game_file=game_file,
            wild_table_offset=wild_table_offset,
            bank_id=bank.bank_id,
            map_id=compiled_map.map_id,
        )
        if wild_info_offset:
            self._randomize_wild_slots(
                game_file=game_file,
                wild_info_offset=wild_info_offset,
                wild_grass_slot_count=wild_grass_slot_count,
                bank=bank,
                compiled_map=compiled_map,
                selected_species=selected_species,
                species_by_id=species_by_id
            )
    
    # End Public Methods

    # Private Methods
    def _process_event_with_items(self, event: CompiledEvent, game_file: bytearray, script_ptr_offset: int) -> None:
        if event.sprite_id != self.config.get("POKEBALL_SPRITE_ID"):
            return

        event_has_item = False
        if event.header_offset is not None and 0 <= event.header_offset < len(game_file):
            original_script_bytes = game_file[event.header_offset : event.header_offset + 20]
            event_has_item = 0x1A in original_script_bytes and b"\x09\x01" in original_script_bytes

        if event_has_item:
            new_script_bytes = self.items.randomize_pokeballs(game_file)
            new_script_offset = self.memory.find_free_space_offset(
                len(new_script_bytes), self.memory.free_space_offset, game_file
            )

            if new_script_offset:
                game_file[new_script_offset : new_script_offset + len(new_script_bytes)] = new_script_bytes
                self.memory.free_space_offset = new_script_offset + len(new_script_bytes)
                self.memory.write_pointer(game_file, script_ptr_offset, new_script_offset)
                self.log.info(self.translator.translate("events.new_script", offset=hex(new_script_offset)), False)
            else:
                self.log.warning(self.translator.translate("events.pokeball_failed"))

    def _find_wild_info_offset(
        self,
        game_file: bytearray,
        wild_table_offset: int,
        bank_id: int,
        map_id: int,
    ) -> int | None:
        max_end_offset = len(game_file) - self.wild_header_struct_size + 1

        for header_offset in range(wild_table_offset, max_end_offset, self.wild_header_struct_size):
            entry_bank_id = game_file[header_offset]
            entry_map_id = game_file[header_offset + 1]

            if entry_bank_id == 0xFF and entry_map_id == 0xFF:
                break

            if entry_bank_id == bank_id and entry_map_id == map_id:
                wild_info_ptr_offset = header_offset + 4
                return self.memory.pointer_to_offset(game_file, wild_info_ptr_offset)

        return None

    def _calculate_adjusted_level(_self, original_level: int) -> int:
        level_mode = _self.difficulty["level_mode"]
        quantity = _self.difficulty["level_quantity"]
        min_allowed = _self.difficulty["min_level"]

        match level_mode:
            case "ADD":
                new_level = original_level + quantity
            case "SUBS":
                new_level = original_level - quantity
            case _:
                new_level = original_level

        return max(min_allowed, min(100, new_level))

    def _build_difficulty_pools(
        self,
        difficulty_groups: list[dict],
        wild_candidates: list[CompiledBaseStats],
        min_pool_size: int = 12,
    ) -> list[tuple[int, list[CompiledBaseStats]]]:
        pools: list[tuple[int, list[CompiledBaseStats]]] = []
        prev_max_bst = 0

        for group in difficulty_groups:
            if not isinstance(group, dict):
                continue

            group_max_level = group["max_level"]
            max_bst = group["max_bst"]
            max_stage = group["max_evolution_stage"]

            lower_bst = prev_max_bst
            upper_bst = max_bst
            pool = [
                sp for sp in wild_candidates
                if lower_bst < sp.bst <= upper_bst
                and sp.evolution_stage <= max_stage and not sp.is_mega
            ]

            step = 50
            while len({sp.name.strip().lower() for sp in pool}) < min_pool_size and lower_bst > 0:
                lower_bst = max(0, lower_bst - step)
                upper_bst = upper_bst + step
                pool = [
                    sp for sp in wild_candidates
                    if lower_bst < sp.bst <= upper_bst
                    and sp.evolution_stage <= max_stage and not sp.is_mega
                ]

            if not pool:
                pool = wild_candidates

            pools.append((group_max_level, pool))
            prev_max_bst = max_bst

        return pools

    def _randomize_wild_slots(
        self,
        game_file: bytearray,
        wild_info_offset: int,
        wild_grass_slot_count: int,
        bank: CompiledBank,
        compiled_map: CompiledMap,
        selected_species: list[CompiledBaseStats],
        species_by_id: dict[int, CompiledBaseStats],
    ) -> None:
        slots_ptr_offset = wild_info_offset + 4
        slots_list_offset = self.memory.pointer_to_offset(game_file, slots_ptr_offset)
        if not slots_list_offset or slots_list_offset in self._randomized_slots_offsets:
            return

        self._randomized_slots_offsets.add(slots_list_offset)
        replacements_log: list[str] = []
        for slot_idx, new_pokemon in enumerate(selected_species[:wild_grass_slot_count]):
            slot_offset = self.memory.get_struct_offset(
                slots_list_offset, slot_idx, self.wild_slot_struct_size
            )
            species_field_offset = slot_offset + 2
            new_min_level = self._calculate_adjusted_level(game_file[slot_offset])
            new_max_level = self._calculate_adjusted_level(game_file[slot_offset + 1])

            replacements_log.append(
                self._get_previous_wild_specie(
                    slot_idx, slot_offset, species_field_offset, new_pokemon, new_min_level, new_max_level,  species_by_id, game_file
                )
            )

            game_file[slot_offset] = new_min_level
            game_file[slot_offset + 1] = new_max_level
            game_file[species_field_offset : species_field_offset + 2] = new_pokemon.id.to_bytes(
                2, byteorder="little"
            )

        bank_label = getattr(bank, "name", f"Bank {bank.bank_id}")
        self.log.info(
            f"Pasto randomizado en [{bank.bank_id} - {bank_label}] | Mapa [{compiled_map.map_id} - {compiled_map.name}]:\n  "
            + "\n  ".join(replacements_log),
            False,
        )

    def _get_previous_wild_specie(
        self,
        slot_idx: int,
        slot_offset: int,
        species_field_offset: int,
        new_pokemon: CompiledBaseStats,
        new_min_level: int,
        new_max_level: int,
        species_by_id: dict[int, CompiledBaseStats],
        game_file: bytearray,
    ) -> str:
        old_species_id = self.memory.read_u16(game_file, species_field_offset)
        old_pokemon = species_by_id.get(old_species_id)
        old_name = old_pokemon.name if old_pokemon else f"ID#{old_species_id}"
        old_min_level = game_file[slot_offset]
        old_max_level = game_file[slot_offset + 1]

        return (
            f"Slot {slot_idx + 1:02d}: "
            f"{old_name} (#{old_species_id:03d} Nv.{old_min_level}-{old_max_level}) -> "
            f"{new_pokemon.name} (#{new_pokemon.id:03d} | BST:{new_pokemon.bst} Nv.{new_min_level}-{new_max_level})"
        )
    # End Private Methods