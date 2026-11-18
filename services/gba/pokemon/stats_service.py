from operator import attrgetter
from models.gba.pokemon.compiled_base_stats import CompiledBaseStats
from helpers.gba.games_helper import GBA_PTR_BYTE_SIZE
from helpers.gba.pokemon.gba_pokemon_helper import MEGA_EVO_METHODS
from decorators.app_decorators import when_enabled
from services.config_service import ConfigService
from services.log_service import LogService
from services.gba.memory_service import GBAMemoryService

class StatsService:
    def __init__(
        self,
        config_service: ConfigService,
        memory_service: GBAMemoryService,
        log_service: LogService,

        
    ):
        self.config = config_service
        self.memory = memory_service
        self.log = log_service
        self.stats: list[CompiledBaseStats] = []

        self.max_species = self.config.get("MAX_POKEMON_SPECIES")
        self.name_length = self.config.get("POKEMON_NAME_LENGTH")
        self.evos_per_mon = self.config.get("EVOS_PER_MON")       
        self.evo_entry_size = self.config.get("EVO_ENTRY_SIZE")   
        self.include_megas = self.config.get("INCLUDE_MEGA_EVOLUTIONS")

    @when_enabled("BASE_STATS", default=True)
    async def get_all_species_data(self, game_file: bytearray) -> list[CompiledBaseStats]:
        """Read and compile base stats, names, and evolution stages for all Pokémon species."""
        game_size = len(game_file)
        stats_offset = self.config.get("POKEMON_STATS_OFFSET")
        names_offset = self.config.get("POKEMON_NAMES_OFFSET")
        raw_evos_offsets = self.config.get("POKEMON_EVOLUTIONS_OFFSET")
        struct_size = self.config.get("POKEMON_STRUCT_SIZE")

        self.log.raw("=" * 80)
        self.log.info(f"Iniciando lectura de tabla Pokémon desde puntero: {hex(stats_offset)}")
        self.log.raw("=" * 80)

        if (
            stats_offset is None
            or names_offset is None
            or stats_offset + GBA_PTR_BYTE_SIZE > game_size
            or names_offset + GBA_PTR_BYTE_SIZE > game_size
        ):
            self.log.info("No se encontraron offsets válidos para stats, nombres o evoluciones.")
            return []

        stats_table_ptr = game_file[stats_offset : stats_offset + GBA_PTR_BYTE_SIZE]
        names_table_ptr = game_file[names_offset : names_offset + GBA_PTR_BYTE_SIZE]

        stats_table_offset = self.memory.pointer_to_offset(stats_table_ptr)
        names_table_offset = self.memory.pointer_to_offset(names_table_ptr)

        if not isinstance(raw_evos_offsets, list):
            raw_evos_offsets = [raw_evos_offsets]

        evos_table_offsets: list[int] = [
            int(off, 16) if isinstance(off, str) else off
            for off in raw_evos_offsets
            if off is not None
        ]

        if stats_table_offset is None or names_table_offset is None or not evos_table_offsets:
            self.log.info("No se encontraron offsets válidos para stats, nombres o evoluciones.")
            return []

        evos_hex_str = ", ".join(hex(off) for off in evos_table_offsets)
        self.log.info(
            f"Tabla de Stats en: {hex(stats_table_offset)} | "
            f"Tabla de Nombres en: {hex(names_table_offset)} | "
            f"Tablas de Evoluciones en: [{evos_hex_str}]"
        )
        self.log.raw("-" * 80)

        processed: dict[int, CompiledBaseStats] = {}
        for evos_table_offset in evos_table_offsets:
            for species_id in range(self.max_species):
                if species_id in processed:
                    continue

                self._allocate_family_recursive(
                    game_file=game_file,
                    stats_table_offset=stats_table_offset,
                    names_table_offset=names_table_offset,
                    evos_table_offset=evos_table_offset,
                    species_id=species_id,
                    struct_size=struct_size,
                    stage=1,
                    processed=processed,
                )

        self.stats.sort(key=attrgetter("bst"))
        for stat in self.stats:
            self.log.info(
                f"ID #{stat.id:03d} - {stat.name:<10} (Etapa {stat.evolution_stage}) ({stat.offset_hex}) | "
                f"BST:{stat.bst:3d} [HP:{stat.hp:3d} ATK:{stat.attack:3d} DEF:{stat.defense:3d} "
                f"SPD:{stat.speed:3d} SPA:{stat.sp_attack:3d} SPD:{stat.sp_defense:3d}] | "
                f"Tipos: {stat.type_1}/{stat.type_2} | "
                f"Habilidades: {stat.ability_1}/{stat.ability_2} | "
                f"Ratio: {stat.catch_rate}"
            )

    def _allocate_family_recursive(
        self,
        game_file: bytearray,
        stats_table_offset: int,
        names_table_offset: int,
        evos_table_offset: int,
        species_id: int,
        struct_size: int,
        stage: int,
        processed: dict[int, CompiledBaseStats],
        ancestors: set[int] | None = None,
        is_mega: bool = False,
    ) -> None:
        """Recursively traverse evolution branches to assign accurate evolution stages and compile stats."""
        if ancestors is None:
            ancestors = set()

        max_evolution_depth = 5
        # Prevent infinite recursion on form-change loops (A <-> B) or corrupted data
        if species_id in ancestors or stage > max_evolution_depth:
            return

        if species_id in processed:
            existing_pokemon = processed[species_id]
            if is_mega:
                existing_pokemon.is_mega = True

            # Only re-traverse children if we discovered a deeper evolution path to this species
            if stage <= existing_pokemon.evolution_stage:
                return
            existing_pokemon.evolution_stage = stage
        else:
            stats_data = self._allocate_stats_data(
                game_file, stats_table_offset, names_table_offset, species_id, struct_size, stage, is_mega
            )
            if stats_data is None:
                return

            processed[species_id] = stats_data
            self.stats.append(stats_data)

        ancestors.add(species_id)
        try:
            for evo_id, evo_is_mega in self._get_species_evolutions(game_file, evos_table_offset, species_id):
                self._allocate_family_recursive(
                    game_file=game_file,
                    stats_table_offset=stats_table_offset,
                    names_table_offset=names_table_offset,
                    evos_table_offset=evos_table_offset,
                    species_id=evo_id,
                    struct_size=struct_size,
                    stage=stage + 1,
                    processed=processed,
                    ancestors=ancestors,
                    is_mega=evo_is_mega,
                )
        finally:
            ancestors.remove(species_id)

    def _get_species_evolutions(
        self,
        game_file: bytearray,
        evos_table_offset: int,
        species_id: int,
    ) -> list[tuple[int, bool]]:
        """Read evolution methods and target species IDs for a given Pokémon species."""
        game_size = len(game_file)
        block_size = self.evos_per_mon * self.evo_entry_size
        base_offset = evos_table_offset + (species_id * block_size)

        if base_offset < 0 or base_offset + block_size > game_size:
            return []

        # Evolution entry struct (8 bytes): [method: u16, param: u16, target_species: u16, unused: u16]
        target_species_field_offset = 4
        evolutions: list[tuple[int, bool]] = []

        u16_fields_per_entry = 4
        method_idx = 0
        target_species_idx = 2
        for i in range(self.evos_per_mon):
            entry_offset = base_offset + (i * self.evo_entry_size)
            entry_fields = self.memory.read_u16_array(game_file, entry_offset, u16_fields_per_entry)

            if len(entry_fields) < u16_fields_per_entry:
                break

            method = entry_fields[method_idx]
            if method == 0:
                break

            is_mega_evo = method in MEGA_EVO_METHODS
            if not self.include_megas and is_mega_evo:
                continue

            target_species = entry_fields[target_species_idx]
            if 0 < target_species < self.max_species and target_species != species_id:
                evolutions.append((target_species, is_mega_evo))

        return evolutions

    def _allocate_stats_data(
        self,
        game_file: bytearray,
        stats_table_offset: int,
        names_table_offset: int,
        species_id: int,
        struct_size: int,
        evolution_stage: int = 1,
        is_mega: bool = False,
    ) -> CompiledBaseStats | None:
        """Parse base stats and species name from `game_file` into a CompiledBaseStats object."""
        game_size = len(game_file)
        species_struct_offset = stats_table_offset + (species_id * struct_size)

        if species_struct_offset < 0 or species_struct_offset + struct_size > game_size:
            return None

        data = game_file[species_struct_offset : species_struct_offset + struct_size]
        bst = sum(data[0:6])

        if bst == 0:
            return None

        name_string_offset = names_table_offset + (species_id * self.name_length)
        pokemon_name = self.memory.read_string(
            game_file, name_string_offset, max_length=self.name_length, fallback=""
        )

        if pokemon_name in ("", "?", "??????????"):
            return None

        # Bytes 10..15 hold three 16-bit unsigned integers: ev_yield_raw, item_1, item_2
        ev_yield_fields_offset = 10
        ev_yield_fields_count = 3
        u16_values = self.memory.read_u16_array(
            game_file, species_struct_offset + ev_yield_fields_offset, ev_yield_fields_count
        )

        if len(u16_values) < ev_yield_fields_count:
            return None

        ev_yield_raw, item_1, item_2 = u16_values

        return CompiledBaseStats(
            id=species_id,
            name=pokemon_name,
            offset=species_struct_offset,
            hp=data[0],
            attack=data[1],
            defense=data[2],
            speed=data[3],
            sp_attack=data[4],
            sp_defense=data[5],
            bst=bst,
            type_1=data[6],
            type_2=data[7],
            catch_rate=data[8],
            base_exp=data[9],
            ev_yield_raw=ev_yield_raw,
            item_1=item_1,
            item_2=item_2,
            gender_ratio=data[16],
            egg_cycles=data[17],
            base_friendship=data[18],
            growth_rate=data[19],
            egg_group_1=data[20],
            egg_group_2=data[21],
            ability_1=data[22],
            ability_2=data[23],
            safari_zone_flee_rate=data[24],
            body_color_and_flip=data[25],
            evolution_stage=evolution_stage,
            is_mega=is_mega,
        )